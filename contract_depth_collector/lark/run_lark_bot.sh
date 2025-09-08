#!/bin/bash
# Lark Webhook机器人启动脚本

echo "🤖 Lark Webhook代币深度分析机器人"
echo "=================================="

# 检查Python版本
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3 未安装或不在PATH中"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖包..."
python3 -c "import aiohttp, websockets, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖包，正在安装..."
    pip3 install aiohttp websockets pandas numpy
fi

# 显示配置信息
echo "📋 配置信息:"
echo "  Webhook地址: https://open.larksuite.com/open-apis/bot/v2/hook/9c4bbe9b-2e01-4d02-9084-151365f73306"
echo "  服务器端口: 8080"
echo "  服务器地址: 0.0.0.0"
echo ""

# 选择运行模式
echo "请选择运行模式:"
echo "1) 测试模式 - 运行功能测试"
echo "2) 启动服务器 - 启动Webhook服务器"
echo "3) 退出"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "🧪 运行测试模式..."
        python3 test_lark_webhook.py
        ;;
    2)
        echo "🚀 启动Webhook服务器..."
        echo "📝 配置说明:"
        echo "  1. 确保服务器可以访问外网"
        echo "  2. 在Lark机器人配置中设置Webhook地址:"
        echo "     http://your-server:8080/webhook"
        echo "  3. 在Lark群聊中使用:"
        echo "     @BTC - 查询BTC铺单量"
        echo "     @ETH - 查询ETH铺单量"
        echo "     @RIF - 查询RIF铺单量"
        echo ""
        echo "按 Ctrl+C 停止服务器"
        echo ""
        python3 start_lark_webhook.py --host 0.0.0.0 --port 8080
        ;;
    3)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac
