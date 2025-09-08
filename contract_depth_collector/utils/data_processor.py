#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理工具模块
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class DepthMetrics:
    """深度数据指标"""
    spread: float
    mid_price: float
    bid_volume: float
    ask_volume: float
    volume_imbalance: float
    price_impact: float
    order_book_pressure: float

class DataProcessor:
    """数据处理类"""
    
    def __init__(self):
        """初始化处理器"""
        self.data_buffer = []
        self.metrics_history = []
    
    def process_depth_data(self, depth_data) -> DepthMetrics:
        """
        处理深度数据并计算指标
        
        Args:
            depth_data: 深度数据对象
            
        Returns:
            计算出的指标
        """
        bids = depth_data.bids
        asks = depth_data.asks
        
        if not bids or not asks:
            return None
        
        # 计算基础指标
        best_bid_price = float(bids[0][0])
        best_ask_price = float(asks[0][0])
        spread = best_ask_price - best_bid_price
        mid_price = (best_bid_price + best_ask_price) / 2
        
        # 计算买卖盘总量
        bid_volume = sum(float(bid[1]) for bid in bids)
        ask_volume = sum(float(ask[1]) for ask in asks)
        
        # 计算量价不平衡
        volume_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
        
        # 计算价格冲击（前5档）
        price_impact = self._calculate_price_impact(bids, asks, mid_price)
        
        # 计算订单簿压力
        order_book_pressure = self._calculate_order_book_pressure(bids, asks)
        
        metrics = DepthMetrics(
            spread=spread,
            mid_price=mid_price,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            volume_imbalance=volume_imbalance,
            price_impact=price_impact,
            order_book_pressure=order_book_pressure
        )
        
        # 保存到历史记录
        self.metrics_history.append({
            'timestamp': depth_data.timestamp,
            'exchange': depth_data.exchange,
            'symbol': depth_data.symbol,
            'metrics': metrics
        })
        
        return metrics
    
    def _calculate_price_impact(self, bids: List[List[float]], asks: List[List[float]], mid_price: float) -> float:
        """计算价格冲击"""
        if not bids or not asks:
            return 0.0
        
        # 计算前5档的平均价格冲击
        bid_impact = 0
        ask_impact = 0
        
        for i in range(min(5, len(bids))):
            bid_price = float(bids[i][0])
            bid_impact += abs(bid_price - mid_price) / mid_price
        
        for i in range(min(5, len(asks))):
            ask_price = float(asks[i][0])
            ask_impact += abs(ask_price - mid_price) / mid_price
        
        return (bid_impact + ask_impact) / 10  # 平均冲击
    
    def _calculate_order_book_pressure(self, bids: List[List[float]], asks: List[List[float]]) -> float:
        """计算订单簿压力"""
        if not bids or not asks:
            return 0.0
        
        # 计算买卖盘价格加权压力
        bid_pressure = sum(float(bid[1]) * float(bid[0]) for bid in bids[:10])
        ask_pressure = sum(float(ask[1]) * float(ask[0]) for ask in asks[:10])
        
        total_pressure = bid_pressure + ask_pressure
        if total_pressure == 0:
            return 0.0
        
        return (bid_pressure - ask_pressure) / total_pressure
    
    def calculate_spread_statistics(self, exchange: str, symbol: str) -> Dict[str, float]:
        """计算价差统计信息"""
        relevant_data = [
            item for item in self.metrics_history
            if item['exchange'] == exchange and item['symbol'] == symbol
        ]
        
        if not relevant_data:
            return {}
        
        spreads = [item['metrics'].spread for item in relevant_data]
        
        return {
            'mean_spread': np.mean(spreads),
            'median_spread': np.median(spreads),
            'std_spread': np.std(spreads),
            'min_spread': np.min(spreads),
            'max_spread': np.max(spreads),
            'count': len(spreads)
        }
    
    def calculate_volume_statistics(self, exchange: str, symbol: str) -> Dict[str, float]:
        """计算成交量统计信息"""
        relevant_data = [
            item for item in self.metrics_history
            if item['exchange'] == exchange and item['symbol'] == symbol
        ]
        
        if not relevant_data:
            return {}
        
        bid_volumes = [item['metrics'].bid_volume for item in relevant_data]
        ask_volumes = [item['metrics'].ask_volume for item in relevant_data]
        
        return {
            'mean_bid_volume': np.mean(bid_volumes),
            'mean_ask_volume': np.mean(ask_volumes),
            'total_bid_volume': np.sum(bid_volumes),
            'total_ask_volume': np.sum(ask_volumes),
            'volume_imbalance_mean': np.mean([item['metrics'].volume_imbalance for item in relevant_data]),
            'count': len(relevant_data)
        }
    
    def get_exchange_comparison(self, symbol: str) -> pd.DataFrame:
        """获取交易所对比数据"""
        relevant_data = [
            item for item in self.metrics_history
            if item['symbol'] == symbol
        ]
        
        if not relevant_data:
            return pd.DataFrame()
        
        # 转换为DataFrame
        data = []
        for item in relevant_data:
            metrics = item['metrics']
            data.append({
                'timestamp': datetime.fromtimestamp(item['timestamp']),
                'exchange': item['exchange'],
                'symbol': item['symbol'],
                'spread': metrics.spread,
                'mid_price': metrics.mid_price,
                'bid_volume': metrics.bid_volume,
                'ask_volume': metrics.ask_volume,
                'volume_imbalance': metrics.volume_imbalance,
                'price_impact': metrics.price_impact,
                'order_book_pressure': metrics.order_book_pressure
            })
        
        return pd.DataFrame(data)
    
    def export_analysis_report(self, output_file: str = None) -> str:
        """导出分析报告"""
        if not self.metrics_history:
            return "没有数据可分析"
        
        # 创建分析报告
        report = {
            'summary': {
                'total_records': len(self.metrics_history),
                'exchanges': list(set(item['exchange'] for item in self.metrics_history)),
                'symbols': list(set(item['symbol'] for item in self.metrics_history)),
                'time_range': {
                    'start': min(item['timestamp'] for item in self.metrics_history),
                    'end': max(item['timestamp'] for item in self.metrics_history)
                }
            },
            'exchange_analysis': {},
            'symbol_analysis': {}
        }
        
        # 按交易所分析
        for exchange in report['summary']['exchanges']:
            report['exchange_analysis'][exchange] = {}
            for symbol in report['summary']['symbols']:
                spread_stats = self.calculate_spread_statistics(exchange, symbol)
                volume_stats = self.calculate_volume_statistics(exchange, symbol)
                
                if spread_stats:
                    report['exchange_analysis'][exchange][symbol] = {
                        'spread': spread_stats,
                        'volume': volume_stats
                    }
        
        # 按交易对分析
        for symbol in report['summary']['symbols']:
            symbol_data = [item for item in self.metrics_history if item['symbol'] == symbol]
            if symbol_data:
                spreads = [item['metrics'].spread for item in symbol_data]
                report['symbol_analysis'][symbol] = {
                    'mean_spread': np.mean(spreads),
                    'std_spread': np.std(spreads),
                    'record_count': len(spreads)
                }
        
        # 保存报告
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/analysis_report_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        return f"分析报告已保存到: {output_file}"
    
    def clear_history(self):
        """清空历史数据"""
        self.metrics_history.clear()
        self.data_buffer.clear()
