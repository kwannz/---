#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket客户端
用于连接Lark机器人WebSocket服务
"""

import asyncio
import json
import logging
import websockets
from typing import Optional, Callable


class WebSocketClient:
    """WebSocket客户端类"""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        """初始化WebSocket客户端"""
        self.uri = uri
        self.websocket = None
        self.is_connected = False
        self.logger = self._setup_logger()
        self.message_handler = None
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('WebSocketClient')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            self.logger.info(f"已连接到WebSocket服务器: {self.uri}")
            return True
        except Exception as e:
            self.logger.error(f"连接WebSocket服务器失败: {e}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            self.logger.info("已断开WebSocket连接")
    
    async def send_message(self, message: str) -> Optional[str]:
        """发送消息并等待响应"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket未连接")
            return None
        
        try:
            await self.websocket.send(message)
            response = await self.websocket.recv()
            return response
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return None
    
    async def listen(self, message_handler: Callable[[str], None]):
        """监听消息"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket未连接")
            return
        
        self.message_handler = message_handler
        
        try:
            async for message in self.websocket:
                self.logger.info(f"收到消息: {message}")
                if self.message_handler:
                    self.message_handler(message)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket连接已关闭")
        except Exception as e:
            self.logger.error(f"监听消息异常: {e}")
        finally:
            self.is_connected = False
    
    async def query_token(self, token: str) -> Optional[str]:
        """查询代币信息"""
        message = f"@{token}"
        return await self.send_message(message)
    
    async def get_help(self) -> Optional[str]:
        """获取帮助信息"""
        return await self.send_message("help")


class LarkBotClient:
    """Lark机器人客户端"""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        """初始化客户端"""
        self.client = WebSocketClient(uri)
        self.logger = logging.getLogger('LarkBotClient')
    
    async def start(self):
        """启动客户端"""
        if await self.client.connect():
            self.logger.info("Lark机器人客户端已启动")
            return True
        return False
    
    async def stop(self):
        """停止客户端"""
        await self.client.disconnect()
        self.logger.info("Lark机器人客户端已停止")
    
    async def query_token(self, token: str) -> Optional[str]:
        """查询代币信息"""
        return await self.client.query_token(token)
    
    async def get_help(self) -> Optional[str]:
        """获取帮助信息"""
        return await self.client.get_help()
    
    async def interactive_mode(self):
        """交互模式"""
        print("🤖 Lark代币深度分析机器人客户端")
        print("=" * 50)
        print("输入 @代币名称 查询铺单量信息")
        print("输入 help 获取帮助信息")
        print("输入 quit 退出")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n请输入命令: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'help':
                    response = await self.get_help()
                    if response:
                        print(f"\n{response}")
                elif user_input.startswith('@'):
                    response = await self.query_token(user_input[1:])
                    if response:
                        print(f"\n{response}")
                else:
                    print("❌ 无效命令，请使用 @代币名称 或 help")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
        
        await self.stop()


async def main():
    """主函数"""
    client = LarkBotClient()
    
    if await client.start():
        await client.interactive_mode()
    else:
        print("❌ 无法连接到Lark机器人服务器")


if __name__ == "__main__":
    asyncio.run(main())
