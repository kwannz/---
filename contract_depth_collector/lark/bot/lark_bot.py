#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人主程序
支持@代币查询铺单量和手续费点差
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import websockets
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bybit_collector import BybitCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.weex_collector_real import WEEXCollectorReal
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings


class LarkBot:
    """Lark机器人主类"""
    
    def __init__(self):
        """初始化Lark机器人"""
        self.settings = Settings()
        self.logger = self._setup_logger()
        
        # 初始化交易所收集器
        self.collectors = {
            'binance': BinanceCollector(self.settings),
            'gate': GateCollector(self.settings),
            'okx': OKXCollector(self.settings),
            'bingx': BingXCollector(self.settings),
            'bybit': BybitCollector(self.settings),
            'bitunix': BitunixCollector(self.settings),
            'weex': WEEXCollectorReal(self.settings),
            'kucoin': KuCoinCollector(self.settings)
        }
        
        # 代币符号映射
        self.symbol_mapping = {
            'binance': 'USDT',
            'gate': '_USDT',
            'okx': '-USDT',
            'bingx': '-USDT',
            'bybit': 'USDT',
            'bitunix': 'USDT',
            'weex': 'USDT',
            'kucoin': 'USDT'
        }
        
        # WebSocket连接
        self.websocket = None
        self.is_connected = False
        
        # 数据缓存
        self.data_cache = {}
        self.cache_timeout = 30  # 30秒缓存
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('LarkBot')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def get_token_depth_data(self, token: str) -> Dict[str, Any]:
        """获取代币深度数据"""
        try:
            # 清理代币名称
            token = token.upper().strip()
            
            # 检查缓存
            cache_key = f"{token}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            if cache_key in self.data_cache:
                return self.data_cache[cache_key]
            
            # 并行获取所有交易所数据
            tasks = []
            for exchange_name, collector in self.collectors.items():
                symbol = f"{token}{self.symbol_mapping[exchange_name]}"
                task = self._get_exchange_data(exchange_name, collector, symbol)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            exchange_data = {}
            for i, (exchange_name, collector) in enumerate(self.collectors.items()):
                result = results[i]
                if isinstance(result, Exception):
                    self.logger.error(f"{exchange_name} 数据获取异常: {result}")
                    continue
                
                if result:
                    exchange_data[exchange_name] = result
            
            # 计算汇总数据
            summary_data = self._calculate_summary_data(exchange_data)
            
            # 缓存数据
            self.data_cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'token': token,
                'exchanges': exchange_data,
                'summary': summary_data
            }
            
            return self.data_cache[cache_key]
            
        except Exception as e:
            self.logger.error(f"获取代币深度数据失败: {e}")
            return {}
    
    async def _get_exchange_data(self, exchange_name: str, collector, symbol: str) -> Optional[Dict]:
        """获取单个交易所数据"""
        try:
            depth_data = await collector.get_depth_rest(symbol, limit=20)
            if not depth_data:
                return None
            
            # 计算指标
            metrics = self._calculate_metrics(depth_data, exchange_name)
            return metrics
            
        except Exception as e:
            self.logger.error(f"{exchange_name} 数据获取失败: {e}")
            return None
    
    def _calculate_metrics(self, depth_data, exchange_name: str) -> Dict[str, Any]:
        """计算深度指标"""
        try:
            bids = depth_data.bids
            asks = depth_data.asks
            
            if not bids or not asks:
                return {}
            
            # 基础价格信息
            best_bid = round(float(bids[0][0]), 6)
            best_ask = round(float(asks[0][0]), 6)
            mid_price = round((best_bid + best_ask) / 2, 6)
            spread = round(best_ask - best_bid, 6)
            spread_percent = round((spread / mid_price * 100), 6)
            
            # 计算铺单量
            bid_volume_1 = sum([float(bid[0]) * float(bid[1]) for bid in bids[:1]])
            ask_volume_1 = sum([float(ask[0]) * float(ask[1]) for ask in asks[:1]])
            total_volume_1 = bid_volume_1 + ask_volume_1
            
            bid_volume_20 = sum([float(bid[0]) * float(bid[1]) for bid in bids[:20]])
            ask_volume_20 = sum([float(ask[0]) * float(ask[1]) for ask in asks[:20]])
            total_volume_20 = bid_volume_20 + ask_volume_20
            
            return {
                'exchange': exchange_name,
                'symbol': depth_data.symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread': spread,
                'spread_percent': spread_percent,
                '1档_买盘量': round(bid_volume_1, 6),
                '1档_卖盘量': round(ask_volume_1, 6),
                '1档_总铺单量': round(total_volume_1, 6),
                '20档_买盘量': round(bid_volume_20, 6),
                '20档_卖盘量': round(ask_volume_20, 6),
                '20档_总铺单量': round(total_volume_20, 6),
                '买卖比例': round(bid_volume_1 / ask_volume_1, 6) if ask_volume_1 > 0 else 0,
                'timestamp': depth_data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(depth_data.timestamp, 'strftime') else str(depth_data.timestamp)
            }
            
        except Exception as e:
            self.logger.error(f"计算 {exchange_name} 指标失败: {e}")
            return {}
    
    def _calculate_summary_data(self, exchange_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算汇总数据"""
        if not exchange_data:
            return {}
        
        # 计算平均价差
        spreads = [data['spread_percent'] for data in exchange_data.values() if 'spread_percent' in data]
        avg_spread = round(sum(spreads) / len(spreads), 6) if spreads else 0
        min_spread = round(min(spreads), 6) if spreads else 0
        max_spread = round(max(spreads), 6) if spreads else 0
        
        # 计算平均铺单量
        volumes_1 = [data['1档_总铺单量'] for data in exchange_data.values() if '1档_总铺单量' in data]
        volumes_20 = [data['20档_总铺单量'] for data in exchange_data.values() if '20档_总铺单量' in data]
        
        avg_volume_1 = round(sum(volumes_1) / len(volumes_1), 6) if volumes_1 else 0
        avg_volume_20 = round(sum(volumes_20) / len(volumes_20), 6) if volumes_20 else 0
        
        # 找到最佳交易所
        best_liquidity = max(exchange_data.items(), key=lambda x: x[1].get('20档_总铺单量', 0))[0] if exchange_data else 'N/A'
        best_spread = min(exchange_data.items(), key=lambda x: x[1].get('spread_percent', float('inf')))[0] if exchange_data else 'N/A'
        
        return {
            'total_exchanges': len(exchange_data),
            'avg_spread_percent': avg_spread,
            'min_spread_percent': min_spread,
            'max_spread_percent': max_spread,
            'avg_1档_铺单量': avg_volume_1,
            'avg_20档_铺单量': avg_volume_20,
            'best_liquidity_exchange': best_liquidity,
            'best_spread_exchange': best_spread
        }
    
    def format_message(self, data: Dict[str, Any]) -> str:
        """格式化消息"""
        if not data:
            return "❌ 无法获取代币数据"
        
        token = data.get('token', 'UNKNOWN')
        summary = data.get('summary', {})
        exchanges = data.get('exchanges', {})
        
        # 构建消息
        message = f"🔍 **{token} 代币深度分析**\n\n"
        
        # 汇总信息
        message += f"📊 **汇总信息**\n"
        message += f"• 交易所数量: {summary.get('total_exchanges', 0)}\n"
        message += f"• 平均价差: {summary.get('avg_spread_percent', 0):.6f}%\n"
        message += f"• 最小价差: {summary.get('min_spread_percent', 0):.6f}%\n"
        message += f"• 最大价差: {summary.get('max_spread_percent', 0):.6f}%\n"
        message += f"• 平均1档铺单量: {summary.get('avg_1档_铺单量', 0):.6f} USDT\n"
        message += f"• 平均20档铺单量: {summary.get('avg_20档_铺单量', 0):.6f} USDT\n"
        message += f"• 最佳流动性: {summary.get('best_liquidity_exchange', 'N/A')}\n"
        message += f"• 最低价差: {summary.get('best_spread_exchange', 'N/A')}\n\n"
        
        # 各交易所详情
        message += f"📈 **各交易所详情**\n"
        for exchange_name, exchange_data in exchanges.items():
            message += f"**{exchange_name.upper()}**\n"
            message += f"• 价格: {exchange_data.get('best_bid', 0):.6f} / {exchange_data.get('best_ask', 0):.6f}\n"
            message += f"• 价差: {exchange_data.get('spread_percent', 0):.6f}%\n"
            message += f"• 1档铺单量: {exchange_data.get('1档_总铺单量', 0):.6f} USDT\n"
            message += f"• 20档铺单量: {exchange_data.get('20档_总铺单量', 0):.6f} USDT\n"
            message += f"• 买卖比例: {exchange_data.get('买卖比例', 0):.6f}\n\n"
        
        message += f"⏰ 更新时间: {data.get('timestamp', 'N/A')}\n"
        
        return message
    
    async def handle_message(self, message: str) -> str:
        """处理消息"""
        try:
            # 解析@代币消息
            if '@' in message:
                # 提取代币名称
                parts = message.split('@')
                if len(parts) > 1:
                    token = parts[1].strip().split()[0]  # 取第一个词作为代币名
                    self.logger.info(f"查询代币: {token}")
                    
                    # 获取数据
                    data = await self.get_token_depth_data(token)
                    
                    # 格式化消息
                    return self.format_message(data)
            
            # 帮助信息
            if 'help' in message.lower() or '帮助' in message:
                return self._get_help_message()
            
            return "请使用 @代币名称 查询铺单量信息，例如: @BTC"
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return "❌ 处理消息时发生错误"
    
    def _get_help_message(self) -> str:
        """获取帮助信息"""
        return """
🤖 **Lark代币深度分析机器人**

**使用方法:**
• @代币名称 - 查询代币铺单量和价差
• help - 显示帮助信息

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
    
    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """启动WebSocket服务器"""
        self.logger.info(f"启动WebSocket服务器: {host}:{port}")
        
        async def handle_client(websocket, path):
            self.logger.info(f"客户端连接: {websocket.remote_address}")
            self.is_connected = True
            
            try:
                async for message in websocket:
                    self.logger.info(f"收到消息: {message}")
                    
                    # 处理消息
                    response = await self.handle_message(message)
                    
                    # 发送响应
                    await websocket.send(response)
                    
            except websockets.exceptions.ConnectionClosed:
                self.logger.info("客户端断开连接")
            except Exception as e:
                self.logger.error(f"WebSocket处理异常: {e}")
            finally:
                self.is_connected = False
        
        # 启动服务器
        server = await websockets.serve(handle_client, host, port)
        self.logger.info(f"WebSocket服务器已启动: ws://{host}:{port}")
        
        # 保持运行
        await server.wait_closed()
    
    async def run(self):
        """运行机器人"""
        self.logger.info("Lark代币深度分析机器人启动")
        
        # 启动WebSocket服务器
        await self.start_websocket_server()


async def main():
    """主函数"""
    bot = LarkBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
