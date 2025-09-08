# 使用指南

## 🚀 快速启动

### 第一次使用
1. **安装依赖包**
   ```bash
   pip3 install --user requests pandas openpyxl
   ```

2. **运行系统**
```bash
# 方法1: 使用启动脚本
./run.sh
 
# 方法2: 直接运行Python
python3 脚本/start_analysis.py
```

### 系统要求
- Python 3.7+
- 网络连接
- 必需库: requests, pandas, openpyxl

## 📋 运行模式

### 1. 连通性测试模式 (默认)
- 快速检测四个平台API状态
- 获取交易对统计信息
- 测试样本交易对的深度数据
- 生成连通性报告

**适用场景**: 
- 首次使用时验证系统状态
- 定期检查API可用性
- 网络问题排查

### 2. 完整分析模式 (需要完整环境)
- 获取所有交易对完整深度数据
- 生成详细的Excel分析报告
- 包含风险评估和对比分析

**启动方法**:
```bash
python3 脚本/depth_analyzerthree.py
```

## 📊 输出说明

### 连通性测试输出
```
📊 第一步: 获取各平台交易对列表
   BingX: 523 个交易对
   MEXC: 811 个交易对  
   Gate.io: 598 个交易对

📊 第二步: 查找共同交易对
   总交易对: 873
   三平台共同: 420

📊 连通性测试结果:
   总体成功率: 100.0%
   🎉 系统运行正常！
```

### Excel报告 (完整模式)
生成文件: `报表/four_platform_summary_analysis_YYYYMMDD_HHMMSS.xlsx`

包含以下工作表:
- **汇总表**: 主要分析结果
- **对比分析**: 四平台对比数据
- **各平台数据**: BingX, MEXC, Gate.io, WEEX详细数据
- **统计汇总**: 成功率和性能指标

## 🔧 故障排除

### 常见错误

#### 1. 依赖库缺失
**错误**: `ModuleNotFoundError: No module named 'requests'`

**解决**:
```bash
# 方法1 (推荐)
pip3 install --user requests pandas openpyxl

# 方法2 (如果方法1失败)
pip3 install --break-system-packages requests pandas openpyxl

# 方法3 (使用虚拟环境)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\\Scripts\\activate  # Windows
pip install requests pandas openpyxl
```

#### 2. 网络连接问题
**症状**: API请求超时或失败

**解决**:
- 检查网络连接
- 确认防火墙设置
- 等待一段时间后重试（可能是API限频）

#### 3. WEEX模块缺失
**错误**: `No module named 'weex_depth_analyzer'`

**说明**: 这是正常的，系统会自动切换到简化模式

#### 4. 权限问题
**错误**: 无法创建或写入文件

**解决**:
```bash
# 确保当前目录有写权限
chmod 755 .
# 或切换到有权限的目录
```

### API状态检查

如果某个平台连接失败，可以手动检查：

#### BingX API
```bash
curl "https://open-api.bingx.com/openApi/swap/v2/quote/contracts"
```

#### MEXC API  
```bash
curl "https://contract.mexc.com/api/v1/contract/ticker"
```

#### Gate.io API
```bash
curl "https://api.gateio.ws/api/v4/futures/usdt/contracts"
```

## 🔄 更新和维护

### 更新系统
```bash
# 备份当前配置
cp -r . backup_$(date +%Y%m%d)

# 更新代码文件
# (替换新版本文件)

# 运行测试
python3 脚本/start_analysis.py
```

### 清理临时文件
```bash
# 清理Python缓存
rm -rf __pycache__/
rm -f *.pyc
```

## 💡 高级用法

### 自定义配置
在代码中可以调整以下参数：
- `max_workers`: 并发线程数
- `request_delay`: 请求间延迟
- `timeout`: API超时时间

### 定时任务
```bash
# 添加到crontab进行定时分析
# 每天上午9点运行
0 9 * * * cd /path/to/analysis && ./run.sh
```

### 批量分析
```python
# 可以在代码中设置特定币对列表
target_symbols = ["BTC_USDT", "ETH_USDT", "BNB_USDT"]
# 修改get_*_symbols函数以过滤特定币对
```

## 📞 支持

### 调试信息收集
运行出错时，请提供：
1. 完整的错误信息
2. Python版本: `python3 --version`
3. 操作系统信息
4. 网络环境（是否使用代理等）

### 调试单个平台
```bash
# 调试Gate.io API格式
python3 脚本/debug_gateio.py

# 调试WEEX API格式
python3 脚本/debug_weex.py
```

---

**系统现已支持四平台完整分析，开始您的风险评估之旅！** 🎯
