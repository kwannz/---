#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件发送到Lark机器人
支持多种Excel文件格式和发送模式
"""

import os
import sys
import json
import pandas as pd
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lark_webhook_bot import LarkWebhookBot

class ExcelToLarkSender:
    """Excel文件发送到Lark的处理器"""
    
    def __init__(self):
        self.bot = LarkWebhookBot()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ExcelToLark')
    
    async def upload_file_to_lark(self, file_path: str, file_name: str = None) -> Optional[str]:
        """
        上传文件到Lark并获取文件key
        
        Args:
            file_path: 本地文件路径
            file_name: 显示的文件名，如果为None则使用原文件名
            
        Returns:
            文件key，用于后续发送消息
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return None
            
        if not file_name:
            file_name = os.path.basename(file_path)
        
        # Lark文件上传API地址
        upload_url = "https://open.larksuite.com/open-apis/im/v1/files"
        
        try:
            # 获取访问token (这里需要app_id和app_secret)
            access_token = await self.get_access_token()
            if not access_token:
                self.logger.error("获取访问token失败")
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # 准备文件上传
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()
            
            data = aiohttp.FormData()
            data.add_field('file_type', 'stream')
            data.add_field('file_name', file_name)
            data.add_field('file', file_content, filename=file_name)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        file_key = result.get('data', {}).get('file_key')
                        self.logger.info(f"文件上传成功: {file_name} -> {file_key}")
                        return file_key
                    else:
                        error_text = await response.text()
                        self.logger.error(f"文件上传失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"上传文件时发生错误: {e}")
            return None
    
    async def get_access_token(self) -> Optional[str]:
        """获取Lark访问token"""
        if not hasattr(self.bot, 'app_id') or not hasattr(self.bot, 'app_secret'):
            self.logger.warning("未配置app_id和app_secret，使用webhook模式发送")
            return None
            
        token_url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        
        payload = {
            "app_id": self.bot.app_id,
            "app_secret": self.bot.app_secret
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('tenant_access_token')
                    else:
                        self.logger.error(f"获取token失败: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"获取token时发生错误: {e}")
            return None
    
    def analyze_excel_file(self, file_path: str) -> Dict[str, Any]:
        """
        分析Excel文件内容
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            分析结果字典
        """
        try:
            # 读取Excel文件
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                self.logger.error(f"不支持的文件格式: {file_path}")
                return {}
            
            # 基本信息统计
            analysis = {
                'file_name': os.path.basename(file_path),
                'file_size': f"{os.path.getsize(file_path) / 1024:.1f} KB",
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'has_data': len(df) > 0,
                'summary': self.generate_data_summary(df)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析Excel文件失败: {e}")
            return {}
    
    def generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据摘要"""
        summary = {}
        
        if len(df) == 0:
            return {'status': 'empty', 'message': '文件为空'}
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            summary['numeric_columns'] = len(numeric_cols)
            summary['numeric_stats'] = {}
            for col in numeric_cols[:3]:  # 只显示前3个数值列的统计
                summary['numeric_stats'][col] = {
                    'min': float(df[col].min()) if pd.notna(df[col].min()) else None,
                    'max': float(df[col].max()) if pd.notna(df[col].max()) else None,
                    'mean': float(df[col].mean()) if pd.notna(df[col].mean()) else None
                }
        
        # 文本列统计
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        if text_cols:
            summary['text_columns'] = len(text_cols)
            summary['sample_data'] = {}
            for col in text_cols[:3]:  # 只显示前3个文本列的样本
                unique_values = df[col].dropna().unique()[:3]
                summary['sample_data'][col] = [str(v) for v in unique_values]
        
        summary['status'] = 'analyzed'
        return summary
    
    def create_excel_message(self, file_path: str, analysis: Dict[str, Any], 
                           file_key: str = None) -> Dict[str, Any]:
        """
        创建Excel文件的Lark消息
        
        Args:
            file_path: Excel文件路径
            analysis: 文件分析结果
            file_key: 上传后的文件key
            
        Returns:
            Lark消息字典
        """
        file_name = analysis.get('file_name', os.path.basename(file_path))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建消息内容
        message_lines = [
            f"📊 **Excel文件报告**",
            f"",
            f"📁 **文件信息**:",
            f"   • 文件名: {file_name}",
            f"   • 大小: {analysis.get('file_size', 'N/A')}",
            f"   • 时间: {timestamp}",
            f"",
            f"📈 **数据概览**:",
            f"   • 行数: {analysis.get('rows', 0):,}",
            f"   • 列数: {analysis.get('columns', 0)}",
        ]
        
        # 添加列名信息
        columns = analysis.get('column_names', [])
        if columns:
            message_lines.append(f"   • 列名: {', '.join(columns[:5])}")
            if len(columns) > 5:
                message_lines.append(f"     等共{len(columns)}列...")
        
        # 添加数据摘要
        summary = analysis.get('summary', {})
        if summary.get('status') == 'analyzed':
            message_lines.append(f"")
            message_lines.append(f"🔢 **数据统计**:")
            
            if summary.get('numeric_stats'):
                for col, stats in list(summary['numeric_stats'].items())[:2]:
                    if stats['min'] is not None:
                        message_lines.append(
                            f"   • {col}: {stats['min']:.2f} ~ {stats['max']:.2f} "
                            f"(均值: {stats['mean']:.2f})"
                        )
            
            if summary.get('sample_data'):
                message_lines.append(f"")
                message_lines.append(f"📝 **样本数据**:")
                for col, samples in list(summary['sample_data'].items())[:2]:
                    if samples:
                        message_lines.append(f"   • {col}: {', '.join(samples)}")
        
        message_text = "\n".join(message_lines)
        
        # 构建消息体
        if file_key:
            # 如果有文件key，发送文件消息
            message = {
                "msg_type": "file",
                "content": {
                    "file_key": file_key
                }
            }
        else:
            # 否则发送文本消息
            message = {
                "msg_type": "text", 
                "content": {
                    "text": message_text
                }
            }
        
        return message
    
    async def send_excel_file(self, file_path: str, send_mode: str = "analysis") -> bool:
        """
        发送Excel文件到Lark
        
        Args:
            file_path: Excel文件路径
            send_mode: 发送模式 ("analysis"=分析报告, "file"=上传文件, "both"=两者都发)
            
        Returns:
            是否发送成功
        """
        self.logger.info(f"开始处理Excel文件: {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        try:
            # 分析文件
            analysis = self.analyze_excel_file(file_path)
            if not analysis:
                self.logger.error("文件分析失败")
                return False
            
            success = True
            
            # 根据发送模式处理
            if send_mode in ["file", "both"]:
                # 尝试上传文件
                file_key = await self.upload_file_to_lark(file_path)
                if file_key:
                    file_message = {
                        "msg_type": "file",
                        "content": {
                            "file_key": file_key
                        }
                    }
                    file_success = await self.bot.send_to_lark(file_message)
                    if not file_success:
                        success = False
                        self.logger.error("发送文件失败")
                else:
                    self.logger.warning("文件上传失败，将发送分析报告")
                    send_mode = "analysis"  # 回退到分析模式
            
            if send_mode in ["analysis", "both"] or send_mode == "analysis":
                # 发送分析报告
                analysis_message = self.create_excel_message(file_path, analysis)
                analysis_success = await self.bot.send_to_lark(analysis_message)
                if not analysis_success:
                    success = False
                    self.logger.error("发送分析报告失败")
            
            if success:
                self.logger.info(f"Excel文件处理完成: {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"处理Excel文件时发生错误: {e}")
            return False
    
    async def send_multiple_excel_files(self, file_paths: List[str], 
                                      send_mode: str = "analysis") -> Dict[str, bool]:
        """
        批量发送多个Excel文件
        
        Args:
            file_paths: Excel文件路径列表
            send_mode: 发送模式
            
        Returns:
            发送结果字典 {文件路径: 是否成功}
        """
        results = {}
        
        self.logger.info(f"开始批量处理{len(file_paths)}个Excel文件")
        
        for file_path in file_paths:
            try:
                result = await self.send_excel_file(file_path, send_mode)
                results[file_path] = result
                
                # 每个文件之间稍微延迟，避免发送过快
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时发生错误: {e}")
                results[file_path] = False
        
        # 发送汇总报告
        success_count = sum(1 for success in results.values() if success)
        summary_message = {
            "msg_type": "text",
            "content": {
                "text": f"📊 **批量Excel处理完成**\n\n"
                       f"• 总文件数: {len(file_paths)}\n"
                       f"• 成功: {success_count}\n"
                       f"• 失败: {len(file_paths) - success_count}\n"
                       f"• 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }
        
        await self.bot.send_to_lark(summary_message)
        
        return results

async def main():
    """主函数 - 用于测试"""
    sender = ExcelToLarkSender()
    
    # 示例使用
    test_files = [
        "../data/depth_data_20250908_203426.csv",  # 如果有CSV转Excel的需求
    ]
    
    print("🧪 测试Excel发送功能")
    print("=" * 50)
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"📄 处理文件: {file_path}")
            success = await sender.send_excel_file(file_path, "analysis")
            print(f"结果: {'✅ 成功' if success else '❌ 失败'}")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())