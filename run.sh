#!/bin/bash
# 四平台风险评估分析启动脚本

echo "🚀 四平台风险评估分析系统启动器"
echo "支持平台: WEEX, BingX, MEXC, Gate.io"
echo "=================================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装或不在PATH中"
    echo "请安装Python 3.7+"
    exit 1
fi

echo "✅ Python环境检查通过"

# 进入脚本目录
cd "$(dirname "$0")"

# 检查依赖
echo "📦 检查依赖库..."
python3 -c "
import sys
required = ['requests', 'pandas', 'openpyxl']
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f'❌ 缺少依赖: {\" \".join(missing)}')
    print('请手动安装依赖:')
    print('方法1 (推荐): pip3 install --user requests pandas openpyxl')
    print('方法2: pip3 install --break-system-packages requests pandas openpyxl')
    print('方法3: 使用虚拟环境')
    print('  python3 -m venv venv')
    print('  source venv/bin/activate')
    print('  pip install requests pandas openpyxl')
    print('')
    print('继续运行测试模式...')
else:
    print('✅ 所有依赖已就绪')
"

# 运行分析
echo ""
echo "🔥 启动分析程序..."

# 准备日志目录与文件
LOG_DIR="缓存/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/analysis_$(date +%Y%m%d_%H%M%S).log"
echo "📝 运行日志: $LOG_FILE"

# 运行并同步输出到终端与日志文件
python3 脚本/start_analysis.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "📋 分析完成！检查生成的Excel文件"
