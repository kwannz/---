# Lark代币深度分析机器人

基于WebSocket的实时代币铺单量和手续费点差分析机器人，支持@代币查询功能。

## 🚀 功能特性

### 核心功能
- **@代币查询**: 支持@代币名称查询实时铺单量数据
- **多交易所对比**: 同时查询8个主要交易所数据
- **实时数据**: 基于WebSocket的实时数据推送
- **深度分析**: 1-20档铺单量分析
- **价差分析**: 手续费点差对比分析
- **流动性排名**: 各交易所流动性排名

### 支持的交易所
- Binance (币安)
- Gate.io (芝麻开门)
- OKX (欧易)
- BingX (必应)
- Bybit (拜比特)
- Bitunix (比特尼克斯)
- WEEX (维克斯)
- KuCoin (库币)

## 📁 项目结构

```
lark/
├── bot/                    # 机器人核心
│   └── lark_bot.py        # 主机器人类
├── websocket/             # WebSocket相关
│   └── websocket_client.py # WebSocket客户端
├── config/                # 配置文件
│   └── lark_config.py     # 配置管理
├── utils/                 # 工具函数
│   └── helpers.py         # 辅助工具
├── handlers/              # 消息处理器
│   └── message_handler.py # 消息处理逻辑
├── start_bot.py          # 启动机器人
├── start_client.py       # 启动客户端
├── requirements.txt      # 依赖包
└── README.md            # 说明文档
```

## 🛠️ 安装和配置

### 1. 安装依赖

```bash
cd lark
pip install -r requirements.txt
```

### 2. 环境配置

创建 `.env` 文件（可选）：

```env
# WebSocket服务器配置
LARK_WS_HOST=localhost
LARK_WS_PORT=8765
LARK_WS_TIMEOUT=30

# 数据收集配置
LARK_CACHE_TIMEOUT=30
LARK_RATE_LIMIT=1.0
LARK_TIMEOUT=30

# 日志配置
LARK_LOG_LEVEL=INFO
LARK_LOG_FILE=lark_bot.log

# 安全配置
LARK_ALLOWED_TOKENS=BTC,ETH,BNB,ADA,SOL,XRP
LARK_RATE_LIMIT_PER_USER=10
LARK_MAX_REQUESTS_PER_MINUTE=100
```

### 3. 启动机器人

```bash
python start_bot.py
```

### 4. 启动客户端

```bash
# 交互模式
python start_client.py --interactive

# 查询特定代币
python start_client.py --token BTC

# 指定服务器地址
python start_client.py --host 192.168.1.100 --port 8765
```

## 💻 使用方法

### 基本命令

#### 查询代币
```
@BTC          # 查询BTC铺单量
@ETH          # 查询ETH铺单量
@RIF          # 查询RIF铺单量
```

#### 系统命令
```
help          # 显示帮助信息
status        # 显示机器人状态
exchanges     # 显示支持的交易所
ping          # 测试连接
clear         # 清空缓存
config        # 显示配置信息
```

#### 高级命令
```
compare BTC ETH    # 对比两个代币
rank BTC          # 显示BTC在各交易所的排名
history BTC       # 显示BTC历史数据（开发中）
alert BTC         # 设置BTC警报（开发中）
```

### 消息格式

#### 代币查询响应
```
🔍 **BTC 代币深度分析**

📊 **汇总信息**
• 交易所数量: 5
• 平均价差: 0.074900%
• 最小价差: 0.017716%
• 最大价差: 0.248139%
• 平均1档铺单量: 168.928150 USDT
• 平均20档铺单量: 22889.299235 USDT
• 最佳流动性: bybit
• 最低价差: binance

📈 **各交易所详情**
**BINANCE**
• 价格: 0.056350 / 0.056360
• 价差: 0.017716%
• 1档铺单量: 168.928150 USDT
• 20档铺单量: 15234.567890 USDT
• 买卖比例: 1.022345

⏰ 更新时间: 2025-09-08 15:16:27
```

## 🔧 配置说明

### WebSocket配置
- `host`: WebSocket服务器地址
- `port`: WebSocket服务器端口
- `timeout`: 连接超时时间
- `max_connections`: 最大连接数

### 数据收集配置
- `cache_timeout`: 缓存超时时间（秒）
- `max_cache_size`: 最大缓存大小
- `rate_limit`: 请求频率限制（秒）
- `timeout`: 请求超时时间

### 安全配置
- `allowed_tokens`: 允许查询的代币列表
- `rate_limit_per_user`: 每用户每分钟请求限制
- `max_requests_per_minute`: 每分钟最大请求数

## 📊 数据格式

### 深度数据
```json
{
  "timestamp": "2025-09-08T15:16:27",
  "token": "BTC",
  "exchanges": {
    "binance": {
      "exchange": "binance",
      "symbol": "BTCUSDT",
      "best_bid": 0.056350,
      "best_ask": 0.056360,
      "mid_price": 0.056355,
      "spread": 0.000010,
      "spread_percent": 0.017716,
      "1档_买盘量": 84.464075,
      "1档_卖盘量": 84.464075,
      "1档_总铺单量": 168.928150,
      "20档_买盘量": 7617.283945,
      "20档_卖盘量": 7617.283945,
      "20档_总铺单量": 15234.567890,
      "买卖比例": 1.000000,
      "timestamp": "2025-09-08 15:16:27"
    }
  },
  "summary": {
    "total_exchanges": 5,
    "avg_spread_percent": 0.074900,
    "min_spread_percent": 0.017716,
    "max_spread_percent": 0.248139,
    "avg_1档_铺单量": 168.928150,
    "avg_20档_铺单量": 22889.299235,
    "best_liquidity_exchange": "bybit",
    "best_spread_exchange": "binance"
  }
}
```

## 🚀 部署指南

### 1. 本地部署

```bash
# 克隆项目
git clone <repository-url>
cd contract_depth_collector/lark

# 安装依赖
pip install -r requirements.txt

# 启动机器人
python start_bot.py

# 启动客户端（新终端）
python start_client.py --interactive
```

### 2. Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8765

CMD ["python", "start_bot.py"]
```

### 3. 生产环境

```bash
# 使用systemd管理服务
sudo systemctl enable lark-bot
sudo systemctl start lark-bot

# 使用nginx反向代理
upstream lark_ws {
    server 127.0.0.1:8765;
}

server {
    location /ws {
        proxy_pass http://lark_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔍 故障排除

### 常见问题

1. **连接失败**
   - 检查WebSocket服务器是否启动
   - 检查端口是否被占用
   - 检查防火墙设置

2. **数据获取失败**
   - 检查网络连接
   - 检查交易所API状态
   - 检查代币符号是否正确

3. **性能问题**
   - 调整缓存超时时间
   - 调整速率限制
   - 增加服务器资源

### 日志查看

```bash
# 查看机器人日志
tail -f lark_bot.log

# 查看系统日志
journalctl -u lark-bot -f
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交 Issue 或联系开发团队。

---

**版本**: v1.0.0  
**更新时间**: 2025年9月8日  
**作者**: Lark代币分析团队
