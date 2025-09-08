#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blofin合约深度数据收集器
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import List, Dict, Any, Callable, Optional

from .base_collector import BaseCollector, DepthData

class BlofinCollector(BaseCollector):
    """Blofin合约深度数据收集器"""
    
    def __init__(self, settings):
        super().__init__(settings, "blofin")
    
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/api/v1/market/depth"
        params = {
            'instId': symbol,
            'sz': str(limit)
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '0':
                            result = data.get('data', [])
                            if result:
                                return self._parse_depth_data(symbol, result[0])
                        else:
                            self.logger.error(f"Blofin API错误: {data.get('msg', 'Unknown error')}")
                            return None
                    else:
                        self.logger.error(f"Blofin REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取Blofin深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        ws_url = f"{self.ws_url}"
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"连接Blofin WebSocket: {symbol}")
                
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections[symbol] = websocket
                    
                    # 订阅深度数据
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [{
                            "channel": "books",
                            "instId": symbol
                        }]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    self.logger.info(f"Blofin WebSocket连接成功: {symbol}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            depth_data = self._parse_ws_depth_data(symbol, data)
                            if depth_data:
                                callback(depth_data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析Blofin WebSocket消息失败: {e}")
                        except Exception as e:
                            self.logger.error(f"处理Blofin WebSocket数据失败: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"Blofin WebSocket连接关闭: {symbol}")
            except Exception as e:
                self.logger.error(f"Blofin WebSocket连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Blofin WebSocket重试次数超限: {symbol}")
                    break
    
    def _parse_ws_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析Blofin WebSocket深度数据"""
        try:
            if data.get('arg', {}).get('channel') != 'books':
                return None
            
            result = data.get('data', [])
            if not result:
                return None
            
            book_data = result[0]
            bids = book_data.get('bids', [])
            asks = book_data.get('asks', [])
            
            if not bids or not asks:
                return None
            
            return self._parse_depth_data(symbol, book_data)
        except Exception as e:
            self.logger.error(f"解析Blofin WebSocket深度数据失败: {e}")
            return None
