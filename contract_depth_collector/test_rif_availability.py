#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试RIF代币在各交易所的可用性
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bybit_collector import BybitCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.weex_collector_real import WEEXCollectorReal
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings

async def test_rif_availability():
    """测试RIF代币在各交易所的可用性"""
    settings = Settings()
    
    # RIF代币符号映射
    rif_symbols = {
        'Binance': 'RIFUSDT',
        'Gate.io': 'RIF_USDT',
        'OKX': 'RIF-USDT',
        'BingX': 'RIF-USDT',
        'Bybit': 'RIFUSDT',
        'Bitunix': 'RIFUSDT',
        'WEEX': 'RIFUSDT',
        'KuCoin': 'RIFUSDT'
    }
    
    # 初始化收集器
    collectors = {
        'Binance': BinanceCollector(settings),
        'Gate.io': GateCollector(settings),
        'OKX': OKXCollector(settings),
        'BingX': BingXCollector(settings),
        'Bybit': BybitCollector(settings),
        'Bitunix': BitunixCollector(settings),
        'WEEX': WEEXCollectorReal(settings),
        'KuCoin': KuCoinCollector(settings)
    }
    
    print("🔍 测试RIF代币在各交易所的可用性...")
    print("=" * 60)
    
    available_exchanges = []
    unavailable_exchanges = []
    
    for exchange_name, symbol in rif_symbols.items():
        collector = collectors.get(exchange_name)
        if not collector:
            print(f"❌ {exchange_name}: 收集器未找到")
            unavailable_exchanges.append(exchange_name)
            continue
        
        try:
            print(f"🔍 测试 {exchange_name} ({symbol})...")
            depth_data = await collector.get_depth_rest(symbol, limit=20)
            
            if depth_data:
                print(f"✅ {exchange_name}: 可用")
                print(f"   最佳买价: {depth_data.bids[0][0] if depth_data.bids else 'N/A'}")
                print(f"   最佳卖价: {depth_data.asks[0][0] if depth_data.asks else 'N/A'}")
                print(f"   买盘档位: {len(depth_data.bids)}")
                print(f"   卖盘档位: {len(depth_data.asks)}")
                available_exchanges.append(exchange_name)
            else:
                print(f"❌ {exchange_name}: 无数据")
                unavailable_exchanges.append(exchange_name)
                
        except Exception as e:
            print(f"❌ {exchange_name}: 异常 - {e}")
            unavailable_exchanges.append(exchange_name)
        
        print()
    
    print("=" * 60)
    print("📊 RIF代币可用性测试结果:")
    print(f"✅ 可用交易所: {len(available_exchanges)} 个")
    for exchange in available_exchanges:
        print(f"   - {exchange}")
    
    print(f"❌ 不可用交易所: {len(unavailable_exchanges)} 个")
    for exchange in unavailable_exchanges:
        print(f"   - {exchange}")
    
    print("=" * 60)
    
    return available_exchanges, unavailable_exchanges

if __name__ == "__main__":
    asyncio.run(test_rif_availability())
