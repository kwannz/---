#!/bin/bash
# 系统启动脚本

echo "🚀 启动代币深度数据收集系统"
echo "================================"

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import aiohttp, asyncio, pandas" 2>/dev/null; then
    echo "❌ 缺少必要依赖，正在安装..."
    pip3 install -r requirements.txt
fi

# 创建日志目录
mkdir -p logs

# 启动系统工作流
echo "启动系统工作流..."
python3 start_system.py
