#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人启动脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.lark_bot import LarkBot
from config.lark_config import config
from utils.helpers import setup_logger


async def main():
    """主函数"""
    # 设置日志
    logger = setup_logger('LarkBot', config.get('logging.level', 'INFO'))
    
    logger.info("🚀 启动Lark代币深度分析机器人")
    logger.info("=" * 50)
    
    # 显示配置信息
    ws_config = config.get_websocket_config()
    logger.info(f"WebSocket服务器: {ws_config['host']}:{ws_config['port']}")
    
    data_config = config.get_data_collection_config()
    logger.info(f"缓存超时: {data_config['cache_timeout']} 秒")
    logger.info(f"速率限制: {data_config['rate_limit']} 秒")
    
    exchanges = config.get_enabled_exchanges()
    logger.info(f"启用的交易所: {', '.join(exchanges)}")
    
    logger.info("=" * 50)
    
    try:
        # 创建并启动机器人
        bot = LarkBot()
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭机器人...")
    except Exception as e:
        logger.error(f"机器人运行异常: {e}")
        sys.exit(1)
    finally:
        logger.info("机器人已关闭")


if __name__ == "__main__":
    asyncio.run(main())
