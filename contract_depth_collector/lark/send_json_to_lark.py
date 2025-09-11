#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送JSON数据到Lark
支持读取收集的数据文件并发送到Lark群聊
"""

import asyncio
import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from lark_webhook_bot import LarkWebhookBot
from json_formatter import JsonFormatter


class JsonToLarkSender:
    """JSON数据到Lark发送器"""
    
    def __init__(self):
        """初始化发送器"""
        self.bot = LarkWebhookBot()
        self.formatter = JsonFormatter()
        
    async def send_json_file(self, json_file: str, format_type: str = "summary") -> bool:
        """发送JSON文件到Lark
        
        Args:
            json_file: JSON文件路径
            format_type: 格式类型 ('summary', 'detailed', 'raw')
            
        Returns:
            bool: 发送是否成功
        """
        try:
            print(f"📄 读取JSON文件: {json_file}")
            
            # 检查文件是否存在
            if not os.path.exists(json_file):
                print(f"❌ 文件不存在: {json_file}")
                return False
                
            # 读取JSON数据
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"✅ JSON文件读取成功，数据大小: {len(str(data))} 字符")
            
            # 格式化消息
            if format_type == "summary":
                message = self.formatter.format_summary_message(data)
            elif format_type == "detailed":
                message = self.formatter.format_detailed_message(data)
            elif format_type == "raw":
                message = self.formatter.format_raw_message(data)
            else:
                print(f"❌ 不支持的格式类型: {format_type}")
                return False
                
            print(f"📝 消息格式化完成，类型: {format_type}")
            print(f"📨 准备发送消息到Lark...")
            
            # 发送到Lark
            success = await self.bot.send_to_lark(message)
            
            if success:
                print("✅ 消息发送成功")
                return True
            else:
                print("❌ 消息发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 发送JSON数据失败: {e}")
            return False
    
    async def send_multiple_files(self, file_pattern: str, format_type: str = "summary") -> List[bool]:
        """批量发送多个JSON文件
        
        Args:
            file_pattern: 文件匹配模式 (如: "collected_data_*.json")
            format_type: 格式类型
            
        Returns:
            List[bool]: 每个文件的发送结果
        """
        try:
            from glob import glob
            
            # 查找匹配的文件
            files = glob(file_pattern)
            if not files:
                print(f"❌ 没有找到匹配的文件: {file_pattern}")
                return []
                
            print(f"📁 找到 {len(files)} 个文件:")
            for f in files:
                print(f"  - {f}")
                
            results = []
            
            # 逐个发送文件
            for i, file_path in enumerate(files):
                print(f"\n📤 发送文件 {i+1}/{len(files)}: {file_path}")
                
                # 添加文件标识到消息中
                result = await self.send_json_file(file_path, format_type)
                results.append(result)
                
                # 如果不是最后一个文件，等待一下避免发送过快
                if i < len(files) - 1:
                    print("⏳ 等待2秒后发送下一个文件...")
                    await asyncio.sleep(2)
                    
            # 发送汇总报告
            success_count = sum(results)
            summary_message = {
                "msg_type": "text",
                "content": {
                    "text": f"📊 **批量发送完成**\n\n"
                           f"✅ 成功: {success_count}/{len(files)} 个文件\n"
                           f"❌ 失败: {len(files) - success_count}/{len(files)} 个文件\n"
                           f"🕐 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
            
            await self.bot.send_to_lark(summary_message)
            
            return results
            
        except Exception as e:
            print(f"❌ 批量发送失败: {e}")
            return []
    
    async def send_realtime_data(self, symbols: List[str] = None) -> bool:
        """发送实时数据到Lark
        
        Args:
            symbols: 要查询的代币符号列表，默认为['BTC', 'ETH', 'RIF']
            
        Returns:
            bool: 发送是否成功
        """
        try:
            if symbols is None:
                symbols = ['BTC', 'ETH', 'RIF']
                
            print(f"🔄 获取实时数据: {', '.join(symbols)}")
            
            success_count = 0
            
            for symbol in symbols:
                try:
                    # 获取实时数据
                    data = await self.bot.get_token_depth_data(symbol)
                    
                    if data:
                        # 格式化并发送
                        message = self.bot.format_lark_message(data)
                        success = await self.bot.send_to_lark(message)
                        
                        if success:
                            print(f"✅ {symbol} 数据发送成功")
                            success_count += 1
                        else:
                            print(f"❌ {symbol} 数据发送失败")
                            
                        # 等待1秒避免发送过快
                        if symbol != symbols[-1]:
                            await asyncio.sleep(1)
                    else:
                        print(f"❌ {symbol} 数据获取失败")
                        
                except Exception as e:
                    print(f"❌ {symbol} 处理失败: {e}")
                    
            print(f"📊 实时数据发送完成: {success_count}/{len(symbols)} 成功")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ 发送实时数据失败: {e}")
            return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="发送JSON数据到Lark")
    parser.add_argument("--file", "-f", type=str, help="JSON文件路径")
    parser.add_argument("--pattern", "-p", type=str, help="文件匹配模式 (如: 'collected_data_*.json')")
    parser.add_argument("--format", "-t", choices=["summary", "detailed", "raw"], 
                       default="summary", help="消息格式类型")
    parser.add_argument("--realtime", "-r", action="store_true", help="发送实时数据")
    parser.add_argument("--symbols", "-s", nargs="+", default=["BTC", "ETH", "RIF"], 
                       help="实时数据的代币符号")
    
    args = parser.parse_args()
    
    print("🚀 启动JSON到Lark发送器")
    print("=" * 50)
    
    sender = JsonToLarkSender()
    
    try:
        if args.realtime:
            # 发送实时数据
            print(f"📡 发送实时数据: {', '.join(args.symbols)}")
            success = await sender.send_realtime_data(args.symbols)
            
        elif args.file:
            # 发送单个文件
            print(f"📄 发送单个文件: {args.file}")
            success = await sender.send_json_file(args.file, args.format)
            
        elif args.pattern:
            # 批量发送文件
            print(f"📁 批量发送文件: {args.pattern}")
            results = await sender.send_multiple_files(args.pattern, args.format)
            success = any(results)
            
        else:
            # 默认发送最新的收集数据文件
            print("🔍 查找最新的数据文件...")
            from glob import glob
            
            # 查找最新的collected_data文件
            pattern = "collected_data_*.json"
            files = glob(pattern)
            
            if files:
                # 按时间排序，选择最新的文件
                latest_file = max(files, key=os.path.getctime)
                print(f"📄 发送最新文件: {latest_file}")
                success = await sender.send_json_file(latest_file, args.format)
            else:
                print("❌ 没有找到数据文件，发送实时数据...")
                success = await sender.send_realtime_data(args.symbols)
        
        if success:
            print("\n🎉 任务执行成功!")
        else:
            print("\n💥 任务执行失败!")
            
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")


if __name__ == "__main__":
    print("""
🤖 JSON到Lark发送器
==================

使用示例:
  python send_json_to_lark.py                          # 发送最新数据文件或实时数据
  python send_json_to_lark.py -f data.json            # 发送指定文件
  python send_json_to_lark.py -p "collected_*.json"   # 批量发送匹配文件
  python send_json_to_lark.py -r -s BTC ETH           # 发送BTC和ETH实时数据
  python send_json_to_lark.py -f data.json -t detailed # 发送详细格式消息

""")
    asyncio.run(main())