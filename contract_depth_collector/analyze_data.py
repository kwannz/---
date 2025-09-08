#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析脚本 - 分析收集到的JSON数据
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob
from pathlib import Path

def analyze_json_files(data_dir="data"):
    """分析JSON数据文件"""
    print("=== 多交易所合约铺单量数据分析 ===\n")
    
    # 查找所有JSON文件
    json_files = glob.glob(os.path.join(data_dir, "depth_data_*.json"))
    if not json_files:
        print("❌ 未找到JSON数据文件")
        return
    
    # 按修改时间排序，获取最新的文件
    json_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = json_files[0]
    
    print(f"📁 分析文件: {latest_file}")
    print(f"📅 文件修改时间: {datetime.fromtimestamp(os.path.getmtime(latest_file))}")
    
    # 读取JSON数据
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 总记录数: {len(data)}")
    print(f"💾 文件大小: {os.path.getsize(latest_file) / 1024:.2f} KB")
    
    # 转换为DataFrame进行分析
    df_data = []
    for record in data:
        df_data.append({
            'exchange': record['exchange'],
            'symbol': record['symbol'],
            'timestamp': datetime.fromtimestamp(record['timestamp']),
            'spread': record['spread'],
            'total_bid_volume': record['total_bid_volume'],
            'total_ask_volume': record['total_ask_volume'],
            'bid_count': len(record['bids']),
            'ask_count': len(record['asks']),
            'mid_price': (record['bids'][0][0] + record['asks'][0][0]) / 2 if record['bids'] and record['asks'] else 0,
            'volume_imbalance': (record['total_bid_volume'] - record['total_ask_volume']) / (record['total_bid_volume'] + record['total_ask_volume']) if (record['total_bid_volume'] + record['total_ask_volume']) > 0 else 0
        })
    
    df = pd.DataFrame(df_data)
    
    # 基本统计信息
    print(f"\n=== 基本统计信息 ===")
    print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    print(f"数据收集时长: {(df['timestamp'].max() - df['timestamp'].min()).total_seconds():.2f} 秒")
    
    # 交易所分布
    print(f"\n=== 交易所分布 ===")
    exchange_counts = df['exchange'].value_counts()
    for exchange, count in exchange_counts.items():
        print(f"{exchange}: {count} 条记录 ({count/len(df)*100:.1f}%)")
    
    # 交易对分布
    print(f"\n=== 交易对分布 ===")
    symbol_counts = df['symbol'].value_counts()
    for symbol, count in symbol_counts.items():
        print(f"{symbol}: {count} 条记录 ({count/len(df)*100:.1f}%)")
    
    # 价差分析
    print(f"\n=== 价差分析 ===")
    print(f"平均价差: {df['spread'].mean():.6f}")
    print(f"价差中位数: {df['spread'].median():.6f}")
    print(f"价差标准差: {df['spread'].std():.6f}")
    print(f"最小价差: {df['spread'].min():.6f}")
    print(f"最大价差: {df['spread'].max():.6f}")
    
    # 按交易对分析价差
    print(f"\n=== 各交易对价差统计 ===")
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol]
        print(f"{symbol}:")
        print(f"  平均价差: {symbol_data['spread'].mean():.6f}")
        print(f"  价差范围: {symbol_data['spread'].min():.6f} - {symbol_data['spread'].max():.6f}")
        print(f"  记录数: {len(symbol_data)}")
    
    # 成交量分析
    print(f"\n=== 成交量分析 ===")
    print(f"平均买盘总量: {df['total_bid_volume'].mean():.2f}")
    print(f"平均卖盘总量: {df['total_ask_volume'].mean():.2f}")
    print(f"总买盘量: {df['total_bid_volume'].sum():.2f}")
    print(f"总卖盘量: {df['total_ask_volume'].sum():.2f}")
    
    # 订单簿深度分析
    print(f"\n=== 订单簿深度分析 ===")
    print(f"平均买盘档位数: {df['bid_count'].mean():.1f}")
    print(f"平均卖盘档位数: {df['ask_count'].mean():.1f}")
    print(f"最大买盘档位: {df['bid_count'].max()}")
    print(f"最大卖盘档位: {df['ask_count'].max()}")
    
    # 成交量不平衡分析
    print(f"\n=== 成交量不平衡分析 ===")
    print(f"平均不平衡度: {df['volume_imbalance'].mean():.4f}")
    print(f"不平衡度标准差: {df['volume_imbalance'].std():.4f}")
    print(f"买盘优势记录: {len(df[df['volume_imbalance'] > 0])} ({len(df[df['volume_imbalance'] > 0])/len(df)*100:.1f}%)")
    print(f"卖盘优势记录: {len(df[df['volume_imbalance'] < 0])} ({len(df[df['volume_imbalance'] < 0])/len(df)*100:.1f}%)")
    
    # 时间序列分析
    print(f"\n=== 时间序列分析 ===")
    df_sorted = df.sort_values('timestamp')
    time_intervals = df_sorted['timestamp'].diff().dropna()
    print(f"平均数据间隔: {time_intervals.mean().total_seconds():.2f} 秒")
    print(f"最小数据间隔: {time_intervals.min().total_seconds():.2f} 秒")
    print(f"最大数据间隔: {time_intervals.max().total_seconds():.2f} 秒")
    
    # 详细记录示例
    print(f"\n=== 详细记录示例 ===")
    sample_record = data[0]
    print(f"交易所: {sample_record['exchange']}")
    print(f"交易对: {sample_record['symbol']}")
    print(f"时间戳: {sample_record['timestamp']}")
    print(f"时间: {datetime.fromtimestamp(sample_record['timestamp'])}")
    print(f"价差: {sample_record['spread']}")
    print(f"买盘总量: {sample_record['total_bid_volume']}")
    print(f"卖盘总量: {sample_record['total_ask_volume']}")
    print(f"买盘档位数: {len(sample_record['bids'])}")
    print(f"卖盘档位数: {len(sample_record['asks'])}")
    
    print(f"\n=== 买盘前10档 ===")
    for i, bid in enumerate(sample_record['bids'][:10]):
        print(f"  {i+1:2d}. 价格: {bid[0]:12.6f}, 数量: {bid[1]:12.6f}")
    
    print(f"\n=== 卖盘前10档 ===")
    for i, ask in enumerate(sample_record['asks'][:10]):
        print(f"  {i+1:2d}. 价格: {ask[0]:12.6f}, 数量: {ask[1]:12.6f}")
    
    # 保存分析报告
    report_file = f"data/analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== 多交易所合约铺单量数据分析报告 ===\n\n")
        f.write(f"分析时间: {datetime.now()}\n")
        f.write(f"数据文件: {latest_file}\n")
        f.write(f"总记录数: {len(data)}\n")
        f.write(f"文件大小: {os.path.getsize(latest_file) / 1024:.2f} KB\n\n")
        
        f.write("=== 交易所分布 ===\n")
        for exchange, count in exchange_counts.items():
            f.write(f"{exchange}: {count} 条记录 ({count/len(df)*100:.1f}%)\n")
        
        f.write("\n=== 交易对分布 ===\n")
        for symbol, count in symbol_counts.items():
            f.write(f"{symbol}: {count} 条记录 ({count/len(df)*100:.1f}%)\n")
        
        f.write(f"\n=== 价差统计 ===\n")
        f.write(f"平均价差: {df['spread'].mean():.6f}\n")
        f.write(f"价差中位数: {df['spread'].median():.6f}\n")
        f.write(f"价差标准差: {df['spread'].std():.6f}\n")
        f.write(f"最小价差: {df['spread'].min():.6f}\n")
        f.write(f"最大价差: {df['spread'].max():.6f}\n")
    
    print(f"\n✅ 分析报告已保存到: {report_file}")
    
    return df

def main():
    """主函数"""
    try:
        df = analyze_json_files()
        if df is not None:
            print(f"\n🎉 数据分析完成！")
            print(f"📈 成功分析了 {len(df)} 条深度数据记录")
            print(f"💡 数据质量良好，可以用于进一步的分析和建模")
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
