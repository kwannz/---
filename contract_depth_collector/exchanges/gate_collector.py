#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate.io合约深度数据收集器
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import List, Dict, Any, Callable, Optional

from .base_collector import BaseCollector, DepthData

class GateCollector(BaseCollector):
    """Gate.io合约深度数据收集器"""
    
    def __init__(self, settings):
        super().__init__(settings, "gate")
    
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/api/v4/futures/usdt/order_book"
        params = {
            'contract': symbol,
            'limit': limit,
            'interval': '0ms'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('id'):
                            return self._parse_depth_data(symbol, data)
                        else:
                            self.logger.error(f"Gate.io API错误: {data}")
                            return None
                    else:
                        self.logger.error(f"Gate.io REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取Gate.io深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        channel = f"futures.order_book"
        ws_url = f"{self.ws_url}"
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"连接Gate.io WebSocket: {channel}")
                
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections[symbol] = websocket
                    
                    # 订阅深度数据
                    subscribe_msg = {
                        "time": int(time.time()),
                        "channel": channel,
                        "event": "subscribe",
                        "payload": [symbol, "20", "0ms"]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    self.logger.info(f"Gate.io WebSocket连接成功: {symbol}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            depth_data = self._parse_ws_depth_data(symbol, data)
                            if depth_data:
                                callback(depth_data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析Gate.io WebSocket消息失败: {e}")
                        except Exception as e:
                            self.logger.error(f"处理Gate.io WebSocket数据失败: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"Gate.io WebSocket连接关闭: {symbol}")
            except Exception as e:
                self.logger.error(f"Gate.io WebSocket连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Gate.io WebSocket重试次数超限: {symbol}")
                    break
    
    def _parse_ws_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析Gate.io WebSocket深度数据"""
        try:
            if data.get('channel') != 'futures.order_book':
                return None
            
            result = data.get('result', {})
            if not result:
                return None
            
            bids = result.get('bids', [])
            asks = result.get('asks', [])
            
            if not bids or not asks:
                return None
            
            return self._parse_depth_data(symbol, result)
        except Exception as e:
            self.logger.error(f"解析Gate.io WebSocket深度数据失败: {e}")
            return None
