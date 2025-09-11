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
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        # MEXC使用下划线格式: BTCUSDT -> BTC_USDT
        mexc_symbol = symbol.replace('USDT', '_USDT')
        
        # 使用正确的合约API基础URL和深度端点
        base_url = "https://contract.mexc.com/api/v1/contract"
        depth_url = f"{base_url}/depth/{mexc_symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(depth_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') == True and data.get('code') == 0:
                            depth_info = data.get('data', {})
                            if 'bids' in depth_info and 'asks' in depth_info:
                                return self._parse_mexc_depth_data(symbol, depth_info)
                            else:
                                self.logger.error(f"MEXC深度数据格式错误: {depth_info}")
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
    
    def _parse_mexc_depth_data(self, symbol: str, data: Dict[str, Any]) -> DepthData:
        """解析MEXC特定格式的深度数据"""
        try:
            # MEXC格式: [price, volume, count] 数组
            raw_bids = data.get('bids', [])
            raw_asks = data.get('asks', [])
            
            # 转换为标准格式 [price, volume]
            bids = []
            asks = []
            
            for bid in raw_bids:
                if isinstance(bid, list) and len(bid) >= 2:
                    bids.append([float(bid[0]), float(bid[1])])
            
            for ask in raw_asks:
                if isinstance(ask, list) and len(ask) >= 2:
                    asks.append([float(ask[0]), float(ask[1])])
            
            if not bids or not asks:
                return None
            
            # 计算价差
            spread = asks[0][0] - bids[0][0] if bids and asks else 0.0
            
            # 计算总量
            total_bid_volume = sum(bid[1] for bid in bids)
            total_ask_volume = sum(ask[1] for ask in asks)
            
            return DepthData(
                exchange="mexc",
                symbol=symbol,
                timestamp=time.time(),
                bids=bids,
                asks=asks,
                spread=spread,
                total_bid_volume=total_bid_volume,
                total_ask_volume=total_ask_volume
            )
            
        except Exception as e:
            self.logger.error(f"解析MEXC深度数据失败: {e}")
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
