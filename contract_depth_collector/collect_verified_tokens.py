#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
已验证代币快速收集脚本
收集已验证能正常工作的交易对数据
"""

import asyncio
import json
from datetime import datetime
import pandas as pd

# 导入交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.bybit_collector import BybitCollector
from config.settings import Settings

async def collect_token_data():
    """收集已验证代币数据"""
    
    settings = Settings()
    
    # 使用已验证可用的交易所
    collectors = {
        'Binance': BinanceCollector(settings),
        'Gate': GateCollector(settings), 
        'OKX': OKXCollector(settings),
        'BingX': BingXCollector(settings),
        'Bitunix': BitunixCollector(settings),
        'Bybit': BybitCollector(settings),
    }
    
    # 已验证在多个交易所都支持的交易对
    verified_symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
        "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT", "POLUSDT",  # MATIC已更名为POL
        "FILUSDT", "TRXUSDT", "ETCUSDT", "XLMUSDT", "VETUSDT"
    ]
    
    results = []
    
    print("🚀 开始收集已验证代币数据")
    print(f"📋 交易对: {len(verified_symbols)} 个")
    print(f"🏢 交易所: {len(collectors)} 个")
    print("=" * 60)
    
    for i, symbol in enumerate(verified_symbols):
        print(f"\n💰 收集 {symbol} ({i+1}/{len(verified_symbols)}):")
        
        symbol_data = []
        for exchange, collector in collectors.items():
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
                        'depth_levels': len(depth_data.bids)
                    }
                    
                    results.append(result)
                    symbol_data.append(result)
                    print(f"  ✅ {exchange}: ${mid_price:.4f}, 价差 {result['spread_pct']:.3f}%")
                else:
                    print(f"  ❌ {exchange}: 无数据")
                    
            except Exception as e:
                print(f"  ⚠️ {exchange}: {str(e)[:40]}...")
        
        # 价格对比分析
        if len(symbol_data) >= 2:
            prices = [d['mid_price'] for d in symbol_data]
            min_price = min(prices)
            max_price = max(prices)
            price_diff = (max_price - min_price) / min_price * 100
            print(f"  📊 价格范围: ${min_price:.4f} - ${max_price:.4f} (差异: {price_diff:.2f}%)")
        
        # 避免API限制
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"✅ 数据收集完成! 总共 {len(results)} 条记录")
    
    # 保存数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON格式
    json_file = f"data/verified_tokens_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'collection_time': datetime.now().isoformat(),
                'total_records': len(results),
                'exchanges': list(collectors.keys()),
                'symbols': verified_symbols
            },
            'data': results
        }, f, ensure_ascii=False, indent=2)
    
    # CSV格式
    csv_file = f"data/verified_tokens_{timestamp}.csv"
    df = pd.DataFrame(results)
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    # 生成分析报告
    generate_analysis_report(results, timestamp)
    
    print(f"\n💾 数据已保存:")
    print(f"  📄 JSON: {json_file}")
    print(f"  📊 CSV: {csv_file}")
    print(f"  📈 报告: 已验证代币分析报告_{timestamp.split('_')[0]}.md")

def generate_analysis_report(results, timestamp):
    """生成分析报告"""
    
    # 统计分析
    exchange_stats = {}
    symbol_stats = {}
    
    for result in results:
        exchange = result['exchange']
        symbol = result['symbol']
        
        # 交易所统计
        if exchange not in exchange_stats:
            exchange_stats[exchange] = {
                'count': 0, 'total_spread': 0, 'symbols': set(),
                'total_volume': 0, 'prices': []
            }
        
        exchange_stats[exchange]['count'] += 1
        exchange_stats[exchange]['total_spread'] += result['spread_pct']
        exchange_stats[exchange]['symbols'].add(symbol)
        exchange_stats[exchange]['total_volume'] += result['bid_volume'] + result['ask_volume']
        exchange_stats[exchange]['prices'].append(result['mid_price'])
        
        # 代币统计
        if symbol not in symbol_stats:
            symbol_stats[symbol] = []
        symbol_stats[symbol].append(result)
    
    # 生成Markdown报告
    report = f"""# 已验证代币深度数据分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据收集**: {len(results)} 条记录  
**覆盖代币**: {len(symbol_stats)} 个  
**覆盖交易所**: {len(exchange_stats)} 个

## 📊 交易所表现分析

| 交易所 | 成功率 | 平均价差 | 平均交易量 | 数据完整性 |
|--------|--------|----------|------------|------------|"""

    for exchange, stats in exchange_stats.items():
        success_rate = len(stats['symbols']) / 20 * 100  # 基于20个测试代币
        avg_spread = stats['total_spread'] / stats['count'] if stats['count'] > 0 else 0
        avg_volume = stats['total_volume'] / stats['count'] if stats['count'] > 0 else 0
        
        report += f"\n| {exchange} | {success_rate:.1f}% | {avg_spread:.3f}% | {avg_volume:.2f} | ✅ 完整 |"
    
    report += f"\n\n## 💰 代币价格分析\n\n"
    
    # 按代币分析价格差异
    for symbol, data in symbol_stats.items():
        if len(data) >= 3:  # 至少3个交易所有数据
            prices = [d['mid_price'] for d in data]
            spreads = [d['spread_pct'] for d in data]
            
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            price_variance = (max_price - min_price) / avg_price * 100
            min_spread = min(spreads)
            
            report += f"### {symbol}\n\n"
            report += f"- **平均价格**: ${avg_price:.4f}\n"
            report += f"- **价格范围**: ${min_price:.4f} - ${max_price:.4f}\n"
            report += f"- **价格差异**: {price_variance:.2f}%\n"
            report += f"- **最低价差**: {min_spread:.3f}%\n"
            report += f"- **支持交易所**: {len(data)} 个\n\n"
            
            report += "| 交易所 | 价格 | 价差 | 买单量 | 卖单量 |\n"
            report += "|--------|------|------|--------|--------|\n"
            
            for d in sorted(data, key=lambda x: x['mid_price']):
                report += f"| {d['exchange']} | ${d['mid_price']:.4f} | {d['spread_pct']:.3f}% | {d['bid_volume']:.2f} | {d['ask_volume']:.2f} |\n"
            
            report += "\n"
    
    # 套利机会分析
    report += f"## 🔄 套利机会分析\n\n"
    
    arbitrage_opportunities = []
    for symbol, data in symbol_stats.items():
        if len(data) >= 2:
            prices = [(d['exchange'], d['mid_price']) for d in data]
            prices.sort(key=lambda x: x[1])
            
            if len(prices) >= 2:
                lowest = prices[0]
                highest = prices[-1]
                profit_pct = (highest[1] - lowest[1]) / lowest[1] * 100
                
                if profit_pct > 0.1:  # 套利机会大于0.1%
                    arbitrage_opportunities.append((symbol, lowest, highest, profit_pct))
    
    # 按套利收益排序
    arbitrage_opportunities.sort(key=lambda x: x[3], reverse=True)
    
    if arbitrage_opportunities:
        report += "| 代币 | 低价交易所 | 高价交易所 | 套利收益 |\n"
        report += "|------|------------|------------|----------|\n"
        
        for symbol, low, high, profit in arbitrage_opportunities[:10]:  # 显示前10个机会
            report += f"| {symbol} | {low[0]} (${low[1]:.4f}) | {high[0]} (${high[1]:.4f}) | {profit:.2f}% |\n"
    else:
        report += "当前市场价格相对统一，暂无明显套利机会。\n"
    
    # 保存报告
    report_file = f"已验证代币分析报告_{timestamp.split('_')[0]}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == "__main__":
    asyncio.run(collect_token_data())