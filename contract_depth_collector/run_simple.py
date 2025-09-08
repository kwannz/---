#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版多交易所合约铺单量数据收集器
只收集2个交易对，少量数据用于测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import ContractDepthCollector

async def main():
    """主函数"""
    # 创建收集器
    collector = ContractDepthCollector()
    
    # 只收集2个交易对
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    print("=== 简化版多交易所合约铺单量数据收集器 ===")
    print("支持的交易所: Binance, MEXC, Gate.io, OKX, BingX, Bitunix, Blofin")
    print(f"目标交易对: {', '.join(symbols)}")
    print("只收集少量数据用于测试")
    print("\n选择运行模式:")
    print("1. 快速测试 (30秒)")
    print("2. 短时间收集 (2分钟)")
    print("3. 自定义收集")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            print("开始30秒快速测试...")
            await collector.collect_depth_data(symbols, duration=30)
        elif choice == "2":
            print("开始2分钟数据收集...")
            await collector.collect_depth_data(symbols, duration=120)
        elif choice == "3":
            custom_duration = int(input("请输入收集时长 (秒): ") or "60")
            await collector.collect_depth_data(symbols, duration=custom_duration)
        else:
            print("无效选择，使用默认模式 (30秒测试)")
            await collector.collect_depth_data(symbols, duration=30)
        
        # 显示统计信息
        stats = collector.get_summary_statistics()
        print("\n=== 收集统计 ===")
        print(f"总记录数: {stats.get('total_records', 0)}")
        print(f"交易所: {', '.join(stats.get('exchanges', []))}")
        print(f"交易对: {', '.join(stats.get('symbols', []))}")
        
        if stats.get('total_records', 0) > 0:
            print(f"\n✅ 数据收集完成！")
            print(f"📊 成功收集了 {stats.get('total_records', 0)} 条深度数据记录")
            print(f"💾 数据已保存到 data/ 目录")
            print(f"📈 可以运行 'python3 analyze_data.py' 分析数据")
        else:
            print(f"\n⚠️ 未收集到数据，请检查网络连接和API配置")
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        collector.running = False
        print("程序结束")

if __name__ == "__main__":
    asyncio.run(main())
