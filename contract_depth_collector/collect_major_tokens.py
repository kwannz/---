#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主要代币深度数据收集脚本
收集各交易所支持的主要代币深度数据
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List
import pandas as pd

# 导入交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.bybit_collector import BybitCollector
from config.settings import Settings

class MajorTokensCollector:
    """主要代币数据收集器"""
    
    def __init__(self):
        self.settings = Settings()
        self.results = []
        
        # 使用能正常工作的交易所
        self.collectors = {
            'Binance': BinanceCollector(self.settings),
            'Gate': GateCollector(self.settings), 
            'OKX': OKXCollector(self.settings),
            'BingX': BingXCollector(self.settings),
            'Bitunix': BitunixCollector(self.settings),
            'Bybit': BybitCollector(self.settings),
        }
        
        # 主要的合约交易对列表 - 按市值和流动性排序
        self.major_symbols = [
            # 主流币 (市值前10)
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
            "ADAUSDT", "DOGEUSDT", "TRXUSDT", "TONUSDT", "AVAXUSDT",
            
            # 知名DeFi币 (前20)
            "LINKUSDT", "UNIUSDT", "LTCUSDT", "BCHUSDT", "DOTUSDT",
            "MATICUSDT", "ICPUSDT", "NEARUSDT", "ATOMUSDT", "FILUSDT",
            
            # 热门Meme币
            "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT", "WIFUSDT",
            
            # Layer1/Layer2
            "ETCUSDT", "ALGOUSDT", "FTMUSDT", "HBARUSDT", "FLOWUSDT",
            "EGLDUSDT", "APTUSDT", "SUIUSDT", "INJUSDT", "ARKMUSDT",
            
            # GameFi & NFT
            "SANDUSDT", "MANAUSDT", "AXSUSDT", "GALAUSDT", "ENJUSDT",
            
            # 其他热门币种
            "VETUSDT", "XLMUSDT", "XMRUSDT", "KASUSDT", "RENDERUSDT",
            "RUNEUSDT", "OPUSDT", "ARBUSDT", "CRVUSDT", "AAVEUSDT"
        ]
    
    async def collect_symbol_data(self, exchange: str, collector, symbol: str):
        """收集单个交易对数据"""
        try:
            depth_data = await collector.get_depth_rest(symbol, limit=10)
            
            if depth_data and depth_data.bids and depth_data.asks:
                best_bid = depth_data.bids[0][0]
                best_ask = depth_data.asks[0][0]
                mid_price = (best_bid + best_ask) / 2
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'exchange': exchange,
                    'symbol': symbol,
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'mid_price': mid_price,
                    'spread': depth_data.spread,
                    'spread_pct': (depth_data.spread / mid_price * 100) if mid_price > 0 else 0,
                    'bid_volume': sum([bid[1] for bid in depth_data.bids]),
                    'ask_volume': sum([ask[1] for ask in depth_data.asks]),
                    'total_volume': sum([bid[1] for bid in depth_data.bids]) + sum([ask[1] for ask in depth_data.asks]),
                    'depth_levels': len(depth_data.bids),
                    'status': 'success'
                }
                
                self.results.append(result)
                print(f"✅ {exchange} - {symbol}: ${mid_price:.2f}, 价差 {result['spread_pct']:.3f}%")
                return True
            else:
                print(f"❌ {exchange} - {symbol}: 无数据")
                return False
                
        except Exception as e:
            print(f"⚠️ {exchange} - {symbol}: {str(e)[:60]}...")
            return False
    
    async def collect_exchange_data(self, exchange: str, collector, symbols: List[str]):
        """收集单个交易所的数据"""
        print(f"\n🏢 收集 {exchange} 数据 ({len(symbols)} 个交易对):")
        print("-" * 50)
        
        success_count = 0
        total_symbols = len(symbols)
        
        # 分批处理，每批3个，避免API限制
        batch_size = 3
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            tasks = [
                asyncio.create_task(self.collect_symbol_data(exchange, collector, symbol))
                for symbol in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count += sum(1 for result in batch_results if result is True)
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                await asyncio.sleep(1.5)
        
        success_rate = success_count / total_symbols * 100 if total_symbols > 0 else 0
        print(f"📊 {exchange} 完成: {success_count}/{total_symbols} ({success_rate:.1f}% 成功率)")
    
    async def collect_all_data(self):
        """收集所有数据"""
        print("🎯 开始收集主要代币深度数据")
        print(f"📋 目标交易对: {len(self.major_symbols)} 个")
        print(f"🏢 目标交易所: {len(self.collectors)} 个")
        print("=" * 70)
        
        start_time = time.time()
        
        # 串行收集各个交易所数据，避免并发过多触发限制
        for exchange, collector in self.collectors.items():
            await self.collect_exchange_data(exchange, collector, self.major_symbols)
        
        duration = time.time() - start_time
        print(f"\n⏱️ 收集耗时: {duration//60:.0f}分{duration%60:.0f}秒")
        print(f"📈 总收集记录: {len(self.results)} 条")
    
    def generate_summary_report(self):
        """生成汇总报告"""
        if not self.results:
            return "没有收集到数据"
        
        # 按交易所统计
        exchange_stats = {}
        symbol_coverage = {}
        
        for result in self.results:
            exchange = result['exchange']
            symbol = result['symbol']
            
            # 交易所统计
            if exchange not in exchange_stats:
                exchange_stats[exchange] = {
                    'count': 0, 'avg_spread': 0, 'symbols': set(),
                    'total_volume': 0
                }
            
            exchange_stats[exchange]['count'] += 1
            exchange_stats[exchange]['avg_spread'] += result['spread_pct']
            exchange_stats[exchange]['symbols'].add(symbol)
            exchange_stats[exchange]['total_volume'] += result['total_volume']
            
            # 代币覆盖统计
            if symbol not in symbol_coverage:
                symbol_coverage[symbol] = []
            symbol_coverage[symbol].append({
                'exchange': exchange,
                'price': result['mid_price'],
                'spread': result['spread_pct'],
                'volume': result['total_volume']
            })
        
        # 生成报告
        report = f"""
# 主要代币深度数据收集报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**目标交易对**: {len(self.major_symbols)} 个
**成功收集**: {len(self.results)} 条记录

## 📊 交易所表现统计

| 交易所 | 成功数量 | 覆盖率 | 平均价差 | 平均交易量 |
|--------|----------|--------|----------|------------|"""

        for exchange, stats in exchange_stats.items():
            coverage = len(stats['symbols']) / len(self.major_symbols) * 100
            avg_spread = stats['avg_spread'] / stats['count'] if stats['count'] > 0 else 0
            avg_volume = stats['total_volume'] / stats['count'] if stats['count'] > 0 else 0
            
            report += f"\n| {exchange} | {stats['count']} | {coverage:.1f}% | {avg_spread:.3f}% | {avg_volume:.2f} |"
        
        # 代币覆盖情况
        report += f"\n\n## 🪙 代币覆盖情况 (支持的交易所数量)\n"
        
        # 按支持交易所数量排序
        coverage_sorted = sorted(symbol_coverage.items(), 
                               key=lambda x: len(x[1]), reverse=True)
        
        report += "\n| 代币 | 支持交易所数 | 价格范围 | 最低价差 |\n"
        report += "|------|--------------|----------|----------|\n"
        
        for symbol, exchanges in coverage_sorted[:20]:  # 显示前20个
            prices = [e['price'] for e in exchanges if e['price'] > 0]
            spreads = [e['spread'] for e in exchanges]
            
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                price_range = f"${min_price:.2f} - ${max_price:.2f}"
                min_spread = min(spreads) if spreads else 0
                
                report += f"| {symbol} | {len(exchanges)} | {price_range} | {min_spread:.3f}% |\n"
        
        # 热门代币详细分析
        report += f"\n## 🔥 热门代币价格对比 (支持≥4个交易所)\n"
        
        popular_tokens = [(symbol, exchanges) for symbol, exchanges in coverage_sorted 
                         if len(exchanges) >= 4][:10]
        
        for symbol, exchanges in popular_tokens:
            report += f"\n### {symbol}\n"
            report += "| 交易所 | 价格 | 价差 | 交易量 |\n"
            report += "|--------|------|------|---------|\n"
            
            for exchange_data in exchanges:
                report += f"| {exchange_data['exchange']} | ${exchange_data['price']:.2f} | {exchange_data['spread']:.3f}% | {exchange_data['volume']:.2f} |\n"
        
        return report
    
    def save_results(self):
        """保存结果"""
        if not self.results:
            print("❌ 没有数据需要保存")
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细JSON数据
        json_file = f"data/major_tokens_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_records': len(self.results),
                    'exchanges': list(self.collectors.keys()),
                    'target_symbols': self.major_symbols,
                    'unique_symbols_collected': len(set(r['symbol'] for r in self.results))
                },
                'results': self.results
            }, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式
        csv_file = f"data/major_tokens_data_{timestamp}.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # 生成和保存分析报告
        report = self.generate_summary_report()
        report_file = f"主要代币数据收集报告_{timestamp.split('_')[0]}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n💾 结果已保存:")
        print(f"  📄 详细数据: {json_file}")
        print(f"  📊 CSV格式: {csv_file}")
        print(f"  📈 分析报告: {report_file}")
        
        # 显示简要统计
        exchanges_count = len(set(r['exchange'] for r in self.results))
        symbols_count = len(set(r['symbol'] for r in self.results))
        avg_spread = sum(r['spread_pct'] for r in self.results) / len(self.results)
        
        print(f"\n📈 收集统计:")
        print(f"  成功记录: {len(self.results)} 条")
        print(f"  覆盖交易所: {exchanges_count} 个")
        print(f"  覆盖代币: {symbols_count} 个")
        print(f"  平均价差: {avg_spread:.3f}%")

async def main():
    """主函数"""
    collector = MajorTokensCollector()
    
    print("🚀 主要代币深度数据收集任务启动")
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await collector.collect_all_data()
        collector.save_results()
        
        print("\n✅ 主要代币数据收集任务完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
        if collector.results:
            collector.save_results()
    except Exception as e:
        print(f"\n❌ 任务执行出错: {e}")
        if collector.results:
            collector.save_results()

if __name__ == "__main__":
    asyncio.run(main())