#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人客户端启动脚本
"""

import asyncio
import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from websocket.websocket_client import LarkBotClient
from config.lark_config import config
from utils.helpers import setup_logger


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Lark代币深度分析机器人客户端')
    parser.add_argument('--host', default='localhost', help='WebSocket服务器地址')
    parser.add_argument('--port', type=int, default=8765, help='WebSocket服务器端口')
    parser.add_argument('--token', help='要查询的代币')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger('LarkBotClient', config.get('logging.level', 'INFO'))
    
    # 创建客户端
    uri = f"ws://{args.host}:{args.port}"
    client = LarkBotClient(uri)
    
    try:
        # 启动客户端
        if await client.start():
            logger.info(f"✅ 已连接到Lark机器人服务器: {uri}")
            
            if args.token:
                # 查询指定代币
                logger.info(f"查询代币: {args.token}")
                response = await client.query_token(args.token)
                if response:
                    print(f"\n{response}")
                else:
                    print("❌ 查询失败")
            else:
                # 交互模式
                await client.interactive_mode()
        else:
            logger.error("❌ 无法连接到Lark机器人服务器")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭客户端...")
    except Exception as e:
        logger.error(f"客户端运行异常: {e}")
        sys.exit(1)
    finally:
        await client.stop()
        logger.info("客户端已关闭")


if __name__ == "__main__":
    asyncio.run(main())
