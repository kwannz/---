#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance合约深度数据收集器
支持REST API和WebSocket实时数据收集
"""

import asyncio
import aiohttp
import websockets
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import logging

from utils.logger_config import get_logger

@dataclass
class DepthData:
    """深度数据结构"""
    exchange: str
    symbol: str
    timestamp: float
    bids: List[List[float]]
    asks: List[List[float]]
    spread: float
    total_bid_volume: float
    total_ask_volume: float

class BinanceCollector:
    """Binance合约深度数据收集器"""
    
    def __init__(self, settings):
        """初始化收集器"""
        self.settings = settings
        self.logger = get_logger("binance_collector")
        self.config = settings.get_exchange_config("binance")
        
        self.base_url = self.config.get("base_url", "https://fapi.binance.com")
        self.ws_url = self.config.get("ws_url", "wss://fstream.binance.com/ws")
        self.api_key = self.config.get("api_key", "")
        self.secret_key = self.config.get("secret_key", "")
        self.rate_limit = self.config.get("rate_limit", 1200)
        self.timeout = self.config.get("timeout", 30)
        
        # 速率限制 - 更保守的设置
        self.last_request_time = 0
        self.min_interval = 5.0  # 最少5秒间隔，避免被限制
        
        # WebSocket连接
        self.ws_connections = {}
        self.running = False
    
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """生成API签名"""
        if not self.secret_key:
            return ""
        
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _rate_limit_wait(self):
        """速率限制等待"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """
        通过REST API获取深度数据
        
        Args:
            symbol: 交易对符号
            limit: 深度级别数量
            
        Returns:
            深度数据对象
        """
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/fapi/v1/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_depth_data(symbol, data)
                    else:
                        self.logger.error(f"REST API请求失败: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            self.logger.error(f"获取REST深度数据失败: {e}")
            return None
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> DepthData:
        """解析深度数据"""
        bids = [[float(bid[0]), float(bid[1])] for bid in data.get('bids', [])]
        asks = [[float(ask[0]), float(ask[1])] for ask in data.get('asks', [])]
        
        # 计算价差
        spread = 0.0
        if bids and asks:
            spread = asks[0][0] - bids[0][0]
        
        # 计算总量
        total_bid_volume = sum(bid[1] for bid in bids)
        total_ask_volume = sum(ask[1] for ask in asks)
        
        return DepthData(
            exchange="binance",
            symbol=symbol,
            timestamp=time.time(),
            bids=bids,
            asks=asks,
            spread=spread,
            total_bid_volume=total_bid_volume,
            total_ask_volume=total_ask_volume
        )
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        stream_name = f"{symbol.lower()}@depth@100ms"
        ws_url = f"{self.ws_url}/{stream_name}"
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"连接Binance WebSocket: {stream_name}")
                
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections[symbol] = websocket
                    self.logger.info(f"WebSocket连接成功: {symbol}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            depth_data = self._parse_ws_depth_data(symbol, data)
                            if depth_data:
                                callback(depth_data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析WebSocket消息失败: {e}")
                        except Exception as e:
                            self.logger.error(f"处理WebSocket数据失败: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"WebSocket连接关闭: {symbol}")
            except Exception as e:
                self.logger.error(f"WebSocket连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"WebSocket重试次数超限: {symbol}")
                    break
    
    def _parse_ws_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析WebSocket深度数据"""
        try:
            if 'b' not in data or 'a' not in data:
                return None
            
            bids = [[float(bid[0]), float(bid[1])] for bid in data['b'] if float(bid[1]) > 0]
            asks = [[float(ask[0]), float(ask[1])] for ask in data['a'] if float(ask[1]) > 0]
            
            if not bids or not asks:
                return None
            
            # 计算价差
            spread = asks[0][0] - bids[0][0]
            
            # 计算总量
            total_bid_volume = sum(bid[1] for bid in bids)
            total_ask_volume = sum(ask[1] for ask in asks)
            
            return DepthData(
                exchange="binance",
                symbol=symbol,
                timestamp=time.time(),
                bids=bids,
                asks=asks,
                spread=spread,
                total_bid_volume=total_bid_volume,
                total_ask_volume=total_ask_volume
            )
        except Exception as e:
            self.logger.error(f"解析WebSocket深度数据失败: {e}")
            return None
    
    async def collect_depth_data(self, symbols: List[str], duration: int, callback: Callable[[DepthData], None]):
        """
        收集深度数据
        
        Args:
            symbols: 交易对列表
            duration: 收集持续时间（秒）
            callback: 数据回调函数
        """
        self.logger.info(f"开始收集Binance深度数据: {symbols}")
        self.running = True
        
        # 创建WebSocket任务
        ws_tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self._websocket_handler(symbol, callback)
            )
            ws_tasks.append(task)
        
        # 创建REST API任务（作为备用）
        rest_task = asyncio.create_task(
            self._rest_collection_loop(symbols, duration, callback)
        )
        
        # 等待指定时间
        try:
            await asyncio.sleep(duration)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            
            # 取消所有任务
            for task in ws_tasks:
                task.cancel()
            rest_task.cancel()
            
            # 关闭WebSocket连接
            for websocket in self.ws_connections.values():
                await websocket.close()
            
            self.logger.info("Binance数据收集完成")
    
    async def _rest_collection_loop(self, symbols: List[str], duration: int, callback: Callable[[DepthData], None]):
        """REST API收集循环（备用方案）"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            for symbol in symbols:
                if not self.running:
                    break
                
                try:
                    depth_data = await self.get_depth_rest(symbol)
                    if depth_data:
                        callback(depth_data)
                except Exception as e:
                    self.logger.error(f"REST收集失败 {symbol}: {e}")
                
                await asyncio.sleep(1)  # 每秒收集一次
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/fapi/v1/exchangeInfo"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"获取交易所信息失败: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"获取交易所信息异常: {e}")
            return {}
    
    async def get_24hr_ticker(self, symbol: str = None) -> Dict[str, Any]:
        """获取24小时价格变动统计"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/fapi/v1/ticker/24hr"
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"获取24hr数据失败: {response.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"获取24hr数据异常: {e}")
            return {}
