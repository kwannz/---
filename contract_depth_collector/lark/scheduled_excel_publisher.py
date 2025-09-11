#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时Excel发布服务
定期将数据文件转换为Excel并发送到Lark
"""

import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging

from data_to_excel_publisher import DataToExcelPublisher

class ScheduledExcelPublisher:
    """定时Excel发布器"""
    
    def __init__(self):
        self.publisher = DataToExcelPublisher()
        self.is_running = False
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/excel_publisher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ScheduledPublisher')
    
    async def publish_hourly_report(self):
        """发布每小时报告"""
        try:
            self.logger.info("开始执行每小时数据发布...")
            success = await self.publisher.publish_latest_data()
            
            if success:
                self.logger.info("每小时报告发布成功")
            else:
                self.logger.error("每小时报告发布失败")
                
        except Exception as e:
            self.logger.error(f"发布每小时报告时发生错误: {e}")
    
    async def publish_daily_summary(self):
        """发布每日汇总"""
        try:
            self.logger.info("开始执行每日汇总发布...")
            
            # 创建每日汇总数据
            today = datetime.now().strftime("%Y-%m-%d")
            summary_data = [
                {
                    "日期": today,
                    "报告类型": "每日汇总",
                    "生成时间": datetime.now().strftime("%H:%M:%S"),
                    "状态": "自动生成"
                }
            ]
            
            success = await self.publisher.publish_custom_excel(
                f"每日汇总_{today}", summary_data
            )
            
            if success:
                self.logger.info("每日汇总发布成功")
            else:
                self.logger.error("每日汇总发布失败")
                
        except Exception as e:
            self.logger.error(f"发布每日汇总时发生错误: {e}")
    
    def run_async_job(self, job_func):
        """在新的事件循环中运行异步任务"""
        def run_job():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(job_func())
            finally:
                loop.close()
        
        # 在新线程中运行
        thread = threading.Thread(target=run_job)
        thread.start()
        thread.join()
    
    def setup_schedules(self):
        """设置定时任务"""
        self.logger.info("设置定时发布任务...")
        
        # 每小时发布数据 (在每小时的第5分钟)
        schedule.every().hour.at(":05").do(
            self.run_async_job, self.publish_hourly_report
        )
        
        # 每日汇总 (每天早上9点)
        schedule.every().day.at("09:00").do(
            self.run_async_job, self.publish_daily_summary
        )
        
        # 每周汇总 (每周一早上10点)
        schedule.every().monday.at("10:00").do(
            self.run_async_job, self.publish_weekly_summary
        )
        
        self.logger.info("定时任务设置完成")
        self.logger.info("计划任务:")
        self.logger.info("  - 每小时第5分钟: 数据报告")
        self.logger.info("  - 每日09:00: 每日汇总")
        self.logger.info("  - 每周一10:00: 每周汇总")
    
    async def publish_weekly_summary(self):
        """发布每周汇总"""
        try:
            self.logger.info("开始执行每周汇总发布...")
            
            # 计算本周日期范围
            today = datetime.now()
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            sunday = monday + timedelta(days=6)
            
            week_range = f"{monday.strftime('%Y-%m-%d')} 至 {sunday.strftime('%Y-%m-%d')}"
            
            summary_data = [
                {
                    "周期": week_range,
                    "报告类型": "每周汇总",
                    "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "状态": "自动生成",
                    "说明": "本周数据收集汇总报告"
                }
            ]
            
            success = await self.publisher.publish_custom_excel(
                f"每周汇总_{monday.strftime('%Y%m%d')}", summary_data
            )
            
            if success:
                self.logger.info("每周汇总发布成功")
            else:
                self.logger.error("每周汇总发布失败")
                
        except Exception as e:
            self.logger.error(f"发布每周汇总时发生错误: {e}")
    
    def start(self):
        """启动定时发布服务"""
        if self.is_running:
            self.logger.warning("定时发布服务已在运行")
            return
        
        self.is_running = True
        self.setup_schedules()
        
        self.logger.info("🚀 定时Excel发布服务已启动")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止服务...")
            self.stop()
    
    def stop(self):
        """停止定时发布服务"""
        self.is_running = False
        schedule.clear()
        self.logger.info("✅ 定时Excel发布服务已停止")
    
    async def test_publish(self):
        """测试发布功能"""
        self.logger.info("🧪 测试Excel发布功能")
        
        # 测试数据发布
        print("1. 测试数据文件发布...")
        success1 = await self.publisher.publish_latest_data()
        print(f"   结果: {'✅ 成功' if success1 else '❌ 失败'}")
        
        # 测试自定义发布
        print("2. 测试自定义Excel发布...")
        test_data = [
            {"项目": "测试发布", "状态": "进行中", "时间": datetime.now().strftime("%H:%M:%S")},
            {"项目": "数据收集", "状态": "正常", "时间": datetime.now().strftime("%H:%M:%S")}
        ]
        success2 = await self.publisher.publish_custom_excel("测试报告", test_data)
        print(f"   结果: {'✅ 成功' if success2 else '❌ 失败'}")
        
        return success1 and success2

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='定时Excel发布服务')
    parser.add_argument('--test', action='store_true', help='测试发布功能')
    parser.add_argument('--once', action='store_true', help='执行一次发布')
    
    args = parser.parse_args()
    
    publisher = ScheduledExcelPublisher()
    
    if args.test:
        print("🧪 测试模式")
        asyncio.run(publisher.test_publish())
        
    elif args.once:
        print("📊 执行一次数据发布")
        asyncio.run(publisher.publish_hourly_report())
        
    else:
        print("⏰ 启动定时发布服务")
        print("按 Ctrl+C 停止服务")
        publisher.start()

if __name__ == "__main__":
    main()