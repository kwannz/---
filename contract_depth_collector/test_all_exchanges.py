#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有交易所API的简化脚本
只收集2个交易对，每个交易对2档深度数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from exchanges.binance_collector import BinanceCollector
from exchanges.mexc_collector import MEXCCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.blofin_collector import BlofinCollector
from exchanges.weex_collector import WEEXCollector
from exchanges.bybit_collector import BybitCollector
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings

async def test_exchange_collector(collector, exchange_name, symbols):
    """测试单个交易所收集器"""
    print(f"\n=== 测试 {exchange_name} ===")
    
    success_count = 0
    total_count = len(symbols)
    
    for symbol in symbols:
        try:
            print(f"  测试 {symbol}...")
            depth_data = await collector.get_depth_rest(symbol, limit=20)
            
            if depth_data:
                print(f"    ✅ 成功获取 {symbol} 数据")
                print(f"    价差: {depth_data.spread}")
                print(f"    买盘档位: {len(depth_data.bids)}")
                print(f"    卖盘档位: {len(depth_data.asks)}")
                print(f"    买盘总量: {depth_data.total_bid_volume}")
                print(f"    卖盘总量: {depth_data.total_ask_volume}")
                success_count += 1
            else:
                print(f"    ❌ 获取 {symbol} 数据失败")
                
        except Exception as e:
            print(f"    ❌ 测试 {symbol} 时出错: {e}")
    
    print(f"  📊 {exchange_name} 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

async def main():
    """主测试函数"""
    print("=== 多交易所API测试脚本 ===")
    print("只收集2个交易对，每个交易对2档深度数据")
    
    # 初始化设置
    settings = Settings()
    symbols = ["BTCUSDT", "ETHUSDT"]
    
    # 初始化所有收集器
    collectors = {
        'Binance': BinanceCollector(settings),
        'MEXC': MEXCCollector(settings),
        'Gate.io': GateCollector(settings),
        'OKX': OKXCollector(settings),
        'BingX': BingXCollector(settings),
        'Bitunix': BitunixCollector(settings),
        'Blofin': BlofinCollector(settings),
        'WEEX': WEEXCollector(settings),
        'Bybit': BybitCollector(settings),
        'KuCoin': KuCoinCollector(settings)
    }
    
    total_success = 0
    total_tests = 0
    
    # 测试所有交易所
    for exchange_name, collector in collectors.items():
        try:
            success, total = await test_exchange_collector(collector, exchange_name, symbols)
            total_success += success
            total_tests += total
        except Exception as e:
            print(f"❌ 测试 {exchange_name} 时出现严重错误: {e}")
    
    # 输出总结
    print(f"\n=== 测试总结 ===")
    print(f"总测试数: {total_tests}")
    print(f"成功数: {total_success}")
    print(f"成功率: {total_success/total_tests*100:.1f}%")
    
    if total_success > 0:
        print(f"\n✅ 有 {total_success} 个API测试成功，可以开始收集数据")
        print("运行 'python3 run.py' 开始收集数据")
    else:
        print(f"\n❌ 所有API测试都失败了，请检查网络连接和API配置")

if __name__ == "__main__":
    asyncio.run(main())
