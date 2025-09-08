#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bybit合约深度数据收集器
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import List, Dict, Any, Callable, Optional

from .base_collector import BaseCollector, DepthData

class BybitCollector(BaseCollector):
    """Bybit合约深度数据收集器"""
    
    def __init__(self, settings):
        super().__init__(settings, "bybit")
        # 更新Bybit特定的配置
        self.base_url = "https://api.bybit.com"
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"
    
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/v5/market/orderbook"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'limit': limit
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('retCode') == 0 and 'result' in data:
                            return self._parse_depth_data(symbol, data['result'])
                        else:
                            self.logger.error(f"Bybit API错误: {data.get('retMsg', 'Unknown error')}")
                            return None
                    else:
                        self.logger.error(f"Bybit REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取Bybit深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        ws_url = f"{self.ws_url}"
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"连接Bybit WebSocket: {symbol}")
                
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections[symbol] = websocket
                    
                    # 订阅深度数据
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [f"orderbook.25.{symbol}"]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    self.logger.info(f"Bybit WebSocket连接成功: {symbol}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            depth_data = self._parse_ws_depth_data(symbol, data)
                            if depth_data:
                                callback(depth_data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析Bybit WebSocket消息失败: {e}")
                        except Exception as e:
                            self.logger.error(f"处理Bybit WebSocket数据失败: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"Bybit WebSocket连接关闭: {symbol}")
            except Exception as e:
                self.logger.error(f"Bybit WebSocket连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Bybit WebSocket重试次数超限: {symbol}")
                    break
    
    def _parse_ws_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析Bybit WebSocket深度数据"""
        try:
            if data.get('topic') != f'orderbook.25.{symbol}':
                return None
            
            result = data.get('data', {})
            if not result:
                return None
            
            bids = result.get('b', [])
            asks = result.get('a', [])
            
            if not bids or not asks:
                return None
            
            return self._parse_depth_data(symbol, result)
        except Exception as e:
            self.logger.error(f"解析Bybit WebSocket深度数据失败: {e}")
            return None
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> DepthData:
        """解析Bybit深度数据"""
        bids = data.get('b', [])
        asks = data.get('a', [])
        
        # 计算价差
        spread = 0.0
        if bids and asks:
            spread = float(asks[0][0]) - float(bids[0][0])
        
        # 计算总量
        total_bid_volume = sum(float(bid[1]) for bid in bids)
        total_ask_volume = sum(float(ask[1]) for ask in asks)
        
        return DepthData(
            exchange="bybit",
            symbol=symbol,
            timestamp=time.time(),
            bids=[[float(bid[0]), float(bid[1])] for bid in bids],
            asks=[[float(ask[0]), float(ask[1])] for ask in asks],
            spread=spread,
            total_bid_volume=total_bid_volume,
            total_ask_volume=total_ask_volume
        )
