#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.lark_bot import LarkBot
from websocket.websocket_client import LarkBotClient


async def test_lark_bot():
    """测试Lark机器人功能"""
    print("🧪 开始测试Lark机器人功能")
    print("=" * 50)
    
    # 测试1: 创建机器人实例
    print("测试1: 创建机器人实例...")
    try:
        bot = LarkBot()
        print("✅ 机器人实例创建成功")
    except Exception as e:
        print(f"❌ 机器人实例创建失败: {e}")
        return
    
    # 测试2: 测试代币查询
    print("\n测试2: 测试代币查询...")
    try:
        # 测试BTC查询
        print("  查询BTC...")
        btc_data = await bot.get_token_depth_data('BTC')
        if btc_data:
            print("  ✅ BTC数据获取成功")
            print(f"  交易所数量: {len(btc_data.get('exchanges', {}))}")
        else:
            print("  ❌ BTC数据获取失败")
        
        # 测试ETH查询
        print("  查询ETH...")
        eth_data = await bot.get_token_depth_data('ETH')
        if eth_data:
            print("  ✅ ETH数据获取成功")
            print(f"  交易所数量: {len(eth_data.get('exchanges', {}))}")
        else:
            print("  ❌ ETH数据获取失败")
            
    except Exception as e:
        print(f"❌ 代币查询测试失败: {e}")
    
    # 测试3: 测试消息处理
    print("\n测试3: 测试消息处理...")
    try:
        # 测试@代币消息
        print("  测试@BTC消息...")
        btc_response = await bot.handle_message("@BTC")
        if btc_response and "BTC" in btc_response:
            print("  ✅ @BTC消息处理成功")
        else:
            print("  ❌ @BTC消息处理失败")
        
        # 测试帮助消息
        print("  测试help消息...")
        help_response = await bot.handle_message("help")
        if help_response and "帮助" in help_response:
            print("  ✅ help消息处理成功")
        else:
            print("  ❌ help消息处理失败")
            
    except Exception as e:
        print(f"❌ 消息处理测试失败: {e}")
    
    # 测试4: 测试消息格式化
    print("\n测试4: 测试消息格式化...")
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
        
        formatted_message = bot.format_message(test_data)
        if formatted_message and "BTC" in formatted_message:
            print("  ✅ 消息格式化成功")
            print(f"  消息长度: {len(formatted_message)} 字符")
        else:
            print("  ❌ 消息格式化失败")
            
    except Exception as e:
        print(f"❌ 消息格式化测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Lark机器人功能测试完成")


async def test_websocket_client():
    """测试WebSocket客户端"""
    print("\n🧪 开始测试WebSocket客户端")
    print("=" * 50)
    
    # 注意: 这个测试需要先启动WebSocket服务器
    print("注意: 此测试需要先启动WebSocket服务器")
    print("请先运行: python start_bot.py")
    print("然后在另一个终端运行此测试")
    
    try:
        client = LarkBotClient()
        
        # 测试连接
        print("测试WebSocket连接...")
        if await client.start():
            print("✅ WebSocket连接成功")
            
            # 测试查询
            print("测试代币查询...")
            response = await client.query_token("BTC")
            if response:
                print("✅ 代币查询成功")
                print(f"响应长度: {len(response)} 字符")
            else:
                print("❌ 代币查询失败")
            
            await client.stop()
        else:
            print("❌ WebSocket连接失败")
            
    except Exception as e:
        print(f"❌ WebSocket客户端测试失败: {e}")


async def main():
    """主函数"""
    print("🚀 Lark机器人测试套件")
    print("=" * 50)
    
    # 测试机器人功能
    await test_lark_bot()
    
    # 测试WebSocket客户端
    await test_websocket_client()
    
    print("\n🎯 测试完成!")
    print("如需测试WebSocket功能，请先启动服务器:")
    print("python start_bot.py")


if __name__ == "__main__":
    asyncio.run(main())
