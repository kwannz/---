#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark Webhook机器人
基于Lark开放平台的Webhook机器人实现
"""

import asyncio
import json
import logging
import hmac
import hashlib
import time
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from aiohttp import web, web_request
import sys
from pathlib import Path
import os
from dataclasses import dataclass

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from exchanges.binance_collector import BinanceCollector
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bybit_collector import BybitCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.weex_collector_real import WEEXCollectorReal
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings
from data_query import DataQuery


class LarkWebhookBot:
    """Lark Webhook机器人"""
    
    def __init__(self):
        """初始化Lark Webhook机器人"""
        self.settings = Settings()
        self.logger = self._setup_logger()
        
        # Lark配置（优先读取环境变量，未设置则使用占位默认值）
        self.webhook_url = os.getenv(
            "LARK_WEBHOOK_URL",
            "https://open.larksuite.com/open-apis/bot/v2/hook/9c4bbe9b-2e01-4d02-9084-151365f73306",
        )
        self.signature_secret = os.getenv("LARK_WEBHOOK_SECRET", "7fvVfwPIgEvIJa1ngHaWPc")
        # 事件订阅签名密钥（Encrypt Key），用于校验回调签名、可与自定义机器人密钥不同
        self.event_encrypt_key = os.getenv("LARK_EVENT_ENCRYPT_KEY", self.signature_secret)
        # 企业自建应用凭据（用于通过开放平台API回复消息）
        self.app_id = os.getenv("LARK_APP_ID", "")
        self.app_secret = os.getenv("LARK_APP_SECRET", "")
        self._tenant_access_token: Optional[str] = None
        self._tenant_token_expire_at: float = 0.0
        
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
        
        # 初始化数据查询器
        self.data_query = DataQuery(data_dir="../data")
        
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
        
        # 数据缓存
        self.data_cache = {}
        self.cache_timeout = 30  # 30秒缓存
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('LarkWebhookBot')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str) -> bool:
        """验证Lark签名"""
        try:
            # 构建待签名字符串
            string_to_sign = f"{timestamp}{nonce}{body}"
            
            # 使用HMAC-SHA256计算签名
            expected_signature = hmac.new(
                # 使用事件订阅的 Encrypt Key
                self.event_encrypt_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Base64编码
            expected_signature = base64.b64encode(expected_signature).decode('utf-8')
            
            # 比较签名
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            self.logger.error(f"签名验证失败: {e}")
            return False

    def _generate_outgoing_sign(self, timestamp: str) -> str:
        """生成Feishu自定义机器人Webhook的签名

        参考官方“自定义机器人-签名校验”算法：
        使用 HMAC-SHA256，key 为 f"{timestamp}\n{secret}"，消息体为空字符串，然后进行 Base64 编码。
        不同语言示例写法略有差异，但等价。
        """
        try:
            string_to_sign = f"{timestamp}\n{self.signature_secret}"
            # 以 string_to_sign 作为 key，空消息体作为 msg 计算 hmac
            h = hmac.new(string_to_sign.encode("utf-8"), msg=b"", digestmod=hashlib.sha256)
            return base64.b64encode(h.digest()).decode("utf-8")
        except Exception as e:
            self.logger.error(f"生成签名失败: {e}, timestamp={timestamp}")
            return ""
    
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
    
    def format_lark_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化Lark消息"""
        if not data:
            return {
                "msg_type": "text",
                "content": {
                    "text": "❌ 无法获取代币数据"
                }
            }
        
        token = data.get('token', 'UNKNOWN')
        summary = data.get('summary', {})
        exchanges = data.get('exchanges', {})
        
        # 构建消息内容
        content = f"🔍 **{token} 代币深度分析**\n\n"
        
        # 汇总信息
        content += f"📊 **汇总信息**\n"
        content += f"• 交易所数量: {summary.get('total_exchanges', 0)}\n"
        content += f"• 平均价差: {summary.get('avg_spread_percent', 0):.6f}%\n"
        content += f"• 最小价差: {summary.get('min_spread_percent', 0):.6f}%\n"
        content += f"• 最大价差: {summary.get('max_spread_percent', 0):.6f}%\n"
        content += f"• 平均1档铺单量: {summary.get('avg_1档_铺单量', 0):.6f} USDT\n"
        content += f"• 平均20档铺单量: {summary.get('avg_20档_铺单量', 0):.6f} USDT\n"
        content += f"• 最佳流动性: {summary.get('best_liquidity_exchange', 'N/A')}\n"
        content += f"• 最低价差: {summary.get('best_spread_exchange', 'N/A')}\n\n"

        # 对比排名（更直观的对比结果）
        if exchanges:
            # 20档总铺单量排名（降序）
            vol_rank = sorted(
                ((ex, v.get('20档_总铺单量', 0)) for ex, v in exchanges.items()),
                key=lambda x: x[1], reverse=True
            )
            # 价差排名（升序）
            spread_rank = sorted(
                ((ex, v.get('spread_percent', 0)) for ex, v in exchanges.items()),
                key=lambda x: x[1]
            )
            content += "🏆 **对比排名**\n"
            if vol_rank:
                top_vol = vol_rank[:3]
                content += "• 20档铺单量TOP3: " + ", ".join([f"{ex}:{val:.2f}" for ex, val in top_vol]) + "\n"
            if spread_rank:
                top_spread = spread_rank[:3]
                content += "• 最低价差TOP3: " + ", ".join([f"{ex}:{val:.6f}%" for ex, val in top_spread]) + "\n\n"
        
        # 排序后展示各交易所详情（按20档总铺单量降序，更突出对比）
        content += f"📈 **各交易所详情（按20档铺单量降序）**\n"
        sorted_items = sorted(
            exchanges.items(),
            key=lambda kv: kv[1].get('20档_总铺单量', 0),
            reverse=True
        )
        for exchange_name, exchange_data in sorted_items:
            content += f"**{exchange_name.upper()}**\n"
            content += f"• 价格: {exchange_data.get('best_bid', 0):.6f} / {exchange_data.get('best_ask', 0):.6f}\n"
            content += f"• 价差: {exchange_data.get('spread_percent', 0):.6f}%\n"
            content += f"• 1档铺单量: {exchange_data.get('1档_总铺单量', 0):.6f} USDT\n"
            content += f"• 20档铺单量: {exchange_data.get('20档_总铺单量', 0):.6f} USDT\n"
            content += f"• 买卖比例: {exchange_data.get('买卖比例', 0):.6f}\n\n"
        
        content += f"⏰ 更新时间: {data.get('timestamp', 'N/A')}\n"
        
        return {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
    
    async def handle_message(self, message: str) -> Dict[str, Any]:
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
                    return self.format_lark_message(data)
            
            # 历史数据分析
            if message.startswith('分析') or message.startswith('trend'):
                parts = message.split()
                if len(parts) > 1:
                    token = parts[1].upper()
                    # 添加USDT后缀
                    if not token.endswith('USDT'):
                        token += 'USDT'
                    days = 7  # 默认7天
                    if len(parts) > 2 and parts[2].isdigit():
                        days = int(parts[2])
                    
                    self.logger.info(f"分析代币趋势: {token}, {days}天")
                    report = self.data_query.generate_report(token, days)
                    return {
                        "msg_type": "text",
                        "content": {
                            "text": report
                        }
                    }
            
            # 数据统计
            if message.startswith('统计') or message.startswith('stats'):
                self.logger.info("获取数据统计")
                stats = self.data_query.get_summary_stats()
                if "error" in stats:
                    return {
                        "msg_type": "text",
                        "content": {
                            "text": f"❌ 获取统计失败: {stats['error']}"
                        }
                    }
                
                stats_text = f"📊 **数据统计报告**\n\n"
                stats_text += f"📈 总记录数: {stats['total_records']}\n"
                stats_text += f"📅 日期范围: {stats['date_range']['start']} - {stats['date_range']['end']}\n"
                stats_text += f"💰 代币: {', '.join(stats['symbols'])}\n"
                stats_text += f"🏢 交易所: {', '.join(stats['exchanges'])}\n\n"
                
                stats_text += "**代币统计:**\n"
                for symbol, symbol_stats in stats['symbol_stats'].items():
                    stats_text += f"• **{symbol}**:\n"
                    stats_text += f"  - 记录数: {symbol_stats['records']}\n"
                    stats_text += f"  - 平均价差: {symbol_stats['avg_spread']:.6f}%\n"
                    stats_text += f"  - 平均铺单量: {symbol_stats['avg_volume']:.2f} USDT\n"
                    stats_text += f"  - 交易所: {len(symbol_stats['exchanges'])}个\n"
                
                return {
                    "msg_type": "text",
                    "content": {
                        "text": stats_text
                    }
                }
            
            # 帮助信息
            if 'help' in message.lower() or '帮助' in message:
                return {
                    "msg_type": "text",
                    "content": {
                        "text": """
🤖 **Lark代币深度分析机器人**

**使用方法:**
• @代币名称 - 查询代币实时铺单量和价差
• 分析 代币名称 [天数] - 分析代币历史趋势
• 统计 - 查看数据统计信息
• help - 显示帮助信息

**示例:**
• @BTC - 查询BTC实时数据
• @ETH - 查询ETH实时数据
• @RIF - 查询RIF实时数据
• 分析 BTC 7 - 分析BTC最近7天趋势
• 分析 ETH 3 - 分析ETH最近3天趋势
• 统计 - 查看数据统计

**支持功能:**
• 实时深度数据查询
• 历史趋势分析
• 多交易所对比分析
• 铺单量和价差分析
• 流动性排名
• 数据统计报告

**数据来源:**
Binance, Gate.io, OKX, BingX, Bybit, Bitunix, WEEX, KuCoin
                        """
                    }
                }
            
            return {
                "msg_type": "text",
                "content": {
                    "text": "请使用 @代币名称 查询铺单量信息，例如: @BTC"
                }
            }
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return {
                "msg_type": "text",
                "content": {
                    "text": "❌ 处理消息时发生错误"
                }
            }
    
    async def webhook_handler(self, request: web_request.Request) -> web.Response:
        """处理Lark Webhook请求"""
        try:
            # 获取请求头
            timestamp = request.headers.get('X-Lark-Request-Timestamp', '')
            nonce = request.headers.get('X-Lark-Request-Nonce', '')
            signature = request.headers.get('X-Lark-Signature', '')
            
            # 获取请求体
            body = await request.text()
            
            # 验证签名
            if not self.verify_signature(timestamp, nonce, body, signature):
                self.logger.warning("签名验证失败")
                return web.Response(status=401, text="Unauthorized")
            
            # 解析请求数据（若启用加密，平台会以明文签名+加密内容推送，这里暂不处理加密payload）
            data = json.loads(body)
            
            # 处理URL验证请求
            if data.get('type') == 'url_verification':
                challenge = data.get('challenge', '')
                self.logger.info(f"URL验证请求: {challenge}")
                return web.Response(text=json.dumps({"challenge": challenge}))
            
            # 处理消息事件
            if data.get('type') == 'event_callback':
                event = data.get('event', {})
                # im:message.receive_v1 或 旧版 'message'
                if event.get('type') in ('message', 'im.message.receive_v1'):
                    msg = event.get('message', {})
                    message_id = msg.get('message_id') or msg.get('message_id_v2') or ''
                    chat_id = msg.get('chat_id', '')
                    message_content = msg.get('content', '')
                    message_text = ''
                    # content 一般为JSON字符串，如 '{"text":"@ETH"}'
                    if isinstance(message_content, str):
                        try:
                            content_obj = json.loads(message_content)
                            message_text = content_obj.get('text', '') or message_content
                        except Exception:
                            message_text = message_content
                    elif isinstance(message_content, dict):
                        message_text = message_content.get('text', '')
                    
                    self.logger.info(f"收到消息: chat_id={chat_id} message_id={message_id} text={message_text}")
                    
                    # 处理消息
                    response = await self.handle_message(message_text)
                    
                    # 优先使用OpenAPI按 message_id 回复；失败则回退到自定义Webhook
                    replied = False
                    if message_id and self.app_id and self.app_secret:
                        replied = await self._reply_via_openapi(message_id, response)
                    if not replied:
                        await self.send_to_lark(response)
                    
                    return web.Response(text="OK")
            
            return web.Response(text="OK")
            
        except Exception as e:
            self.logger.error(f"处理Webhook请求失败: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    async def send_to_lark(self, message: Dict[str, Any]) -> bool:
        """发送消息到Lark"""
        try:
            # 若用户在Lark中启用了“签名校验”，需要在请求体增加 timestamp 与 sign 字段
            timestamp = str(int(time.time()))
            sign = self._generate_outgoing_sign(timestamp) if self.signature_secret else ""

            payload = dict(message)
            if sign:
                # 仅当配置了密钥时才附加签名字段（避免影响未开启签名校验的机器人）
                payload.update({
                    "timestamp": timestamp,
                    "sign": sign,
                })

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        self.logger.info("消息发送成功")
                        return True
                    else:
                        try:
                            err_text = await response.text()
                        except Exception:
                            err_text = ""
                        self.logger.error(f"消息发送失败: {response.status} {err_text}")
                        return False
        except Exception as e:
            self.logger.error(f"发送消息到Lark失败: {e}")
            return False

    async def _get_tenant_access_token(self) -> Optional[str]:
        """获取或缓存 tenant_access_token（用于企业自建应用回复消息）"""
        try:
            if not self.app_id or not self.app_secret:
                return None
            now = time.time()
            if self._tenant_access_token and now < self._tenant_token_expire_at - 60:
                return self._tenant_access_token
            url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
            payload = {"app_id": self.app_id, "app_secret": self.app_secret}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers={"Content-Type": "application/json"}) as resp:
                    data = await resp.json(content_type=None)
                    if data.get("code") == 0 and data.get("tenant_access_token"):
                        self._tenant_access_token = data["tenant_access_token"]
                        expire = data.get("expire", 3600)
                        self._tenant_token_expire_at = now + int(expire)
                        return self._tenant_access_token
                    self.logger.error(f"获取tenant_access_token失败: {data}")
                    return None
        except Exception as e:
            self.logger.error(f"获取tenant_access_token异常: {e}")
            return None

    async def _reply_via_openapi(self, message_id: str, message: Dict[str, Any]) -> bool:
        """通过开放平台API回复消息（优先推荐）"""
        try:
            token = await self._get_tenant_access_token()
            if not token:
                return False
            # 仅支持文本格式（当前format_lark_message返回的正是 text）
            if message.get("msg_type") != "text":
                self.logger.warning("当前仅实现文本回复，已跳过非文本消息")
                return False
            text = message.get("content", {}).get("text", "")
            url = f"https://open.larksuite.com/open-apis/im/v1/messages/{message_id}/reply"
            payload = {
                "msg_type": "text",
                # OpenAPI 需要字符串形式的 JSON 内容
                "content": json.dumps({"text": text}, ensure_ascii=False)
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        if data.get("code") == 0:
                            self.logger.info("OpenAPI 回复成功")
                            return True
                        self.logger.error(f"OpenAPI 回复失败: {data}")
                        return False
                    else:
                        self.logger.error(f"OpenAPI 回复HTTP错误: {resp.status} {await resp.text()}")
                        return False
        except Exception as e:
            self.logger.error(f"OpenAPI 回复异常: {e}")
            return False

    async def set_bot_menu(self, menu_items: Optional[list] = None) -> bool:
        """设置机器人自定义菜单

        需要企业自建应用凭据（LARK_APP_ID/LARK_APP_SECRET）。
        注：具体菜单结构以官方文档为准，这里给出常见结构示例。
        """
        try:
            token = await self._get_tenant_access_token()
            if not token:
                self.logger.error("未配置 LARK_APP_ID/LARK_APP_SECRET，无法设置菜单")
                return False

            # 默认菜单项：点击后由平台向群里发送指定文本，触发你的消息处理逻辑
            default_menu = [
                {"name": "查询 BTC", "type": "message", "text": "@BTC"},
                {"name": "查询 ETH", "type": "message", "text": "@ETH"},
                {"name": "帮助", "type": "message", "text": "help"}
            ]
            items = menu_items or default_menu

            url = "https://open.larksuite.com/open-apis/bot/v3/bot/menu/set"
            bot_id = os.getenv("LARK_BOT_ID", "")
            payload = {
                "menu": {
                    "button": items
                }
            }
            if bot_id:
                payload["bot_id"] = bot_id
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8"
            }

            async with aiohttp.ClientSession() as session:
                # 策略1：menu.button + type=message + text
                async with session.post(url, json=payload, headers=headers) as resp:
                    text = await resp.text()
                    ok = resp.status == 200 and ("\"code\":0" in text or '"code": 0' in text)
                    if ok:
                        self.logger.info("机器人菜单设置成功（button + message+text）")
                        return True
                    self.logger.warning(f"菜单设置失败（button+message+text）: HTTP {resp.status} {text}")

                # 策略2：menu.buttons（有些文档或版本使用复数）
                payload2 = dict(payload)
                payload2["menu"] = {"buttons": items}
                async with session.post(url, json=payload2, headers=headers) as resp:
                    text = await resp.text()
                    ok = resp.status == 200 and ("\"code\":0" in text or '"code": 0' in text)
                    if ok:
                        self.logger.info("机器人菜单设置成功（buttons + message+text）")
                        return True
                    self.logger.warning(f"菜单设置失败（buttons+message+text）: HTTP {resp.status} {text}")

                # 策略3：type=lark_cmd + value，适配仅支持命令按钮的场景
                def to_cmd_items(items_in: list) -> list:
                    out = []
                    for it in items_in:
                        name = it.get("name") or it.get("text") or "菜单项"
                        val = it.get("text") or it.get("value") or "help"
                        out.append({
                            "name": name,
                            "type": "lark_cmd",
                            "value": val
                        })
                    return out

                payload3 = {"menu": {"button": to_cmd_items(items)}}
                if bot_id:
                    payload3["bot_id"] = bot_id
                async with session.post(url, json=payload3, headers=headers) as resp:
                    text = await resp.text()
                    ok = resp.status == 200 and ("\"code\":0" in text or '"code": 0' in text)
                    if ok:
                        self.logger.info("机器人菜单设置成功（button + lark_cmd+value）")
                        return True
                    self.logger.error(f"菜单设置失败（尝试三种payload均失败）: HTTP {resp.status} {text}")
                    return False
        except Exception as e:
            self.logger.error(f"设置机器人菜单异常: {e}")
            return False
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """启动Webhook服务器"""
        app = web.Application()
        app.router.add_post('/webhook', self.webhook_handler)
        
        self.logger.info(f"启动Lark Webhook服务器: {host}:{port}")
        self.logger.info(f"Webhook地址: http://{host}:{port}/webhook")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        self.logger.info("Lark Webhook服务器已启动")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭服务器...")
        finally:
            await runner.cleanup()
    
    async def test_webhook(self):
        """测试Webhook功能"""
        self.logger.info("🧪 开始测试Lark Webhook功能")
        
        # 测试代币查询
        test_tokens = ['BTC', 'ETH', 'RIF']
        
        for token in test_tokens:
            self.logger.info(f"测试代币: {token}")
            try:
                data = await self.get_token_depth_data(token)
                if data:
                    message = self.format_lark_message(data)
                    self.logger.info(f"✅ {token} 数据获取成功")
                    self.logger.info(f"消息长度: {len(str(message))} 字符")
                else:
                    self.logger.warning(f"❌ {token} 数据获取失败")
            except Exception as e:
                self.logger.error(f"❌ {token} 测试异常: {e}")
        
        self.logger.info("🎉 Webhook功能测试完成")


async def main():
    """主函数"""
    bot = LarkWebhookBot()
    
    # 测试Webhook功能
    await bot.test_webhook()
    
    # 启动Webhook服务器
    await bot.start_server()


if __name__ == "__main__":
    asyncio.run(main())
