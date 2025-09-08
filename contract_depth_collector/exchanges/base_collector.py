#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础收集器类
"""

import asyncio
import aiohttp
import websockets
import json
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

from utils.logger_config import get_logger

@dataclass
class DepthData:
    """深度数据结构"""
    exchange: str
    symbol: str
    timestamp: float
    bids: List[List[float]]
    asks: List[List[float]]
    spread: float
    total_bid_volume: float
    total_ask_volume: float

class BaseCollector(ABC):
    """基础收集器抽象类"""
    
    def __init__(self, settings, exchange_name: str):
        """初始化收集器"""
        self.settings = settings
        self.exchange_name = exchange_name
        self.logger = get_logger(f"{exchange_name}_collector")
        self.config = settings.get_exchange_config(exchange_name)
        
        self.base_url = self.config.get("base_url", "")
        self.ws_url = self.config.get("ws_url", "")
        self.api_key = self.config.get("api_key", "")
        self.secret_key = self.config.get("secret_key", "")
        self.rate_limit = self.config.get("rate_limit", 600)
        self.timeout = self.config.get("timeout", 30)
        
        # 速率限制
        self.last_request_time = 0
        self.min_interval = 1.0 / (self.rate_limit / 60)
        
        # WebSocket连接
        self.ws_connections = {}
        self.running = False
    
    async def _rate_limit_wait(self):
        """速率限制等待"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    @abstractmethod
    async def get_depth_rest(self, symbol: str, limit: int = 20) -> Optional[DepthData]:
        """通过REST API获取深度数据"""
        pass
    
    @abstractmethod
    async def _websocket_handler(self, symbol: str, callback: Callable[[DepthData], None]):
        """WebSocket处理器"""
        pass
    
    def _parse_depth_data(self, symbol: str, data: Dict[str, Any]) -> DepthData:
        """解析深度数据（子类可重写）"""
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
            exchange=self.exchange_name,
            symbol=symbol,
            timestamp=time.time(),
            bids=[[float(bid[0]), float(bid[1])] for bid in bids],
            asks=[[float(ask[0]), float(ask[1])] for ask in asks],
            spread=spread,
            total_bid_volume=total_bid_volume,
            total_ask_volume=total_ask_volume
        )
    
    async def collect_depth_data(self, symbols: List[str], duration: int, callback: Callable[[DepthData], None]):
        """收集深度数据"""
        self.logger.info(f"开始收集{self.exchange_name}深度数据: {symbols}")
        self.running = True
        
        # 创建WebSocket任务
        ws_tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self._websocket_handler(symbol, callback)
            )
            ws_tasks.append(task)
        
        # 创建REST API任务（作为备用）
        rest_task = asyncio.create_task(
            self._rest_collection_loop(symbols, duration, callback)
        )
        
        # 等待指定时间
        try:
            await asyncio.sleep(duration)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            
            # 取消所有任务
            for task in ws_tasks:
                task.cancel()
            rest_task.cancel()
            
            # 关闭WebSocket连接
            for websocket in self.ws_connections.values():
                await websocket.close()
            
            self.logger.info(f"{self.exchange_name}数据收集完成")
    
    async def _rest_collection_loop(self, symbols: List[str], duration: int, callback: Callable[[DepthData], None]):
        """REST API收集循环（备用方案）"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            for symbol in symbols:
                if not self.running:
                    break
                
                try:
                    depth_data = await self.get_depth_rest(symbol)
                    if depth_data:
                        callback(depth_data)
                except Exception as e:
                    self.logger.error(f"REST收集失败 {symbol}: {e}")
                
                await asyncio.sleep(2)  # 每2秒收集一次
