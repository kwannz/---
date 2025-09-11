#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动定时任务调度器
"""

import asyncio
import sys
import schedule
import time
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ContractDepthCollector
from utils.logger_config import setup_logger


class SimpleScheduler:
    """简化的调度器"""
    
    def __init__(self):
        self.logger = setup_logger("scheduler")
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'RIFUSDT']
        self.running = False
    
    async def collect_data(self):
        """收集数据"""
        self.logger.info("开始定时数据收集...")
        try:
            collector = ContractDepthCollector()
            await collector.collect_depth_data(self.symbols, duration=300)  # 5分钟
            self.logger.info("定时数据收集完成")
        except Exception as e:
            self.logger.error(f"数据收集失败: {e}")
    
    def schedule_job(self):
        """调度任务"""
        asyncio.create_task(self.collect_data())
    
    async def start(self):
        """启动调度器"""
        self.logger.info("启动定时调度器...")
        self.running = True
        
        # 设置定时任务
        schedule.every().day.at("09:00").do(self.schedule_job)
        schedule.every().day.at("15:00").do(self.schedule_job)
        schedule.every().day.at("21:00").do(self.schedule_job)
        
        self.logger.info("定时任务已设置:")
        self.logger.info("  • 09:00 - 数据收集")
        self.logger.info("  • 15:00 - 数据收集")
        self.logger.info("  • 21:00 - 数据收集")
        
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(1)
    
    def stop(self):
        """停止调度器"""
        self.running = False


async def main():
    """主函数"""
    print("🤖 数据收集定时调度器")
    print("=" * 50)
    
    scheduler = SimpleScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        print("\n收到停止信号，正在停止调度器...")
        scheduler.stop()
    except Exception as e:
        print(f"调度器运行出错: {e}")
    
    print("调度器已停止")


if __name__ == "__main__":
    asyncio.run(main())
