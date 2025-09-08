#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据可视化脚本 - 可视化收集到的深度数据
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import glob
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def load_latest_data(data_dir="data"):
    """加载最新的JSON数据"""
    json_files = glob.glob(os.path.join(data_dir, "depth_data_*.json"))
    if not json_files:
        print("❌ 未找到JSON数据文件")
        return None
    
    json_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = json_files[0]
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换为DataFrame
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
    
    return pd.DataFrame(df_data)

def create_visualizations(df):
    """创建数据可视化图表"""
    print("📊 创建数据可视化图表...")
    
    # 设置图表样式
    plt.style.use('seaborn-v0_8')
    fig = plt.figure(figsize=(20, 15))
    
    # 1. 价差分布图
    plt.subplot(3, 3, 1)
    df['spread'].hist(bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title('价差分布图', fontsize=14, fontweight='bold')
    plt.xlabel('价差')
    plt.ylabel('频次')
    plt.yscale('log')
    
    # 2. 各交易对价差箱线图
    plt.subplot(3, 3, 2)
    df.boxplot(column='spread', by='symbol', ax=plt.gca())
    plt.title('各交易对价差分布', fontsize=14, fontweight='bold')
    plt.xlabel('交易对')
    plt.ylabel('价差')
    plt.xticks(rotation=45)
    plt.suptitle('')  # 移除自动标题
    
    # 3. 成交量不平衡分布
    plt.subplot(3, 3, 3)
    df['volume_imbalance'].hist(bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.title('成交量不平衡分布', fontsize=14, fontweight='bold')
    plt.xlabel('成交量不平衡度')
    plt.ylabel('频次')
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='平衡线')
    plt.legend()
    
    # 4. 时间序列 - 价差变化
    plt.subplot(3, 3, 4)
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol].sort_values('timestamp')
        plt.plot(symbol_data['timestamp'], symbol_data['spread'], label=symbol, alpha=0.7)
    plt.title('价差时间序列', fontsize=14, fontweight='bold')
    plt.xlabel('时间')
    plt.ylabel('价差')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 5. 买卖盘总量对比
    plt.subplot(3, 3, 5)
    plt.scatter(df['total_bid_volume'], df['total_ask_volume'], alpha=0.6, s=20)
    plt.plot([df['total_bid_volume'].min(), df['total_bid_volume'].max()], 
             [df['total_bid_volume'].min(), df['total_bid_volume'].max()], 
             'r--', alpha=0.7, label='平衡线')
    plt.title('买卖盘总量对比', fontsize=14, fontweight='bold')
    plt.xlabel('买盘总量')
    plt.ylabel('卖盘总量')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    
    # 6. 订单簿深度分布
    plt.subplot(3, 3, 6)
    plt.scatter(df['bid_count'], df['ask_count'], alpha=0.6, s=20, c=df['spread'], cmap='viridis')
    plt.colorbar(label='价差')
    plt.title('订单簿深度分布', fontsize=14, fontweight='bold')
    plt.xlabel('买盘档位数')
    plt.ylabel('卖盘档位数')
    
    # 7. 各交易对记录数
    plt.subplot(3, 3, 7)
    symbol_counts = df['symbol'].value_counts()
    plt.bar(symbol_counts.index, symbol_counts.values, color='lightgreen', edgecolor='black')
    plt.title('各交易对记录数', fontsize=14, fontweight='bold')
    plt.xlabel('交易对')
    plt.ylabel('记录数')
    plt.xticks(rotation=45)
    
    # 8. 价差与成交量关系
    plt.subplot(3, 3, 8)
    total_volume = df['total_bid_volume'] + df['total_ask_volume']
    plt.scatter(total_volume, df['spread'], alpha=0.6, s=20)
    plt.title('价差与总成交量关系', fontsize=14, fontweight='bold')
    plt.xlabel('总成交量')
    plt.ylabel('价差')
    plt.xscale('log')
    plt.yscale('log')
    
    # 9. 成交量不平衡时间序列
    plt.subplot(3, 3, 9)
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol].sort_values('timestamp')
        plt.plot(symbol_data['timestamp'], symbol_data['volume_imbalance'], label=symbol, alpha=0.7)
    plt.title('成交量不平衡时间序列', fontsize=14, fontweight='bold')
    plt.xlabel('时间')
    plt.ylabel('成交量不平衡度')
    plt.xticks(rotation=45)
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    # 保存图表
    output_file = f"data/visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 可视化图表已保存到: {output_file}")
    
    plt.show()

def create_summary_table(df):
    """创建汇总统计表"""
    print("\n📋 创建汇总统计表...")
    
    # 按交易对汇总统计
    summary_stats = df.groupby('symbol').agg({
        'spread': ['mean', 'std', 'min', 'max'],
        'total_bid_volume': 'mean',
        'total_ask_volume': 'mean',
        'bid_count': 'mean',
        'ask_count': 'mean',
        'volume_imbalance': 'mean'
    }).round(6)
    
    # 展平列名
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
    summary_stats = summary_stats.reset_index()
    
    print("\n=== 各交易对汇总统计 ===")
    print(summary_stats.to_string(index=False))
    
    # 保存为CSV
    csv_file = f"data/summary_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    summary_stats.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"✅ 汇总统计表已保存到: {csv_file}")

def main():
    """主函数"""
    print("=== 多交易所合约铺单量数据可视化 ===\n")
    
    try:
        # 加载数据
        df = load_latest_data()
        if df is None:
            return
        
        print(f"📊 成功加载 {len(df)} 条记录")
        print(f"📅 时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print(f"💰 交易对: {', '.join(df['symbol'].unique())}")
        
        # 创建可视化图表
        create_visualizations(df)
        
        # 创建汇总统计表
        create_summary_table(df)
        
        print(f"\n🎉 数据可视化完成！")
        print(f"📈 生成了9个不同的分析图表")
        print(f"📋 创建了详细的汇总统计表")
        
    except Exception as e:
        print(f"❌ 可视化过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
