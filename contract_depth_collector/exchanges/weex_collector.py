#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WEEX合约深度数据收集器
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import List, Dict, Any, Callable, Optional

from .base_collector import BaseCollector, DepthData

class WEEXCollector(BaseCollector):
    """WEEX合约深度数据收集器"""
    
    def __init__(self, settings):
        super().__init__(settings, "weex")
        # 更新WEEX特定的配置
        self.base_url = "https://api-contract.weex.com/capi/v2"
        self.ws_url = "wss://api-contract.weex.com/capi/v2/ws"
    
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/market/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        # 尝试解析响应
                        try:
                            data = await response.json()
                            if data.get('code') == 0 and 'data' in data:
                                return self._parse_depth_data(symbol, data['data'])
                            else:
                                self.logger.error(f"WEEX API错误: {data.get('msg', 'Unknown error')}")
                                return None
                        except Exception as json_error:
                            # 如果JSON解析失败，尝试直接解析
                            text_data = await response.text()
                            if text_data:
                                try:
                                    # 尝试直接解析为JSON
                                    data = json.loads(text_data)
                                    if 'bids' in data and 'asks' in data:
                                        return self._parse_depth_data(symbol, data)
                                    else:
                                        self.logger.error(f"WEEX API数据格式错误: {text_data[:200]}")
                                        return None
                                except:
                                    self.logger.error(f"WEEX API返回非JSON格式: {text_data[:200]}")
                                    return None
                            else:
                                self.logger.error(f"WEEX API返回空响应")
                                return None
                    else:
                        self.logger.error(f"WEEX REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取WEEX深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        ws_url = f"{self.ws_url}"
        
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries and self.running:
            try:
                self.logger.info(f"连接WEEX WebSocket: {symbol}")
                
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections[symbol] = websocket
                    
                    # 订阅深度数据
                    subscribe_msg = {
                        "method": "subscribe",
                        "params": [f"{symbol}@depth"],
                        "id": int(time.time())
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    self.logger.info(f"WEEX WebSocket连接成功: {symbol}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            depth_data = self._parse_ws_depth_data(symbol, data)
                            if depth_data:
                                callback(depth_data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"解析WEEX WebSocket消息失败: {e}")
                        except Exception as e:
                            self.logger.error(f"处理WEEX WebSocket数据失败: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(f"WEEX WebSocket连接关闭: {symbol}")
            except Exception as e:
                self.logger.error(f"WEEX WebSocket连接错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"WEEX WebSocket重试次数超限: {symbol}")
                    break
    
    def _parse_ws_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析WEEX WebSocket深度数据"""
        try:
            if 'data' not in data or 'bids' not in data['data'] or 'asks' not in data['data']:
                return None
            
            depth_data = data['data']
            bids = depth_data['bids']
            asks = depth_data['asks']
            
            if not bids or not asks:
                return None
            
            return self._parse_depth_data(symbol, depth_data)
        except Exception as e:
            self.logger.error(f"解析WEEX WebSocket深度数据失败: {e}")
            return None
    
    async def get_contracts(self) -> List[str]:
        """获取WEEX支持的合约列表"""
        await self._rate_limit_wait()
        
        url = f"{self.base_url}/market/contracts"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0 and 'data' in data:
                            contracts = []
                            for contract in data['data']:
                                if contract.get('status') == 1:  # 只获取活跃合约
                                    contracts.append(contract.get('symbol', ''))
                            return contracts
                        else:
                            self.logger.error(f"WEEX获取合约列表失败: {data.get('msg', 'Unknown error')}")
                            return []
                    else:
                        self.logger.error(f"WEEX获取合约列表请求失败: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"获取WEEX合约列表失败: {e}")
            return []
