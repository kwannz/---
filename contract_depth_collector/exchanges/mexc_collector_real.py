#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEXC交易所数据收集器 - 真实数据版本
基于脚本发现，使用正确的API端点
"""

import asyncio
import aiohttp
import websockets
import json
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import time

from .base_collector import BaseCollector, DepthData


class MEXCCollectorReal(BaseCollector):
    """MEXC交易所数据收集器 - 真实数据版本"""
    
    def __init__(self, settings):
        super().__init__(settings, "mexc")
        self.name = "MEXC"
        self.base_url = "https://contract.mexc.com/api/v1/contract"
        self.ws_url = "wss://contract.mexc.com/ws"
        self.timeout = 30
        self.rate_limit = 1.0  # 每秒1个请求
        
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据 - 使用正确的API端点"""
        await self._rate_limit_wait()
        
        # 使用脚本中发现的正确API端点
        mexc_symbol = symbol.replace('USDT', '_USDT')
        url = f"{self.base_url}/depth/{mexc_symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and 'data' in data:
                            depth_data = data['data']
                            if 'asks' in depth_data and 'bids' in depth_data:
                                return self._parse_depth_data(symbol, depth_data)
                            else:
                                self.logger.error(f"MEXC深度数据格式错误")
                                return None
                        else:
                            self.logger.error(f"MEXC API错误: {data.get('msg', 'Unknown error')}")
                            return None
                    else:
                        self.logger.error(f"MEXC REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取MEXC深度数据失败: {e}")
            return None
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析深度数据"""
        try:
            asks = data.get('asks', [])
            bids = data.get('bids', [])
            
            if not asks or not bids:
                return None
            
            # 限制档位数
            asks = asks[:20]
            bids = bids[:20]
            
            # 计算价差
            spread = float(asks[0][0]) - float(bids[0][0]) if asks and bids else 0
            
            return DepthData(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=datetime.now(),
                spread=spread,
                exchange="mexc",
                total_bid_volume=sum([float(bid[1]) for bid in bids]),
                total_ask_volume=sum([float(ask[1]) for ask in asks])
            )
            
        except Exception as e:
            self.logger.error(f"解析MEXC深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器 - 暂时禁用"""
        self.logger.warning("MEXC WebSocket暂时禁用，使用REST API")
        return
