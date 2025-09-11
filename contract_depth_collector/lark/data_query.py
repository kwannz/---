#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据查询功能
用于查询历史数据并生成报告
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging


class DataQuery:
    """数据查询类"""
    
    def __init__(self, data_dir: str = "data"):
        """初始化数据查询器"""
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger("data_query")
        
    def get_available_dates(self) -> List[str]:
        """获取可用的日期列表"""
        try:
            data_files = list(self.data_dir.glob("depth_data_*.json"))
            dates = set()
            
            for file in data_files:
                # 从文件名提取日期
                filename = file.stem
                if "depth_data_" in filename:
                    date_part = filename.replace("depth_data_", "")
                    if len(date_part) >= 8:
                        date = date_part[:8]  # YYYYMMDD
                        dates.add(date)
            
            return sorted(list(dates), reverse=True)
            
        except Exception as e:
            self.logger.error(f"获取可用日期失败: {e}")
            return []
    
    def get_data_by_date(self, date: str) -> List[Dict]:
        """获取指定日期的数据"""
        try:
            data_files = list(self.data_dir.glob(f"depth_data_{date}_*.json"))
            all_data = []
            
            for file in data_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data.extend(data)
                except Exception as e:
                    self.logger.warning(f"读取文件 {file} 失败: {e}")
            
            return all_data
            
        except Exception as e:
            self.logger.error(f"获取日期 {date} 数据失败: {e}")
            return []
    
    def get_data_by_symbol(self, symbol: str, days: int = 7) -> List[Dict]:
        """获取指定代币最近N天的数据"""
        try:
            available_dates = self.get_available_dates()
            recent_dates = available_dates[:days]
            
            all_data = []
            for date in recent_dates:
                date_data = self.get_data_by_date(date)
                symbol_data = [d for d in date_data if d.get('symbol') == symbol]
                all_data.extend(symbol_data)
            
            return all_data
            
        except Exception as e:
            self.logger.error(f"获取代币 {symbol} 数据失败: {e}")
            return []
    
    def get_latest_data(self, limit: int = 100) -> List[Dict]:
        """获取最新数据"""
        try:
            data_files = list(self.data_dir.glob("depth_data_*.json"))
            if not data_files:
                return []
            
            # 按修改时间排序
            latest_files = sorted(data_files, key=lambda x: x.stat().st_mtime, reverse=True)
            
            all_data = []
            for file in latest_files[:5]:  # 只检查最新的5个文件
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data.extend(data)
                        
                    if len(all_data) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"读取文件 {file} 失败: {e}")
            
            return all_data[:limit]
            
        except Exception as e:
            self.logger.error(f"获取最新数据失败: {e}")
            return []
    
    def analyze_symbol_trend(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """分析代币趋势"""
        try:
            data = self.get_data_by_symbol(symbol, days)
            if not data:
                return {"error": f"没有找到 {symbol} 的数据"}
            
            # 按时间排序
            data.sort(key=lambda x: x.get('timestamp', 0))
            
            # 计算趋势指标
            spreads = [d.get('spread', 0) for d in data if d.get('spread')]
            bid_volumes = [d.get('total_bid_volume', 0) for d in data if d.get('total_bid_volume')]
            ask_volumes = [d.get('total_ask_volume', 0) for d in data if d.get('total_ask_volume')]
            
            analysis = {
                "symbol": symbol,
                "period_days": days,
                "total_records": len(data),
                "time_range": {
                    "start": min([d.get('timestamp', 0) for d in data]),
                    "end": max([d.get('timestamp', 0) for d in data])
                },
                "spread_analysis": {
                    "avg": sum(spreads) / len(spreads) if spreads else 0,
                    "min": min(spreads) if spreads else 0,
                    "max": max(spreads) if spreads else 0,
                    "trend": self.calculate_trend(spreads)
                },
                "volume_analysis": {
                    "avg_bid": sum(bid_volumes) / len(bid_volumes) if bid_volumes else 0,
                    "avg_ask": sum(ask_volumes) / len(ask_volumes) if ask_volumes else 0,
                    "total_volume": sum(bid_volumes) + sum(ask_volumes),
                    "bid_ask_ratio": sum(bid_volumes) / sum(ask_volumes) if ask_volumes and sum(ask_volumes) > 0 else 0
                },
                "exchange_analysis": self.analyze_by_exchange(data),
                "daily_analysis": self.analyze_daily_trend(data)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析代币 {symbol} 趋势失败: {e}")
            return {"error": str(e)}
    
    def calculate_trend(self, values: List[float]) -> str:
        """计算趋势方向"""
        if len(values) < 2:
            return "stable"
        
        # 简单线性趋势分析
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        change_percent = (avg_second - avg_first) / avg_first * 100 if avg_first > 0 else 0
        
        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    def analyze_by_exchange(self, data: List[Dict]) -> Dict[str, Any]:
        """按交易所分析数据"""
        exchange_data = {}
        
        for d in data:
            exchange = d.get('exchange')
            if exchange not in exchange_data:
                exchange_data[exchange] = {
                    'count': 0,
                    'spreads': [],
                    'bid_volumes': [],
                    'ask_volumes': []
                }
            
            exchange_data[exchange]['count'] += 1
            if d.get('spread'):
                exchange_data[exchange]['spreads'].append(d['spread'])
            if d.get('total_bid_volume'):
                exchange_data[exchange]['bid_volumes'].append(d['total_bid_volume'])
            if d.get('total_ask_volume'):
                exchange_data[exchange]['ask_volumes'].append(d['total_ask_volume'])
        
        # 计算各交易所统计
        for exchange, stats in exchange_data.items():
            if stats['spreads']:
                stats['avg_spread'] = sum(stats['spreads']) / len(stats['spreads'])
                stats['min_spread'] = min(stats['spreads'])
                stats['max_spread'] = max(stats['spreads'])
            
            if stats['bid_volumes']:
                stats['avg_bid_volume'] = sum(stats['bid_volumes']) / len(stats['bid_volumes'])
            
            if stats['ask_volumes']:
                stats['avg_ask_volume'] = sum(stats['ask_volumes']) / len(stats['ask_volumes'])
            
            stats['total_volume'] = sum(stats['bid_volumes']) + sum(stats['ask_volumes'])
        
        return exchange_data
    
    def analyze_daily_trend(self, data: List[Dict]) -> Dict[str, Any]:
        """分析每日趋势"""
        daily_data = {}
        
        for d in data:
            timestamp = d.get('timestamp', 0)
            if timestamp:
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                if date not in daily_data:
                    daily_data[date] = []
                daily_data[date].append(d)
        
        daily_analysis = {}
        for date, day_data in daily_data.items():
            spreads = [d.get('spread', 0) for d in day_data if d.get('spread')]
            bid_volumes = [d.get('total_bid_volume', 0) for d in day_data if d.get('total_bid_volume')]
            ask_volumes = [d.get('total_ask_volume', 0) for d in day_data if d.get('total_ask_volume')]
            
            daily_analysis[date] = {
                'records': len(day_data),
                'avg_spread': sum(spreads) / len(spreads) if spreads else 0,
                'total_volume': sum(bid_volumes) + sum(ask_volumes),
                'exchanges': list(set([d.get('exchange') for d in day_data]))
            }
        
        return daily_analysis
    
    def generate_report(self, symbol: str, days: int = 7) -> str:
        """生成分析报告"""
        try:
            analysis = self.analyze_symbol_trend(symbol, days)
            
            if "error" in analysis:
                return f"❌ 分析失败: {analysis['error']}"
            
            report = f"📊 **{symbol} 趋势分析报告**\n\n"
            report += f"📅 分析周期: {days} 天\n"
            report += f"📈 总记录数: {analysis['total_records']}\n"
            report += f"⏰ 时间范围: {datetime.fromtimestamp(analysis['time_range']['start']).strftime('%Y-%m-%d %H:%M')} - {datetime.fromtimestamp(analysis['time_range']['end']).strftime('%Y-%m-%d %H:%M')}\n\n"
            
            # 价差分析
            spread_analysis = analysis['spread_analysis']
            report += f"💰 **价差分析**\n"
            report += f"• 平均价差: {spread_analysis['avg']:.6f}%\n"
            report += f"• 最低价差: {spread_analysis['min']:.6f}%\n"
            report += f"• 最高价差: {spread_analysis['max']:.6f}%\n"
            report += f"• 趋势: {self.get_trend_emoji(spread_analysis['trend'])} {spread_analysis['trend']}\n\n"
            
            # 铺单量分析
            volume_analysis = analysis['volume_analysis']
            report += f"📊 **铺单量分析**\n"
            report += f"• 平均买量: {volume_analysis['avg_bid']:.2f} USDT\n"
            report += f"• 平均卖量: {volume_analysis['avg_ask']:.2f} USDT\n"
            report += f"• 总铺单量: {volume_analysis['total_volume']:.2f} USDT\n"
            report += f"• 买卖比例: {volume_analysis['bid_ask_ratio']:.2f}\n\n"
            
            # 交易所分析
            exchange_analysis = analysis['exchange_analysis']
            if exchange_analysis:
                report += f"🏢 **交易所分析**\n"
                for exchange, stats in exchange_analysis.items():
                    report += f"• **{exchange}**:\n"
                    report += f"  - 记录数: {stats['count']}\n"
                    if 'avg_spread' in stats:
                        report += f"  - 平均价差: {stats['avg_spread']:.6f}%\n"
                    if 'total_volume' in stats:
                        report += f"  - 总铺单量: {stats['total_volume']:.2f} USDT\n"
                report += "\n"
            
            # 每日趋势
            daily_analysis = analysis['daily_analysis']
            if daily_analysis:
                report += f"📅 **每日趋势**\n"
                for date, day_stats in sorted(daily_analysis.items()):
                    report += f"• {date}: 价差 {day_stats['avg_spread']:.6f}%, 铺单量 {day_stats['total_volume']:.2f} USDT, 交易所 {len(day_stats['exchanges'])}个\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            return f"❌ 生成报告失败: {str(e)}"
    
    def get_trend_emoji(self, trend: str) -> str:
        """获取趋势表情符号"""
        trend_emojis = {
            "increasing": "📈",
            "decreasing": "📉", 
            "stable": "➡️"
        }
        return trend_emojis.get(trend, "❓")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取汇总统计"""
        try:
            available_dates = self.get_available_dates()
            if not available_dates:
                return {"error": "没有可用数据"}
            
            # 获取最近7天数据
            recent_data = []
            for date in available_dates[:7]:
                date_data = self.get_data_by_date(date)
                recent_data.extend(date_data)
            
            if not recent_data:
                return {"error": "没有找到最近数据"}
            
            # 统计信息
            symbols = list(set([d.get('symbol') for d in recent_data]))
            exchanges = list(set([d.get('exchange') for d in recent_data]))
            
            # 按代币统计
            symbol_stats = {}
            for symbol in symbols:
                symbol_data = [d for d in recent_data if d.get('symbol') == symbol]
                if symbol_data:
                    spreads = [d.get('spread', 0) for d in symbol_data if d.get('spread')]
                    volumes = [d.get('total_bid_volume', 0) + d.get('total_ask_volume', 0) for d in symbol_data]
                    
                    symbol_stats[symbol] = {
                        'records': len(symbol_data),
                        'avg_spread': sum(spreads) / len(spreads) if spreads else 0,
                        'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
                        'exchanges': list(set([d.get('exchange') for d in symbol_data]))
                    }
            
            return {
                'total_records': len(recent_data),
                'date_range': {
                    'start': available_dates[-1] if available_dates else None,
                    'end': available_dates[0] if available_dates else None
                },
                'symbols': symbols,
                'exchanges': exchanges,
                'symbol_stats': symbol_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取汇总统计失败: {e}")
            return {"error": str(e)}


def main():
    """测试函数"""
    query = DataQuery()
    
    print("📊 数据查询测试")
    print("=" * 50)
    
    # 获取可用日期
    dates = query.get_available_dates()
    print(f"可用日期: {dates[:5]}...")
    
    # 获取汇总统计
    stats = query.get_summary_stats()
    if "error" not in stats:
        print(f"总记录数: {stats['total_records']}")
        print(f"代币: {stats['symbols']}")
        print(f"交易所: {stats['exchanges']}")
    
    # 生成BTC报告
    if 'BTCUSDT' in stats.get('symbols', []):
        print("\n生成BTC报告...")
        report = query.generate_report('BTCUSDT', 3)
        print(report)


if __name__ == "__main__":
    main()
