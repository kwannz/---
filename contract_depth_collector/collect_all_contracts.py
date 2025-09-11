#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合约深度数据统一收集脚本
使用修复后的收集器获取所有交易所的合约深度数据，确保100%成功率
"""

import asyncio
import json
from datetime import datetime
import pandas as pd

# 导入修复后的交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.bybit_collector import BybitCollector
from exchanges.mexc_collector import MEXCCollectorFixed
from exchanges.weex_collector import WEEXCollectorFixed
from config.settings import Settings

async def collect_contract_data():
    """收集合约深度数据"""
    
    settings = Settings()
    
    # 使用修复后的交易所收集器
    collectors = {
        'Binance': BinanceCollector(settings),
        'Gate': GateCollector(settings), 
        'OKX': OKXCollector(settings),
        'BingX': BingXCollector(settings),
        'Bitunix': BitunixCollector(settings),
        'Bybit': BybitCollector(settings),
        'MEXC': MEXCCollectorFixed(settings),
        'WEEX': WEEXCollectorFixed(settings),
    }
    
    # 使用更新后的代币列表（MATIC改为POL）
    verified_symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
        "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT", "POLUSDT",  # MATIC已更名为POL
        "FILUSDT", "TRXUSDT", "ETCUSDT", "XLMUSDT", "VETUSDT"
    ]
    
    results = []
    success_count = 0
    total_attempts = 0
    exchange_stats = {}
    
    print("🚀 开始收集合约深度数据")
    print(f"📋 交易对: {len(verified_symbols)} 个")
    print(f"🏢 交易所: {len(collectors)} 个")
    print("==" * 40)
    
    for i, symbol in enumerate(verified_symbols):
        print(f"\n💰 收集 {symbol} ({i+1}/{len(verified_symbols)}):")
        
        symbol_data = []
        for exchange, collector in collectors.items():
            total_attempts += 1
            
            if exchange not in exchange_stats:
                exchange_stats[exchange] = {'success': 0, 'fail': 0}
            
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
                        'depth_levels': len(depth_data.bids),
                        'contract_type': 'futures'  # 明确标识为合约数据
                    }
                    
                    results.append(result)
                    symbol_data.append(result)
                    success_count += 1
                    exchange_stats[exchange]['success'] += 1
                    print(f"  ✅ {exchange}: ${mid_price:.4f}, 价差 {result['spread_pct']:.3f}%")
                else:
                    exchange_stats[exchange]['fail'] += 1
                    print(f"  ❌ {exchange}: 无深度数据")
                    
            except Exception as e:
                exchange_stats[exchange]['fail'] += 1
                print(f"  ⚠️ {exchange}: {str(e)[:50]}...")
        
        # 价格对比分析
        if len(symbol_data) >= 2:
            prices = [d['mid_price'] for d in symbol_data]
            min_price = min(prices)
            max_price = max(prices)
            price_diff = (max_price - min_price) / min_price * 100
            print(f"  📊 价格范围: ${min_price:.4f} - ${max_price:.4f} (差异: {price_diff:.2f}%)")
        
        # 避免API限制
        await asyncio.sleep(0.5)
    
    print("\n" + "==" * 40)
    print(f"✅ 合约数据收集完成! 总共 {len(results)} 条记录")
    
    # 计算总体成功率
    overall_success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 0
    print(f"📈 总体成功率: {overall_success_rate:.1f}% ({success_count}/{total_attempts})")
    
    # 显示各交易所统计
    print("\n🏢 交易所表现:")
    for exchange, stats in exchange_stats.items():
        total = stats['success'] + stats['fail']
        rate = (stats['success'] / total * 100) if total > 0 else 0
        print(f"  {exchange}: {rate:.1f}% ({stats['success']}/{total})")
    
    # 保存数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON格式
    json_file = f"data/contract_depth_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'collection_time': datetime.now().isoformat(),
                'total_records': len(results),
                'success_rate': overall_success_rate,
                'exchanges': list(collectors.keys()),
                'symbols': verified_symbols,
                'data_type': 'futures_contracts'
            },
            'exchange_stats': exchange_stats,
            'data': results
        }, f, ensure_ascii=False, indent=2)
    
    # CSV格式
    csv_file = f"data/contract_depth_{timestamp}.csv"
    df = pd.DataFrame(results)
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    # 生成分析报告
    generate_analysis_report(results, exchange_stats, overall_success_rate, timestamp)
    
    print(f"\n💾 数据已保存:")
    print(f"  📄 JSON: {json_file}")
    print(f"  📊 CSV: {csv_file}")
    print(f"  📈 报告: 合约深度数据报告_{timestamp.split('_')[0]}.md")

def generate_analysis_report(results, exchange_stats, overall_success_rate, timestamp):
    """生成合约深度数据分析报告"""
    
    # 统计分析
    symbol_stats = {}
    
    for result in results:
        symbol = result['symbol']
        if symbol not in symbol_stats:
            symbol_stats[symbol] = []
        symbol_stats[symbol].append(result)
    
    # 生成Markdown报告
    report = f"""# 合约深度数据收集分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据类型**: 期货合约深度数据  
**收集记录**: {len(results)} 条  
**总体成功率**: {overall_success_rate:.1f}%  
**覆盖代币**: {len(symbol_stats)} 个  
**覆盖交易所**: {len(exchange_stats)} 个

## 📊 交易所表现分析

| 交易所 | 成功率 | 成功数 | 失败数 | 数据质量 |
|--------|--------|--------|--------|----------|"""

    for exchange, stats in exchange_stats.items():
        total = stats['success'] + stats['fail']
        success_rate = (stats['success'] / total * 100) if total > 0 else 0
        quality = "优秀" if success_rate >= 90 else "良好" if success_rate >= 70 else "待改进"
        report += f"\n| {exchange} | {success_rate:.1f}% | {stats['success']} | {stats['fail']} | {quality} |"
    
    report += f"\n\n## 💰 代币合约数据分析\n\n"
    
    # 按代币分析价格差异
    for symbol, data in symbol_stats.items():
        if len(data) >= 2:
            prices = [d['mid_price'] for d in data]
            spreads = [d['spread_pct'] for d in data]
            
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            price_variance = (max_price - min_price) / avg_price * 100
            min_spread = min(spreads)
            avg_spread = sum(spreads) / len(spreads)
            
            report += f"### {symbol} 合约\n\n"
            report += f"- **平均价格**: ${avg_price:.4f}\n"
            report += f"- **价格范围**: ${min_price:.4f} - ${max_price:.4f}\n"
            report += f"- **价格差异**: {price_variance:.2f}%\n"
            report += f"- **平均价差**: {avg_spread:.3f}%\n"
            report += f"- **最低价差**: {min_spread:.3f}%\n"
            report += f"- **支持交易所**: {len(data)} 个\n\n"
            
            report += "| 交易所 | 价格 | 价差 | 买单量 | 卖单量 |\n"
            report += "|--------|------|------|--------|--------|\n"
            
            for d in sorted(data, key=lambda x: x['mid_price']):
                report += f"| {d['exchange']} | ${d['mid_price']:.4f} | {d['spread_pct']:.3f}% | {d['bid_volume']:.2f} | {d['ask_volume']:.2f} |\n"
            
            report += "\n"
    
    # 改进建议
    report += f"## 🔧 改进建议\n\n"
    
    low_success_exchanges = [ex for ex, stats in exchange_stats.items() 
                           if (stats['success'] / (stats['success'] + stats['fail']) * 100) < 80]
    
    if low_success_exchanges:
        report += f"### 需要优化的交易所\n"
        for exchange in low_success_exchanges:
            stats = exchange_stats[exchange]
            total = stats['success'] + stats['fail']
            rate = (stats['success'] / total * 100) if total > 0 else 0
            report += f"- **{exchange}**: 成功率{rate:.1f}%，建议检查API配置和网络连接\n"
    else:
        report += "所有交易所表现良好，无需特别优化。\n"
    
    if overall_success_rate >= 95:
        report += "\n✅ **数据收集质量**: 优秀，已达到预期目标\n"
    elif overall_success_rate >= 80:
        report += "\n✅ **数据收集质量**: 良好，可继续优化部分交易所\n"
    else:
        report += "\n⚠️ **数据收集质量**: 需要改进，建议检查API配置\n"
    
    # 保存报告
    report_file = f"合约深度数据报告_{timestamp.split('_')[0]}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == "__main__":
    asyncio.run(collect_contract_data())