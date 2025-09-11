#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户反馈处理器
增强Lark机器人的用户交互功能，处理各种用户反馈和命令
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path


class FeedbackHandler:
    """用户反馈处理器"""
    
    def __init__(self, lark_bot=None):
        """初始化反馈处理器
        
        Args:
            lark_bot: LarkWebhookBot实例
        """
        self.lark_bot = lark_bot
        self.command_history = []  # 命令历史记录
        self.user_preferences = {}  # 用户偏好设置
        
        # 支持的命令模式
        self.command_patterns = {
            'token_query': r'@(\w+)',  # @BTC, @ETH 等
            'analysis': r'分析\s+(\w+)(?:\s+(\d+))?',  # 分析 BTC 7
            'compare': r'对比\s+(\w+)\s+(\w+)',  # 对比 BTC ETH
            'trend': r'趋势\s+(\w+)(?:\s+(\d+))?',  # 趋势 BTC 30
            'alert': r'提醒\s+(\w+)\s+([\d.]+)',  # 提醒 BTC 50000
            'stats': r'统计|数据统计|stats',  # 统计信息
            'help': r'帮助|help|使用说明',  # 帮助信息
            'settings': r'设置\s+(\w+)\s+(.+)',  # 设置 format detailed
            'history': r'历史|记录|history',  # 历史记录
            'export': r'导出\s+(\w+)(?:\s+(\w+))?',  # 导出 BTC json
            'subscription': r'订阅\s+(\w+)',  # 订阅 BTC
            'unsubscribe': r'取消订阅\s+(\w+)',  # 取消订阅 BTC
        }
        
        # 用户订阅管理
        self.subscriptions = {}
        
    async def handle_user_message(self, message: str, user_id: str = None, chat_id: str = None) -> Dict[str, Any]:
        """处理用户消息
        
        Args:
            message: 用户消息内容
            user_id: 用户ID
            chat_id: 聊天ID
            
        Returns:
            Dict: 响应消息
        """
        try:
            # 记录命令历史
            self._record_command(message, user_id, chat_id)
            
            # 去除多余空格并转换为小写进行匹配
            clean_message = message.strip()
            
            # 匹配命令模式
            for command_type, pattern in self.command_patterns.items():
                match = re.search(pattern, clean_message, re.IGNORECASE)
                if match:
                    # 调用对应的处理方法
                    handler_method = getattr(self, f'_handle_{command_type}', None)
                    if handler_method:
                        return await handler_method(match, clean_message, user_id, chat_id)
            
            # 如果没有匹配到任何命令，返回默认帮助信息
            return await self._handle_unknown_command(clean_message, user_id, chat_id)
            
        except Exception as e:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 处理消息时出错: {str(e)}\n\n💡 请输入 'help' 查看使用说明"
                }
            }
    
    async def _handle_token_query(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理代币查询 @BTC"""
        token = match.group(1).upper()
        
        if not self.lark_bot:
            return {
                "msg_type": "text",
                "content": {
                    "text": "❌ 机器人未初始化，无法查询数据"
                }
            }
        
        try:
            # 获取代币数据
            data = await self.lark_bot.get_token_depth_data(token)
            
            if data:
                # 使用机器人的格式化方法
                response = self.lark_bot.format_lark_message(data)
                
                # 添加用户偏好格式
                user_format = self.user_preferences.get(user_id, {}).get('format', 'default')
                if user_format == 'simple':
                    response = self._format_simple_token_data(data, token)
                elif user_format == 'detailed':
                    response = self._format_detailed_token_data(data, token)
                
                return response
            else:
                return {
                    "msg_type": "text",
                    "content": {
                        "text": f"❌ 无法获取 {token} 的数据\n\n💡 请检查代币符号是否正确，支持的代币: BTC, ETH, RIF 等"
                    }
                }
                
        except Exception as e:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 查询 {token} 数据时出错: {str(e)}"
                }
            }
    
    async def _handle_analysis(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理分析命令 分析 BTC 7"""
        token = match.group(1).upper()
        days = int(match.group(2)) if match.group(2) else 7
        
        try:
            # 这里可以集成历史数据分析功能
            if not self.lark_bot or not hasattr(self.lark_bot, 'data_query'):
                return {
                    "msg_type": "text",
                    "content": {
                        "text": f"❌ 历史数据分析功能暂未可用\n\n💡 请使用 @{token} 查询实时数据"
                    }
                }
            
            # 调用数据查询器的分析功能
            analysis_result = self.lark_bot.data_query.analyze_token_trend(token, days)
            
            if "error" in analysis_result:
                return {
                    "msg_type": "text",
                    "content": {
                        "text": f"❌ 分析 {token} 失败: {analysis_result['error']}"
                    }
                }
            
            # 格式化分析结果
            content = f"📊 **{token} {days}天趋势分析**\n\n"
            
            # 基础统计
            stats = analysis_result.get('stats', {})
            content += f"📈 **基础统计**:\n"
            content += f"  • 总记录数: {stats.get('total_records', 0)}\n"
            content += f"  • 平均价差: {stats.get('avg_spread', 0):.6f}%\n"
            content += f"  • 平均铺单量: {stats.get('avg_volume', 0):.2f} USDT\n\n"
            
            # 趋势分析
            trend = analysis_result.get('trend', {})
            if trend:
                content += f"📊 **趋势分析**:\n"
                content += f"  • 价差趋势: {trend.get('spread_trend', '平稳')}\n"
                content += f"  • 流动性趋势: {trend.get('volume_trend', '平稳')}\n"
                content += f"  • 最佳交易所: {trend.get('best_exchange', 'N/A')}\n\n"
            
            content += f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }
            
        except Exception as e:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 分析 {token} 时出错: {str(e)}"
                }
            }
    
    async def _handle_compare(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理对比命令 对比 BTC ETH"""
        token1 = match.group(1).upper()
        token2 = match.group(2).upper()
        
        if not self.lark_bot:
            return {
                "msg_type": "text",
                "content": {
                    "text": "❌ 机器人未初始化，无法执行对比"
                }
            }
        
        try:
            # 获取两个代币的数据
            data1 = await self.lark_bot.get_token_depth_data(token1)
            data2 = await self.lark_bot.get_token_depth_data(token2)
            
            if not data1 or not data2:
                missing = []
                if not data1:
                    missing.append(token1)
                if not data2:
                    missing.append(token2)
                return {
                    "msg_type": "text",
                    "content": {
                        "text": f"❌ 无法获取 {', '.join(missing)} 的数据"
                    }
                }
            
            # 构建对比结果
            content = f"⚖️ **{token1} vs {token2} 对比分析**\n\n"
            
            # 提取汇总数据
            summary1 = data1.get('summary', {})
            summary2 = data2.get('summary', {})
            
            # 基础对比
            content += f"📊 **基础对比**:\n"
            content += f"| 指标 | {token1} | {token2} | 优势 |\n"
            content += f"|------|------|------|------|\n"
            
            # 交易所数量对比
            exchanges1 = summary1.get('total_exchanges', 0)
            exchanges2 = summary2.get('total_exchanges', 0)
            ex_winner = token1 if exchanges1 > exchanges2 else token2 if exchanges2 > exchanges1 else "平手"
            content += f"| 交易所数量 | {exchanges1} | {exchanges2} | {ex_winner} |\n"
            
            # 平均价差对比
            spread1 = summary1.get('avg_spread_percent', 0)
            spread2 = summary2.get('avg_spread_percent', 0)
            spread_winner = token1 if spread1 < spread2 else token2 if spread2 < spread1 else "平手"
            content += f"| 平均价差 | {spread1:.6f}% | {spread2:.6f}% | {spread_winner} |\n"
            
            # 平均铺单量对比
            volume1 = summary1.get('avg_20档_铺单量', 0)
            volume2 = summary2.get('avg_20档_铺单量', 0)
            volume_winner = token1 if volume1 > volume2 else token2 if volume2 > volume1 else "平手"
            content += f"| 平均铺单量 | {volume1:.2f} | {volume2:.2f} | {volume_winner} |\n\n"
            
            # 综合评价
            score1 = self._calculate_token_score(summary1)
            score2 = self._calculate_token_score(summary2)
            overall_winner = token1 if score1 > score2 else token2 if score2 > score1 else "平手"
            
            content += f"🏆 **综合评价**:\n"
            content += f"  • {token1} 得分: {score1:.1f}/10\n"
            content += f"  • {token2} 得分: {score2:.1f}/10\n"
            content += f"  • 综合优势: {overall_winner}\n\n"
            
            content += f"🕐 对比时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }
            
        except Exception as e:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 对比 {token1} 和 {token2} 时出错: {str(e)}"
                }
            }
    
    async def _handle_alert(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理提醒设置 提醒 BTC 50000"""
        token = match.group(1).upper()
        price_threshold = float(match.group(2))
        
        # 这是一个价格提醒功能的示例实现
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = {}
        
        if 'alerts' not in self.subscriptions[user_id]:
            self.subscriptions[user_id]['alerts'] = {}
        
        self.subscriptions[user_id]['alerts'][token] = {
            'threshold': price_threshold,
            'created_at': datetime.now().isoformat(),
            'chat_id': chat_id
        }
        
        return {
            "msg_type": "text",
            "content": {
                "text": f"✅ **价格提醒已设置**\n\n"
                       f"💰 代币: {token}\n"
                       f"💵 触发价格: {price_threshold:,.2f} USDT\n"
                       f"⏰ 设置时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                       f"💡 当 {token} 价格达到 {price_threshold:,.2f} 时，我会通知你"
            }
        }
    
    async def _handle_settings(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理设置命令 设置 format detailed"""
        setting_key = match.group(1).lower()
        setting_value = match.group(2).strip()
        
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        # 支持的设置项
        valid_settings = {
            'format': ['default', 'simple', 'detailed'],
            'language': ['zh', 'en'],
            'timezone': ['UTC', 'Asia/Shanghai'],
            'notifications': ['on', 'off']
        }
        
        if setting_key not in valid_settings:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 不支持的设置项: {setting_key}\n\n"
                           f"📋 支持的设置项:\n" +
                           "\n".join([f"  • {k}: {', '.join(v)}" for k, v in valid_settings.items()])
                }
            }
        
        if setting_value not in valid_settings[setting_key]:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 不支持的设置值: {setting_value}\n\n"
                           f"📋 {setting_key} 的有效值: {', '.join(valid_settings[setting_key])}"
                }
            }
        
        self.user_preferences[user_id][setting_key] = setting_value
        
        return {
            "msg_type": "text",
            "content": {
                "text": f"✅ **设置已更新**\n\n"
                       f"🔧 设置项: {setting_key}\n"
                       f"📝 新值: {setting_value}\n\n"
                       f"💡 设置将在下次查询时生效"
            }
        }
    
    async def _handle_history(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理历史记录命令"""
        user_commands = [cmd for cmd in self.command_history if cmd.get('user_id') == user_id]
        
        if not user_commands:
            return {
                "msg_type": "text",
                "content": {
                    "text": "📝 暂无历史记录\n\n💡 使用 @BTC 等命令开始查询数据"
                }
            }
        
        # 显示最近10条记录
        recent_commands = user_commands[-10:]
        
        content = f"📋 **历史记录** (最近10条)\n\n"
        
        for i, cmd in enumerate(recent_commands, 1):
            timestamp = datetime.fromisoformat(cmd['timestamp']).strftime('%m-%d %H:%M')
            content += f"{i}. {timestamp} - {cmd['message']}\n"
        
        content += f"\n📊 总命令数: {len(user_commands)}"
        
        return {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
    
    async def _handle_stats(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理统计命令"""
        if not self.lark_bot or not hasattr(self.lark_bot, 'data_query'):
            return {
                "msg_type": "text",
                "content": {
                    "text": "❌ 数据查询功能暂未可用"
                }
            }
        
        try:
            # 调用现有的统计功能
            stats = self.lark_bot.data_query.get_summary_stats()
            
            if "error" in stats:
                return {
                    "msg_type": "text",
                    "content": {
                        "text": f"❌ 获取统计失败: {stats['error']}"
                    }
                }
            
            # 格式化统计结果
            content = f"📊 **系统数据统计**\n\n"
            content += f"📈 总记录数: {stats['total_records']}\n"
            content += f"📅 数据范围: {stats['date_range']['start']} - {stats['date_range']['end']}\n"
            content += f"💰 支持代币: {', '.join(stats['symbols'])}\n"
            content += f"🏢 支持交易所: {', '.join(stats['exchanges'])}\n\n"
            
            # 用户个人统计
            user_commands = [cmd for cmd in self.command_history if cmd.get('user_id') == user_id]
            content += f"👤 **个人统计**:\n"
            content += f"  • 查询次数: {len(user_commands)}\n"
            
            if user_commands:
                last_query = datetime.fromisoformat(user_commands[-1]['timestamp'])
                content += f"  • 最后查询: {last_query.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            return {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }
            
        except Exception as e:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ 获取统计信息时出错: {str(e)}"
                }
            }
    
    async def _handle_help(self, match, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理帮助命令"""
        return {
            "msg_type": "text",
            "content": {
                "text": """🤖 **增强版Lark代币分析机器人**

**📋 基础查询:**
• @代币名称 - 查询实时数据 (如: @BTC, @ETH)
• 统计 - 查看系统数据统计
• 历史 - 查看个人查询历史

**📊 高级分析:**
• 分析 代币名称 [天数] - 历史趋势分析 (如: 分析 BTC 7)
• 对比 代币1 代币2 - 代币对比分析 (如: 对比 BTC ETH)
• 趋势 代币名称 [天数] - 价格趋势分析

**⚙️ 个人设置:**
• 设置 format [default/simple/detailed] - 设置显示格式
• 设置 notifications [on/off] - 设置通知开关

**🔔 提醒功能:**
• 提醒 代币名称 价格 - 设置价格提醒 (如: 提醒 BTC 50000)
• 订阅 代币名称 - 订阅代币更新
• 取消订阅 代币名称 - 取消订阅

**📤 数据导出:**
• 导出 代币名称 [格式] - 导出历史数据

**💡 使用提示:**
- 支持的代币: BTC, ETH, RIF 等
- 数据来源: 8个主流交易所实时数据
- 更新频率: 5分钟一次

输入任意命令开始使用! 🚀"""
            }
        }
    
    async def _handle_unknown_command(self, message: str, user_id: str, chat_id: str) -> Dict[str, Any]:
        """处理未知命令"""
        return {
            "msg_type": "text",
            "content": {
                "text": f"❓ 不理解的命令: {message}\n\n"
                       f"💡 输入 'help' 查看所有可用命令\n\n"
                       f"🔍 快速开始:\n"
                       f"  • @BTC - 查询BTC数据\n"
                       f"  • @ETH - 查询ETH数据\n"
                       f"  • 统计 - 查看数据统计"
            }
        }
    
    def _record_command(self, message: str, user_id: str, chat_id: str):
        """记录用户命令"""
        self.command_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'chat_id': chat_id,
            'message': message
        })
        
        # 只保留最近1000条记录
        if len(self.command_history) > 1000:
            self.command_history = self.command_history[-1000:]
    
    def _calculate_token_score(self, summary: Dict[str, Any]) -> float:
        """计算代币综合评分"""
        try:
            # 基础分数
            score = 5.0
            
            # 交易所数量加分 (最多+2分)
            exchanges = summary.get('total_exchanges', 0)
            score += min(2.0, exchanges * 0.3)
            
            # 价差扣分 (价差越小越好)
            avg_spread = summary.get('avg_spread_percent', 0)
            if avg_spread > 0:
                score -= min(2.0, avg_spread * 10)  # 0.1%价差扣1分
            
            # 流动性加分 (铺单量越大越好)
            avg_volume = summary.get('avg_20档_铺单量', 0)
            if avg_volume > 10000:
                score += min(2.0, (avg_volume - 10000) / 50000)  # 每5万加1分
            
            return max(0, min(10, score))
            
        except Exception:
            return 5.0
    
    def _format_simple_token_data(self, data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """简单格式的代币数据"""
        summary = data.get('summary', {})
        
        content = f"💰 **{token}**\n"
        content += f"💹 平均价差: {summary.get('avg_spread_percent', 0):.4f}%\n"
        content += f"💰 平均铺单量: {summary.get('avg_20档_铺单量', 0):,.0f} USDT\n"
        content += f"🏢 交易所: {summary.get('total_exchanges', 0)}个\n"
        content += f"🥇 最佳流动性: {summary.get('best_liquidity_exchange', 'N/A')}"
        
        return {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
    
    def _format_detailed_token_data(self, data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """详细格式的代币数据"""
        # 使用原有的详细格式，这里可以进一步定制
        return self.lark_bot.format_lark_message(data)


# 测试代码
if __name__ == "__main__":
    async def test_feedback_handler():
        handler = FeedbackHandler()
        
        # 测试不同的命令
        test_commands = [
            "@BTC",
            "分析 ETH 7", 
            "对比 BTC ETH",
            "设置 format simple",
            "help",
            "统计"
        ]
        
        for cmd in test_commands:
            print(f"\n测试命令: {cmd}")
            response = await handler.handle_user_message(cmd, "test_user", "test_chat")
            print(f"响应: {response['content']['text'][:200]}...")
    
    asyncio.run(test_feedback_handler())