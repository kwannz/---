# 四平台风险评估分析系统

## 概述

本系统对四个主要加密货币交易平台进行深度铺单量风险评估分析：
- **四大平台**: WEEX、BingX、MEXC、Gate.io (四平台并行获取，全面覆盖市场)

## 功能特点

### 🎯 核心功能
- **多平台交易对获取**: 自动获取所有平台的USDT永续合约交易对
- **深度数据分析**: 获取1-20档订单簿深度，计算铺单量
- **风险评估**: 基于流动性指标进行风险分类
- **智能对比**: 找出四平台共同交易对并进行深度对比
- **Excel报告**: 生成详细的多sheet分析报告

### 📊 分析维度
- **1档铺单量**: 最优买卖价铺单量
- **1-3档总量**: 前3档深度总和
- **1-20档总量**: 前20档深度总和  
- **买卖比例**: bid/ask ratio分析
- **平台对比**: 识别最优流动性平台

## 快速开始

### 方法1: 一键启动 (推荐)
```bash
# 给启动脚本执行权限并运行
chmod +x run.sh
./run.sh
```

### 方法2: Python直接运行
```bash
# 安装依赖
pip install requests pandas openpyxl

# 运行分析
python3 脚本/start_analysis.py
```

### 方法3: 完整分析 (需要完整环境)
```bash
python3 脚本/depth_analyzerthree.py
```

## 目录结构

- `脚本/` — 所有 Python 源码（start_analysis.py、depth_analyzerthree.py 等）
- `报表/` — 导出的 Excel 报告（自动保存）
- `文档/` — 使用说明与README
- `缓存/` — 运行日志与临时文件（run.sh 会写入 `缓存/logs/analysis_*.log`）
- `个别代币/` — 预留的个别代币资料目录

## 输出文件

### Excel报告包含以下工作表:
1. **汇总表** - 主要分析结果，按风险等级排序
2. **对比分析** - 四平台深度对比数据
3. **BingX数据** - BingX平台详细数据
4. **MEXC数据** - MEXC平台详细数据  
5. **Gate.io数据** - Gate.io平台详细数据
6. **WEEX数据** - WEEX平台详细数据
7. **详细汇总数据** - 包含基础风险等级的完整数据
8. **统计汇总** - 各平台成功率和性能统计

### 日志输出
- 运行日志自动保存到: `缓存/logs/analysis_YYYYMMDD_HHMMSS.log`
- 可在终端实时查看，同时写入日志文件

## API端点

### Gate.io API
- **合约列表**: `GET /api/v4/futures/usdt/contracts`
- **订单簿**: `GET /api/v4/futures/usdt/order_book`
- **文档**: https://www.gate.com/docs/developers/apiv4/zh_CN/#futures

### BingX API  
- **合约列表**: `GET /openApi/swap/v2/quote/contracts`
- **深度数据**: `GET /openApi/swap/v2/quote/depth`

### MEXC API
- **行情数据**: `GET /api/v1/contract/ticker`  
- **深度数据**: `GET /api/v1/contract/depth/{symbol}`

### WEEX API
- **元数据获取**: `POST https://http-gateway1.huabihui.cn/api/v1/public/meta/getMetaData`
  - 用途: 获取所有可交易合约列表
  - 参数: `{"languageType": 0}`
  - 返回: 包含enableTrade标志的合约列表
- **合约信息**: `GET https://api-contract.weex.com/capi/v2/market/contracts`
- **深度数据**: `GET https://api-contract.weex.com/capi/v2/market/depth`
- **行情数据**: `GET https://api-contract.weex.com/capi/v2/market/ticker`

## 系统架构

### 核心组件
- `ThreePlatformRiskAnalyzer` - 主分析器类
- `get_*_symbols()` - 交易对获取模块
- `get_*_depth()` - 深度数据获取模块  
- `calculate_*_volumes()` - 铺单量计算模块
- `create_comparison_data()` - 对比分析模块

### 执行流程
1. **并行获取交易对列表** (WEEX + BingX + MEXC + Gate.io 四平台同步)
2. **批量获取深度数据** (四平台并行处理 + 智能重试机制)
3. **数据整合与分析** (计算各维度铺单量指标)
4. **风险评估对比** (四平台流动性深度对比)
5. **生成分析报告** (Excel多sheet详细输出)

## 错误处理

### 智能重试机制
- **网络超时**: 自动重试，递增延迟
- **频率限制**: 智能等待，避免429错误  
- **API格式**: 兼容各平台不同响应格式
- **兜底策略**: 失败交易对逐个重试

### 容错设计
- **平台故障**: 单平台故障不影响其他平台分析
- **数据缺失**: 优雅处理空深度数据
- **格式异常**: 自动转换不同API格式

## 性能优化

### 并发策略
- **平台级并发**: 四个平台完全并行处理
- **批量处理**: 智能批量大小动态调整
- **线程池**: 合理控制并发数避免限频

### 频率控制  
- **请求限制**: 智能延迟控制
- **成功率优先**: 确保100%数据获取成功率
- **资源优化**: 内存和网络使用优化

## 依赖要求

```txt
requests>=2.25.0
pandas>=1.3.0  
openpyxl>=3.0.0
```

## 故障排除

### 常见问题
1. **网络连接问题**: 检查防火墙和代理设置
2. **API限制**: 等待一段时间后重试
3. **依赖缺失**: 确保安装所有必需的Python包
4. **权限问题**: 确保有文件写入权限
5. **WEEX域名解析**: 如遇到http-gateway1.huabihui.cn解析失败，属正常现象，系统会降级处理

### 调试模式
使用调试脚本进行单独平台测试:
```bash
python3 脚本/debug_gateio.py     # 调试Gate.io API格式
python3 脚本/debug_weex.py       # 调试WEEX API格式
python3 脚本/start_analysis.py   # 四平台连通性测试
```

### 平台状态说明
- **BingX**: 523个交易对，API稳定
- **MEXC**: 811个交易对，API稳定  
- **Gate.io**: 598个交易对，API稳定
- **WEEX**: 深度数据可获取，部分API端点可能需要特殊网络环境

## 更新日志

### v2.0.0 (最新)
- ✅ 新增Gate.io期货合约支持
- ✅ 升级为四平台并行分析架构
- ✅ 优化API格式解析和错误处理
- ✅ 增强批量处理和重试机制
- ✅ 完善Excel报告结构

### v1.0.0
- 支持WEEX、BingX、MEXC三平台分析
- 基础深度数据获取和分析功能

---

## 支持

如有问题请检查:
1. 网络连接状态  
2. API服务可用性
3. Python环境和依赖库
4. 生成的日志文件

**系统已完成Gate.io集成，现支持四平台完整分析！** 🎉
