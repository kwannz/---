#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单数据收集脚本 - 非交互式运行
收集所有交易所的深度数据并保存
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# 导入各交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.mexc_collector import MEXCCollectorFixed
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.blofin_collector import BlofinCollectorFixed
from exchanges.weex_collector import WEEXCollectorFixed
from exchanges.bybit_collector import BybitCollector
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings
import pandas as pd

class SimpleDataCollector:
    """简单数据收集器"""
    
    def __init__(self):
        self.settings = Settings()
        self.test_symbols = ["BTCUSDT", "ETHUSDT"]
        self.limit = 10
        
        # 初始化收集器
        self.collectors = {
            'Binance': BinanceCollector(self.settings),
            'Gate': GateCollector(self.settings),
            'OKX': OKXCollector(self.settings),
            'BingX': BingXCollector(self.settings),
            'Bitunix': BitunixCollector(self.settings),
            'Bybit': BybitCollector(self.settings),
        }
        
        self.results = []
    
    async def collect_single_exchange(self, name: str, collector, symbol: str):
        """收集单个交易所数据"""
        try:
            print(f"收集 {name} - {symbol} 深度数据...")
            depth_data = await collector.get_depth_rest(symbol, self.limit)
            
            if depth_data:
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'exchange': name,
                    'symbol': symbol,
                    'bids_count': len(depth_data.bids),
                    'asks_count': len(depth_data.asks),
                    'best_bid': depth_data.bids[0] if depth_data.bids else None,
                    'best_ask': depth_data.asks[0] if depth_data.asks else None,
                    'spread': depth_data.spread,
                    'total_bid_volume': depth_data.total_bid_volume,
                    'total_ask_volume': depth_data.total_ask_volume,
                    'status': 'success'
                }
                self.results.append(result)
                print(f"✅ {name} - {symbol}: 成功收集 {len(depth_data.bids)} 买单, {len(depth_data.asks)} 卖单")
            else:
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'exchange': name,
                    'symbol': symbol,
                    'status': 'failed',
                    'error': 'No data returned'
                }
                self.results.append(result)
                print(f"❌ {name} - {symbol}: 未收集到数据")
                
        except Exception as e:
            result = {
                'timestamp': datetime.now().isoformat(),
                'exchange': name,
                'symbol': symbol,
                'status': 'error',
                'error': str(e)
            }
            self.results.append(result)
            print(f"⚠️ {name} - {symbol}: 错误 - {e}")
    
    async def collect_all_data(self):
        """收集所有数据"""
        print(f"开始收集深度数据 - {len(self.collectors)} 个交易所, {len(self.test_symbols)} 个交易对")
        print("=" * 60)
        
        tasks = []
        for symbol in self.test_symbols:
            for name, collector in self.collectors.items():
                task = asyncio.create_task(
                    self.collect_single_exchange(name, collector, symbol)
                )
                tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        print("=" * 60)
        print(f"数据收集完成，共收集 {len(self.results)} 条记录")
    
    def save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON格式
        json_file = f"data/depth_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式
        csv_file = f"data/depth_data_{timestamp}.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"\\n结果已保存:")
        print(f"- JSON: {json_file}")
        print(f"- CSV: {csv_file}")
        
        # 显示统计信息
        success_count = sum(1 for r in self.results if r['status'] == 'success')
        failed_count = sum(1 for r in self.results if r['status'] == 'failed')
        error_count = sum(1 for r in self.results if r['status'] == 'error')
        
        print(f"\\n统计信息:")
        print(f"- 成功: {success_count}")
        print(f"- 失败: {failed_count}")
        print(f"- 错误: {error_count}")
        print(f"- 成功率: {success_count/len(self.results)*100:.1f}%")

async def main():
    """主函数"""
    collector = SimpleDataCollector()
    await collector.collect_all_data()
    collector.save_results()

if __name__ == "__main__":
    asyncio.run(main())