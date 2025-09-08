#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试收集器功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from exchanges.binance_collector import BinanceCollector
from config.settings import Settings

async def test_binance_collector():
    """测试Binance收集器"""
    print("测试Binance收集器...")
    
    settings = Settings()
    collector = BinanceCollector(settings)
    
    # 测试REST API
    print("测试REST API...")
    depth_data = await collector.get_depth_rest("BTCUSDT", limit=5)
    
    if depth_data:
        print(f"✅ REST API测试成功")
        print(f"   交易对: {depth_data.symbol}")
        print(f"   价差: {depth_data.spread}")
        print(f"   买盘档位: {len(depth_data.bids)}")
        print(f"   卖盘档位: {len(depth_data.asks)}")
        print(f"   买盘总量: {depth_data.total_bid_volume}")
        print(f"   卖盘总量: {depth_data.total_ask_volume}")
    else:
        print("❌ REST API测试失败")
    
    # 测试交易所信息
    print("\n测试交易所信息...")
    exchange_info = await collector.get_exchange_info()
    if exchange_info:
        print("✅ 交易所信息获取成功")
        symbols = exchange_info.get('symbols', [])
        print(f"   支持的交易对数量: {len(symbols)}")
    else:
        print("❌ 交易所信息获取失败")
    
    # 测试24小时数据
    print("\n测试24小时数据...")
    ticker_data = await collector.get_24hr_ticker("BTCUSDT")
    if ticker_data:
        print("✅ 24小时数据获取成功")
        print(f"   价格: {ticker_data.get('lastPrice', 'N/A')}")
        print(f"   24h变化: {ticker_data.get('priceChangePercent', 'N/A')}%")
    else:
        print("❌ 24小时数据获取失败")

async def test_data_processing():
    """测试数据处理功能"""
    print("\n测试数据处理功能...")
    
    from utils.data_processor import DataProcessor
    from main import DepthData
    
    processor = DataProcessor()
    
    # 创建测试数据
    test_data = DepthData(
        exchange="test",
        symbol="BTCUSDT",
        timestamp=1234567890,
        bids=[[50000, 1.5], [49999, 2.0], [49998, 1.0]],
        asks=[[50001, 1.2], [50002, 1.8], [50003, 0.9]],
        spread=1.0,
        total_bid_volume=4.5,
        total_ask_volume=3.9
    )
    
    # 处理数据
    metrics = processor.process_depth_data(test_data)
    
    if metrics:
        print("✅ 数据处理测试成功")
        print(f"   价差: {metrics.spread}")
        print(f"   中间价: {metrics.mid_price}")
        print(f"   成交量不平衡: {metrics.volume_imbalance}")
        print(f"   价格冲击: {metrics.price_impact}")
        print(f"   订单簿压力: {metrics.order_book_pressure}")
    else:
        print("❌ 数据处理测试失败")

async def main():
    """主测试函数"""
    print("=== 多交易所合约铺单量数据收集器测试 ===\n")
    
    try:
        await test_binance_collector()
        await test_data_processing()
        
        print("\n=== 测试完成 ===")
        print("如果所有测试都通过，说明收集器配置正确")
        print("可以运行 'python run.py' 开始收集数据")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
