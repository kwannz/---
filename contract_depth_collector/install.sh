#!/bin/bash
# 多交易所合约铺单量数据收集器安装脚本

echo "=== 多交易所合约铺单量数据收集器安装脚本 ==="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "✅ 检测到Python版本: $python_version"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n): " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
fi

# 安装依赖
echo "安装Python依赖包..."
pip install -r requirements.txt

if [[ $? -eq 0 ]]; then
    echo "✅ 依赖包安装成功"
else
    echo "❌ 依赖包安装失败"
    exit 1
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p data logs

# 设置权限
chmod +x run.py
chmod +x test_collector.py

echo "✅ 目录创建完成"

# 运行测试
echo "运行功能测试..."
python3 test_collector.py

if [[ $? -eq 0 ]]; then
    echo "✅ 测试通过"
else
    echo "⚠️  测试未完全通过，但程序可能仍可正常运行"
fi

echo ""
echo "=== 安装完成 ==="
echo "使用方法:"
echo "1. 编辑 config/settings.json 配置API密钥"
echo "2. 运行: python3 run.py"
echo "3. 或运行测试: python3 test_collector.py"
echo ""
echo "支持的交易所: Binance, MEXC, Gate.io, OKX, BingX, Bitunix, Blofin"
echo "数据将保存在 data/ 目录中"
echo "日志将保存在 logs/ 目录中"
