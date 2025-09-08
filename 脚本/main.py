#!/usr/bin/env python3
"""
四平台风险评估分析系统 - Main Analyzer
支持平台: WEEX, BingX, MEXC, Gate.io
分别获取四个平台的所有代币铺单数据，并生成全面的对比分析Excel报告
"""

import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback
import numpy as np
import sys
import os

class FourPlatformRiskAnalyzer:
    def __init__(self, max_workers: int = 8, request_delay: float = 0.2):
        """初始化WEEX、BingX、MEXC和Gate.io四平台深度分析器"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.request_lock = threading.Lock()
        self.last_request_time = 0
        
        # WEEX API配置
        self.weex_base_url = "https://api-contract.weex.com/capi/v2"
        self.weex_symbols_url = f"{self.weex_base_url}/market/contracts"
        self.weex_depth_url = f"{self.weex_base_url}/market/depth"
        self.weex_ticker_url = f"{self.weex_base_url}/market/ticker"
        self.weex_headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        # BingX API配置
        self.bingx_base_url = "https://open-api.bingx.com"
        self.bingx_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # MEXC API配置 
        self.mexc_base_url = "https://contract.mexc.com/api/v1/contract"
        self.mexc_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Gate.io API配置
        self.gateio_base_url = "https://api.gateio.ws/api/v4"
        self.gateio_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
    
    # ================ WEEX API Functions ================
    def get_weex_symbols(self) -> List[str]:
        """获取WEEX所有可交易的合约符号"""
        try:
            print("🔍 正在获取WEEX交易对列表...")
            response = requests.get(self.weex_symbols_url, headers=self.weex_headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                symbols = []
                for contract in data:
                    symbol = contract.get('symbol', '')
                    if symbol and 'usdt' in symbol.lower():
                        # 转换格式: 'cmt_btcusdt' -> 'BTC_USDT'
                        if '_' in symbol:
                            parts = symbol.split('_')
                            if len(parts) >= 2 and parts[1].lower().endswith('usdt'):
                                base = parts[1][:-4].upper()  # 去掉'usdt'并转大写
                                formatted_symbol = f"{base}_USDT"
                                symbols.append(formatted_symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                print(f"✅ 成功获取 {len(symbols)} 个WEEX交易对")
                return symbols
            return []
        except Exception as e:
            print(f"❌ 获取WEEX交易对失败: {e}")
            return []
    
    def get_weex_depth(self, symbol: str) -> Optional[Dict]:
        """获取WEEX深度数据"""
        try:
            self.rate_limit_request()
            
            # 将标准格式转换为WEEX格式
            if '_USDT' in symbol:
                base = symbol.replace('_USDT', '').lower()
                weex_symbol = f"cmt_{base}usdt"
            else:
                weex_symbol = symbol.lower()
            
            # WEEX API不需要limit参数，否则返回空
            params = {'symbol': weex_symbol}
            response = requests.get(self.weex_depth_url, headers=self.weex_headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'asks' in data and 'bids' in data:
                self.weex_success += 1
                return {
                    'asks': data['asks'][:20],
                    'bids': data['bids'][:20],
                    'timestamp': data.get('timestamp', int(time.time() * 1000))
                }
            else:
                self.weex_error += 1
                return None
        except Exception as e:
            self.weex_error += 1
            return None
    
    # ================ BingX API Functions ================
    def get_bingx_symbols(self) -> List[str]:
        """获取BingX所有可用的永续合约交易对"""
        url = f"{self.bingx_base_url}/openApi/swap/v2/quote/contracts"
        
        try:
            print("🔍 正在获取BingX交易对列表...")
            response = requests.get(url, headers=self.bingx_headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data:
                symbols = []
                for contract in data['data']:
                    symbol = contract.get('symbol', '')
                    if symbol and symbol.endswith('-USDT') and contract.get('status') == 1:
                        # 转换格式: 'BTC-USDT' -> 'BTC_USDT'
                        symbol = symbol.replace('-', '_')
                        symbols.append(symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                print(f"✅ 成功获取 {len(symbols)} 个BingX永续合约交易对")
                return symbols
            else:
                print(f"❌ BingX API返回格式异常")
                return []
        except Exception as e:
            print(f"❌ 获取BingX交易对失败: {e}")
            return []
    
    def get_bingx_depth(self, symbol: str) -> Optional[Dict]:
        """获取BingX深度数据"""
        try:
            self.rate_limit_request()
            
            # 转换格式: 'BTC_USDT' -> 'BTC-USDT'
            bingx_symbol = symbol.replace('_', '-')
            
            url = f"{self.bingx_base_url}/openApi/swap/v2/quote/depth"
            params = {'symbol': bingx_symbol, 'limit': 20}
            
            response = requests.get(url, headers=self.bingx_headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data:
                depth_data = data['data']
                if 'asks' in depth_data and 'bids' in depth_data:
                    self.bingx_success += 1
                    return {
                        'asks': depth_data['asks'][:20],
                        'bids': depth_data['bids'][:20],
                        'timestamp': depth_data.get('T', int(time.time() * 1000))
                    }
            
            self.bingx_error += 1
            return None
        except Exception as e:
            self.bingx_error += 1
            return None
    
    # ================ MEXC API Functions ================
    def get_mexc_symbols(self) -> List[str]:
        """获取MEXC所有可用的永续合约交易对"""
        url = f"{self.mexc_base_url}/ticker"
        
        try:
            print("🔍 正在获取MEXC交易对列表...")
            response = requests.get(url, headers=self.mexc_headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                symbols = []
                for contract in data['data']:
                    symbol = contract.get('symbol', '')
                    if symbol and '_' in symbol and symbol.endswith('_USDT'):
                        symbols.append(symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                print(f"✅ 成功获取 {len(symbols)} 个MEXC永续合约交易对")
                return symbols
            else:
                print(f"❌ MEXC API返回格式异常")
                return []
        except Exception as e:
            print(f"❌ 获取MEXC交易对失败: {e}")
            return []
    
    def get_mexc_depth(self, symbol: str) -> Optional[Dict]:
        """获取MEXC深度数据"""
        try:
            self.rate_limit_request()
            
            url = f"{self.mexc_base_url}/depth/{symbol}"
            response = requests.get(url, headers=self.mexc_headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                depth_data = data['data']
                if 'asks' in depth_data and 'bids' in depth_data:
                    self.mexc_success += 1
                    return {
                        'asks': depth_data['asks'][:20],
                        'bids': depth_data['bids'][:20],
                        'timestamp': depth_data.get('time', int(time.time() * 1000))
                    }
            
            self.mexc_error += 1
            return None
        except Exception as e:
            self.mexc_error += 1
            return None
    
    # ================ Gate.io API Functions ================
    def get_gateio_symbols(self) -> List[str]:
        """获取Gate.io所有可用的永续合约交易对"""
        url = f"{self.gateio_base_url}/futures/usdt/contracts"
        
        try:
            print("🔍 正在获取Gate.io交易对列表...")
            response = requests.get(url, headers=self.gateio_headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                symbols = []
                for contract in data:
                    name = contract.get('name', '')
                    if name and name.endswith('_USDT') and not contract.get('in_delisting', False):
                        symbols.append(name)
                
                symbols = list(set(symbols))
                symbols.sort()
                print(f"✅ 成功获取 {len(symbols)} 个Gate.io永续合约交易对")
                return symbols
            else:
                print(f"❌ Gate.io API返回格式异常")
                return []
        except Exception as e:
            print(f"❌ 获取Gate.io交易对失败: {e}")
            return []
    
    def get_gateio_depth(self, symbol: str) -> Optional[Dict]:
        """获取Gate.io深度数据"""
        try:
            self.rate_limit_request()
            
            url = f"{self.gateio_base_url}/futures/usdt/order_book"
            params = {'contract': symbol, 'limit': 20}
            
            response = requests.get(url, headers=self.gateio_headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'asks' in data and 'bids' in data:
                # Gate.io返回格式: [{'p': 'price', 's': size}]
                # 转换为标准格式: [['price', 'size']]
                asks = [[item['p'], str(item['s'])] for item in data['asks'][:20]]
                bids = [[item['p'], str(item['s'])] for item in data['bids'][:20]]
                
                self.gateio_success += 1
                return {
                    'asks': asks,
                    'bids': bids,
                    'timestamp': int(time.time() * 1000)
                }
            
            self.gateio_error += 1
            return None
        except Exception as e:
            self.gateio_error += 1
            return None
    
    # ================ Data Processing Functions ================
    def calculate_volumes(self, depth_data: Dict, symbol: str, platform: str) -> Dict:
        """计算各档位铺单量"""
        if not depth_data:
            return {}
        
        asks = depth_data.get('asks', [])
        bids = depth_data.get('bids', [])
        
        if not asks or not bids:
            return {}
        
        result = {'symbol': symbol, 'platform': platform}
        
        try:
            # 计算各档位总量
            for level in [1, 3, 20]:
                ask_volume = sum(float(ask[0]) * float(ask[1]) for ask in asks[:level])
                bid_volume = sum(float(bid[0]) * float(bid[1]) for bid in bids[:level])
                
                result[f'{level}档_ask_volume'] = ask_volume
                result[f'{level}档_bid_volume'] = bid_volume
                result[f'{level}档_total_volume'] = ask_volume + bid_volume
                result[f'{level}档_total_divided_by_2'] = (ask_volume + bid_volume) / 2
            
            # 计算买卖比例
            if result['1档_ask_volume'] > 0:
                result['买卖比例'] = result['1档_bid_volume'] / result['1档_ask_volume']
            else:
                result['买卖比例'] = 0
                
        except Exception as e:
            print(f"❌ 计算 {platform} {symbol} 铺单量时出错: {e}")
            return {}
        
        return result
    
    def get_batch_data(self, symbols: List[str], platform: str, max_workers: int = 6) -> List[Dict]:
        """批量获取平台深度数据"""
        print(f"🚀 开始获取 {platform} 深度数据 (总计: {len(symbols)} 个交易对)")
        
        batch_data = []
        batch_size = 50
        
        # 获取深度数据函数映射
        depth_functions = {
            'WEEX': self.get_weex_depth,
            'BingX': self.get_bingx_depth,
            'MEXC': self.get_mexc_depth,
            'Gate.io': self.get_gateio_depth
        }
        
        depth_func = depth_functions.get(platform)
        if not depth_func:
            print(f"❌ 未知平台: {platform}")
            return []
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]
            print(f"📦 处理 {platform} 批次 {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size} ({len(batch_symbols)} 个交易对)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {
                    executor.submit(depth_func, symbol): symbol 
                    for symbol in batch_symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        depth_data = future.result()
                        if depth_data:
                            volume_data = self.calculate_volumes(depth_data, symbol, platform)
                            if volume_data:
                                batch_data.append(volume_data)
                    except Exception as e:
                        print(f"❌ 处理 {platform} {symbol} 时出错: {e}")
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                time.sleep(1)
        
        success_count = len(batch_data)
        error_count = len(symbols) - success_count
        success_rate = (success_count / len(symbols)) * 100 if symbols else 0
        
        print(f"✅ {platform} 数据获取完成: 成功 {success_count}/{len(symbols)} ({success_rate:.1f}%)")
        
        return batch_data
    
    def create_comparison_data(self, weex_data: List[Dict], bingx_data: List[Dict], 
                             mexc_data: List[Dict], gateio_data: List[Dict]) -> List[Dict]:
        """创建四平台对比数据"""
        print("🔍 正在创建四平台对比数据...")
        
        # 创建平台数据映射
        platform_data = {
            'WEEX': {item['symbol']: item for item in weex_data},
            'BingX': {item['symbol']: item for item in bingx_data},
            'MEXC': {item['symbol']: item for item in mexc_data},
            'Gate.io': {item['symbol']: item for item in gateio_data}
        }
        
        # 找出所有平台都有的交易对
        all_symbols = set()
        for data in platform_data.values():
            all_symbols.update(data.keys())
        
        common_symbols = set(platform_data['WEEX'].keys()) & \
                        set(platform_data['BingX'].keys()) & \
                        set(platform_data['MEXC'].keys()) & \
                        set(platform_data['Gate.io'].keys())
        
        print(f"📊 交易对统计:")
        print(f"   - 总交易对: {len(all_symbols)}")
        print(f"   - 四平台共同: {len(common_symbols)}")
        
        comparison_data = []
        
        for symbol in sorted(common_symbols):
            row = {'币对': symbol}
            
            for platform in ['WEEX', 'BingX', 'MEXC', 'Gate.io']:
                data = platform_data[platform].get(symbol, {})
                for level in [1, 3, 20]:
                    row[f'{platform}_{level}档总量除以2'] = data.get(f'{level}档_total_divided_by_2', 0)
                row[f'{platform}_买卖比例'] = data.get('买卖比例', 0)
            
            comparison_data.append(row)
        
        print(f"✅ 成功创建 {len(comparison_data)} 个交易对的对比数据")
        return comparison_data
    
    def export_to_excel(self, weex_data: List[Dict], bingx_data: List[Dict], 
                       mexc_data: List[Dict], gateio_data: List[Dict], comparison_data: List[Dict]) -> str:
        """导出数据到Excel"""
        filename = f"four_platform_summary_analysis_{self.timestamp}.xlsx"
        print(f"📊 正在导出数据到 {filename}...")
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                # 1. 汇总表
                if comparison_data:
                    summary_df = pd.DataFrame(comparison_data)
                    summary_df.to_excel(writer, sheet_name='汇总表', index=False)
                
                # 2. 对比分析
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    comparison_df.to_excel(writer, sheet_name='对比分析', index=False)
                
                # 3. 各平台数据
                platform_data = [
                    ('WEEX数据', weex_data),
                    ('BingX数据', bingx_data),
                    ('MEXC数据', mexc_data),
                    ('Gate.io数据', gateio_data)
                ]
                
                for sheet_name, data in platform_data:
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 4. 统计汇总
                stats_data = [
                    ['平台', '成功', '失败', '成功率'],
                    ['WEEX', self.weex_success, self.weex_error, 
                     f"{(self.weex_success/(self.weex_success+self.weex_error)*100) if (self.weex_success+self.weex_error) > 0 else 0:.1f}%"],
                    ['BingX', self.bingx_success, self.bingx_error, 
                     f"{(self.bingx_success/(self.bingx_success+self.bingx_error)*100) if (self.bingx_success+self.bingx_error) > 0 else 0:.1f}%"],
                    ['MEXC', self.mexc_success, self.mexc_error, 
                     f"{(self.mexc_success/(self.mexc_success+self.mexc_error)*100) if (self.mexc_success+self.mexc_error) > 0 else 0:.1f}%"],
                    ['Gate.io', self.gateio_success, self.gateio_error, 
                     f"{(self.gateio_success/(self.gateio_success+self.gateio_error)*100) if (self.gateio_success+self.gateio_error) > 0 else 0:.1f}%"],
                ]
                
                stats_df = pd.DataFrame(stats_data[1:], columns=stats_data[0])
                stats_df.to_excel(writer, sheet_name='统计汇总', index=False)
            
            print(f"✅ Excel文件导出成功: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 导出Excel文件失败: {e}")
            return ""
    
    def run_full_analysis(self) -> str:
        """运行完整的四平台对比分析"""
        print("=" * 80)
        print("🚀 WEEX、BingX、MEXC、Gate.io四平台深度铺单量风险评估分析器")
        print("🎯 四平台并行获取，全面对比分析")
        print("=" * 80)
        
        # 1. 获取所有平台的交易对列表
        print("\n📊 第一步: 获取所有平台交易对列表")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            weex_future = executor.submit(self.get_weex_symbols)
            bingx_future = executor.submit(self.get_bingx_symbols)
            mexc_future = executor.submit(self.get_mexc_symbols)
            gateio_future = executor.submit(self.get_gateio_symbols)
            
            weex_symbols = weex_future.result()
            bingx_symbols = bingx_future.result()
            mexc_symbols = mexc_future.result()
            gateio_symbols = gateio_future.result()
        
        # 检查获取结果
        if not any([weex_symbols, bingx_symbols, mexc_symbols, gateio_symbols]):
            print("❌ 所有平台交易对获取失败")
            return ""
        
        print(f"📋 交易对统计: WEEX({len(weex_symbols)}) | BingX({len(bingx_symbols)}) | MEXC({len(mexc_symbols)}) | Gate.io({len(gateio_symbols)})")
        
        # 2. 并行获取深度数据
        print("\n📊 第二步: 并行获取四平台深度数据")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            print("🚀 启动四平台并行数据获取...")
            
            weex_future = executor.submit(self.get_batch_data, weex_symbols, 'WEEX') if weex_symbols else None
            bingx_future = executor.submit(self.get_batch_data, bingx_symbols, 'BingX') if bingx_symbols else None
            mexc_future = executor.submit(self.get_batch_data, mexc_symbols, 'MEXC') if mexc_symbols else None
            gateio_future = executor.submit(self.get_batch_data, gateio_symbols, 'Gate.io') if gateio_symbols else None
            
            print("⏳ 等待四平台数据获取完成...")
            
            weex_data = weex_future.result() if weex_future else []
            bingx_data = bingx_future.result() if bingx_future else []
            mexc_data = mexc_future.result() if mexc_future else []
            gateio_data = gateio_future.result() if gateio_future else []
        
        print(f"\n✅ 数据获取汇总:")
        print(f"   - WEEX: {len(weex_data)} 个交易对")
        print(f"   - BingX: {len(bingx_data)} 个交易对") 
        print(f"   - MEXC: {len(mexc_data)} 个交易对")
        print(f"   - Gate.io: {len(gateio_data)} 个交易对")
        
        # 3. 创建对比数据
        print("\n📊 第三步: 创建四平台对比分析")
        comparison_data = self.create_comparison_data(weex_data, bingx_data, mexc_data, gateio_data)
        
        # 4. 导出Excel报告
        print("\n📊 第四步: 导出Excel报告")
        excel_file = self.export_to_excel(weex_data, bingx_data, mexc_data, gateio_data, comparison_data)
        
        if excel_file:
            print("\n" + "=" * 80)
            print("🎉 四平台风险评估分析完成!")
            print(f"📊 Excel报告: {excel_file}")
            print(f"📂 报告位置: {os.path.abspath(excel_file)}")
            
            # 统计总体成功率
            total_success = self.weex_success + self.bingx_success + self.mexc_success + self.gateio_success
            total_attempts = (self.weex_success + self.weex_error + 
                            self.bingx_success + self.bingx_error + 
                            self.mexc_success + self.mexc_error + 
                            self.gateio_success + self.gateio_error)
            
            if total_attempts > 0:
                overall_success_rate = (total_success / total_attempts) * 100
                print(f"📈 总体成功率: {overall_success_rate:.1f}%")
            
            print("=" * 80)
        
        return excel_file

def main():
    """主函数"""
    print("🌟 四平台风险评估分析系统")
    print("支持平台: WEEX, BingX, MEXC, Gate.io")
    print("=" * 50)
    
    analyzer = FourPlatformRiskAnalyzer()
    excel_file = analyzer.run_full_analysis()
    
    if excel_file:
        print(f"\n🎉 四平台对比分析成功完成！")
        print(f"📋 Excel报告: {excel_file}")
        print(f"\n📊 报告包含以下工作表:")
        print(f"   📈 WEEX数据: WEEX平台所有交易对的深度数据")
        print(f"   📈 BingX数据: BingX平台所有交易对的深度数据")
        print(f"   📈 MEXC数据: MEXC平台所有交易对的深度数据")
        print(f"   📈 Gate.io数据: Gate.io平台所有交易对的深度数据")
        print(f"   🔍 对比分析: 四平台共同交易对的详细对比")
        print(f"   📋 汇总表: 币对和各交易所1-3档、1-20档总量除以2的数据")
        print(f"   📊 统计汇总: 全局分析统计")
    else:
        print("\n❌ 分析失败")

if __name__ == "__main__":
    main()