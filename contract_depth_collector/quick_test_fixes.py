#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试修复后的收集器
"""

import asyncio
from datetime import datetime

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

async def quick_test():
    """快速测试各交易所"""
    
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
    
    # 只测试几个主要代币
    test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    print("🧪 快速测试修复后的收集器")
    print("=" * 50)
    
    total_success = 0
    total_attempts = 0
    
    for symbol in test_symbols:
        print(f"\n💰 测试 {symbol}:")
        
        for exchange, collector in collectors.items():
            total_attempts += 1
            
            try:
                depth_data = await collector.get_depth_rest(symbol, limit=5)
                
                if depth_data and depth_data.bids and depth_data.asks:
                    total_success += 1
                    best_bid = depth_data.bids[0][0]
                    best_ask = depth_data.asks[0][0]
                    mid_price = (best_bid + best_ask) / 2
                    spread_pct = (depth_data.spread / mid_price * 100) if mid_price > 0 else 0
                    print(f"  ✅ {exchange}: ${mid_price:.4f}, 价差 {spread_pct:.3f}%")
                else:
                    print(f"  ❌ {exchange}: 无深度数据")
                    
            except Exception as e:
                print(f"  ⚠️ {exchange}: {str(e)[:40]}...")
            
            await asyncio.sleep(0.2)  # 避免API限制
    
    success_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
    print("\n" + "=" * 50)
    print(f"📈 测试结果: {success_rate:.1f}% ({total_success}/{total_attempts})")
    
    if success_rate >= 90:
        print("🎉 修复成功! 可以运行完整收集!")
    elif success_rate >= 70:
        print("✅ 大部分修复成功，可以继续优化")
    else:
        print("⚠️ 仍有问题需要解决")

if __name__ == "__main__":
    asyncio.run(quick_test())