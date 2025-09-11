#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全代币深度数据收集脚本
获取所有交易所的全部支持交易对并收集深度数据
"""

import asyncio
import json
import time
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import pandas as pd

# 导入交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.bybit_collector import BybitCollector
from config.settings import Settings

class AllTokensCollector:
    """全代币数据收集器"""
    
    def __init__(self):
        self.settings = Settings()
        self.results = []
        self.symbol_stats = {}
        
        # 只使用能正常工作的交易所
        self.collectors = {
            'Binance': BinanceCollector(self.settings),
            'Gate': GateCollector(self.settings), 
            'OKX': OKXCollector(self.settings),
            'BingX': BingXCollector(self.settings),
            'Bitunix': BitunixCollector(self.settings),
            'Bybit': BybitCollector(self.settings),
        }
        
        # 常见的合约交易对
        self.common_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
            "SOLUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT",
            "AVAXUSDT", "TRXUSDT", "LINKUSDT", "ATOMUSDT", "UNIUSDT",
            "XLMUSDT", "BCHUSDT", "FILUSDT", "ETCUSDT", "VETUSDT",
            "ICPUSDT", "FTMUSDT", "HBARUSDT", "NEARUSDT", "ALGOUSDT",
            "FLOWUSDT", "EGLDUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT"
        ]
    
    async def get_exchange_symbols(self, exchange_name: str) -> Set[str]:
        """获取单个交易所支持的交易对"""
        symbols = set()
        
        try:
            if exchange_name == "Binance":
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://fapi.binance.com/fapi/v1/exchangeInfo") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for symbol_info in data.get('symbols', []):
                                if symbol_info.get('status') == 'TRADING':
                                    symbols.add(symbol_info['symbol'])
            
            elif exchange_name == "Gate":
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.gateio.ws/api/v4/futures/usdt/contracts") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for contract in data:
                                if not contract.get('expired', True):
                                    symbol = contract['name'].replace('_', 'USDT') if '_' in contract['name'] else contract['name']
                                    symbols.add(symbol)
            
            elif exchange_name == "OKX":
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://www.okx.com/api/v5/public/instruments?instType=SWAP") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('code') == '0':
                                for instrument in data.get('data', []):
                                    if instrument.get('state') == 'live':
                                        symbol = instrument['instId'].replace('-USDT-SWAP', 'USDT')
                                        symbols.add(symbol)
            
            elif exchange_name == "BingX":
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://open-api.bingx.com/openApi/swap/v2/quote/contracts") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('code') == 0:
                                for contract in data.get('data', []):
                                    if contract.get('contractStatus') == 1:
                                        symbols.add(contract['symbol'])
            
            elif exchange_name == "Bybit":
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.bybit.com/v5/market/instruments-info?category=linear") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('retCode') == 0:
                                for instrument in data.get('result', {}).get('list', []):
                                    if instrument.get('status') == 'Trading':
                                        symbols.add(instrument['symbol'])
            
            elif exchange_name == "Bitunix":
                # Bitunix使用与Binance兼容的API
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://fapi.bitunix.com/fapi/v1/exchangeInfo") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for symbol_info in data.get('symbols', []):
                                if symbol_info.get('status') == 'TRADING':
                                    symbols.add(symbol_info['symbol'])
            
            print(f"✅ {exchange_name}: 获取到 {len(symbols)} 个交易对")
            
        except Exception as e:
            print(f"❌ {exchange_name}: 获取交易对失败 - {e}")
            # 如果API失败，使用常见交易对
            symbols = set(self.common_symbols)
            print(f"🔄 {exchange_name}: 使用默认交易对 {len(symbols)} 个")
        
        return symbols
    
    async def collect_exchange_data(self, name: str, collector, symbols: List[str], batch_size: int = 5):
        """收集单个交易所的数据"""
        print(f"\n🚀 开始收集 {name} 数据 - {len(symbols)} 个交易对")
        
        success_count = 0
        failed_count = 0
        
        # 分批处理以避免API限制
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            batch_tasks = []
            
            print(f"📦 处理批次 {i//batch_size + 1} - 交易对: {', '.join(batch_symbols)}")
            
            for symbol in batch_symbols:
                task = asyncio.create_task(self.collect_single_symbol(name, collector, symbol))
                batch_tasks.append(task)
            
            # 等待当前批次完成
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    failed_count += 1
                elif result:
                    success_count += 1
                else:
                    failed_count += 1
            
            # 批次间延迟，避免触发限制
            if i + batch_size < len(symbols):
                await asyncio.sleep(2)
        
        print(f"✅ {name} 收集完成: 成功 {success_count}, 失败 {failed_count}")
    
    async def collect_single_symbol(self, exchange: str, collector, symbol: str):
        """收集单个交易对数据"""
        try:
            depth_data = await collector.get_depth_rest(symbol, limit=10)
            
            if depth_data and depth_data.bids and depth_data.asks:
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'exchange': exchange,
                    'symbol': symbol,
                    'best_bid': depth_data.bids[0][0] if depth_data.bids else 0,
                    'best_ask': depth_data.asks[0][0] if depth_data.asks else 0,
                    'spread': depth_data.spread,
                    'spread_pct': (depth_data.spread / depth_data.bids[0][0] * 100) if depth_data.bids and depth_data.bids[0][0] > 0 else 0,
                    'bid_volume': sum([bid[1] for bid in depth_data.bids]),
                    'ask_volume': sum([ask[1] for ask in depth_data.asks]),
                    'depth_levels': len(depth_data.bids),
                    'status': 'success'
                }
                
                self.results.append(result)
                
                # 更新统计信息
                if symbol not in self.symbol_stats:
                    self.symbol_stats[symbol] = []
                self.symbol_stats[symbol].append({
                    'exchange': exchange,
                    'price': depth_data.bids[0][0] if depth_data.bids else 0,
                    'spread': depth_data.spread,
                    'volume': sum([bid[1] for bid in depth_data.bids])
                })
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"⚠️ {exchange} - {symbol}: {str(e)[:50]}...")
            return False
    
    async def collect_all_data(self):
        """收集所有数据"""
        print("🎯 开始收集所有交易所的全部代币数据...")
        print("=" * 80)
        
        # 首先获取每个交易所的交易对列表
        print("📋 第一阶段: 获取交易对列表")
        exchange_symbols = {}
        
        for name in self.collectors.keys():
            print(f"🔍 获取 {name} 交易对...")
            symbols = await self.get_exchange_symbols(name)
            # 转换为列表并排序
            exchange_symbols[name] = sorted(list(symbols))
        
        print(f"\n📊 交易对统计:")
        for name, symbols in exchange_symbols.items():
            print(f"  {name}: {len(symbols)} 个交易对")
        
        # 获取所有独特的交易对
        all_symbols = set()
        for symbols in exchange_symbols.values():
            all_symbols.update(symbols)
        print(f"  总计独特交易对: {len(all_symbols)} 个")
        
        print("\n" + "=" * 80)
        print("💰 第二阶段: 收集深度数据")
        
        # 收集每个交易所的数据
        collection_tasks = []
        for name, collector in self.collectors.items():
            symbols = exchange_symbols.get(name, [])
            if symbols:
                task = asyncio.create_task(
                    self.collect_exchange_data(name, collector, symbols, batch_size=3)
                )
                collection_tasks.append(task)
        
        # 并行收集所有交易所数据
        await asyncio.gather(*collection_tasks)
        
        print("\n" + "=" * 80)
        print(f"🎉 数据收集完成! 总共收集 {len(self.results)} 条记录")
    
    def analyze_results(self):
        """分析收集结果"""
        if not self.results:
            print("❌ 没有收集到数据")
            return
        
        print("\n📈 数据分析结果:")
        print("=" * 60)
        
        # 按交易所统计
        exchange_stats = {}
        for result in self.results:
            exchange = result['exchange']
            if exchange not in exchange_stats:
                exchange_stats[exchange] = {'count': 0, 'avg_spread': 0, 'symbols': set()}
            
            exchange_stats[exchange]['count'] += 1
            exchange_stats[exchange]['avg_spread'] += result['spread_pct']
            exchange_stats[exchange]['symbols'].add(result['symbol'])
        
        print("🏢 按交易所统计:")
        for exchange, stats in exchange_stats.items():
            avg_spread = stats['avg_spread'] / stats['count'] if stats['count'] > 0 else 0
            print(f"  {exchange}: {stats['count']} 条记录, {len(stats['symbols'])} 个交易对, 平均价差: {avg_spread:.3f}%")
        
        # 热门交易对统计
        symbol_counts = {}
        for result in self.results:
            symbol = result['symbol']
            if symbol not in symbol_counts:
                symbol_counts[symbol] = 0
            symbol_counts[symbol] += 1
        
        print(f"\n🔥 热门交易对 (支持交易所数量 >= 3):")
        popular_symbols = [(symbol, count) for symbol, count in symbol_counts.items() if count >= 3]
        popular_symbols.sort(key=lambda x: x[1], reverse=True)
        
        for symbol, count in popular_symbols[:20]:  # 显示前20个
            print(f"  {symbol}: {count} 个交易所支持")
        
        # 价格差异分析
        print(f"\n💰 价格差异分析 (热门交易对):")
        for symbol, count in popular_symbols[:10]:  # 分析前10个热门交易对
            if symbol in self.symbol_stats:
                prices = [data['price'] for data in self.symbol_stats[symbol] if data['price'] > 0]
                if len(prices) >= 2:
                    min_price = min(prices)
                    max_price = max(prices)
                    price_diff_pct = (max_price - min_price) / min_price * 100
                    print(f"  {symbol}: 最低 ${min_price:.2f} - 最高 ${max_price:.2f} (差异: {price_diff_pct:.2f}%)")
    
    def save_results(self):
        """保存结果"""
        if not self.results:
            print("❌ 没有数据需要保存")
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细数据
        json_file = f"data/all_tokens_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_records': len(self.results),
                    'exchanges': list(self.collectors.keys()),
                    'unique_symbols': len(set(r['symbol'] for r in self.results))
                },
                'data': self.results
            }, f, ensure_ascii=False, indent=2)
        
        # 保存CSV
        csv_file = f"data/all_tokens_data_{timestamp}.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # 保存统计数据
        stats_file = f"data/token_statistics_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.symbol_stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 数据已保存:")
        print(f"  📄 详细数据: {json_file}")
        print(f"  📊 CSV格式: {csv_file}")
        print(f"  📈 统计数据: {stats_file}")

async def main():
    """主函数"""
    collector = AllTokensCollector()
    
    start_time = time.time()
    print("🚀 开始全代币数据收集任务...")
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await collector.collect_all_data()
        collector.analyze_results()
        collector.save_results()
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n⏱️ 总耗时: {duration//60:.0f}分{duration%60:.0f}秒")
        print("✅ 全代币数据收集任务完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
        collector.save_results()
    except Exception as e:
        print(f"\n❌ 任务执行出错: {e}")
        collector.save_results()

if __name__ == "__main__":
    asyncio.run(main())