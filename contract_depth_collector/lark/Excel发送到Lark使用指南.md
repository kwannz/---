# 📊 Excel发送到Lark使用指南

## ✅ 功能已部署成功！

Excel文件发送功能已经成功部署并测试通过，可以将服务器上的数据文件自动转换为Excel格式并发送到Lark机器人。

## 🚀 立即使用

### 1. 发送最新数据文件
```bash
python3 send_excel_now.py
```
这个命令会：
- 自动查找最新的数据文件（JSON/CSV）
- 转换为Excel格式
- 分析数据内容
- 发送到Lark群聊

### 2. 发送指定文件
```bash
# 发送Excel文件
python3 send_excel_now.py /path/to/your/file.xlsx

# 发送CSV文件（自动转换为Excel）
python3 send_excel_now.py /path/to/your/file.csv

# 发送JSON文件（自动转换为Excel）
python3 send_excel_now.py /path/to/your/file.json
```

## 📈 支持的文件格式

- ✅ **Excel文件** (.xlsx, .xls) - 直接发送
- ✅ **CSV文件** (.csv) - 自动转换为Excel后发送
- ✅ **JSON文件** (.json) - 自动转换为Excel后发送

## 🤖 机器人消息内容

发送的Excel报告包含：

### 📁 文件基本信息
- 文件名和大小
- 处理时间戳
- 数据行数和列数

### 📊 数据分析
- 列名列表
- 数值列统计（最小值、最大值、平均值）
- 文本列样本数据
- 数据质量评估

### 💡 示例消息
```
📊 Excel文件报告

📁 文件信息:
   • 文件名: depth_data_20250908_203426.xlsx
   • 大小: 15.2 KB
   • 时间: 2025-09-08 22:15:58

📈 数据概览:
   • 行数: 148
   • 列数: 6
   • 列名: Exchange, Symbol, Side, Price, Size, Timestamp

🔢 数据统计:
   • Price: 0.58 ~ 70125.00 (均值: 8456.23)
   • Size: 0.01 ~ 1000.00 (均值: 45.67)

📝 样本数据:
   • Exchange: binance, okx, gate
   • Side: bid, ask
```

## ⏰ 定时发布功能

### 启动定时发布服务
```bash
python3 scheduled_excel_publisher.py
```

### 定时任务计划
- **每小时第5分钟**: 自动发送最新数据报告
- **每日09:00**: 发送每日数据汇总
- **每周一10:00**: 发送每周数据汇总

### 测试定时功能
```bash
# 测试发布功能
python3 scheduled_excel_publisher.py --test

# 手动执行一次发布
python3 scheduled_excel_publisher.py --once
```

## 🔧 高级功能

### 1. 批量发送多个文件
```python
from data_to_excel_publisher import DataToExcelPublisher
import asyncio

async def send_multiple():
    publisher = DataToExcelPublisher()
    files = ["file1.csv", "file2.json", "file3.xlsx"]
    
    for file_path in files:
        success = await publisher.excel_sender.send_excel_file(file_path)
        print(f"{file_path}: {'✅' if success else '❌'}")

asyncio.run(send_multiple())
```

### 2. 发送自定义Excel数据
```python
from data_to_excel_publisher import DataToExcelPublisher
import asyncio

async def send_custom_data():
    publisher = DataToExcelPublisher()
    
    # 自定义数据
    data = [
        {"交易所": "Binance", "状态": "正常", "延迟": "50ms"},
        {"交易所": "OKX", "状态": "正常", "延迟": "45ms"}
    ]
    
    success = await publisher.publish_custom_excel("服务器状态报告", data)
    return success

asyncio.run(send_custom_data())
```

## 📝 日志和监控

### 查看日志
```bash
# Excel发送日志
tail -f logs/excel_publisher.log

# Lark机器人日志
tail -f logs/lark_bot.log
```

### 服务状态
```bash
# 检查机器人服务状态
./lark_daemon.sh status

# 检查隧道连接状态
cat current_tunnel_url.txt
```

## ⚠️ 注意事项

1. **文件大小限制**: 建议Excel文件小于10MB
2. **发送频率**: 避免频繁发送，建议间隔至少1秒
3. **网络连接**: 确保Cloudflare隧道保持连接
4. **文件格式**: 确保数据文件格式正确

## 🔄 与现有系统集成

### 在数据收集脚本中添加Excel发送
```python
# 在你的数据收集脚本末尾添加
import subprocess
import sys

def send_data_to_lark(data_file):
    """发送数据文件到Lark"""
    try:
        result = subprocess.run([
            sys.executable, 
            "lark/send_excel_now.py", 
            data_file
        ], capture_output=True, text=True, cwd="..")
        
        if result.returncode == 0:
            print("✅ 数据已发送到Lark")
        else:
            print(f"❌ 发送失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 发送错误: {e}")

# 使用示例
send_data_to_lark("data/depth_data_20250908_203426.json")
```

## 🎉 成功部署总结

✅ **Excel发送功能**: 已测试成功  
✅ **自动格式转换**: CSV/JSON → Excel  
✅ **数据分析报告**: 智能内容分析  
✅ **Lark消息发送**: 正常工作  
✅ **定时发布服务**: 可选启用  
✅ **便捷脚本**: 一键发送  

现在您可以轻松地将服务器上的任何数据文件发送到Lark群聊了！🚀