#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置 Lark 机器人自定义菜单的脚本

要求：
- 已创建企业自建应用，并已在环境中设置：
  - LARK_APP_ID
  - LARK_APP_SECRET
- 机器人已被加入到目标群聊

可选：
- 自定义菜单项，默认提供“查询 BTC / 查询 ETH / 帮助”。
"""

import asyncio
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lark_webhook_bot import LarkWebhookBot


async def main():
    bot = LarkWebhookBot()

    # 可自定义菜单项（按需修改）
    menu = [
        {"name": "查询 BTC", "type": "message", "text": "@BTC"},
        {"name": "查询 ETH", "type": "message", "text": "@ETH"},
        {"name": "帮助", "type": "message", "text": "help"}
    ]

    ok = await bot.set_bot_menu(menu_items=menu)
    if ok:
        print("✅ 机器人菜单设置成功")
    else:
        print("❌ 机器人菜单设置失败（脚本已尝试多种payload；请检查返回日志/权限/字段要求）")


if __name__ == "__main__":
    asyncio.run(main())
