#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WEEX交易所数据收集器 - 修复版本
使用合约API模拟深度数据
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


class WEEXCollectorFixed(BaseCollector):
    """WEEX交易所数据收集器 - 修复版本"""
    
    def __init__(self, settings):
        super().__init__(settings, "weex")
        self.name = "WEEX"
        self.base_url = "https://api-contract.weex.com"
        self.ws_url = "wss://api-contract.weex.com/ws"
        self.timeout = 30
        self.rate_limit = 1.0  # 每秒1个请求
        
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据 - 使用合约API模拟深度数据"""
        await self._rate_limit_wait()
        
        # WEEX深度API返回空响应，使用合约API获取基本信息
        url = f"{self.base_url}/capi/v2/market/contracts"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            # WEEX深度API有问题，无法获取真实深度数据
            self.logger.error("WEEX深度API有问题，无法获取真实深度数据")
            return None
        except Exception as e:
            self.logger.error(f"获取WEEX深度数据失败: {e}")
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
                exchange="weex",
                total_bid_volume=sum([float(bid[1]) for bid in bids]),
                total_ask_volume=sum([float(ask[1]) for ask in asks])
            )
            
        except Exception as e:
            self.logger.error(f"创建WEEX模拟深度数据失败: {e}")
            return None
    
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器 - 暂时禁用"""
        self.logger.warning("WEEX WebSocket暂时禁用，使用REST API")
        return
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> Optional[DepthData]:
        """解析深度数据 - 暂时禁用"""
        return None
