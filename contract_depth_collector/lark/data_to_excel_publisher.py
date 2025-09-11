#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据文件转Excel并发布到Lark
支持CSV、JSON等格式转换为Excel并发送
"""

import os
import sys
import json
import pandas as pd
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from excel_to_lark_sender import ExcelToLarkSender

class DataToExcelPublisher:
    """数据转Excel发布器"""
    
    def __init__(self):
        self.excel_sender = ExcelToLarkSender()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('DataToExcel')
    
    def csv_to_excel(self, csv_file: str, excel_file: str = None) -> str:
        """
        CSV转Excel
        
        Args:
            csv_file: CSV文件路径
            excel_file: 输出Excel文件路径，如果为None则自动生成
            
        Returns:
            Excel文件路径
        """
        if not excel_file:
            base_name = os.path.splitext(csv_file)[0]
            excel_file = f"{base_name}.xlsx"
        
        try:
            df = pd.read_csv(csv_file)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            self.logger.info(f"CSV转Excel成功: {csv_file} -> {excel_file}")
            return excel_file
        except Exception as e:
            self.logger.error(f"CSV转Excel失败: {e}")
            raise
    
    def json_to_excel(self, json_file: str, excel_file: str = None) -> str:
        """
        JSON转Excel
        
        Args:
            json_file: JSON文件路径
            excel_file: 输出Excel文件路径，如果为None则自动生成
            
        Returns:
            Excel文件路径
        """
        if not excel_file:
            base_name = os.path.splitext(json_file)[0]
            excel_file = f"{base_name}.xlsx"
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果是字典，尝试转换为DataFrame
            if isinstance(data, dict):
                # 如果字典的值是列表，可能是列格式的数据
                if all(isinstance(v, list) for v in data.values()):
                    df = pd.DataFrame(data)
                else:
                    # 转换为键值对格式
                    df = pd.DataFrame([data])
            elif isinstance(data, list):
                # 如果是列表，直接转换
                df = pd.DataFrame(data)
            else:
                # 其他类型，转换为单行数据
                df = pd.DataFrame([{"value": data}])
            
            df.to_excel(excel_file, index=False, engine='openpyxl')
            self.logger.info(f"JSON转Excel成功: {json_file} -> {excel_file}")
            return excel_file
        except Exception as e:
            self.logger.error(f"JSON转Excel失败: {e}")
            raise
    
    def create_depth_data_excel(self, depth_data: Dict[str, Any], 
                               output_file: str = None) -> str:
        """
        创建深度数据Excel文件
        
        Args:
            depth_data: 深度数据字典
            output_file: 输出文件路径
            
        Returns:
            Excel文件路径
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"depth_data_{timestamp}.xlsx"
        
        try:
            # 创建多个工作表
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                
                # 汇总工作表
                summary_data = []
                for exchange, data in depth_data.items():
                    if isinstance(data, dict) and 'symbols' in data:
                        for symbol, symbol_data in data['symbols'].items():
                            summary_data.append({
                                'Exchange': exchange,
                                'Symbol': symbol,
                                'Bids': len(symbol_data.get('bids', [])),
                                'Asks': len(symbol_data.get('asks', [])),
                                'Timestamp': symbol_data.get('timestamp', ''),
                                'Status': 'Success' if symbol_data.get('bids') else 'Failed'
                            })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # 详细数据工作表 (每个交易所一个)
                for exchange, data in depth_data.items():
                    if isinstance(data, dict) and 'symbols' in data:
                        exchange_data = []
                        for symbol, symbol_data in data['symbols'].items():
                            # 买单数据
                            for i, bid in enumerate(symbol_data.get('bids', [])[:10]):  # 只取前10个
                                exchange_data.append({
                                    'Symbol': symbol,
                                    'Side': 'Bid',
                                    'Level': i + 1,
                                    'Price': bid[0] if len(bid) > 0 else '',
                                    'Size': bid[1] if len(bid) > 1 else '',
                                    'Timestamp': symbol_data.get('timestamp', '')
                                })
                            
                            # 卖单数据
                            for i, ask in enumerate(symbol_data.get('asks', [])[:10]):  # 只取前10个
                                exchange_data.append({
                                    'Symbol': symbol,
                                    'Side': 'Ask',
                                    'Level': i + 1,
                                    'Price': ask[0] if len(ask) > 0 else '',
                                    'Size': ask[1] if len(ask) > 1 else '',
                                    'Timestamp': symbol_data.get('timestamp', '')
                                })
                        
                        if exchange_data:
                            exchange_df = pd.DataFrame(exchange_data)
                            # 限制工作表名长度
                            sheet_name = exchange.capitalize()[:31]
                            exchange_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            self.logger.info(f"深度数据Excel创建成功: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"创建深度数据Excel失败: {e}")
            raise
    
    async def publish_latest_data(self, data_dir: str = "../data") -> bool:
        """
        发布最新的数据文件
        
        Args:
            data_dir: 数据目录路径
            
        Returns:
            是否成功发布
        """
        try:
            data_path = Path(data_dir)
            if not data_path.exists():
                self.logger.error(f"数据目录不存在: {data_dir}")
                return False
            
            # 查找最新的数据文件
            json_files = list(data_path.glob("depth_data_*.json"))
            csv_files = list(data_path.glob("depth_data_*.csv"))
            
            latest_files = []
            
            # 添加JSON文件
            if json_files:
                latest_json = max(json_files, key=os.path.getmtime)
                latest_files.append(('json', str(latest_json)))
            
            # 添加CSV文件
            if csv_files:
                latest_csv = max(csv_files, key=os.path.getmtime)
                latest_files.append(('csv', str(latest_csv)))
            
            if not latest_files:
                self.logger.warning(f"在 {data_dir} 中未找到数据文件")
                return False
            
            success = True
            
            for file_type, file_path in latest_files:
                try:
                    self.logger.info(f"处理{file_type.upper()}文件: {file_path}")
                    
                    # 转换为Excel
                    if file_type == 'json':
                        excel_file = self.json_to_excel(file_path)
                    else:  # csv
                        excel_file = self.csv_to_excel(file_path)
                    
                    # 发送到Lark
                    send_success = await self.excel_sender.send_excel_file(
                        excel_file, "analysis"
                    )
                    
                    if send_success:
                        self.logger.info(f"文件发布成功: {excel_file}")
                    else:
                        self.logger.error(f"文件发布失败: {excel_file}")
                        success = False
                    
                    # 清理临时Excel文件
                    if os.path.exists(excel_file):
                        os.remove(excel_file)
                        
                except Exception as e:
                    self.logger.error(f"处理文件 {file_path} 时发生错误: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"发布最新数据时发生错误: {e}")
            return False
    
    async def publish_custom_excel(self, title: str, data: List[Dict], 
                                 columns: List[str] = None) -> bool:
        """
        发布自定义Excel数据
        
        Args:
            title: Excel标题
            data: 数据列表
            columns: 列名列表
            
        Returns:
            是否成功发布
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = f"{title}_{timestamp}.xlsx"
            
            df = pd.DataFrame(data)
            if columns:
                df = df.reindex(columns=columns)
            
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            # 发送到Lark
            success = await self.excel_sender.send_excel_file(excel_file, "analysis")
            
            # 清理临时文件
            if os.path.exists(excel_file):
                os.remove(excel_file)
            
            return success
            
        except Exception as e:
            self.logger.error(f"发布自定义Excel失败: {e}")
            return False

async def main():
    """主函数 - 用于测试和手动发布"""
    publisher = DataToExcelPublisher()
    
    print("📊 数据Excel发布工具")
    print("=" * 50)
    
    # 发布最新数据
    print("🚀 发布最新数据文件...")
    success = await publisher.publish_latest_data()
    
    if success:
        print("✅ 数据发布成功！")
    else:
        print("❌ 数据发布失败！")
    
    # 示例：发布自定义数据
    print("\n📈 发布自定义数据示例...")
    custom_data = [
        {"交易所": "Binance", "状态": "正常", "延迟": "50ms"},
        {"交易所": "OKX", "状态": "正常", "延迟": "45ms"},
        {"交易所": "Gate", "状态": "异常", "延迟": "200ms"}
    ]
    
    custom_success = await publisher.publish_custom_excel(
        "交易所状态报告", custom_data
    )
    
    if custom_success:
        print("✅ 自定义数据发布成功！")
    else:
        print("❌ 自定义数据发布失败！")

if __name__ == "__main__":
    asyncio.run(main())