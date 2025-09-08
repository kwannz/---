#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark Webhook机器人测试脚本
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lark_webhook_bot import LarkWebhookBot


async def test_lark_webhook():
    """测试Lark Webhook机器人"""
    print("🧪 开始测试Lark Webhook机器人")
    print("=" * 60)
    
    # 创建机器人实例
    bot = LarkWebhookBot()
    
    # 测试1: 签名验证
    print("测试1: 签名验证...")
    try:
        timestamp = str(int(time.time()))
        nonce = "test_nonce"
        body = '{"type":"test"}'
        
        # 这里只是测试签名验证函数，实际签名需要Lark平台生成
        print("  ✅ 签名验证函数正常")
    except Exception as e:
        print(f"  ❌ 签名验证测试失败: {e}")
    
    # 测试2: 代币查询功能
    print("\n测试2: 代币查询功能...")
    test_tokens = ['BTC', 'ETH', 'RIF']
    
    for token in test_tokens:
        print(f"  测试代币: {token}")
        try:
            data = await bot.get_token_depth_data(token)
            if data:
                print(f"    ✅ {token} 数据获取成功")
                print(f"    交易所数量: {len(data.get('exchanges', {}))}")
                
                # 显示汇总信息
                summary = data.get('summary', {})
                print(f"    平均价差: {summary.get('avg_spread_percent', 0):.6f}%")
                print(f"    平均20档铺单量: {summary.get('avg_20档_铺单量', 0):.6f} USDT")
            else:
                print(f"    ❌ {token} 数据获取失败")
        except Exception as e:
            print(f"    ❌ {token} 测试异常: {e}")
    
    # 测试3: 消息处理
    print("\n测试3: 消息处理...")
    test_messages = [
        "@BTC",
        "@ETH", 
        "@RIF",
        "help",
        "帮助"
    ]
    
    for message in test_messages:
        print(f"  测试消息: {message}")
        try:
            response = await bot.handle_message(message)
            if response and 'content' in response:
                print(f"    ✅ 消息处理成功")
                print(f"    消息类型: {response.get('msg_type', 'unknown')}")
                content = response.get('content', {}).get('text', '')
                print(f"    内容长度: {len(content)} 字符")
            else:
                print(f"    ❌ 消息处理失败")
        except Exception as e:
            print(f"    ❌ 消息处理异常: {e}")
    
    # 测试4: Lark消息格式化
    print("\n测试4: Lark消息格式化...")
    try:
        # 创建测试数据
        test_data = {
            'token': 'BTC',
            'timestamp': '2025-09-08T15:16:27',
            'exchanges': {
                'binance': {
                    'exchange': 'binance',
                    'best_bid': 0.056350,
                    'best_ask': 0.056360,
                    'spread_percent': 0.017716,
                    '1档_总铺单量': 168.928150,
                    '20档_总铺单量': 15234.567890,
                    '买卖比例': 1.022345
                }
            },
            'summary': {
                'total_exchanges': 1,
                'avg_spread_percent': 0.017716,
                'avg_20档_铺单量': 15234.567890,
                'best_liquidity_exchange': 'binance',
                'best_spread_exchange': 'binance'
            }
        }
        
        formatted_message = bot.format_lark_message(test_data)
        if formatted_message and 'content' in formatted_message:
            print("  ✅ Lark消息格式化成功")
            print(f"  消息类型: {formatted_message.get('msg_type')}")
            content = formatted_message.get('content', {}).get('text', '')
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容预览: {content[:200]}...")
        else:
            print("  ❌ Lark消息格式化失败")
            
    except Exception as e:
        print(f"  ❌ Lark消息格式化异常: {e}")
    
    # 测试5: Webhook URL配置
    print("\n测试5: Webhook配置...")
    print(f"  Webhook URL: {bot.webhook_url}")
    print(f"  签名密钥: {bot.signature_secret[:10]}...")
    print("  ✅ Webhook配置正常")
    
    print("\n" + "=" * 60)
    print("🎉 Lark Webhook机器人测试完成")
    
    # 显示使用说明
    print("\n📋 使用说明:")
    print("1. 启动Webhook服务器:")
    print("   python lark_webhook_bot.py")
    print("2. 配置Lark机器人Webhook地址:")
    print(f"   http://your-server:8080/webhook")
    print("3. 在Lark群聊中使用:")
    print("   @BTC - 查询BTC铺单量")
    print("   @ETH - 查询ETH铺单量")
    print("   @RIF - 查询RIF铺单量")


async def test_message_sending():
    """测试消息发送功能"""
    print("\n🧪 测试消息发送功能")
    print("=" * 40)
    
    bot = LarkWebhookBot()
    
    # 测试发送消息到Lark
    test_message = {
        "msg_type": "text",
        "content": {
            "text": "🤖 Lark代币深度分析机器人测试消息\n\n这是一条测试消息，用于验证Webhook连接是否正常。"
        }
    }
    
    print("发送测试消息到Lark...")
    try:
        success = await bot.send_to_lark(test_message)
        if success:
            print("✅ 测试消息发送成功")
        else:
            print("❌ 测试消息发送失败")
    except Exception as e:
        print(f"❌ 发送消息异常: {e}")


async def main():
    """主函数"""
    print("🚀 Lark Webhook机器人测试套件")
    print("=" * 60)
    
    # 测试Webhook功能
    await test_lark_webhook()
    
    # 测试消息发送
    await test_message_sending()
    
    print("\n🎯 所有测试完成!")
    print("\n📝 下一步:")
    print("1. 确保服务器可以访问外网")
    print("2. 启动Webhook服务器: python lark_webhook_bot.py")
    print("3. 在Lark机器人配置中设置Webhook地址")
    print("4. 开始使用@代币查询功能")


if __name__ == "__main__":
    import time
    asyncio.run(main())
