#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统启动工作流
1. 验证数据收集
2. 部署定时任务
3. 启动Lark机器人
统一日志管理
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from main import ContractDepthCollector
from utils.logger_config import setup_logger


class SystemWorkflow:
    """系统启动工作流管理器"""
    
    def __init__(self):
        # 设置统一日志
        self.logger = setup_logger("system_workflow", log_file="logs/system_workflow.log")
        self.processes = []  # 存储启动的进程
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """设置信号处理器，优雅关闭"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，开始优雅关闭...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("正在关闭所有子进程...")
        for process in self.processes:
            if process.poll() is None:  # 进程还在运行
                self.logger.info(f"关闭进程 PID: {process.pid}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"强制关闭进程 PID: {process.pid}")
                    process.kill()
    
    async def step1_validate_data_collection(self) -> bool:
        """步骤1: 验证数据收集"""
        self.logger.info("=" * 60)
        self.logger.info("🔍 步骤1: 验证数据收集功能")
        self.logger.info("=" * 60)
        
        try:
            collector = ContractDepthCollector()
            test_symbols = ['BTCUSDT', 'ETHUSDT']
            
            self.logger.info(f"开始验证数据收集，测试代币: {', '.join(test_symbols)}")
            
            # 收集30秒数据进行验证
            await collector.collect_depth_data(test_symbols, duration=30)
            
            # 获取统计信息
            stats = collector.get_summary_statistics()
            
            total_records = stats.get('total_records', 0)
            exchanges = stats.get('exchanges', [])
            symbols = stats.get('symbols', [])
            
            self.logger.info(f"✅ 数据收集验证完成")
            self.logger.info(f"   总记录数: {total_records}")
            self.logger.info(f"   交易所: {', '.join(exchanges)}")
            self.logger.info(f"   交易对: {', '.join(symbols)}")
            
            # 验证成功条件：至少收集到100条记录
            if total_records >= 100:
                self.logger.info("🎉 数据收集验证成功！")
                return True
            else:
                self.logger.error(f"❌ 数据收集验证失败，记录数不足: {total_records} < 100")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 数据收集验证失败: {e}")
            return False
    
    def step2_deploy_scheduler(self) -> bool:
        """步骤2: 部署定时任务"""
        self.logger.info("=" * 60)
        self.logger.info("⏰ 步骤2: 部署定时任务调度器")
        self.logger.info("=" * 60)
        
        try:
            # 启动定时调度器
            scheduler_script = Path(__file__).parent / "lark" / "start_scheduler.py"
            
            if not scheduler_script.exists():
                self.logger.error(f"❌ 调度器脚本不存在: {scheduler_script}")
                return False
            
            self.logger.info("启动定时任务调度器...")
            
            # 启动调度器进程
            process = subprocess.Popen([
                sys.executable, str(scheduler_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.processes.append(process)
            
            # 等待几秒检查进程状态
            time.sleep(3)
            
            if process.poll() is None:  # 进程还在运行
                self.logger.info(f"✅ 定时任务调度器启动成功 (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ 定时任务调度器启动失败")
                self.logger.error(f"   stdout: {stdout}")
                self.logger.error(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 部署定时任务失败: {e}")
            return False
    
    def step3_start_lark_bot(self) -> bool:
        """步骤3: 启动Lark机器人"""
        self.logger.info("=" * 60)
        self.logger.info("🤖 步骤3: 启动Lark Webhook机器人")
        self.logger.info("=" * 60)
        
        try:
            # 启动Lark Webhook服务器
            lark_script = Path(__file__).parent / "lark" / "start_lark_webhook.py"
            
            if not lark_script.exists():
                self.logger.error(f"❌ Lark脚本不存在: {lark_script}")
                return False
            
            self.logger.info("启动Lark Webhook服务器...")
            
            # 启动Lark服务器进程
            process = subprocess.Popen([
                sys.executable, str(lark_script), 
                "--host", "0.0.0.0", 
                "--port", "8080"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.processes.append(process)
            
            # 等待几秒检查进程状态
            time.sleep(3)
            
            if process.poll() is None:  # 进程还在运行
                self.logger.info(f"✅ Lark Webhook服务器启动成功 (PID: {process.pid})")
                self.logger.info("   服务地址: http://0.0.0.0:8080/webhook")
                return True
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"❌ Lark Webhook服务器启动失败")
                self.logger.error(f"   stdout: {stdout}")
                self.logger.error(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 启动Lark机器人失败: {e}")
            return False
    
    def monitor_system(self):
        """监控系统状态"""
        self.logger.info("=" * 60)
        self.logger.info("📊 系统监控开始")
        self.logger.info("=" * 60)
        
        try:
            while True:
                # 检查所有进程状态
                running_processes = []
                failed_processes = []
                
                for i, process in enumerate(self.processes):
                    if process.poll() is None:
                        running_processes.append(f"进程{i+1} (PID: {process.pid})")
                    else:
                        failed_processes.append(f"进程{i+1} (PID: {process.pid})")
                
                if failed_processes:
                    self.logger.error(f"❌ 发现失败进程: {', '.join(failed_processes)}")
                    break
                
                self.logger.info(f"✅ 系统运行正常，活跃进程: {len(running_processes)}")
                
                # 每30秒检查一次
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，开始关闭系统...")
        except Exception as e:
            self.logger.error(f"系统监控异常: {e}")
    
    async def run_workflow(self):
        """运行完整工作流"""
        start_time = datetime.now()
        
        self.logger.info("🚀 开始系统启动工作流")
        self.logger.info(f"启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 步骤1: 验证数据收集
            if not await self.step1_validate_data_collection():
                self.logger.error("❌ 工作流失败：数据收集验证未通过")
                return False
            
            # 步骤2: 部署定时任务
            if not self.step2_deploy_scheduler():
                self.logger.error("❌ 工作流失败：定时任务部署失败")
                return False
            
            # 步骤3: 启动Lark机器人
            if not self.step3_start_lark_bot():
                self.logger.error("❌ 工作流失败：Lark机器人启动失败")
                return False
            
            # 工作流成功完成
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info("=" * 60)
            self.logger.info("🎉 系统启动工作流完成！")
            self.logger.info("=" * 60)
            self.logger.info(f"✅ 所有步骤执行成功")
            self.logger.info(f"⏱️  总耗时: {duration:.1f}秒")
            self.logger.info(f"🔧 运行进程: {len(self.processes)}个")
            self.logger.info(f"📊 系统状态: 正常运行")
            
            # 显示系统信息
            self.logger.info("\n📋 系统服务信息:")
            self.logger.info("   1. 定时任务调度器 - 运行中")
            self.logger.info("   2. Lark Webhook服务器 - http://0.0.0.0:8080/webhook")
            
            self.logger.info("\n🎯 使用说明:")
            self.logger.info("   • 在Lark群聊中使用: @BTC, @ETH, @RIF")
            self.logger.info("   • 历史分析: 分析 BTC 7")
            self.logger.info("   • 数据统计: 统计")
            self.logger.info("   • 帮助信息: help")
            
            # 开始系统监控
            self.monitor_system()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 工作流执行异常: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """主函数"""
    print("🚀 代币深度数据收集系统启动工作流")
    print("=" * 60)
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 启动工作流
    workflow = SystemWorkflow()
    
    try:
        # 运行异步工作流
        asyncio.run(workflow.run_workflow())
    except KeyboardInterrupt:
        print("\n用户中断，正在关闭系统...")
        workflow.cleanup()
    except Exception as e:
        print(f"系统启动失败: {e}")
        workflow.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
