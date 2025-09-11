# JSON数据到Lark发送使用指南

## 📋 概述

这套工具可以帮你将收集的深度数据JSON文件发送到Lark群聊，并提供增强的用户交互功能。

## 🚀 快速开始

### 1. 基础配置

确保已设置环境变量：
```bash
export LARK_WEBHOOK_URL="你的Webhook地址"
export LARK_WEBHOOK_SECRET="签名密钥"
```

### 2. 测试集成功能

```bash
cd contract_depth_collector/lark
python test_json_lark_integration.py
```

### 3. 发送数据到Lark

```bash
# 发送最新的数据文件
python send_json_to_lark.py

# 发送指定文件
python send_json_to_lark.py -f collected_data_20250908_203813.json

# 批量发送所有数据文件
python send_json_to_lark.py -p "collected_data_*.json"

# 发送实时数据
python send_json_to_lark.py -r -s BTC ETH RIF
```

## 🛠️ 核心功能

### 📤 数据发送器 (send_json_to_lark.py)

主要功能：
- **单文件发送**: 发送指定的JSON数据文件
- **批量发送**: 使用通配符匹配多个文件
- **实时数据**: 获取并发送最新的市场数据
- **多种格式**: 支持汇总、详细、原始三种显示格式

使用示例：
```bash
# 汇总格式 (默认)
python send_json_to_lark.py -f data.json -t summary

# 详细格式
python send_json_to_lark.py -f data.json -t detailed

# 原始JSON格式
python send_json_to_lark.py -f data.json -t raw
```

### 📊 数据格式化器 (json_formatter.py)

支持的格式：
- **汇总格式**: 显示关键统计信息和数据质量评估
- **详细格式**: 包含交易所结果、代币统计和数据采样
- **原始格式**: 显示JSON数据结构（大数据时显示摘要）

### 🤖 反馈处理器 (feedback_handler.py)

增强的用户交互命令：

#### 基础查询
- `@BTC` - 查询BTC实时数据
- `@ETH` - 查询ETH实时数据
- `统计` - 显示系统数据统计

#### 高级分析
- `分析 BTC 7` - 分析BTC最近7天趋势
- `对比 BTC ETH` - 对比两个代币的数据
- `趋势 ETH 30` - 查看ETH 30天价格趋势

#### 个人设置
- `设置 format simple` - 设置简单显示格式
- `设置 format detailed` - 设置详细显示格式
- `设置 notifications on` - 开启通知

#### 提醒功能
- `提醒 BTC 50000` - 设置BTC价格提醒
- `订阅 ETH` - 订阅ETH更新通知
- `取消订阅 BTC` - 取消BTC订阅

#### 实用工具
- `历史` - 查看个人查询历史
- `帮助` - 显示所有可用命令

## 📊 消息格式示例

### 汇总格式消息
```
📊 数据收集汇总报告

🕐 收集时间: 2025-09-08 20:38:13
📈 总记录数: 24
🏢 交易所数量: 8
💰 代币数量: 3

📍 交易所列表:
  • binance
  • gate
  • okx
  • bingx

💎 代币列表:
  • BTCUSDT
  • ETHUSDT
  • RIFUSDT

📊 数据统计:
  • 平均价差: 0.045000%
  • 平均铺单量: 125000.00 USDT
  • 最高流动性: binance

✅ 数据质量: 8.5/10 (优秀)
📝 质量说明: 数据覆盖完整，质量很高
```

### 详细格式消息
包含更多交易所结果详情和代币统计信息。

### 用户交互示例
```
用户: @BTC
机器人: 🔍 BTC 代币深度分析
        📊 汇总信息
        • 交易所数量: 8
        • 平均价差: 0.050000%
        • 平均铺单量: 500000.00 USDT
        ...

用户: 对比 BTC ETH
机器人: ⚖️ BTC vs ETH 对比分析
        📊 基础对比
        | 指标 | BTC | ETH | 优势 |
        |------|-----|-----|------|
        | 交易所数量 | 8 | 8 | 平手 |
        ...
```

## ⚙️ 配置说明

### Lark机器人配置
在 `larkkey.md` 文件中已包含基本配置：
- Webhook URL: `https://open.larksuite.com/open-apis/bot/v2/hook/...`
- 签名密钥: `7fvVfwPIgEvIJa1ngHaWPc`

### 环境变量 (可选)
```bash
# 基础配置
export LARK_WEBHOOK_URL="你的webhook地址"
export LARK_WEBHOOK_SECRET="签名密钥"

# 高级功能 (OpenAPI)
export LARK_APP_ID="应用ID"
export LARK_APP_SECRET="应用密钥"
export LARK_BOT_ID="机器人ID"
```

### 用户偏好设置
支持个性化设置：
- **显示格式**: default/simple/detailed
- **语言**: zh/en
- **时区**: UTC/Asia/Shanghai
- **通知**: on/off

## 🔧 故障排除

### 常见问题

1. **消息发送失败**
   ```
   ❌ 消息发送失败: 401
   ```
   解决方案：检查签名密钥和Webhook URL是否正确

2. **数据格式化错误**
   ```
   ❌ 格式化汇总消息失败
   ```
   解决方案：检查JSON文件格式是否正确

3. **环境配置问题**
   ```
   ❌ 机器人未初始化
   ```
   解决方案：确保环境变量正确设置

### 调试步骤

1. **运行集成测试**
   ```bash
   python test_json_lark_integration.py
   ```

2. **检查配置文件**
   ```bash
   cat larkkey.md
   env | grep LARK
   ```

3. **测试单个功能**
   ```bash
   # 测试JSON格式化
   python json_formatter.py
   
   # 测试反馈处理
   python feedback_handler.py
   ```

## 📈 使用建议

### 最佳实践

1. **定时发送数据**
   ```bash
   # 添加到crontab，每小时发送一次汇总
   0 * * * * cd /path/to/lark && python send_json_to_lark.py -t summary
   ```

2. **监控数据质量**
   - 使用汇总格式监控数据收集质量
   - 设置数据质量低于阈值时的告警

3. **用户体验优化**
   - 鼓励用户使用简单命令如 `@BTC`
   - 提供清晰的帮助信息
   - 记录用户偏好设置

4. **性能优化**
   - 批量发送时添加适当延时
   - 大文件使用汇总格式避免消息过长
   - 缓存常用查询结果

## 🎯 扩展功能

### 计划中的功能
- [ ] 价格提醒实际执行
- [ ] 数据导出为Excel/PDF
- [ ] 图表生成和发送
- [ ] 多语言支持
- [ ] 用户权限管理

### 自定义扩展
可以通过修改 `feedback_handler.py` 添加新的命令：

```python
async def _handle_custom_command(self, match, message, user_id, chat_id):
    """自定义命令处理"""
    # 你的逻辑
    return {
        "msg_type": "text",
        "content": {"text": "自定义响应"}
    }
```

## 📞 技术支持

如遇问题，请：
1. 查看错误日志
2. 运行集成测试
3. 检查配置文件
4. 参考示例代码

---

🎉 现在你可以开始使用这套强大的JSON到Lark集成工具了！