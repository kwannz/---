# 交易所API状态报告

生成时间: 2025-09-08 23:31:46
测试交易对: BTCUSDT

## API状态汇总

| 交易所 | 状态 | 响应时间(s) | 支持深度数据 | API地址 |
|--------|------|-------------|-------------|---------|
| Binance | ✅ success | 0.90 | 是 | https://fapi.binance.com |\n| MEXC | ❌ failed | 1.10 | 否 | https://futures.mexc.com |\n| Gate | ✅ success | 0.69 | 是 | https://api.gateio.ws |\n| OKX | ✅ success | 0.48 | 是 | https://www.okx.com |\n| BingX | ✅ success | 0.52 | 是 | https://open-api.bingx.com |\n| Bitunix | ✅ success | 0.81 | 是 | https://fapi.bitunix.com |\n| Blofin | ❌ failed | 0.66 | 否 | https://blofin.com |\n| WEEX | ❌ failed | 0.00 | 否 | https://api-contract.weex.com |\n| Bybit | ✅ success | 1.19 | 是 | https://api.bybit.com |\n| KuCoin | ❌ failed | 0.61 | 否 | https://api-futures.kucoin.com |\n\n## 详细信息\n\n### Binance\n\n- **API地址**: https://fapi.binance.com\n- **状态**: success\n- **响应时间**: 0.90秒\n- **支持深度数据**: 是\n- **数据样例**:\n  - symbol: BTCUSDT\n  - bids_count: 10\n  - asks_count: 10\n  - best_bid: [112732.5, 23.159]\n  - best_ask: [112732.6, 8.699]\n  - spread: 0.10000000000582077\n\n### MEXC\n\n- **API地址**: https://futures.mexc.com\n- **状态**: failed\n- **响应时间**: 1.10秒\n- **支持深度数据**: 否\n- **错误信息**: 返回空数据\n\n### Gate\n\n- **API地址**: https://api.gateio.ws\n- **状态**: success\n- **响应时间**: 0.69秒\n- **支持深度数据**: 是\n- **数据样例**:\n  - symbol: BTCUSDT\n  - bids_count: 10\n  - asks_count: 10\n  - best_bid: [112780.0, 1.55887]\n  - best_ask: [112780.1, 0.044913]\n  - spread: 0.10000000000582077\n\n### OKX\n\n- **API地址**: https://www.okx.com\n- **状态**: success\n- **响应时间**: 0.48秒\n- **支持深度数据**: 是\n- **数据样例**:\n  - symbol: BTCUSDT\n  - bids_count: 10\n  - asks_count: 10\n  - best_bid: [112789.8, 1.73343066]\n  - best_ask: [112789.9, 0.01142699]\n  - spread: 0.09999999999126885\n\n### BingX\n\n- **API地址**: https://open-api.bingx.com\n- **状态**: success\n- **响应时间**: 0.52秒\n- **支持深度数据**: 是\n- **数据样例**:\n  - symbol: BTCUSDT\n  - bids_count: 10\n  - asks_count: 10\n  - best_bid: [112743.1, 25.8189]\n  - best_ask: [112746.0, 0.0056]\n  - spread: 2.8999999999941792\n\n### Bitunix\n\n- **API地址**: https://fapi.bitunix.com\n- **状态**: success\n- **响应时间**: 0.81秒\n- **支持深度数据**: 是\n- **数据样例**:\n  - symbol: BTCUSDT\n  - bids_count: 5\n  - asks_count: 5\n  - best_bid: [112732.5, 0.5602]\n  - best_ask: [112732.6, 2.1561]\n  - spread: 0.10000000000582077\n\n### Blofin\n\n- **API地址**: https://blofin.com\n- **状态**: failed\n- **响应时间**: 0.66秒\n- **支持深度数据**: 否\n- **错误信息**: 返回空数据\n\n### WEEX\n\n- **API地址**: https://api-contract.weex.com\n- **状态**: failed\n- **响应时间**: 0.00秒\n- **支持深度数据**: 否\n- **错误信息**: 返回空数据\n\n### Bybit\n\n- **API地址**: https://api.bybit.com\n- **状态**: success\n- **响应时间**: 1.19秒\n- **支持深度数据**: 是\n- **数据样例**:\n  - symbol: BTCUSDT\n  - bids_count: 10\n  - asks_count: 10\n  - best_bid: [112747.1, 3.565]\n  - best_ask: [112747.2, 4.206]\n  - spread: 0.09999999999126885\n\n### KuCoin\n\n- **API地址**: https://api-futures.kucoin.com\n- **状态**: failed\n- **响应时间**: 0.61秒\n- **支持深度数据**: 否\n- **错误信息**: 返回空数据\n\n## 统计信息

- **总交易所数量**: 10
- **成功连接**: 6 (60.0%)
- **连接失败**: 4 (40.0%)
- **连接错误**: 0 (0.0%)
- **平均响应时间**: 0.70秒
