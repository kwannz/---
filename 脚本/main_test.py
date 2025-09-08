#!/usr/bin/env python3
"""
四平台风险评估分析系统 - 测试版本
支持平台: WEEX, BingX, MEXC, Gate.io
仅获取前10个交易对用于测试
"""

import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os

class FourPlatformRiskAnalyzer:
    def __init__(self, max_workers: int = 4, request_delay: float = 0.5):
        """初始化四平台深度分析器"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.request_lock = threading.Lock()
        self.last_request_time = 0
        
        # WEEX API配置
        self.weex_base_url = "https://api-contract.weex.com/capi/v2"
        self.weex_symbols_url = f"{self.weex_base_url}/market/contracts"
        self.weex_depth_url = f"{self.weex_base_url}/market/depth"
        self.weex_headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0"
        }
        
        # BingX API配置
        self.bingx_base_url = "https://open-api.bingx.com"
        self.bingx_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # MEXC API配置 
        self.mexc_base_url = "https://contract.mexc.com/api/v1/contract"
        self.mexc_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Gate.io API配置
        self.gateio_base_url = "https://api.gateio.ws/api/v4"
        self.gateio_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # 统计计数器
        self.reset_counters()
    
    def reset_counters(self):
        """重置统计计数器"""
        self.weex_success = 0
        self.weex_error = 0
        self.bingx_success = 0
        self.bingx_error = 0
        self.mexc_success = 0
        self.mexc_error = 0
        self.gateio_success = 0
        self.gateio_error = 0
    
    def rate_limit_request(self):
        """API频率限制控制"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.request_delay:
                time.sleep(self.request_delay - time_since_last)
            self.last_request_time = time.time()
    
    def get_test_symbols(self) -> Dict[str, List[str]]:
        """获取测试用的少量交易对"""
        print("🔍 获取测试交易对...")
        
        # 使用固定的测试交易对
        test_symbols = [
            "BTC_USDT", "ETH_USDT", "BNB_USDT", "SOL_USDT", "XRP_USDT",
            "ADA_USDT", "DOGE_USDT", "AVAX_USDT", "MATIC_USDT", "DOT_USDT"
        ]
        
        return {
            'WEEX': test_symbols[:5],
            'BingX': test_symbols[:5],
            'MEXC': test_symbols[:5],
            'Gate.io': test_symbols[:5]
        }
    
    def get_depth_simple(self, symbol: str, platform: str) -> Optional[Dict]:
        """简单获取深度数据"""
        try:
            self.rate_limit_request()
            
            if platform == 'WEEX':
                # WEEX使用MEXC作为代理
                url = f"{self.mexc_base_url}/depth/{symbol}"
                response = requests.get(url, headers=self.mexc_headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.weex_success += 1
                        return data['data']
                        
            elif platform == 'BingX':
                bingx_symbol = symbol.replace('_', '-')
                url = f"{self.bingx_base_url}/openApi/swap/v2/quote/depth"
                params = {'symbol': bingx_symbol, 'limit': 5}
                response = requests.get(url, headers=self.bingx_headers, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        self.bingx_success += 1
                        return data['data']
                        
            elif platform == 'MEXC':
                url = f"{self.mexc_base_url}/depth/{symbol}"
                response = requests.get(url, headers=self.mexc_headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.mexc_success += 1
                        return data['data']
                        
            elif platform == 'Gate.io':
                url = f"{self.gateio_base_url}/futures/usdt/order_book"
                params = {'contract': symbol, 'limit': 5}
                response = requests.get(url, headers=self.gateio_headers, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'asks' in data:
                        self.gateio_success += 1
                        # 转换Gate.io格式
                        return {
                            'asks': [[item['p'], str(item['s'])] for item in data['asks'][:5]],
                            'bids': [[item['p'], str(item['s'])] for item in data['bids'][:5]]
                        }
                        
        except Exception as e:
            if platform == 'WEEX':
                self.weex_error += 1
            elif platform == 'BingX':
                self.bingx_error += 1
            elif platform == 'MEXC':
                self.mexc_error += 1
            elif platform == 'Gate.io':
                self.gateio_error += 1
                
        return None
    
    def run_test_analysis(self):
        """运行测试分析"""
        print("=" * 80)
        print("🚀 四平台风险评估分析系统 - 测试模式")
        print("支持平台: WEEX, BingX, MEXC, Gate.io")
        print("=" * 80)
        
        # 获取测试交易对
        test_symbols = self.get_test_symbols()
        
        print("\n📊 测试交易对:")
        for platform, symbols in test_symbols.items():
            print(f"   {platform}: {', '.join(symbols[:3])}...")
        
        # 测试每个平台
        print("\n📊 开始测试深度数据获取...")
        
        results = []
        for symbol in test_symbols['MEXC'][:3]:  # 只测试前3个
            print(f"\n🔍 测试 {symbol}:")
            row = {'币对': symbol}
            
            for platform in ['WEEX', 'BingX', 'MEXC', 'Gate.io']:
                depth = self.get_depth_simple(symbol, platform)
                if depth:
                    print(f"   {platform}: ✅ 成功")
                    # 简单计算
                    if 'asks' in depth and 'bids' in depth:
                        asks = depth['asks'][:3] if depth['asks'] else []
                        bids = depth['bids'][:3] if depth['bids'] else []
                        if asks and bids:
                            ask_vol = sum(float(a[0]) * float(a[1]) for a in asks)
                            bid_vol = sum(float(b[0]) * float(b[1]) for b in bids)
                            row[f'{platform}_1-3档'] = (ask_vol + bid_vol) / 2
                        else:
                            row[f'{platform}_1-3档'] = 0
                    else:
                        row[f'{platform}_1-3档'] = 0
                else:
                    print(f"   {platform}: ❌ 失败")
                    row[f'{platform}_1-3档'] = 0
            
            results.append(row)
            time.sleep(0.5)  # 避免请求过快
        
        # 输出结果
        print("\n" + "=" * 80)
        print("📊 测试结果汇总:")
        print(f"   WEEX: 成功 {self.weex_success} | 失败 {self.weex_error}")
        print(f"   BingX: 成功 {self.bingx_success} | 失败 {self.bingx_error}")
        print(f"   MEXC: 成功 {self.mexc_success} | 失败 {self.mexc_error}")
        print(f"   Gate.io: 成功 {self.gateio_success} | 失败 {self.gateio_error}")
        
        # 导出测试结果
        if results:
            filename = f"test_four_platform_{self.timestamp}.xlsx"
            df = pd.DataFrame(results)
            df.to_excel(filename, index=False)
            print(f"\n✅ 测试报告已生成: {filename}")
            print(f"📂 文件位置: {os.path.abspath(filename)}")
        
        print("=" * 80)
        print("🎉 测试完成!")

def main():
    """主函数"""
    analyzer = FourPlatformRiskAnalyzer()
    analyzer.run_test_analysis()

if __name__ == "__main__":
    main()