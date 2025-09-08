#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人消息处理器
"""

import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from ..utils.helpers import TokenValidator, MessageFormatter, DataProcessor, RateLimiter


class MessageHandler:
    """消息处理器"""
    
    def __init__(self, bot_instance):
        """初始化消息处理器"""
        self.bot = bot_instance
        self.logger = logging.getLogger('MessageHandler')
        self.rate_limiter = RateLimiter(max_requests=10, time_window=60)  # 每分钟10个请求
        
        # 命令处理器映射
        self.command_handlers = {
            'help': self._handle_help,
            'status': self._handle_status,
            'exchanges': self._handle_exchanges,
            'ping': self._handle_ping,
            'clear': self._handle_clear,
            'config': self._handle_config
        }
    
    async def handle_message(self, message: str, user_id: Optional[str] = None) -> str:
        """处理消息"""
        try:
            # 速率限制检查
            if not self.rate_limiter.is_allowed():
                wait_time = self.rate_limiter.get_wait_time()
                return f"⏰ 请求过于频繁，请等待 {wait_time:.1f} 秒后重试"
            
            # 清理消息
            message = message.strip()
            if not message:
                return "❌ 消息不能为空"
            
            # 记录消息
            self.logger.info(f"处理消息: {message} (用户: {user_id})")
            
            # 解析命令
            command, args = self._parse_message(message)
            
            # 处理命令
            if command in self.command_handlers:
                return await self.command_handlers[command](args)
            elif command == 'query':
                return await self._handle_token_query(args)
            else:
                return await self._handle_unknown_command(message)
                
        except Exception as e:
            self.logger.error(f"处理消息异常: {e}")
            return "❌ 处理消息时发生错误"
    
    def _parse_message(self, message: str) -> tuple:
        """解析消息"""
        # 检查是否是@代币查询
        if message.startswith('@'):
            token = message[1:].strip().split()[0]
            return 'query', token
        
        # 检查是否是命令
        parts = message.split()
        if parts:
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            return command, args
        
        return 'unknown', []
    
    async def _handle_token_query(self, token: str) -> str:
        """处理代币查询"""
        try:
            # 验证代币
            if not TokenValidator.is_valid_token(token):
                return f"❌ 无效的代币符号: {token}"
            
            # 标准化代币
            normalized_token = TokenValidator.normalize_token(token)
            
            # 获取数据
            data = await self.bot.get_token_depth_data(normalized_token)
            
            if not data:
                return f"❌ 无法获取 {normalized_token} 的数据"
            
            # 格式化消息
            return self.bot.format_message(data)
            
        except Exception as e:
            self.logger.error(f"处理代币查询异常: {e}")
            return f"❌ 查询 {token} 时发生错误"
    
    async def _handle_help(self, args: List[str]) -> str:
        """处理帮助命令"""
        return """
🤖 **Lark代币深度分析机器人**

**基本命令:**
• @代币名称 - 查询代币铺单量和价差
• help - 显示帮助信息
• status - 显示机器人状态
• exchanges - 显示支持的交易所
• ping - 测试连接
• clear - 清空缓存
• config - 显示配置信息

**示例:**
• @BTC - 查询BTC铺单量
• @ETH - 查询ETH铺单量
• @RIF - 查询RIF铺单量

**支持功能:**
• 实时深度数据查询
• 多交易所对比分析
• 铺单量和价差分析
• 流动性排名

**数据来源:**
Binance, Gate.io, OKX, BingX, Bybit, Bitunix, WEEX, KuCoin
        """
    
    async def _handle_status(self, args: List[str]) -> str:
        """处理状态命令"""
        try:
            # 获取机器人状态
            status = {
                '运行时间': '正常',
                'WebSocket连接': '已连接' if self.bot.is_connected else '未连接',
                '缓存大小': len(self.bot.data_cache),
                '支持的交易所': len(self.bot.collectors),
                '当前时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            message = "📊 **机器人状态**\n\n"
            for key, value in status.items():
                message += f"• {key}: {value}\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"处理状态命令异常: {e}")
            return "❌ 获取状态信息失败"
    
    async def _handle_exchanges(self, args: List[str]) -> str:
        """处理交易所命令"""
        try:
            exchanges = list(self.bot.collectors.keys())
            
            message = "🏢 **支持的交易所**\n\n"
            for i, exchange in enumerate(exchanges, 1):
                message += f"{i}. {exchange.upper()}\n"
            
            message += f"\n总计: {len(exchanges)} 个交易所"
            
            return message
            
        except Exception as e:
            self.logger.error(f"处理交易所命令异常: {e}")
            return "❌ 获取交易所信息失败"
    
    async def _handle_ping(self, args: List[str]) -> str:
        """处理ping命令"""
        return "🏓 Pong! 机器人运行正常"
    
    async def _handle_clear(self, args: List[str]) -> str:
        """处理清空缓存命令"""
        try:
            self.bot.data_cache.clear()
            return "✅ 缓存已清空"
        except Exception as e:
            self.logger.error(f"清空缓存异常: {e}")
            return "❌ 清空缓存失败"
    
    async def _handle_config(self, args: List[str]) -> str:
        """处理配置命令"""
        try:
            config = self.bot.settings
            
            message = "⚙️ **机器人配置**\n\n"
            message += f"• 缓存超时: {getattr(config, 'cache_timeout', 30)} 秒\n"
            message += f"• 速率限制: {getattr(config, 'rate_limit', 1.0)} 秒\n"
            message += f"• 超时设置: {getattr(config, 'timeout', 30)} 秒\n"
            message += f"• 支持的交易所: {len(self.bot.collectors)} 个\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"处理配置命令异常: {e}")
            return "❌ 获取配置信息失败"
    
    async def _handle_unknown_command(self, message: str) -> str:
        """处理未知命令"""
        return f"❌ 未知命令: {message}\n\n输入 'help' 查看可用命令"
    
    def add_command_handler(self, command: str, handler: Callable) -> None:
        """添加自定义命令处理器"""
        self.command_handlers[command] = handler
    
    def remove_command_handler(self, command: str) -> None:
        """移除命令处理器"""
        if command in self.command_handlers:
            del self.command_handlers[command]
    
    def get_command_list(self) -> List[str]:
        """获取命令列表"""
        return list(self.command_handlers.keys())


class AdvancedMessageHandler(MessageHandler):
    """高级消息处理器"""
    
    def __init__(self, bot_instance):
        """初始化高级消息处理器"""
        super().__init__(bot_instance)
        
        # 添加高级命令
        self.command_handlers.update({
            'compare': self._handle_compare,
            'rank': self._handle_rank,
            'history': self._handle_history,
            'alert': self._handle_alert
        })
    
    async def _handle_compare(self, args: List[str]) -> str:
        """处理对比命令"""
        if len(args) < 2:
            return "❌ 对比命令需要至少2个代币，例如: compare BTC ETH"
        
        try:
            tokens = args[:2]  # 只取前两个代币
            results = []
            
            for token in tokens:
                if not TokenValidator.is_valid_token(token):
                    return f"❌ 无效的代币符号: {token}"
                
                normalized_token = TokenValidator.normalize_token(token)
                data = await self.bot.get_token_depth_data(normalized_token)
                
                if data:
                    results.append((token, data))
            
            if len(results) < 2:
                return "❌ 无法获取足够的代币数据进行对比"
            
            # 格式化对比结果
            message = f"🔍 **代币对比分析**\n\n"
            
            for token, data in results:
                summary = data.get('summary', {})
                message += f"**{token}**\n"
                message += f"• 平均价差: {summary.get('avg_spread_percent', 0):.6f}%\n"
                message += f"• 平均20档铺单量: {summary.get('avg_20档_铺单量', 0):.6f} USDT\n"
                message += f"• 最佳流动性: {summary.get('best_liquidity_exchange', 'N/A')}\n\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"处理对比命令异常: {e}")
            return "❌ 对比分析失败"
    
    async def _handle_rank(self, args: List[str]) -> str:
        """处理排名命令"""
        if not args:
            return "❌ 排名命令需要代币名称，例如: rank BTC"
        
        token = args[0]
        
        try:
            if not TokenValidator.is_valid_token(token):
                return f"❌ 无效的代币符号: {token}"
            
            normalized_token = TokenValidator.normalize_token(token)
            data = await self.bot.get_token_depth_data(normalized_token)
            
            if not data:
                return f"❌ 无法获取 {normalized_token} 的数据"
            
            exchanges = data.get('exchanges', {})
            if not exchanges:
                return f"❌ {normalized_token} 没有可用的交易所数据"
            
            # 计算排名
            liquidity_rankings = DataProcessor.calculate_rankings(exchanges, '20档_总铺单量')
            spread_rankings = DataProcessor.calculate_rankings(exchanges, 'spread_percent')
            
            # 格式化排名结果
            message = f"🏆 **{normalized_token} 交易所排名**\n\n"
            
            message += "**流动性排名 (20档铺单量):**\n"
            for exchange, rank in sorted(liquidity_rankings.items(), key=lambda x: x[1]):
                volume = exchanges[exchange].get('20档_总铺单量', 0)
                message += f"{rank}. {exchange.upper()}: {volume:.6f} USDT\n"
            
            message += "\n**价差排名 (越小越好):**\n"
            for exchange, rank in sorted(spread_rankings.items(), key=lambda x: x[1]):
                spread = exchanges[exchange].get('spread_percent', 0)
                message += f"{rank}. {exchange.upper()}: {spread:.6f}%\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"处理排名命令异常: {e}")
            return f"❌ 排名分析失败"
    
    async def _handle_history(self, args: List[str]) -> str:
        """处理历史命令"""
        return "📈 历史数据功能正在开发中..."
    
    async def _handle_alert(self, args: List[str]) -> str:
        """处理警报命令"""
        return "🚨 警报功能正在开发中..."
