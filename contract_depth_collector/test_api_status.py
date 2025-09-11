#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易所API状态测试脚本
测试所有交易所的真实API连接状态并生成文档
"""

import asyncio
import json
import aiohttp
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# 导入各交易所模块
from exchanges.binance_collector import BinanceCollector
from exchanges.mexc_collector import MEXCCollectorFixed
from exchanges.gate_collector import GateCollector
from exchanges.okx_collector import OKXCollector
from exchanges.bingx_collector import BingXCollector
from exchanges.bitunix_collector import BitunixCollector
from exchanges.blofin_collector import BlofinCollectorFixed
from exchanges.weex_collector import WEEXCollectorFixed
from exchanges.bybit_collector import BybitCollector
from exchanges.kucoin_collector import KuCoinCollector
from config.settings import Settings

@dataclass
class ExchangeAPIStatus:
    """交易所API状态"""
    name: str
    api_url: str
    status: str  # 'success', 'failed', 'error'
    response_time: float
    error_message: Optional[str] = None
    data_sample: Optional[Dict] = None
    supports_depth: bool = False

class APIStatusTester:
    """API状态测试器"""
    
    def __init__(self):
        self.test_symbol = "BTCUSDT"
        self.timeout = 10
        self.results: List[ExchangeAPIStatus] = []
        
        # 加载设置
        self.settings = Settings()
        
        # 初始化所有交易所收集器
        self.exchanges = {
            'Binance': BinanceCollector(self.settings),
            'MEXC': MEXCCollectorFixed(self.settings), 
            'Gate': GateCollector(self.settings),
            'OKX': OKXCollector(self.settings),
            'BingX': BingXCollector(self.settings),
            'Bitunix': BitunixCollector(self.settings),
            'Blofin': BlofinCollectorFixed(self.settings),
            'WEEX': WEEXCollectorFixed(self.settings),
            'Bybit': BybitCollector(self.settings),
            'KuCoin': KuCoinCollector(self.settings)
        }
    
    async def test_exchange_api(self, name: str, collector) -> ExchangeAPIStatus:
        """测试单个交易所API"""
        print(f"测试 {name} API...")
        start_time = time.time()
        
        try:
            # 尝试获取深度数据
            depth_data = await collector.get_depth_rest(self.test_symbol, limit=10)
            response_time = time.time() - start_time
            
            if depth_data is not None:
                return ExchangeAPIStatus(
                    name=name,
                    api_url=getattr(collector, 'base_url', 'Unknown'),
                    status='success',
                    response_time=response_time,
                    supports_depth=True,
                    data_sample={
                        'symbol': depth_data.symbol,
                        'bids_count': len(depth_data.bids) if depth_data.bids else 0,
                        'asks_count': len(depth_data.asks) if depth_data.asks else 0,
                        'best_bid': depth_data.bids[0] if depth_data.bids else None,
                        'best_ask': depth_data.asks[0] if depth_data.asks else None,
                        'spread': depth_data.spread
                    }
                )
            else:
                return ExchangeAPIStatus(
                    name=name,
                    api_url=getattr(collector, 'base_url', 'Unknown'),
                    status='failed',
                    response_time=response_time,
                    error_message='返回空数据',
                    supports_depth=False
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return ExchangeAPIStatus(
                name=name,
                api_url=getattr(collector, 'base_url', 'Unknown'),
                status='error',
                response_time=response_time,
                error_message=str(e),
                supports_depth=False
            )
    
    async def test_all_exchanges(self):
        """测试所有交易所API"""
        print("开始测试所有交易所API状态...")
        
        # 并行测试所有交易所
        tasks = []
        for name, collector in self.exchanges.items():
            task = asyncio.create_task(self.test_exchange_api(name, collector))
            tasks.append(task)
        
        self.results = await asyncio.gather(*tasks)
        
        print(f"\\n测试完成，共测试 {len(self.results)} 个交易所")
    
    def generate_api_documentation(self) -> str:
        """生成API文档"""
        doc = f"""# 交易所API状态报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试交易对: {self.test_symbol}

## API状态汇总

| 交易所 | 状态 | 响应时间(s) | 支持深度数据 | API地址 |
|--------|------|-------------|-------------|---------|
"""
        
        for result in self.results:
            status_emoji = "✅" if result.status == "success" else "❌" if result.status == "failed" else "⚠️"
            depth_support = "是" if result.supports_depth else "否"
            
            doc += f"| {result.name} | {status_emoji} {result.status} | {result.response_time:.2f} | {depth_support} | {result.api_url} |\\n"
        
        doc += "\\n## 详细信息\\n\\n"
        
        for result in self.results:
            doc += f"### {result.name}\\n\\n"
            doc += f"- **API地址**: {result.api_url}\\n"
            doc += f"- **状态**: {result.status}\\n"
            doc += f"- **响应时间**: {result.response_time:.2f}秒\\n"
            doc += f"- **支持深度数据**: {'是' if result.supports_depth else '否'}\\n"
            
            if result.error_message:
                doc += f"- **错误信息**: {result.error_message}\\n"
            
            if result.data_sample:
                doc += f"- **数据样例**:\\n"
                for key, value in result.data_sample.items():
                    doc += f"  - {key}: {value}\\n"
            
            doc += "\\n"
        
        # 添加统计信息
        success_count = sum(1 for r in self.results if r.status == 'success')
        failed_count = sum(1 for r in self.results if r.status == 'failed')
        error_count = sum(1 for r in self.results if r.status == 'error')
        
        doc += f"""## 统计信息

- **总交易所数量**: {len(self.results)}
- **成功连接**: {success_count} ({success_count/len(self.results)*100:.1f}%)
- **连接失败**: {failed_count} ({failed_count/len(self.results)*100:.1f}%)
- **连接错误**: {error_count} ({error_count/len(self.results)*100:.1f}%)
- **平均响应时间**: {sum(r.response_time for r in self.results)/len(self.results):.2f}秒
"""
        
        return doc
    
    def save_results(self):
        """保存结果到文件"""
        # 保存详细JSON结果
        with open('data/api_test_results.json', 'w', encoding='utf-8') as f:
            json.dump([asdict(result) for result in self.results], f, ensure_ascii=False, indent=2)
        
        # 保存API文档
        doc = self.generate_api_documentation()
        with open('交易所API状态报告.md', 'w', encoding='utf-8') as f:
            f.write(doc)
        
        print("结果已保存到:")
        print("- data/api_test_results.json (详细JSON数据)")
        print("- 交易所API状态报告.md (API文档)")

async def main():
    """主函数"""
    tester = APIStatusTester()
    await tester.test_all_exchanges()
    tester.save_results()
    
    # 显示简要结果
    print("\\n=== API测试结果汇总 ===")
    for result in tester.results:
        status_icon = "✅" if result.status == "success" else "❌" if result.status == "failed" else "⚠️"
        print(f"{status_icon} {result.name}: {result.status} ({result.response_time:.2f}s)")

if __name__ == "__main__":
    asyncio.run(main())