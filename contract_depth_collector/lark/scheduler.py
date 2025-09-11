#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器
用于每日定时收集数据并发送到Lark
"""

import asyncio
import schedule
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pandas as pd
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ContractDepthCollector
from lark_webhook_bot import LarkWebhookBot
from utils.logger_config import setup_logger


class DataScheduler:
    """数据收集定时调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.logger = setup_logger("scheduler")
        self.collector = ContractDepthCollector()
        self.lark_bot = LarkWebhookBot()
        self.running = False
        
        # 配置
        self.collection_symbols = ['BTCUSDT', 'ETHUSDT', 'RIFUSDT', 'BNBUSDT', 'ADAUSDT']
        self.collection_duration = 300  # 5分钟收集
        self.data_dir = Path("data")
        
    def setup_schedule(self):
        """设置定时任务"""
        self.logger.info("设置定时任务...")
        
        # 每日早上9点收集数据
        schedule.every().day.at("09:00").do(self.daily_collection)
        
        # 每日下午3点收集数据
        schedule.every().day.at("15:00").do(self.daily_collection)
        
        # 每日晚上9点收集数据
        schedule.every().day.at("21:00").do(self.daily_collection)
        
        # 每日晚上11点发送汇总报告
        schedule.every().day.at("23:00").do(self.daily_summary_report)
        
        # 每小时检查数据并发送异常报告
        schedule.every().hour.do(self.hourly_check)
        
        self.logger.info("定时任务设置完成")
    
    async def daily_collection(self):
        """每日数据收集任务"""
        try:
            self.logger.info("开始每日数据收集...")
            
            # 收集数据
            await self.collector.collect_depth_data(
                self.collection_symbols, 
                self.collection_duration
            )
            
            # 分析数据
            analysis_result = await self.analyze_collected_data()
            
            # 发送到Lark
            await self.send_to_lark(analysis_result)
            
            self.logger.info("每日数据收集完成")
            
        except Exception as e:
            self.logger.error(f"每日数据收集失败: {e}")
            await self.send_error_notification(f"数据收集失败: {str(e)}")
    
    async def daily_summary_report(self):
        """每日汇总报告"""
        try:
            self.logger.info("生成每日汇总报告...")
            
            # 分析当日所有数据
            summary = await self.generate_daily_summary()
            
            # 发送汇总报告到Lark
            await self.send_summary_to_lark(summary)
            
            self.logger.info("每日汇总报告发送完成")
            
        except Exception as e:
            self.logger.error(f"每日汇总报告失败: {e}")
            await self.send_error_notification(f"汇总报告失败: {str(e)}")
    
    async def hourly_check(self):
        """每小时检查任务"""
        try:
            self.logger.info("执行每小时检查...")
            
            # 检查最新数据
            latest_data = await self.get_latest_data()
            
            if not latest_data:
                await self.send_error_notification("警告: 最近1小时没有收集到数据")
                return
            
            # 检查异常情况
            anomalies = await self.check_anomalies(latest_data)
            
            if anomalies:
                await self.send_anomaly_alert(anomalies)
            
            self.logger.info("每小时检查完成")
            
        except Exception as e:
            self.logger.error(f"每小时检查失败: {e}")
    
    async def analyze_collected_data(self) -> Dict[str, Any]:
        """分析收集的数据"""
        try:
            # 获取最新数据
            latest_data = await self.get_latest_data()
            
            if not latest_data:
                return {"error": "没有找到最新数据"}
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "total_records": len(latest_data),
                "exchanges": list(set([d.get('exchange') for d in latest_data])),
                "symbols": list(set([d.get('symbol') for d in latest_data])),
                "summary": {}
            }
            
            # 按代币分析
            for symbol in self.collection_symbols:
                symbol_data = [d for d in latest_data if d.get('symbol') == symbol]
                if symbol_data:
                    analysis["summary"][symbol] = self.analyze_symbol_data(symbol_data)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"数据分析失败: {e}")
            return {"error": str(e)}
    
    def analyze_symbol_data(self, data: List[Dict]) -> Dict[str, Any]:
        """分析单个代币数据"""
        if not data:
            return {}
        
        # 计算价差
        spreads = [d.get('spread', 0) for d in data if d.get('spread')]
        avg_spread = sum(spreads) / len(spreads) if spreads else 0
        
        # 计算铺单量
        bid_volumes = [d.get('total_bid_volume', 0) for d in data if d.get('total_bid_volume')]
        ask_volumes = [d.get('total_ask_volume', 0) for d in data if d.get('total_ask_volume')]
        
        avg_bid_volume = sum(bid_volumes) / len(bid_volumes) if bid_volumes else 0
        avg_ask_volume = sum(ask_volumes) / len(ask_volumes) if ask_volumes else 0
        
        # 按交易所分析
        exchange_stats = {}
        for d in data:
            exchange = d.get('exchange')
            if exchange not in exchange_stats:
                exchange_stats[exchange] = {
                    'count': 0,
                    'spreads': [],
                    'bid_volumes': [],
                    'ask_volumes': []
                }
            
            exchange_stats[exchange]['count'] += 1
            if d.get('spread'):
                exchange_stats[exchange]['spreads'].append(d['spread'])
            if d.get('total_bid_volume'):
                exchange_stats[exchange]['bid_volumes'].append(d['total_bid_volume'])
            if d.get('total_ask_volume'):
                exchange_stats[exchange]['ask_volumes'].append(d['total_ask_volume'])
        
        # 计算各交易所统计
        for exchange, stats in exchange_stats.items():
            if stats['spreads']:
                stats['avg_spread'] = sum(stats['spreads']) / len(stats['spreads'])
            if stats['bid_volumes']:
                stats['avg_bid_volume'] = sum(stats['bid_volumes']) / len(stats['bid_volumes'])
            if stats['ask_volumes']:
                stats['avg_ask_volume'] = sum(stats['ask_volumes']) / len(stats['ask_volumes'])
        
        return {
            "avg_spread": avg_spread,
            "avg_bid_volume": avg_bid_volume,
            "avg_ask_volume": avg_ask_volume,
            "total_volume": avg_bid_volume + avg_ask_volume,
            "exchange_stats": exchange_stats,
            "record_count": len(data)
        }
    
    async def get_latest_data(self) -> List[Dict]:
        """获取最新数据"""
        try:
            # 查找最新的数据文件
            data_files = list(self.data_dir.glob("depth_data_*.json"))
            if not data_files:
                return []
            
            # 按修改时间排序，获取最新的
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            
            # 读取数据
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取最新数据失败: {e}")
            return []
    
    async def generate_daily_summary(self) -> Dict[str, Any]:
        """生成每日汇总"""
        try:
            # 获取当日所有数据文件
            today = datetime.now().strftime("%Y%m%d")
            data_files = list(self.data_dir.glob(f"depth_data_{today}_*.json"))
            
            all_data = []
            for file in data_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data.extend(data)
                except Exception as e:
                    self.logger.warning(f"读取文件 {file} 失败: {e}")
            
            if not all_data:
                return {"error": "当日没有数据"}
            
            # 生成汇总
            summary = {
                "date": today,
                "total_records": len(all_data),
                "exchanges": list(set([d.get('exchange') for d in all_data])),
                "symbols": list(set([d.get('symbol') for d in all_data])),
                "time_range": {
                    "start": min([d.get('timestamp', 0) for d in all_data]),
                    "end": max([d.get('timestamp', 0) for d in all_data])
                },
                "symbol_analysis": {}
            }
            
            # 按代币分析
            for symbol in self.collection_symbols:
                symbol_data = [d for d in all_data if d.get('symbol') == symbol]
                if symbol_data:
                    summary["symbol_analysis"][symbol] = self.analyze_symbol_data(symbol_data)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"生成每日汇总失败: {e}")
            return {"error": str(e)}
    
    async def check_anomalies(self, data: List[Dict]) -> List[Dict]:
        """检查异常情况"""
        anomalies = []
        
        try:
            # 检查数据量异常
            if len(data) < 10:  # 数据量太少
                anomalies.append({
                    "type": "low_data_volume",
                    "message": f"数据量异常: 只有 {len(data)} 条记录",
                    "severity": "warning"
                })
            
            # 检查价差异常
            for d in data:
                spread = d.get('spread', 0)
                if spread > 0.1:  # 价差超过10%
                    anomalies.append({
                        "type": "high_spread",
                        "message": f"{d.get('exchange')} {d.get('symbol')} 价差异常: {spread:.4f}",
                        "severity": "warning",
                        "exchange": d.get('exchange'),
                        "symbol": d.get('symbol'),
                        "spread": spread
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"异常检查失败: {e}")
            return []
    
    async def send_to_lark(self, analysis_result: Dict[str, Any]):
        """发送分析结果到Lark"""
        try:
            if "error" in analysis_result:
                await self.send_error_notification(analysis_result["error"])
                return
            
            # 格式化消息
            message = self.format_analysis_message(analysis_result)
            
            # 发送到Lark
            success = await self.lark_bot.send_to_lark(message)
            
            if success:
                self.logger.info("分析结果已发送到Lark")
            else:
                self.logger.error("发送到Lark失败")
                
        except Exception as e:
            self.logger.error(f"发送到Lark失败: {e}")
    
    async def send_summary_to_lark(self, summary: Dict[str, Any]):
        """发送汇总报告到Lark"""
        try:
            if "error" in summary:
                await self.send_error_notification(summary["error"])
                return
            
            # 格式化汇总消息
            message = self.format_summary_message(summary)
            
            # 发送到Lark
            success = await self.lark_bot.send_to_lark(message)
            
            if success:
                self.logger.info("汇总报告已发送到Lark")
            else:
                self.logger.error("发送汇总报告到Lark失败")
                
        except Exception as e:
            self.logger.error(f"发送汇总报告到Lark失败: {e}")
    
    async def send_error_notification(self, error_message: str):
        """发送错误通知到Lark"""
        try:
            message = {
                "msg_type": "text",
                "content": {
                    "text": f"🚨 **数据收集系统错误**\n\n{error_message}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
            
            await self.lark_bot.send_to_lark(message)
            
        except Exception as e:
            self.logger.error(f"发送错误通知失败: {e}")
    
    async def send_anomaly_alert(self, anomalies: List[Dict]):
        """发送异常警报到Lark"""
        try:
            message_text = "⚠️ **数据异常警报**\n\n"
            
            for anomaly in anomalies:
                message_text += f"• {anomaly['message']}\n"
            
            message_text += f"\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            message = {
                "msg_type": "text",
                "content": {
                    "text": message_text
                }
            }
            
            await self.lark_bot.send_to_lark(message)
            
        except Exception as e:
            self.logger.error(f"发送异常警报失败: {e}")
    
    def format_analysis_message(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化分析消息"""
        timestamp = analysis.get('timestamp', datetime.now().isoformat())
        total_records = analysis.get('total_records', 0)
        exchanges = analysis.get('exchanges', [])
        symbols = analysis.get('symbols', [])
        summary = analysis.get('summary', {})
        
        message_text = f"📊 **数据收集报告**\n\n"
        message_text += f"⏰ 时间: {timestamp}\n"
        message_text += f"📈 总记录数: {total_records}\n"
        message_text += f"🏢 交易所: {', '.join(exchanges)}\n"
        message_text += f"💰 代币: {', '.join(symbols)}\n\n"
        
        # 添加各代币分析
        for symbol, data in summary.items():
            if isinstance(data, dict):
                message_text += f"**{symbol}**\n"
                message_text += f"• 平均价差: {data.get('avg_spread', 0):.6f}%\n"
                message_text += f"• 平均买量: {data.get('avg_bid_volume', 0):.2f} USDT\n"
                message_text += f"• 平均卖量: {data.get('avg_ask_volume', 0):.2f} USDT\n"
                message_text += f"• 总铺单量: {data.get('total_volume', 0):.2f} USDT\n\n"
        
        return {
            "msg_type": "text",
            "content": {
                "text": message_text
            }
        }
    
    def format_summary_message(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """格式化汇总消息"""
        date = summary.get('date', '')
        total_records = summary.get('total_records', 0)
        exchanges = summary.get('exchanges', [])
        symbols = summary.get('symbols', [])
        symbol_analysis = summary.get('symbol_analysis', {})
        
        message_text = f"📈 **每日数据汇总报告**\n\n"
        message_text += f"📅 日期: {date}\n"
        message_text += f"📊 总记录数: {total_records}\n"
        message_text += f"🏢 交易所: {', '.join(exchanges)}\n"
        message_text += f"💰 代币: {', '.join(symbols)}\n\n"
        
        # 添加各代币汇总
        for symbol, data in symbol_analysis.items():
            if isinstance(data, dict):
                message_text += f"**{symbol} 汇总**\n"
                message_text += f"• 记录数: {data.get('record_count', 0)}\n"
                message_text += f"• 平均价差: {data.get('avg_spread', 0):.6f}%\n"
                message_text += f"• 总铺单量: {data.get('total_volume', 0):.2f} USDT\n"
                
                # 添加交易所统计
                exchange_stats = data.get('exchange_stats', {})
                if exchange_stats:
                    message_text += f"• 交易所统计:\n"
                    for exchange, stats in exchange_stats.items():
                        message_text += f"  - {exchange}: 价差 {stats.get('avg_spread', 0):.6f}%, 铺单量 {stats.get('avg_bid_volume', 0) + stats.get('avg_ask_volume', 0):.2f} USDT\n"
                
                message_text += "\n"
        
        return {
            "msg_type": "text",
            "content": {
                "text": message_text
            }
        }
    
    async def start(self):
        """启动调度器"""
        self.logger.info("启动定时任务调度器...")
        self.setup_schedule()
        self.running = True
        
        # 发送启动通知
        await self.send_startup_notification()
        
        # 运行调度器
        while self.running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                self.logger.info("收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"调度器运行错误: {e}")
                await asyncio.sleep(30)
        
        self.logger.info("调度器已停止")
    
    async def send_startup_notification(self):
        """发送启动通知"""
        try:
            message = {
                "msg_type": "text",
                "content": {
                    "text": f"🚀 **数据收集调度器已启动**\n\n"
                           f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                           f"📊 监控代币: {', '.join(self.collection_symbols)}\n"
                           f"⏱️ 收集间隔: {self.collection_duration}秒\n"
                           f"📅 定时任务:\n"
                           f"• 09:00 - 数据收集\n"
                           f"• 15:00 - 数据收集\n"
                           f"• 21:00 - 数据收集\n"
                           f"• 23:00 - 汇总报告\n"
                           f"• 每小时 - 异常检查"
                }
            }
            
            await self.lark_bot.send_to_lark(message)
            
        except Exception as e:
            self.logger.error(f"发送启动通知失败: {e}")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        self.logger.info("调度器停止信号已发送")


async def main():
    """主函数"""
    scheduler = DataScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        print("\n收到停止信号，正在停止调度器...")
        scheduler.stop()
    except Exception as e:
        print(f"调度器运行出错: {e}")
    finally:
        print("调度器已停止")


if __name__ == "__main__":
    asyncio.run(main())
