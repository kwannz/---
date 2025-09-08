#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动Lark Webhook机器人
"""

import asyncio
import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lark_webhook_bot import LarkWebhookBot


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Lark Webhook代币深度分析机器人')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口')
    parser.add_argument('--test', action='store_true', help='运行测试模式')
    
    args = parser.parse_args()
    
    print("🤖 Lark Webhook代币深度分析机器人")
    print("=" * 50)
    print(f"服务器地址: {args.host}:{args.port}")
    print(f"Webhook地址: http://{args.host}:{args.port}/webhook")
    print("=" * 50)
    
    # 创建机器人实例
    bot = LarkWebhookBot()
    
    if args.test:
        # 测试模式
        print("🧪 运行测试模式...")
        await bot.test_webhook()
    else:
        # 启动服务器
        print("🚀 启动Webhook服务器...")
        print("\n📋 配置说明:")
        print("1. 确保服务器可以访问外网")
        print("2. 在Lark机器人配置中设置Webhook地址:")
        print(f"   http://{args.host}:{args.port}/webhook")
        print("3. 在Lark群聊中使用:")
        print("   @BTC - 查询BTC铺单量")
        print("   @ETH - 查询ETH铺单量")
        print("   @RIF - 查询RIF铺单量")
        print("\n按 Ctrl+C 停止服务器")
        
        try:
            await bot.start_server(args.host, args.port)
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")


if __name__ == "__main__":
    asyncio.run(main())
