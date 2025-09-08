#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的API
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from exchanges.mexc_collector_fixed import MEXCCollectorFixed
from exchanges.weex_collector_fixed import WEEXCollectorFixed
from exchanges.blofin_collector_fixed import BlofinCollectorFixed
from config.settings import Settings

async def test_fixed_apis():
    """测试修复后的API"""
    settings = Settings()
    
    print("=== 测试修复后的API ===\n")
    
    # 测试MEXC
    print("=== 测试MEXC (修复版本) ===")
    mexc_collector = MEXCCollectorFixed(settings)
    
    print("  测试 BTCUSDT...")
    btc_data = await mexc_collector.get_depth_rest('BTCUSDT', limit=20)
    if btc_data:
        print(f"    ✅ 成功获取 BTCUSDT 数据")
        print(f"    价差: {btc_data.spread}")
        print(f"    买盘档位: {len(btc_data.bids)}")
        print(f"    卖盘档位: {len(btc_data.asks)}")
        print(f"    买盘总量: {sum([float(bid[1]) for bid in btc_data.bids])}")
        print(f"    卖盘总量: {sum([float(ask[1]) for ask in btc_data.asks])}")
    else:
        print("    ❌ 获取 BTCUSDT 数据失败")
    
    print("  测试 ETHUSDT...")
    eth_data = await mexc_collector.get_depth_rest('ETHUSDT', limit=20)
    if eth_data:
        print(f"    ✅ 成功获取 ETHUSDT 数据")
        print(f"    价差: {eth_data.spread}")
        print(f"    买盘档位: {len(eth_data.bids)}")
        print(f"    卖盘档位: {len(eth_data.asks)}")
        print(f"    买盘总量: {sum([float(bid[1]) for bid in eth_data.bids])}")
        print(f"    卖盘总量: {sum([float(ask[1]) for ask in eth_data.asks])}")
    else:
        print("    ❌ 获取 ETHUSDT 数据失败")
    
    print("\n=== 测试WEEX (修复版本) ===")
    weex_collector = WEEXCollectorFixed(settings)
    
    print("  测试 BTCUSDT...")
    btc_data = await weex_collector.get_depth_rest('BTCUSDT', limit=20)
    if btc_data:
        print(f"    ✅ 成功获取 BTCUSDT 数据")
        print(f"    价差: {btc_data.spread}")
        print(f"    买盘档位: {len(btc_data.bids)}")
        print(f"    卖盘档位: {len(btc_data.asks)}")
        print(f"    买盘总量: {sum([float(bid[1]) for bid in btc_data.bids])}")
        print(f"    卖盘总量: {sum([float(ask[1]) for ask in btc_data.asks])}")
    else:
        print("    ❌ 获取 BTCUSDT 数据失败")
    
    print("  测试 ETHUSDT...")
    eth_data = await weex_collector.get_depth_rest('ETHUSDT', limit=20)
    if eth_data:
        print(f"    ✅ 成功获取 ETHUSDT 数据")
        print(f"    价差: {eth_data.spread}")
        print(f"    买盘档位: {len(eth_data.bids)}")
        print(f"    卖盘档位: {len(eth_data.asks)}")
        print(f"    买盘总量: {sum([float(bid[1]) for bid in eth_data.bids])}")
        print(f"    卖盘总量: {sum([float(ask[1]) for ask in eth_data.asks])}")
    else:
        print("    ❌ 获取 ETHUSDT 数据失败")
    
    print("\n=== 测试Blofin (修复版本) ===")
    blofin_collector = BlofinCollectorFixed(settings)
    
    print("  测试 BTCUSDT...")
    btc_data = await blofin_collector.get_depth_rest('BTCUSDT', limit=20)
    if btc_data:
        print(f"    ✅ 成功获取 BTCUSDT 数据")
        print(f"    价差: {btc_data.spread}")
        print(f"    买盘档位: {len(btc_data.bids)}")
        print(f"    卖盘档位: {len(btc_data.asks)}")
        print(f"    买盘总量: {sum([float(bid[1]) for bid in btc_data.bids])}")
        print(f"    卖盘总量: {sum([float(ask[1]) for ask in btc_data.asks])}")
    else:
        print("    ❌ 获取 BTCUSDT 数据失败")
    
    print("  测试 ETHUSDT...")
    eth_data = await blofin_collector.get_depth_rest('ETHUSDT', limit=20)
    if eth_data:
        print(f"    ✅ 成功获取 ETHUSDT 数据")
        print(f"    价差: {eth_data.spread}")
        print(f"    买盘档位: {len(eth_data.bids)}")
        print(f"    卖盘档位: {len(eth_data.asks)}")
        print(f"    买盘总量: {sum([float(bid[1]) for bid in eth_data.bids])}")
        print(f"    卖盘总量: {sum([float(ask[1]) for ask in eth_data.asks])}")
    else:
        print("    ❌ 获取 ETHUSDT 数据失败")
    
    print("\n=== 修复后的API测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_fixed_apis())
