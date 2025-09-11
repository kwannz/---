#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON数据格式化器
用于将收集的JSON数据格式化为适合Lark显示的消息格式
"""

import json
from datetime import datetime
from typing import Dict, Any, List


class JsonFormatter:
    """JSON数据格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        pass
    
    def format_summary_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化汇总消息
        
        Args:
            data: JSON数据
            
        Returns:
            Dict: Lark消息格式
        """
        try:
            collection_info = data.get("collection_info", {})
            data_records = data.get("data_records", [])
            
            # 基础信息
            timestamp = collection_info.get("timestamp", "未知")
            total_records = collection_info.get("total_records", 0)
            exchanges = collection_info.get("exchanges", [])
            symbols = collection_info.get("symbols", [])
            
            # 统计信息
            stats = self._calculate_statistics(data_records)
            
            # 构建消息内容
            content = f"📊 **数据收集汇总报告**\n\n"
            
            # 基础信息
            content += f"🕐 **收集时间**: {self._format_timestamp(timestamp)}\n"
            content += f"📈 **总记录数**: {total_records}\n"
            content += f"🏢 **交易所数量**: {len(exchanges)}\n"
            content += f"💰 **代币数量**: {len(symbols)}\n\n"
            
            # 交易所列表
            if exchanges:
                content += f"**📍 交易所列表**:\n"
                for exchange in exchanges:
                    content += f"  • {exchange}\n"
                content += "\n"
            
            # 代币列表
            if symbols:
                content += f"**💎 代币列表**:\n"
                for symbol in symbols:
                    content += f"  • {symbol}\n"
                content += "\n"
            
            # 统计数据
            if stats:
                content += f"**📊 数据统计**:\n"
                content += f"  • 平均价差: {stats.get('avg_spread', 0):.6f}%\n"
                content += f"  • 最大价差: {stats.get('max_spread', 0):.6f}%\n"
                content += f"  • 最小价差: {stats.get('min_spread', 0):.6f}%\n"
                content += f"  • 平均铺单量: {stats.get('avg_volume', 0):.2f} USDT\n"
                content += f"  • 最高流动性: {stats.get('best_exchange', 'N/A')}\n\n"
            
            # 数据质量评估
            quality = self._assess_data_quality(data_records, exchanges, symbols)
            content += f"**✅ 数据质量**: {quality['score']}/10 ({quality['level']})\n"
            content += f"**📝 质量说明**: {quality['description']}\n\n"
            
            content += f"🔗 **使用提示**: 回复 '@代币名称' 可查询实时数据"
            
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
                    "text": f"❌ 格式化汇总消息失败: {str(e)}"
                }
            }
    
    def format_detailed_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化详细消息
        
        Args:
            data: JSON数据
            
        Returns:
            Dict: Lark消息格式
        """
        try:
            collection_info = data.get("collection_info", {})
            exchange_results = data.get("exchange_results", {})
            data_records = data.get("data_records", [])
            
            content = f"📋 **详细数据报告**\n\n"
            
            # 基础信息
            timestamp = collection_info.get("timestamp", "未知")
            content += f"🕐 **收集时间**: {self._format_timestamp(timestamp)}\n"
            content += f"📊 **数据方法**: {collection_info.get('collection_method', '未知')}\n"
            content += f"📈 **总记录数**: {len(data_records)}\n\n"
            
            # 交易所结果详情
            if exchange_results:
                content += f"**🏢 交易所收集结果**:\n"
                for exchange, result in exchange_results.items():
                    success_count = result.get('success_count', 0)
                    total_count = result.get('total_count', 0)
                    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                    
                    status_emoji = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                    content += f"  {status_emoji} **{exchange}**: {success_count}/{total_count} ({success_rate:.1f}%)\n"
                content += "\n"
            
            # 代币数据详情
            symbol_stats = self._get_symbol_statistics(data_records)
            if symbol_stats:
                content += f"**💰 代币数据详情**:\n"
                for symbol, stats in list(symbol_stats.items())[:5]:  # 只显示前5个
                    content += f"  **{symbol}**:\n"
                    content += f"    📊 记录数: {stats['count']}\n"
                    content += f"    💹 平均价差: {stats['avg_spread']:.6f}%\n"
                    content += f"    💰 平均铺单量: {stats['avg_volume']:.2f} USDT\n"
                    content += f"    🏢 支持交易所: {stats['exchange_count']}个\n\n"
            
            # 数据采样
            if data_records:
                content += f"**🔍 数据采样** (前3条记录):\n"
                for i, record in enumerate(data_records[:3]):
                    exchange = record.get('exchange', 'Unknown')
                    symbol = record.get('symbol', 'Unknown')
                    spread = record.get('spread_percent', 0)
                    volume = record.get('20档_总铺单量', 0)
                    
                    content += f"  {i+1}. **{exchange}** - {symbol}\n"
                    content += f"     💹 价差: {spread:.6f}%\n"
                    content += f"     💰 铺单量: {volume:.2f} USDT\n"
            
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
                    "text": f"❌ 格式化详细消息失败: {str(e)}"
                }
            }
    
    def format_raw_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化原始JSON消息
        
        Args:
            data: JSON数据
            
        Returns:
            Dict: Lark消息格式
        """
        try:
            # 限制显示的数据大小
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 如果数据太大，只显示摘要
            if len(json_str) > 3000:
                collection_info = data.get("collection_info", {})
                sample_records = data.get("data_records", [])[:2]  # 只显示前2条记录
                
                limited_data = {
                    "collection_info": collection_info,
                    "sample_records": sample_records,
                    "total_records": len(data.get("data_records", [])),
                    "note": "数据过大，仅显示摘要信息"
                }
                
                json_str = json.dumps(limited_data, ensure_ascii=False, indent=2)
            
            content = f"📄 **原始JSON数据**\n\n"
            content += f"```json\n{json_str}\n```\n\n"
            content += f"💡 **提示**: 如需查看完整数据，请使用汇总或详细格式"
            
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
                    "text": f"❌ 格式化原始消息失败: {str(e)}"
                }
            }
    
    def format_comparison_message(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化多个数据文件的对比消息
        
        Args:
            data_list: 多个JSON数据的列表
            
        Returns:
            Dict: Lark消息格式
        """
        try:
            if not data_list:
                return {
                    "msg_type": "text",
                    "content": {
                        "text": "❌ 没有数据可供对比"
                    }
                }
            
            content = f"📊 **数据对比分析** ({len(data_list)}个数据集)\n\n"
            
            # 对比表格
            content += f"| 序号 | 收集时间 | 记录数 | 交易所数 | 代币数 |\n"
            content += f"|------|----------|--------|----------|--------|\n"
            
            for i, data in enumerate(data_list):
                collection_info = data.get("collection_info", {})
                timestamp = self._format_timestamp(collection_info.get("timestamp", ""))
                total_records = collection_info.get("total_records", 0)
                exchange_count = len(collection_info.get("exchanges", []))
                symbol_count = len(collection_info.get("symbols", []))
                
                content += f"| {i+1} | {timestamp} | {total_records} | {exchange_count} | {symbol_count} |\n"
            
            # 趋势分析
            content += f"\n**📈 趋势分析**:\n"
            
            # 计算记录数趋势
            record_counts = [data.get("collection_info", {}).get("total_records", 0) for data in data_list]
            if len(record_counts) >= 2:
                trend = "📈 上升" if record_counts[-1] > record_counts[0] else "📉 下降" if record_counts[-1] < record_counts[0] else "📊 平稳"
                content += f"  • 记录数趋势: {trend}\n"
                content += f"  • 最新记录数: {record_counts[-1]}\n"
                content += f"  • 平均记录数: {sum(record_counts) / len(record_counts):.0f}\n"
            
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
                    "text": f"❌ 格式化对比消息失败: {str(e)}"
                }
            }
    
    def _calculate_statistics(self, data_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息"""
        if not data_records:
            return {}
        
        try:
            spreads = []
            volumes = []
            exchanges = set()
            
            for record in data_records:
                if 'spread_percent' in record:
                    spreads.append(record['spread_percent'])
                if '20档_总铺单量' in record:
                    volumes.append(record['20档_总铺单量'])
                if 'exchange' in record:
                    exchanges.add(record['exchange'])
            
            stats = {}
            
            if spreads:
                stats['avg_spread'] = sum(spreads) / len(spreads)
                stats['max_spread'] = max(spreads)
                stats['min_spread'] = min(spreads)
            
            if volumes:
                stats['avg_volume'] = sum(volumes) / len(volumes)
                # 找到最高流动性的交易所
                best_record = max(data_records, key=lambda x: x.get('20档_总铺单量', 0))
                stats['best_exchange'] = best_record.get('exchange', 'N/A')
            
            return stats
            
        except Exception:
            return {}
    
    def _get_symbol_statistics(self, data_records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """获取代币统计信息"""
        symbol_data = {}
        
        try:
            for record in data_records:
                symbol = record.get('symbol', 'Unknown')
                
                if symbol not in symbol_data:
                    symbol_data[symbol] = {
                        'count': 0,
                        'spreads': [],
                        'volumes': [],
                        'exchanges': set()
                    }
                
                symbol_data[symbol]['count'] += 1
                
                if 'spread_percent' in record:
                    symbol_data[symbol]['spreads'].append(record['spread_percent'])
                
                if '20档_总铺单量' in record:
                    symbol_data[symbol]['volumes'].append(record['20档_总铺单量'])
                
                if 'exchange' in record:
                    symbol_data[symbol]['exchanges'].add(record['exchange'])
            
            # 计算平均值
            result = {}
            for symbol, data in symbol_data.items():
                result[symbol] = {
                    'count': data['count'],
                    'avg_spread': sum(data['spreads']) / len(data['spreads']) if data['spreads'] else 0,
                    'avg_volume': sum(data['volumes']) / len(data['volumes']) if data['volumes'] else 0,
                    'exchange_count': len(data['exchanges'])
                }
            
            return result
            
        except Exception:
            return {}
    
    def _assess_data_quality(self, data_records: List[Dict[str, Any]], exchanges: List[str], symbols: List[str]) -> Dict[str, Any]:
        """评估数据质量"""
        try:
            total_expected = len(exchanges) * len(symbols)
            actual_records = len(data_records)
            
            if total_expected == 0:
                return {
                    'score': 0,
                    'level': '无数据',
                    'description': '没有可评估的数据'
                }
            
            coverage_rate = (actual_records / total_expected) * 100
            
            # 检查数据完整性
            complete_records = 0
            for record in data_records:
                if all(key in record for key in ['exchange', 'symbol', 'spread_percent', '20档_总铺单量']):
                    complete_records += 1
            
            completeness_rate = (complete_records / actual_records * 100) if actual_records > 0 else 0
            
            # 计算综合评分
            score = (coverage_rate * 0.6 + completeness_rate * 0.4) / 10
            score = min(10, max(0, score))
            
            if score >= 9:
                level = "优秀"
                description = "数据覆盖完整，质量很高"
            elif score >= 7:
                level = "良好"
                description = "数据覆盖较好，质量较高"
            elif score >= 5:
                level = "一般"
                description = "数据覆盖一般，存在部分缺失"
            elif score >= 3:
                level = "较差"
                description = "数据覆盖不足，质量有待改善"
            else:
                level = "很差"
                description = "数据严重缺失，需要检查收集程序"
            
            return {
                'score': round(score, 1),
                'level': level,
                'description': description
            }
            
        except Exception:
            return {
                'score': 0,
                'level': '未知',
                'description': '质量评估失败'
            }
    
    def _format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳"""
        try:
            if not timestamp or timestamp == "未知":
                return "未知时间"
            
            # 如果是 YYYYMMDD_HHMMSS 格式
            if len(timestamp) == 15 and '_' in timestamp:
                date_part, time_part = timestamp.split('_')
                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                formatted_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                return f"{formatted_date} {formatted_time}"
            
            return timestamp
            
        except Exception:
            return timestamp or "未知时间"


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_data = {
        "collection_info": {
            "timestamp": "20250908_203813",
            "total_records": 100,
            "exchanges": ["binance", "gate", "okx"],
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "collection_method": "REST API Only"
        },
        "data_records": [
            {
                "exchange": "binance",
                "symbol": "BTCUSDT",
                "spread_percent": 0.05,
                "20档_总铺单量": 50000.0
            },
            {
                "exchange": "gate",
                "symbol": "ETHUSDT", 
                "spread_percent": 0.08,
                "20档_总铺单量": 30000.0
            }
        ]
    }
    
    formatter = JsonFormatter()
    
    print("测试汇总格式:")
    summary_msg = formatter.format_summary_message(test_data)
    print(summary_msg["content"]["text"])
    
    print("\n" + "="*50 + "\n")
    
    print("测试详细格式:")
    detailed_msg = formatter.format_detailed_message(test_data)
    print(detailed_msg["content"]["text"])