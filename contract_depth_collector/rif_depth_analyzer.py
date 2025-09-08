#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RIF代币铺单量深度分析器
对比多个交易所的RIF代币深度数据，生成Excel分析报告
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bybit_collector import BybitCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.weex_collector_real import WEEXCollectorReal
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings


class RIFDepthAnalyzer:
    """RIF代币深度分析器"""
    
    def __init__(self):
        """初始化RIF深度分析器"""
        self.settings = Settings()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 初始化所有收集器
        self.collectors = {
            'Binance': BinanceCollector(self.settings),
            'Gate.io': GateCollector(self.settings),
            'OKX': OKXCollector(self.settings),
            'BingX': BingXCollector(self.settings),
            'Bybit': BybitCollector(self.settings),
            'Bitunix': BitunixCollector(self.settings),
            'WEEX': WEEXCollectorReal(self.settings),
            'KuCoin': KuCoinCollector(self.settings)
        }
        
        # RIF代币符号映射
        self.rif_symbols = {
            'Binance': 'RIFUSDT',
            'Gate.io': 'RIF_USDT',
            'OKX': 'RIF-USDT',
            'BingX': 'RIF-USDT',
            'Bybit': 'RIFUSDT',
            'Bitunix': 'RIFUSDT',
            'WEEX': 'RIFUSDT',
            'KuCoin': 'RIFUSDT'
        }
        
        # 统计计数器
        self.reset_counters()
    
    def reset_counters(self):
        """重置统计计数器"""
        self.success_count = 0
        self.error_count = 0
        self.exchange_results = {}
    
    async def get_rif_depth_data(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """获取RIF代币深度数据"""
        collector = self.collectors.get(exchange_name)
        if not collector:
            return None
        
        try:
            print(f"🔍 正在获取 {exchange_name} RIF深度数据...")
            depth_data = await collector.get_depth_rest(symbol, limit=20)
            
            if depth_data:
                self.success_count += 1
                self.exchange_results[exchange_name] = {
                    'status': 'success',
                    'data': depth_data,
                    'symbol': symbol
                }
                print(f"✅ {exchange_name} RIF数据获取成功")
                return depth_data
            else:
                self.error_count += 1
                self.exchange_results[exchange_name] = {
                    'status': 'failed',
                    'data': None,
                    'symbol': symbol,
                    'error': 'No data returned'
                }
                print(f"❌ {exchange_name} RIF数据获取失败")
                return None
                
        except Exception as e:
            self.error_count += 1
            self.exchange_results[exchange_name] = {
                'status': 'error',
                'data': None,
                'symbol': symbol,
                'error': str(e)
            }
            print(f"❌ {exchange_name} RIF数据获取异常: {e}")
            return None
    
    def calculate_depth_metrics(self, depth_data, exchange_name: str) -> Dict:
        """计算深度指标"""
        if not depth_data:
            return {}
        
        try:
            bids = depth_data.bids
            asks = depth_data.asks
            
            if not bids or not asks:
                return {}
            
            # 基础价格信息
            best_bid = float(bids[0][0]) if bids else 0
            best_ask = float(asks[0][0]) if asks else 0
            mid_price = (best_bid + best_ask) / 2 if best_bid > 0 and best_ask > 0 else 0
            spread = best_ask - best_bid if best_bid > 0 and best_ask > 0 else 0
            spread_percent = (spread / mid_price * 100) if mid_price > 0 else 0
            
            # 格式化数值到6位小数
            best_bid = round(best_bid, 6)
            best_ask = round(best_ask, 6)
            mid_price = round(mid_price, 6)
            spread = round(spread, 6)
            spread_percent = round(spread_percent, 6)
            
            # 计算各档位数据
            metrics = {
                'exchange': exchange_name,
                'symbol': depth_data.symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread': spread,
                'spread_percent': spread_percent,
                'timestamp': depth_data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(depth_data.timestamp, 'strftime') else str(depth_data.timestamp)
            }
            
            # 计算1-20档铺单量
            for level in [1, 3, 5, 10, 20]:
                bid_volume = sum([float(bid[0]) * float(bid[1]) for bid in bids[:level]])
                ask_volume = sum([float(ask[0]) * float(ask[1]) for ask in asks[:level]])
                total_volume = bid_volume + ask_volume
                buy_sell_ratio = bid_volume / ask_volume if ask_volume > 0 else 0
                
                # 格式化数值到6位小数
                bid_volume = round(bid_volume, 6)
                ask_volume = round(ask_volume, 6)
                total_volume = round(total_volume, 6)
                buy_sell_ratio = round(buy_sell_ratio, 6)
                
                metrics[f'{level}档_买盘量'] = bid_volume
                metrics[f'{level}档_卖盘量'] = ask_volume
                metrics[f'{level}档_总铺单量'] = total_volume
                metrics[f'{level}档_买卖比例'] = buy_sell_ratio
            
            # 计算价格分布
            bid_prices = [float(bid[0]) for bid in bids[:20]]
            ask_prices = [float(ask[0]) for ask in asks[:20]]
            
            if bid_prices and ask_prices:
                bid_price_min = round(min(bid_prices), 6)
                bid_price_max = round(max(bid_prices), 6)
                ask_price_min = round(min(ask_prices), 6)
                ask_price_max = round(max(ask_prices), 6)
                bid_price_diff = round(max(bid_prices) - min(bid_prices), 6)
                ask_price_diff = round(max(ask_prices) - min(ask_prices), 6)
                
                metrics['买盘价格范围'] = f"{bid_price_min:.6f} - {bid_price_max:.6f}"
                metrics['卖盘价格范围'] = f"{ask_price_min:.6f} - {ask_price_max:.6f}"
                metrics['买盘价格差'] = bid_price_diff
                metrics['卖盘价格差'] = ask_price_diff
            
            return metrics
            
        except Exception as e:
            print(f"❌ 计算 {exchange_name} 深度指标失败: {e}")
            return {}
    
    async def collect_all_rif_data(self) -> List[Dict]:
        """收集所有交易所的RIF数据"""
        print("🚀 开始收集RIF代币深度数据...")
        print("=" * 60)
        
        all_metrics = []
        
        # 并行获取所有交易所数据
        tasks = []
        for exchange_name, symbol in self.rif_symbols.items():
            task = self.get_rif_depth_data(exchange_name, symbol)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, (exchange_name, symbol) in enumerate(self.rif_symbols.items()):
            result = results[i]
            if isinstance(result, Exception):
                print(f"❌ {exchange_name} 任务异常: {result}")
                continue
            
            if result:
                metrics = self.calculate_depth_metrics(result, exchange_name)
                if metrics:
                    all_metrics.append(metrics)
        
        print("=" * 60)
        print(f"📊 RIF数据收集完成: 成功 {self.success_count} 个，失败 {self.error_count} 个")
        
        return all_metrics
    
    def create_comparison_analysis(self, metrics_list: List[Dict]) -> pd.DataFrame:
        """创建对比分析表格"""
        if not metrics_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(metrics_list)
        
        # 按交易所排序
        df = df.sort_values('exchange')
        
        # 添加排名
        for level in [1, 3, 5, 10, 20]:
            df[f'{level}档_总铺单量_排名'] = df[f'{level}档_总铺单量'].rank(ascending=False, method='min')
            df[f'{level}档_买卖比例_排名'] = df[f'{level}档_买卖比例'].rank(ascending=False, method='min')
        
        # 添加价差排名
        df['价差_排名'] = df['spread_percent'].rank(ascending=True, method='min')
        
        return df
    
    def create_summary_analysis(self, df: pd.DataFrame) -> Dict:
        """创建汇总分析"""
        if df.empty:
            return {}
        
        summary = {
            '总交易所数': len(df),
            '成功获取数据': len(df[df['exchange'].notna()]),
            '平均价差': df['spread_percent'].mean(),
            '最小价差': df['spread_percent'].min(),
            '最大价差': df['spread_percent'].max(),
            '平均1档铺单量': df['1档_总铺单量'].mean(),
            '平均20档铺单量': df['20档_总铺单量'].mean(),
            '最佳流动性交易所': df.loc[df['20档_总铺单量'].idxmax(), 'exchange'] if not df.empty else 'N/A',
            '最低价差交易所': df.loc[df['spread_percent'].idxmin(), 'exchange'] if not df.empty else 'N/A'
        }
        
        return summary
    
    def export_to_excel(self, df: pd.DataFrame, summary: Dict) -> str:
        """导出到Excel文件"""
        filename = f"RIF代币深度分析_{self.timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 1. 汇总分析
                summary_data = [
                    ['指标', '数值'],
                    ['总交易所数', summary.get('总交易所数', 0)],
                    ['成功获取数据', summary.get('成功获取数据', 0)],
                    ['平均价差(%)', f"{summary.get('平均价差', 0):.6f}"],
                    ['最小价差(%)', f"{summary.get('最小价差', 0):.6f}"],
                    ['最大价差(%)', f"{summary.get('最大价差', 0):.6f}"],
                    ['平均1档铺单量', f"{summary.get('平均1档铺单量', 0):.6f}"],
                    ['平均20档铺单量', f"{summary.get('平均20档铺单量', 0):.6f}"],
                    ['最佳流动性交易所', summary.get('最佳流动性交易所', 'N/A')],
                    ['最低价差交易所', summary.get('最低价差交易所', 'N/A')]
                ]
                
                summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
                summary_df.to_excel(writer, sheet_name='汇总分析', index=False)
                
                # 设置数值格式
                worksheet = writer.sheets['汇总分析']
                for row in range(2, len(summary_data) + 1):
                    if '价差' in summary_data[row-1][0] or '铺单量' in summary_data[row-1][0]:
                        worksheet.cell(row=row, column=2).number_format = '0.000000'
                
                # 2. 详细对比数据
                if not df.empty:
                    df.to_excel(writer, sheet_name='详细对比', index=False)
                    self._format_excel_numbers(writer, '详细对比', df.columns)
                
                # 3. 铺单量排名
                if not df.empty:
                    ranking_columns = ['exchange', 'symbol', 'mid_price', 'spread_percent']
                    for level in [1, 3, 5, 10, 20]:
                        ranking_columns.extend([
                            f'{level}档_总铺单量', f'{level}档_总铺单量_排名',
                            f'{level}档_买卖比例', f'{level}档_买卖比例_排名'
                        ])
                    
                    ranking_df = df[ranking_columns].copy()
                    ranking_df.to_excel(writer, sheet_name='铺单量排名', index=False)
                    self._format_excel_numbers(writer, '铺单量排名', ranking_df.columns)
                
                # 4. 价差分析
                if not df.empty:
                    spread_columns = ['exchange', 'symbol', 'best_bid', 'best_ask', 'mid_price', 
                                    'spread', 'spread_percent', '价差_排名']
                    spread_df = df[spread_columns].copy()
                    spread_df.to_excel(writer, sheet_name='价差分析', index=False)
                    self._format_excel_numbers(writer, '价差分析', spread_df.columns)
            
            print(f"✅ Excel文件导出成功: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 导出Excel文件失败: {e}")
            return ""
    
    def _format_excel_numbers(self, writer, sheet_name: str, columns):
        """格式化Excel中的数值列"""
        try:
            worksheet = writer.sheets[sheet_name]
            
            # 定义需要格式化的列
            numeric_columns = [
                'best_bid', 'best_ask', 'mid_price', 'spread', 'spread_percent',
                '买盘价格差', '卖盘价格差'
            ]
            
            # 添加铺单量列
            for level in [1, 3, 5, 10, 20]:
                numeric_columns.extend([
                    f'{level}档_买盘量', f'{level}档_卖盘量', f'{level}档_总铺单量', f'{level}档_买卖比例'
                ])
            
            # 找到数值列的索引
            for col_idx, col_name in enumerate(columns, 1):
                if col_name in numeric_columns:
                    # 设置数值格式为6位小数
                    for row in range(2, worksheet.max_row + 1):
                        cell = worksheet.cell(row=row, column=col_idx)
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = '0.000000'
                            
        except Exception as e:
            print(f"❌ 格式化Excel数值失败: {e}")
    
    async def run_rif_analysis(self) -> str:
        """运行RIF代币分析"""
        print("🎯 RIF代币铺单量深度分析器")
        print("=" * 60)
        print("📊 分析目标: RIF代币在各交易所的深度数据对比")
        print("📈 分析内容: 铺单量、价差、流动性排名")
        print("=" * 60)
        
        # 1. 收集数据
        metrics_list = await self.collect_all_rif_data()
        
        if not metrics_list:
            print("❌ 没有获取到任何RIF数据")
            return ""
        
        # 2. 创建对比分析
        print("\n📊 正在创建对比分析...")
        df = self.create_comparison_analysis(metrics_list)
        
        # 3. 创建汇总分析
        print("📊 正在创建汇总分析...")
        summary = self.create_summary_analysis(df)
        
        # 4. 导出Excel
        print("📊 正在导出Excel报告...")
        excel_file = self.export_to_excel(df, summary)
        
        if excel_file:
            print("\n" + "=" * 60)
            print("🎉 RIF代币深度分析完成!")
            print(f"📊 Excel报告: {excel_file}")
            print(f"📂 报告位置: {Path(excel_file).absolute()}")
            print("=" * 60)
            
            # 显示关键指标
            print("\n📈 关键指标:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
        
        return excel_file


async def main():
    """主函数"""
    analyzer = RIFDepthAnalyzer()
    excel_file = await analyzer.run_rif_analysis()
    
    if excel_file:
        print(f"\n🎉 RIF代币分析成功完成！")
        print(f"📋 Excel报告: {excel_file}")
        print(f"\n📊 报告包含以下工作表:")
        print(f"   📈 汇总分析: 整体统计和关键指标")
        print(f"   📈 详细对比: 各交易所详细数据对比")
        print(f"   📈 铺单量排名: 1-20档铺单量排名")
        print(f"   📈 价差分析: 价差和价格分析")
    else:
        print("\n❌ RIF代币分析失败")


if __name__ == "__main__":
    asyncio.run(main())
