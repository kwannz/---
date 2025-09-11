# Lark机器人配置指南

## 📋 概述

本指南将详细介绍如何配置和使用Lark代币深度分析机器人，包括后台运行、日志管理和用户交互功能。

## 🚀 快速开始

### 1. 后台启动服务

```bash
cd /Users/zhaoleon/Downloads/铺单量/contract_depth_collector/lark

# 启动服务
./lark_daemon.sh start

# 查看状态
./lark_daemon.sh status

# 查看日志
./lark_daemon.sh logs main
```

### 2. 服务管理命令

```bash
./lark_daemon.sh start      # 启动服务
./lark_daemon.sh stop       # 停止服务  
./lark_daemon.sh restart    # 重启服务
./lark_daemon.sh status     # 查看状态
./lark_daemon.sh logs       # 查看日志
./lark_daemon.sh follow     # 实时日志
./lark_daemon.sh clean      # 清理日志
./lark_daemon.sh help       # 帮助信息
```

## ⚙️ Lark开放平台配置

### 第一步：创建企业自建应用

1. **访问Lark开放平台**
   - 网址：https://open.larksuite.com
   - 登录你的Lark开发者账号

2. **创建应用**
   - 点击"创建企业自建应用"
   - 填写应用名称：`代币深度分析机器人`
   - 填写应用描述：`提供实时代币深度数据查询和分析服务`
   - 上传应用图标（可选）

3. **获取应用凭证**
   - 记录 `App ID`
   - 记录 `App Secret`

### 第二步：配置应用权限

1. **添加应用能力**
   - 启用"机器人"功能
   - 启用"消息与群组"功能

2. **设置机器人权限**
   - 接收消息：`im:message.receive_v1`
   - 读取用户发送给机器人的单聊消息：✅
   - 读取群组中@机器人的消息：✅
   - 发送消息：`im:message`
   - 向用户或群组发送消息：✅

3. **事件订阅配置**
   - 开启事件订阅：✅
   - 事件类型：`接收消息 - im.message.receive_v1`
   - 请求网址：`http://你的服务器IP:8080/webhook`
   - 加密方式：建议关闭（开发阶段）

### 第三步：配置Webhook

1. **设置回调地址**
   ```
   http://你的服务器IP:8080/webhook
   ```
   
   > ⚠️ 注意：确保你的服务器能被Lark访问，如果是内网需要配置内网穿透

2. **配置签名验证**
   - 使用现有密钥：`7fvVfwPIgEvIJa1ngHaWPc`
   - 或者生成新的密钥并更新 `larkkey.md` 文件

3. **验证Webhook**
   - Lark会发送验证请求
   - 服务器自动响应验证
   - 验证成功后显示绿色✅

### 第四步：发布和安装应用

1. **应用发布**
   - 点击"发布版本"
   - 选择发布范围（推荐：仅对当前企业可见）
   - 提交审核

2. **添加机器人到群聊**
   - 在Lark群聊中点击"+"
   - 选择"机器人"
   - 搜索并添加你的机器人
   - 或者直接@机器人名称邀请

## 🤖 机器人使用方法

### 基础查询命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `@BTC` | 查询BTC实时深度数据 | @BTC |
| `@ETH` | 查询ETH实时深度数据 | @ETH |
| `@RIF` | 查询RIF实时深度数据 | @RIF |
| `help` | 显示帮助信息 | help |
| `统计` | 查看系统数据统计 | 统计 |

### 高级分析命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `分析 代币 天数` | 历史趋势分析 | 分析 BTC 7 |
| `对比 代币1 代币2` | 代币对比分析 | 对比 BTC ETH |
| `趋势 代币 天数` | 价格趋势分析 | 趋势 ETH 30 |

### 个人设置命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `设置 format 格式` | 设置显示格式 | 设置 format detailed |
| `设置 notifications 开关` | 通知开关 | 设置 notifications on |
| `历史` | 查看查询历史 | 历史 |

### 实用工具命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `提醒 代币 价格` | 价格提醒 | 提醒 BTC 50000 |
| `订阅 代币` | 订阅更新 | 订阅 ETH |
| `取消订阅 代币` | 取消订阅 | 取消订阅 BTC |

## 📊 日志系统

### 日志文件类型

1. **主日志** (`logs/lark_bot.log`)
   - 记录机器人主要运行信息
   - 用户命令处理记录
   - 服务启停信息

2. **错误日志** (`logs/lark_error.log`)
   - 详细的错误信息和堆栈跟踪
   - 异常处理记录
   - 调试信息

3. **访问日志** (`logs/lark_access.log`)
   - HTTP请求记录
   - 客户端IP和User-Agent
   - 请求时间和响应状态

4. **性能日志** (`logs/lark_performance.log`)
   - 请求处理时间
   - 系统性能指标
   - 统计信息

5. **守护进程日志** (`logs/daemon.log`)
   - 服务启停记录
   - 进程管理信息

### 日志管理命令

```bash
# 查看不同类型的日志
./lark_daemon.sh logs main      # 主日志
./lark_daemon.sh logs error     # 错误日志  
./lark_daemon.sh logs access    # 访问日志
./lark_daemon.sh logs perf      # 性能日志
./lark_daemon.sh logs daemon    # 守护进程日志

# 实时查看日志
./lark_daemon.sh follow main    # 实时主日志
./lark_daemon.sh follow error   # 实时错误日志

# 查看指定行数
./lark_daemon.sh logs main 100  # 查看主日志最后100行

# 清理所有日志
./lark_daemon.sh clean
```

### 日志轮转配置

- **主日志**：10MB自动轮转，保留5个历史文件
- **错误日志**：5MB自动轮转，保留3个历史文件  
- **访问日志**：20MB自动轮转，保留7个历史文件
- **性能日志**：5MB自动轮转，保留3个历史文件

## 🔧 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 检查Python环境
python3 --version

# 检查依赖包
pip3 list | grep aiohttp

# 检查端口占用
lsof -i :8080

# 查看详细错误
./lark_daemon.sh logs error
```

#### 2. Webhook验证失败

- **检查网络连通性**：确保Lark能访问你的服务器
- **检查端口开放**：确保8080端口开放
- **检查签名密钥**：确认`larkkey.md`中的密钥正确
- **查看访问日志**：`./lark_daemon.sh logs access`

#### 3. 机器人不响应

```bash
# 检查服务状态
./lark_daemon.sh status

# 查看实时日志
./lark_daemon.sh follow main

# 检查错误日志
./lark_daemon.sh logs error 50
```

#### 4. 数据查询失败

- **检查数据收集器**：确认交易所API正常
- **查看性能日志**：`./lark_daemon.sh logs perf`
- **重启服务**：`./lark_daemon.sh restart`

### 调试模式

```bash
# 测试模式运行
python3 start_lark_with_logging.py --test

# 查看统计信息
python3 start_lark_with_logging.py --stats

# 前台运行（便于调试）
python3 start_lark_with_logging.py --host 0.0.0.0 --port 8080
```

## 📈 性能优化

### 监控指标

- **请求处理时间**：平均响应时间应小于2秒
- **成功率**：应保持在95%以上
- **内存使用**：定期检查内存占用
- **日志大小**：定期清理或压缩日志文件

### 优化建议

1. **定期重启**：建议每天重启一次服务
2. **日志清理**：每周清理一次日志
3. **监控告警**：设置服务监控和告警
4. **负载均衡**：高并发时考虑部署多实例

## 🔒 安全配置

### 网络安全

- **防火墙设置**：只开放必要的8080端口
- **IP白名单**：如可能，限制Lark服务器IP访问
- **HTTPS配置**：生产环境建议使用HTTPS

### 签名验证

```python
# 启用签名验证（推荐）
export LARK_WEBHOOK_SECRET="your-secret-key"
```

### 日志安全

- **敏感信息过滤**：日志中不记录用户敏感信息
- **日志文件权限**：设置适当的文件访问权限
- **日志加密**：必要时考虑日志文件加密

## 📞 支持与维护

### 服务监控

```bash
# 定期检查脚本（可加入crontab）
*/5 * * * * cd /path/to/lark && ./lark_daemon.sh status >/dev/null || ./lark_daemon.sh start
```

### 备份策略

- **配置文件备份**：定期备份配置文件
- **日志文件归档**：重要日志文件定期归档
- **数据库备份**：如有数据持久化需求

### 更新维护

1. **停止服务**：`./lark_daemon.sh stop`
2. **备份配置**：备份重要配置文件
3. **更新代码**：更新机器人代码
4. **测试验证**：测试新版本功能
5. **启动服务**：`./lark_daemon.sh start`

---

## 🎉 结语

现在你已经拥有了一个功能完整的Lark代币分析机器人！

**核心功能**：
- ✅ 实时代币深度数据查询
- ✅ 历史趋势分析和对比
- ✅ 用户个性化设置
- ✅ 完整的日志记录和监控
- ✅ 后台服务自动化管理

**使用场景**：
- 📊 实时监控代币市场
- 📈 分析市场趋势变化  
- ⚖️ 对比不同交易所数据
- 🔔 设置价格提醒通知
- 📋 导出数据报告

开始在你的Lark群聊中使用 `@BTC` 命令体验强大的数据分析功能吧！🚀