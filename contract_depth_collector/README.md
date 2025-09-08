# 多交易所合约铺单量数据收集器

一个支持多个主流加密货币交易所的合约深度数据（铺单量）收集工具，支持实时数据采集和分析。

## 支持的交易所

- **Binance** - 币安合约
- **MEXC** - MEXC合约  
- **Gate.io** - 芝麻开门合约
- **OKX** - 欧易合约
- **BingX** - BingX合约
- **Bitunix** - Bitunix合约
- **Blofin** - Blofin合约

## 功能特性

- 🔄 **实时数据收集** - 支持WebSocket实时数据流
- 📊 **多交易所支持** - 同时收集多个交易所数据
- 💾 **数据存储** - 自动保存为JSON和CSV格式
- 📈 **数据分析** - 内置深度数据分析和指标计算
- ⚡ **高性能** - 异步并发处理，支持高频率数据收集
- 🛡️ **错误处理** - 完善的错误处理和重连机制
- 📝 **日志记录** - 详细的日志记录和监控

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置设置

1. 编辑 `config/settings.json` 文件
2. 配置各交易所的API密钥（如需要）
3. 设置数据收集参数

### 配置示例

```json
{
  "exchanges": {
    "binance": {
      "enabled": true,
      "api_key": "your_api_key",
      "secret_key": "your_secret_key",
      "base_url": "https://fapi.binance.com",
      "ws_url": "wss://fstream.binance.com/ws",
      "rate_limit": 1200,
      "timeout": 30
    }
  },
  "data_collection": {
    "default_symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    "depth_levels": 20,
    "update_interval": 1.0,
    "max_retries": 3,
    "retry_delay": 5.0
  }
}
```

## 使用方法

### 基本使用

```bash
python run.py
```

### 程序化使用

```python
import asyncio
from main import ContractDepthCollector

async def main():
    collector = ContractDepthCollector()
    symbols = ['BTCUSDT', 'ETHUSDT']
    await collector.collect_depth_data(symbols, duration=3600)

asyncio.run(main())
```

## 数据格式

### 深度数据结构

```python
@dataclass
class DepthData:
    exchange: str          # 交易所名称
    symbol: str           # 交易对符号
    timestamp: float      # 时间戳
    bids: List[List[float]]  # 买盘 [[价格, 数量], ...]
    asks: List[List[float]]  # 卖盘 [[价格, 数量], ...]
    spread: float         # 价差
    total_bid_volume: float  # 买盘总量
    total_ask_volume: float  # 卖盘总量
```

### 分析指标

- **价差 (Spread)** - 最优买卖价差
- **中间价 (Mid Price)** - 买卖盘中间价格
- **成交量不平衡** - 买卖盘成交量差异
- **价格冲击** - 大单对价格的影响
- **订单簿压力** - 买卖盘压力对比

## 文件结构

```
contract_depth_collector/
├── main.py                 # 主程序入口
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖包
├── config/                 # 配置文件
│   ├── settings.json      # 主配置文件
│   └── settings.py        # 配置管理类
├── exchanges/             # 交易所模块
│   ├── __init__.py
│   ├── base_collector.py  # 基础收集器类
│   ├── binance_collector.py
│   ├── mexc_collector.py
│   ├── gate_collector.py
│   ├── okx_collector.py
│   ├── bingx_collector.py
│   ├── bitunix_collector.py
│   └── blofin_collector.py
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── logger_config.py   # 日志配置
│   └── data_processor.py  # 数据处理
├── data/                  # 数据存储目录
└── logs/                  # 日志目录
```

## API接口说明

### Binance
- **REST API**: `/fapi/v1/depth`
- **WebSocket**: `wss://fstream.binance.com/ws/{symbol}@depth@100ms`

### MEXC
- **REST API**: `/api/v1/contract/depth`
- **WebSocket**: `wss://contract.mexc.com/ws/contract@public.deals@{symbol}`

### Gate.io
- **REST API**: `/api/v4/futures/usdt/order_book`
- **WebSocket**: `wss://fx-ws.gateio.ws/v4/ws/usdt`

### OKX
- **REST API**: `/api/v5/market/books`
- **WebSocket**: `wss://ws.okx.com:8443/ws/v5/public`

### BingX
- **REST API**: `/openApi/swap/v2/quote/depth`
- **WebSocket**: `wss://open-api-ws.bingx.com/market`

### Bitunix
- **REST API**: `/api/v1/market/depth`
- **WebSocket**: `wss://ws.bitunix.com`

### Blofin
- **REST API**: `/api/v1/market/depth`
- **WebSocket**: `wss://open-api-ws.blofin.com/public`

## 注意事项

1. **API限制** - 各交易所都有API调用频率限制，请合理设置收集间隔
2. **网络连接** - 确保网络连接稳定，程序会自动重连
3. **数据存储** - 数据会定期自动保存，避免数据丢失
4. **日志监控** - 建议定期查看日志文件，监控程序运行状态

## 故障排除

### 常见问题

1. **连接失败** - 检查网络连接和API配置
2. **数据为空** - 确认交易对符号正确
3. **频繁断线** - 调整重连参数和超时设置

### 日志查看

```bash
tail -f logs/collector.log
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持7个主流交易所
- 实现实时数据收集和分析功能
