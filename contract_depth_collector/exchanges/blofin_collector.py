#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blofin交易所数据收集器 - 修复版本
使用合约信息API模拟深度数据
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


class BlofinCollectorFixed(BaseCollector):
    """Blofin交易所数据收集器 - 修复版本"""
    
    def __init__(self, settings):
        super().__init__(settings, "blofin")
        self.name = "Blofin"
        self.base_url = "https://blofin.com"
        self.ws_url = "wss://open-api-ws.blofin.com/public"
        self.timeout = 30
        self.rate_limit = 1.0  # 每秒1个请求
        
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据 - 使用合约信息API模拟深度数据"""
        await self._rate_limit_wait()
        
        # Blofin深度API返回404，使用合约信息API获取基本信息
        url = f"{self.base_url}/uapi/v1/basic/contract/info"
        params = {
            'symbol': symbol.replace('USDT', '-USDT')
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 200:
                            # 从合约信息中提取相关信息
                            contract_info = data.get('data', {})
                            if contract_info:
                                # Blofin深度API有问题，无法获取真实深度数据
                                self.logger.error(f"Blofin深度API有问题，无法获取真实深度数据")
                                return None
                            else:
                                self.logger.error(f"Blofin未找到交易对信息: {symbol}")
                                return None
                        else:
                            self.logger.error(f"Blofin API错误: {data.get('msg', 'Unknown error')}")
                            return None
                    else:
                        self.logger.error(f"Blofin REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取Blofin深度数据失败: {e}")
            return None
    
    def _create_mock_depth_data(self, symbol: str, contract_info: Dict[str, Any], limit: int) -> DepthData:
        """基于合约信息创建模拟深度数据"""
        try:
            # 获取价格信息 - 使用默认价格
            price = 50000.0 if 'BTC' in symbol else 3000.0
            
            # 创建模拟的买卖盘数据
            bids = []
            asks = []
            
            # 生成模拟的买卖盘数据
            for i in range(limit):
                # 买盘价格递减
                bid_price = price * (1 - (i + 1) * 0.001)
                bid_quantity = 1.0 + i * 0.5
                bids.append([bid_price, bid_quantity])
                
                # 卖盘价格递增
                ask_price = price * (1 + (i + 1) * 0.001)
                ask_quantity = 1.0 + i * 0.3
                asks.append([ask_price, ask_quantity])
            
            # 计算价差
            spread = asks[0][0] - bids[0][0] if bids and asks else 0
            
            return DepthData(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=datetime.now(),
                spread=spread,
                exchange="blofin",
                total_bid_volume=sum([float(bid[1]) for bid in bids]),
                total_ask_volume=sum([float(ask[1]) for ask in asks])
            )
            
        except Exception as e:
            self.logger.error(f"创建Blofin模拟深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器 - 暂时禁用"""
        self.logger.warning("Blofin WebSocket暂时禁用，使用REST API")
        return
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析深度数据 - 暂时禁用"""
        return None
