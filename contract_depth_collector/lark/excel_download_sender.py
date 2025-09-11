#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件下载发送器
通过生成下载链接或分段发送的方式发送Excel内容
"""

import os
import sys
import json
import pandas as pd
import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lark_webhook_bot import LarkWebhookBot

class ExcelDownloadSender:
    """Excel下载发送器"""
    
    def __init__(self):
        self.bot = LarkWebhookBot()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ExcelDownloader')
    
    def create_simple_web_server(self, file_path: str, port: int = 8081) -> Optional[str]:
        """
        创建简单的文件下载服务器
        
        Args:
            file_path: 要下载的文件路径
            port: 服务器端口
            
        Returns:
            下载URL
        """
        try:
            import threading
            import http.server
            import socketserver
            from urllib.parse import quote
            
            # 获取文件名
            file_name = os.path.basename(file_path)
            
            # 创建临时目录结构
            temp_dir = "temp_download"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 复制文件到临时目录
            import shutil
            temp_file_path = os.path.join(temp_dir, file_name)
            shutil.copy2(file_path, temp_file_path)
            
            # 创建简单的HTTP服务器
            class FileHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=temp_dir, **kwargs)
                
                def end_headers(self):
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET')
                    self.send_header('Content-Disposition', f'attachment; filename="{file_name}"')
                    super().end_headers()
            
            # 启动服务器
            with socketserver.TCPServer(("", port), FileHandler) as httpd:
                def serve_forever():
                    httpd.serve_forever()
                
                server_thread = threading.Thread(target=serve_forever, daemon=True)
                server_thread.start()
                
                # 获取当前隧道URL
                tunnel_url = self.get_current_tunnel_url()
                if tunnel_url:
                    download_url = f"{tunnel_url.replace(':8080', f':{port}')}/{quote(file_name)}"
                    return download_url
                else:
                    return f"http://localhost:{port}/{quote(file_name)}"
                    
        except Exception as e:
            self.logger.error(f"创建下载服务器失败: {e}")
            return None
    
    def get_current_tunnel_url(self) -> Optional[str]:
        """获取当前隧道URL"""
        try:
            tunnel_file = "current_tunnel_url.txt"
            if os.path.exists(tunnel_file):
                with open(tunnel_file, 'r') as f:
                    url = f.read().strip()
                    return url if url else None
        except:
            pass
        return None
    
    def excel_to_csv_chunks(self, excel_file: str, max_rows: int = 50) -> List[str]:
        """
        将Excel文件分割为多个CSV块
        
        Args:
            excel_file: Excel文件路径
            max_rows: 每个块的最大行数
            
        Returns:
            CSV文本块列表
        """
        try:
            df = pd.read_excel(excel_file)
            
            chunks = []
            total_rows = len(df)
            
            for i in range(0, total_rows, max_rows):
                chunk_df = df.iloc[i:i + max_rows]
                csv_text = chunk_df.to_csv(index=False)
                
                # 添加块信息
                chunk_info = f"# Excel数据块 {i//max_rows + 1}/{(total_rows + max_rows - 1)//max_rows}\n"
                chunk_info += f"# 行数: {len(chunk_df)} (总计: {total_rows})\n"
                chunk_info += f"# 文件: {os.path.basename(excel_file)}\n\n"
                
                chunks.append(chunk_info + csv_text)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Excel分割失败: {e}")
            return []
    
    async def send_excel_as_download(self, file_path: str) -> bool:
        """
        以下载链接方式发送Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            是否成功发送
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return False
            
            file_name = os.path.basename(file_path)
            file_size = f"{os.path.getsize(file_path) / 1024:.1f} KB"
            
            # 分析Excel内容
            try:
                df = pd.read_excel(file_path)
                rows = len(df)
                columns = len(df.columns)
                column_names = df.columns.tolist()[:5]  # 只显示前5个列名
            except:
                rows = "未知"
                columns = "未知"
                column_names = []
            
            # 创建下载服务器
            download_url = self.create_simple_web_server(file_path)
            
            # 构建消息
            message_lines = [
                "📊 **Excel文件下载**",
                "",
                f"📁 **文件信息**:",
                f"   • 文件名: {file_name}",
                f"   • 大小: {file_size}",
                f"   • 行数: {rows}",
                f"   • 列数: {columns}",
            ]
            
            if column_names:
                message_lines.append(f"   • 列名: {', '.join(column_names)}{'...' if len(df.columns) > 5 else ''}")
            
            message_lines.extend([
                "",
                "💾 **下载方式**:",
            ])
            
            if download_url:
                message_lines.append(f"🔗 **下载链接**: {download_url}")
                message_lines.append("   (点击链接直接下载Excel文件)")
            else:
                message_lines.append("⚠️ 无法生成下载链接，将发送数据内容")
            
            message_lines.extend([
                "",
                f"⏰ **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "📝 **使用说明**:",
                "   • 点击链接即可下载完整Excel文件",
                "   • 如无法下载，请查看后续消息中的数据内容"
            ])
            
            message = {
                "msg_type": "text",
                "content": {
                    "text": "\n".join(message_lines)
                }
            }
            
            success = await self.bot.send_to_lark(message)
            
            if success:
                self.logger.info(f"下载链接发送成功: {file_path}")
                
                # 如果没有下载链接，发送数据内容
                if not download_url:
                    await self.send_excel_as_chunks(file_path)
            
            return success
            
        except Exception as e:
            self.logger.error(f"发送Excel下载链接失败: {e}")
            return False
    
    async def send_excel_as_chunks(self, file_path: str, chunk_size: int = 30) -> bool:
        """
        分段发送Excel内容
        
        Args:
            file_path: Excel文件路径
            chunk_size: 每段的行数
            
        Returns:
            是否成功发送
        """
        try:
            chunks = self.excel_to_csv_chunks(file_path, chunk_size)
            
            if not chunks:
                self.logger.error("生成数据块失败")
                return False
            
            # 发送总览消息
            overview_message = {
                "msg_type": "text",
                "content": {
                    "text": f"📋 **Excel数据内容** ({len(chunks)}段)\n\n"
                           f"文件: {os.path.basename(file_path)}\n"
                           f"将分{len(chunks)}段发送数据内容..."
                }
            }
            
            await self.bot.send_to_lark(overview_message)
            
            # 分段发送
            success_count = 0
            for i, chunk in enumerate(chunks):
                try:
                    chunk_message = {
                        "msg_type": "text",
                        "content": {
                            "text": f"```csv\n{chunk}\n```"
                        }
                    }
                    
                    chunk_success = await self.bot.send_to_lark(chunk_message)
                    if chunk_success:
                        success_count += 1
                        self.logger.info(f"数据块 {i+1}/{len(chunks)} 发送成功")
                    else:
                        self.logger.error(f"数据块 {i+1}/{len(chunks)} 发送失败")
                    
                    # 避免发送过快
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"发送数据块 {i+1} 时发生错误: {e}")
            
            # 发送完成消息
            completion_message = {
                "msg_type": "text",
                "content": {
                    "text": f"✅ **数据发送完成**\n\n"
                           f"成功发送: {success_count}/{len(chunks)} 段\n"
                           f"文件: {os.path.basename(file_path)}"
                }
            }
            
            await self.bot.send_to_lark(completion_message)
            
            return success_count == len(chunks)
            
        except Exception as e:
            self.logger.error(f"分段发送Excel失败: {e}")
            return False
    
    async def send_excel_hybrid(self, file_path: str) -> bool:
        """
        混合方式发送Excel：先尝试下载链接，再发送部分内容
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            是否成功发送
        """
        try:
            # 1. 发送下载链接
            download_success = await self.send_excel_as_download(file_path)
            
            # 2. 发送前几行数据预览
            try:
                df = pd.read_excel(file_path)
                if len(df) > 0:
                    preview_df = df.head(10)  # 只显示前10行
                    csv_preview = preview_df.to_csv(index=False)
                    
                    preview_message = {
                        "msg_type": "text",
                        "content": {
                            "text": f"👀 **数据预览** (前10行)\n\n```csv\n{csv_preview}\n```"
                        }
                    }
                    
                    await self.bot.send_to_lark(preview_message)
            except Exception as e:
                self.logger.warning(f"发送数据预览失败: {e}")
            
            return download_success
            
        except Exception as e:
            self.logger.error(f"混合发送Excel失败: {e}")
            return False

async def main():
    """主函数 - 测试"""
    sender = ExcelDownloadSender()
    
    # 测试文件
    test_file = "../data/depth_data_20250908_203426.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 转换为Excel
    excel_file = test_file.replace('.csv', '_download_test.xlsx')
    df = pd.read_csv(test_file)
    df.to_excel(excel_file, index=False)
    
    print("📊 测试Excel下载发送功能")
    print("=" * 50)
    
    # 测试混合发送
    print("🧪 测试混合发送模式...")
    success = await sender.send_excel_hybrid(excel_file)
    print(f"结果: {'✅ 成功' if success else '❌ 失败'}")
    
    # 清理临时文件
    if os.path.exists(excel_file):
        os.remove(excel_file)
    
    print("🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())