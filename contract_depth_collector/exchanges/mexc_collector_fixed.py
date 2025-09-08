#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEXC交易所数据收集器 - 修复版本
使用合约详情API模拟深度数据
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


class MEXCCollectorFixed(BaseCollector):
    """MEXC交易所数据收集器 - 修复版本"""
    
    def __init__(self, settings):
        super().__init__(settings, "mexc")
        self.name = "MEXC"
        self.base_url = "https://futures.mexc.com"
        self.ws_url = "wss://futures.mexc.com/ws"
        self.timeout = 30
        self.rate_limit = 1.0  # 每秒1个请求
        
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据 - 使用合约详情API模拟深度数据"""
        await self._rate_limit_wait()
        
        # MEXC深度API需要认证，使用合约详情API获取基本信息
        mexc_symbol = symbol.replace('USDT', '_USDT')
        url = f"{self.base_url}/api/v1/contract/detail"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://futures.mexc.com',
            'Referer': 'https://futures.mexc.com/',
            'Connection': 'keep-alive'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') == True and data.get('code') == 0:
                            # 从合约详情中提取相关信息
                            contracts = data.get('data', [])
                            target_contract = None
                            for contract in contracts:
                                if contract.get('symbol') == mexc_symbol:
                                    target_contract = contract
                                    break
                            
                            if target_contract:
                                # MEXC深度API需要认证，无法获取真实深度数据
                                self.logger.error(f"MEXC深度API需要认证，无法获取真实深度数据")
                                return None
                            else:
                                self.logger.error(f"MEXC未找到交易对: {mexc_symbol}")
                                return None
                        else:
                            self.logger.error(f"MEXC API错误: {data.get('msg', 'Unknown error')}")
                            return None
                    else:
                        self.logger.error(f"MEXC REST API请求失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"MEXC REST API异常: {e}")
            return None
    
    def _create_mock_depth_data(self, symbol: str, contract: Dict[str, Any], limit: int) -> DepthData:
        """基于合约详情创建模拟深度数据"""
        try:
            # 获取价格信息
            price = float(contract.get('lastPrice', 0))
            if price <= 0:
                # 尝试从其他字段获取价格
                price = float(contract.get('price', 0))
            
            if price <= 0:
                # 使用默认价格
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
                exchange="mexc",
                total_bid_volume=sum([float(bid[1]) for bid in bids]),
                total_ask_volume=sum([float(ask[1]) for ask in asks])
            )
            
        except Exception as e:
            self.logger.error(f"创建MEXC模拟深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器 - 暂时禁用"""
        self.logger.warning("MEXC WebSocket暂时禁用，使用REST API")
        return
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析深度数据 - 暂时禁用"""
        return None
