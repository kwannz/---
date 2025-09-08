#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易所合约铺单量数据收集器
支持Binance、MEXC、Gate.io、OKX、BingX、Bitunix、Blofin等主流交易所
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import aiohttp
import websockets
from dataclasses import dataclass
from pathlib import Path

# 导入各交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.mexc_collector import MEXCCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.blofin_collector import BlofinCollector
from utils.data_processor import DataProcessor
from utils.logger_config import setup_logger
from config.settings import Settings

@dataclass
class DepthData:
    """深度数据结构"""
    exchange: str
    symbol: str
    timestamp: float
    bids: List[List[float]]  # [[price, quantity], ...]
    asks: List[List[float]]  # [[price, quantity], ...]
    spread: float
    total_bid_volume: float
    total_ask_volume: float

class ContractDepthCollector:
    """多交易所合约铺单量收集器主类"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """初始化收集器"""
        self.settings = Settings(config_path)
        self.logger = setup_logger("main_collector")
        self.data_processor = DataProcessor()
        
        # 初始化各交易所收集器
        self.collectors = {
            'binance': BinanceCollector(self.settings),
            'mexc': MEXCCollector(self.settings),
            'gate': GateCollector(self.settings),
            'okx': OKXCollector(self.settings),
            'bingx': BingXCollector(self.settings),
            'bitunix': BitunixCollector(self.settings),
            'blofin': BlofinCollector(self.settings)
        }
        
        # 数据存储
        self.depth_data: List[DepthData] = []
        self.running = False
        
    async def collect_depth_data(self, symbols: List[str], duration: int = 3600):
        """
        收集指定交易对的深度数据
        
        Args:
            symbols: 交易对列表，如 ['BTCUSDT', 'ETHUSDT']
            duration: 收集持续时间（秒），默认1小时
        """
        self.logger.info(f"开始收集深度数据，交易对: {symbols}，持续时间: {duration}秒")
        self.running = True
        start_time = time.time()
        
        # 创建收集任务
        tasks = []
        for exchange_name, collector in self.collectors.items():
            if self.settings.is_exchange_enabled(exchange_name):
                task = asyncio.create_task(
                    self._collect_exchange_data(exchange_name, collector, symbols, duration)
                )
                tasks.append(task)
        
        # 等待所有任务完成
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"收集过程中出现错误: {e}")
        finally:
            self.running = False
            self.logger.info("深度数据收集完成")
    
    async def _collect_exchange_data(self, exchange_name: str, collector, symbols: List[str], duration: int):
        """收集单个交易所的数据"""
        try:
            self.logger.info(f"开始收集 {exchange_name} 的数据")
            await collector.collect_depth_data(symbols, duration, self._on_depth_data)
        except Exception as e:
            self.logger.error(f"收集 {exchange_name} 数据时出错: {e}")
    
    def _on_depth_data(self, data: DepthData):
        """处理接收到的深度数据"""
        self.depth_data.append(data)
        
        # 实时处理数据
        self.data_processor.process_depth_data(data)
        
        # 定期保存数据
        if len(self.depth_data) % 100 == 0:
            self._save_data()
    
    def _save_data(self):
        """保存数据到文件"""
        if not self.depth_data:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/depth_data_{timestamp}.json"
        
        # 转换为可序列化的格式
        data_to_save = []
        for data in self.depth_data:
            data_to_save.append({
                'exchange': data.exchange,
                'symbol': data.symbol,
                'timestamp': data.timestamp,
                'bids': data.bids,
                'asks': data.asks,
                'spread': data.spread,
                'total_bid_volume': data.total_bid_volume,
                'total_ask_volume': data.total_ask_volume
            })
        
        # 保存为JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        # 保存为CSV
        csv_filename = f"data/depth_data_{timestamp}.csv"
        df = self._convert_to_dataframe()
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        self.logger.info(f"数据已保存到 {filename} 和 {csv_filename}")
    
    def _convert_to_dataframe(self) -> pd.DataFrame:
        """将深度数据转换为DataFrame"""
        data = []
        for depth in self.depth_data:
            data.append({
                'exchange': depth.exchange,
                'symbol': depth.symbol,
                'timestamp': datetime.fromtimestamp(depth.timestamp),
                'spread': depth.spread,
                'total_bid_volume': depth.total_bid_volume,
                'total_ask_volume': depth.total_ask_volume,
                'bid_count': len(depth.bids),
                'ask_count': len(depth.asks)
            })
        return pd.DataFrame(data)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """获取汇总统计信息"""
        if not self.depth_data:
            return {}
        
        df = self._convert_to_dataframe()
        
        stats = {
            'total_records': len(df),
            'exchanges': df['exchange'].unique().tolist(),
            'symbols': df['symbol'].unique().tolist(),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            },
            'avg_spread_by_exchange': df.groupby('exchange')['spread'].mean().to_dict(),
            'avg_volume_by_exchange': df.groupby('exchange')[['total_bid_volume', 'total_ask_volume']].mean().to_dict()
        }
        
        return stats
    
    async def start_continuous_collection(self, symbols: List[str]):
        """开始持续收集数据"""
        self.logger.info(f"开始持续收集数据，交易对: {symbols}")
        
        while self.running:
            try:
                await self.collect_depth_data(symbols, duration=300)  # 每5分钟收集一次
                await asyncio.sleep(60)  # 休息1分钟
            except KeyboardInterrupt:
                self.logger.info("收到停止信号，正在停止收集...")
                break
            except Exception as e:
                self.logger.error(f"持续收集中出现错误: {e}")
                await asyncio.sleep(30)  # 出错后等待30秒再重试

async def main():
    """主函数"""
    # 创建收集器
    collector = ContractDepthCollector()
    
    # 默认交易对
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
    
    print("=== 多交易所合约铺单量数据收集器 ===")
    print("支持的交易所: Binance, MEXC, Gate.io, OKX, BingX, Bitunix, Blofin")
    print(f"目标交易对: {', '.join(symbols)}")
    print("\n选择运行模式:")
    print("1. 单次收集 (1小时)")
    print("2. 持续收集")
    print("3. 自定义收集")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            await collector.collect_depth_data(symbols, duration=3600)
        elif choice == "2":
            collector.running = True
            await collector.start_continuous_collection(symbols)
        elif choice == "3":
            custom_symbols = input("请输入交易对 (用逗号分隔): ").strip().split(',')
            custom_symbols = [s.strip().upper() for s in custom_symbols if s.strip()]
            duration = int(input("请输入收集时长 (秒): ") or "3600")
            await collector.collect_depth_data(custom_symbols, duration)
        else:
            print("无效选择，使用默认模式")
            await collector.collect_depth_data(symbols, duration=3600)
        
        # 显示统计信息
        stats = collector.get_summary_statistics()
        print("\n=== 收集统计 ===")
        print(f"总记录数: {stats.get('total_records', 0)}")
        print(f"交易所: {', '.join(stats.get('exchanges', []))}")
        print(f"交易对: {', '.join(stats.get('symbols', []))}")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        collector.running = False
        print("程序结束")

if __name__ == "__main__":
    asyncio.run(main())
