#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KuCoin合约深度数据收集器
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import List, Dict, Any, Callable, Optional

from .base_collector import BaseCollector, DepthData

class KuCoinCollector(BaseCollector):
    """KuCoin合约深度数据收集器"""
    
    def __init__(self, settings):
        super().__init__(settings, "kucoin")
        # 更新KuCoin特定的配置
        self.base_url = "https://api-futures.kucoin.com"
        self.ws_url = "wss://api-futures.kucoin.com/endpoint"
    
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        # KuCoin需要特定的交易对格式
        kucoin_symbol = symbol.replace('USDT', 'USDTM')
        url = f"{self.base_url}/api/v1/level2/snapshot"
        params = {
            'symbol': kucoin_symbol,
            'level': limit
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '200000' and 'data' in data:
                            return self._parse_depth_data(symbol, data['data'])
                        else:
                            self.logger.error(f"KuCoin API错误: {data.get('msg', 'Unknown error')}")
                            return None
                    else:
                        self.logger.error(f"KuCoin REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取KuCoin深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        ws_url = f"{self.ws_url}"
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"连接KuCoin WebSocket: {symbol}")
                
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections[symbol] = websocket
                    
                    # 订阅深度数据
                    subscribe_msg = {
                        "id": int(time.time()),
                        "type": "subscribe",
                        "topic": f"/market/level2:{symbol}",
                        "response": True
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    self.logger.info(f"KuCoin WebSocket连接成功: {symbol}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            depth_data = self._parse_ws_depth_data(symbol, data)
                            if depth_data:
                                callback(depth_data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析KuCoin WebSocket消息失败: {e}")
                        except Exception as e:
                            self.logger.error(f"处理KuCoin WebSocket数据失败: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"KuCoin WebSocket连接关闭: {symbol}")
            except Exception as e:
                self.logger.error(f"KuCoin WebSocket连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"KuCoin WebSocket重试次数超限: {symbol}")
                    break
    
    def _parse_ws_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析KuCoin WebSocket深度数据"""
        try:
            if data.get('type') != 'message':
                return None
            
            topic = data.get('topic', '')
            if not topic.endswith(f':{symbol}'):
                return None
            
            result = data.get('data', {})
            if not result:
                return None
            
            bids = result.get('bids', [])
            asks = result.get('asks', [])
            
            if not bids or not asks:
                return None
            
            return self._parse_depth_data(symbol, result)
        except Exception as e:
            self.logger.error(f"解析KuCoin WebSocket深度数据失败: {e}")
            return None
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> DepthData:
        """解析KuCoin深度数据"""
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        # 计算价差
        spread = 0.0
        if bids and asks:
            spread = float(asks[0][0]) - float(bids[0][0])
        
        # 计算总量
        total_bid_volume = sum(float(bid[1]) for bid in bids)
        total_ask_volume = sum(float(ask[1]) for ask in asks)
        
        return DepthData(
            exchange="kucoin",
            symbol=symbol,
            timestamp=time.time(),
            bids=[[float(bid[0]), float(bid[1])] for bid in bids],
            asks=[[float(ask[0]), float(ask[1])] for ask in asks],
            spread=spread,
            total_bid_volume=total_bid_volume,
            total_ask_volume=total_ask_volume
        )
