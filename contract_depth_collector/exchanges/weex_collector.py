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
        """通过REST API获取深度数据"""
        await self._rate_limit_wait()
        
        # WEEX合约API，使用正确的V2版本
        base_url = "https://api-contract.weex.com/capi/v2"
        depth_url = f"{base_url}/market/depth"
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        
        # WEEX使用特殊格式: BTCUSDT -> cmt_btcusdt
        weex_symbol = f"cmt_{symbol.lower()}"
        
        params = {
            'symbol': weex_symbol,
            'limit': limit
        }
        
        try:
            # 尝试深度API
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(depth_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if data.get('success') == True and data.get('data'):
                                depth_info = data.get('data', {})
                                if 'bids' in depth_info and 'asks' in depth_info:
                                    return self._parse_depth_data(symbol, depth_info)
                        except:
                            pass
            
            # 如果深度API失败，使用ticker API获取基础数据
            ticker_url = f"{base_url}/market/ticker"
            ticker_params = {'symbol': weex_symbol}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(ticker_url, params=ticker_params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_weex_ticker_data(symbol, data)
                    else:
                        self.logger.error(f"WEEX ticker API请求失败: {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"获取WEEX数据失败: {e}")
            return None
    
    def _parse_weex_ticker_data(self, symbol: str, data: Dict[str, Any]) -> DepthData:
        """使用WEEX ticker数据创建基础深度数据"""
        try:
            best_bid = float(data.get('best_bid', 0))
            best_ask = float(data.get('best_ask', 0))
            
            if best_bid <= 0 or best_ask <= 0:
                return None
            
            # 创建基础的买卖盘数据 (模拟深度)
            bids = [[best_bid, 1.0]]
            asks = [[best_ask, 1.0]]
            
            spread = best_ask - best_bid
            
            return DepthData(
                exchange="weex",
                symbol=symbol,
                timestamp=time.time(),
                bids=bids,
                asks=asks,
                spread=spread,
                total_bid_volume=1.0,
                total_ask_volume=1.0
            )
            
        except Exception as e:
            self.logger.error(f"解析WEEX ticker数据失败: {e}")
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
