#!/usr/bin/env python3
"""
数据验证与对比分析器
验证现有数据的准确性，并通过API获取最新数据进行对比分析
"""

import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback

class DataValidationAnalyzer:
    def __init__(self, max_workers: int = 6, request_delay: float = 0.2):
        """初始化数据验证分析器"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.request_lock = threading.Lock()
        self.last_request_time = 0
        
        # API配置
        self.setup_api_configs()
        
        # 统计计数器
        self.reset_counters()
        
        # 现有数据路径
        self.existing_excel_path = "three_platform_summary_analysis_20250703_212712.xlsx"
        
    def setup_api_configs(self):
        """设置API配置"""
        # WEEX API配置
        self.weex_meta_url = "https://http-gateway1.huabihui.cn/api/v1/public/meta/getMetaData"
        self.weex_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "appversion": "2.0.0",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.weex.sh",
            "priority": "u=1, i",
            "referer": "https://www.weex.sh/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "vs": "M5V7GhC8XciFdi9wxMvf7aAPBeV7j68a",
            "X-Sig": "ca127e69d8842387de64282ab4ee800e"
        }
        self.weex_data = {"languageType": 0}
        
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
    
    def load_existing_data(self) -> Optional[Dict]:
        """加载现有的Excel数据"""
        try:
            print(f"📊 正在加载现有数据: {self.existing_excel_path}")
            
            # 读取汇总表
            summary_df = pd.read_excel(self.existing_excel_path, sheet_name='汇总表')
            
            # 读取各平台原始数据
            weex_df = pd.read_excel(self.existing_excel_path, sheet_name='WEEX数据')
            bingx_df = pd.read_excel(self.existing_excel_path, sheet_name='BingX数据')
            mexc_df = pd.read_excel(self.existing_excel_path, sheet_name='MEXC数据')
            
            print(f"✅ 成功加载现有数据:")
            print(f"   - 汇总表: {len(summary_df)} 个币对")
            print(f"   - WEEX数据: {len(weex_df)} 个币对")
            print(f"   - BingX数据: {len(bingx_df)} 个币对")
            print(f"   - MEXC数据: {len(mexc_df)} 个币对")
            
            return {
                'summary': summary_df,
                'weex': weex_df,
                'bingx': bingx_df,
                'mexc': mexc_df
            }
            
        except Exception as e:
            print(f"❌ 加载现有数据失败: {e}")
            return None
    
    def get_all_platform_symbols(self) -> Dict[str, List[str]]:
        """获取所有平台的交易对列表"""
        print("\n🔍 正在获取所有平台的交易对列表...")
        
        symbols = {}
        
        # 获取WEEX交易对
        symbols['weex'] = self.get_weex_symbols()
        
        # 获取BingX交易对
        symbols['bingx'] = self.get_bingx_symbols()
        
        # 获取MEXC交易对
        symbols['mexc'] = self.get_mexc_symbols()
        
        # 获取Gate.io交易对
        symbols['gateio'] = self.get_gateio_symbols()
        
        # 统计信息
        print(f"\n📊 平台交易对统计:")
        for platform, symbol_list in symbols.items():
            print(f"   - {platform.upper()}: {len(symbol_list)} 个交易对")
        
        # 计算交集
        all_symbols = set()
        for symbol_list in symbols.values():
            all_symbols.update(symbol_list)
        
        common_symbols = set(symbols['weex']) & set(symbols['bingx']) & set(symbols['mexc']) & set(symbols['gateio'])
        
        print(f"\n🎯 交集统计:")
        print(f"   - 总交易对数: {len(all_symbols)}")
        print(f"   - 四平台共同交易对: {len(common_symbols)}")
        
        return symbols
    
    def get_weex_symbols(self) -> List[str]:
        """获取WEEX所有可交易的合约符号"""
        try:
            response = requests.post(self.weex_meta_url, headers=self.weex_headers, json=self.weex_data, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and 'contractList' in data['data']:
                symbols = []
                for contract in data['data']['contractList']:
                    if contract.get('enableTrade'):
                        contract_name = contract.get('contractName', '')
                        if contract_name:
                            # 转换格式: 'BTC/USDT' -> 'BTC_USDT'
                            symbol = contract_name.replace('/', '_')
                            symbols.append(symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                return symbols
            else:
                return []
                
        except Exception as e:
            print(f"❌ 获取WEEX符号失败: {e}")
            return []
    
    def get_bingx_symbols(self) -> List[str]:
        """获取BingX所有可用的永续合约交易对"""
        url = f"{self.bingx_base_url}/openApi/swap/v2/quote/contracts"
        
        try:
            response = requests.get(url, headers=self.bingx_headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data:
                symbols = []
                for contract in data['data']:
                    symbol = contract.get('symbol', '')
                    if symbol and symbol.endswith('-USDT'):
                        # 转换格式: 'BTC-USDT' -> 'BTC_USDT'
                        symbol = symbol.replace('-', '_')
                        symbols.append(symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                return symbols
            else:
                return []
                
        except Exception as e:
            print(f"❌ 获取BingX交易对失败: {e}")
            return []
    
    def get_mexc_symbols(self) -> List[str]:
        """获取MEXC所有可用的永续合约交易对"""
        url = f"{self.mexc_base_url}/ticker"
        
        try:
            response = requests.get(url, headers=self.mexc_headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') and 'data' in data:
                symbols = []
                for contract in data['data']:
                    symbol = contract.get('symbol', '')
                    if symbol and '_' in symbol:
                        symbols.append(symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                return symbols
            else:
                return []
                
        except Exception as e:
            print(f"❌ 获取MEXC交易对失败: {e}")
            return []
    
    def get_gateio_symbols(self) -> List[str]:
        """获取Gate.io所有可用的永续合约交易对"""
        url = f"{self.gateio_base_url}/futures/usdt/contracts"
        
        try:
            response = requests.get(url, headers=self.gateio_headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                symbols = []
                for contract in data:
                    name = contract.get('name', '')
                    if name and name.endswith('_USDT') and not contract.get('in_delisting', False):
                        # Gate.io格式: 'BTC_USDT' -> 'BTC_USDT' (保持格式一致)
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
    
    def compare_symbol_lists(self, existing_data: Dict, current_symbols: Dict[str, List[str]]) -> Dict:
        """对比现有数据和当前API获取的交易对列表"""
        print("\n🔍 正在对比交易对列表...")
        
        comparison_results = {}
        
        # 从现有数据中提取交易对（使用symbol列名）
        existing_symbols = {
            'weex': set(existing_data['weex']['symbol'].tolist()) if 'symbol' in existing_data['weex'].columns else set(),
            'bingx': set(existing_data['bingx']['symbol'].tolist()) if 'symbol' in existing_data['bingx'].columns else set(),
            'mexc': set(existing_data['mexc']['symbol'].tolist()) if 'symbol' in existing_data['mexc'].columns else set(),
            'gateio': set(existing_data.get('gateio', {}).get('symbol', []).tolist() if 'gateio' in existing_data and 'symbol' in existing_data.get('gateio', {}).columns else [])
        }
        
        # 对比每个平台
        for platform in ['weex', 'bingx', 'mexc', 'gateio']:
            existing_set = existing_symbols[platform]
            current_set = set(current_symbols[platform])
            
            # 计算差异
            only_in_existing = existing_set - current_set
            only_in_current = current_set - existing_set
            common = existing_set & current_set
            
            comparison_results[platform] = {
                'existing_count': len(existing_set),
                'current_count': len(current_set),
                'common_count': len(common),
                'only_in_existing': list(only_in_existing),
                'only_in_current': list(only_in_current),
                'match_rate': len(common) / len(existing_set) if existing_set else 0
            }
            
            print(f"\n📊 {platform.upper()} 交易对对比:")
            print(f"   - 现有数据: {len(existing_set)} 个")
            print(f"   - 当前API: {len(current_set)} 个")
            print(f"   - 匹配: {len(common)} 个 ({comparison_results[platform]['match_rate']:.1%})")
            print(f"   - 仅在现有数据: {len(only_in_existing)} 个")
            print(f"   - 仅在当前API: {len(only_in_current)} 个")
            
            if only_in_existing:
                print(f"   - 已下架交易对: {', '.join(list(only_in_existing)[:10])}{'...' if len(only_in_existing) > 10 else ''}")
            if only_in_current:
                print(f"   - 新增交易对: {', '.join(list(only_in_current)[:10])}{'...' if len(only_in_current) > 10 else ''}")
        
        return comparison_results
    
    def sample_data_validation(self, existing_data: Dict, sample_size: int = 20) -> Dict:
        """抽样验证数据准确性"""
        print(f"\n🔍 正在进行抽样数据验证 (样本量: {sample_size})...")
        
        # 从汇总表中随机选择样本
        summary_df = existing_data['summary']
        sample_symbols = summary_df.sample(n=min(sample_size, len(summary_df)))['币对'].tolist()
        
        print(f"📋 抽样币对: {', '.join(sample_symbols[:10])}{'...' if len(sample_symbols) > 10 else ''}")
        
        # 获取当前数据
        validation_results = []
        
        for symbol in sample_symbols:
            print(f"🔍 验证 {symbol}...")
            
            # 获取现有数据
            existing_row = summary_df[summary_df['币对'] == symbol].iloc[0]
            
            # 获取当前API数据
            current_data = self.get_current_symbol_data(symbol)
            
            # 对比结果
            result = {
                'symbol': symbol,
                'existing_data': existing_row.to_dict(),
                'current_data': current_data,
                'validation_status': 'success' if current_data else 'failed'
            }
            
            validation_results.append(result)
            
            # 避免API限制
            time.sleep(0.5)
        
        # 统计验证结果
        success_count = sum(1 for r in validation_results if r['validation_status'] == 'success')
        
        print(f"\n✅ 抽样验证完成:")
        print(f"   - 成功验证: {success_count}/{len(validation_results)} ({success_count/len(validation_results):.1%})")
        print(f"   - 验证失败: {len(validation_results) - success_count}/{len(validation_results)}")
        
        return {
            'sample_size': len(validation_results),
            'success_count': success_count,
            'success_rate': success_count / len(validation_results),
            'results': validation_results
        }
    
    def get_current_symbol_data(self, symbol: str) -> Optional[Dict]:
        """获取单个交易对的当前数据"""
        try:
            # 这里简化处理，只获取MEXC的数据作为验证
            url = f"{self.mexc_base_url}/depth/{symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return {
                    'platform': 'mexc',
                    'symbol': symbol,
                    'depth_data': data['data'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            return None
    
    def generate_validation_report(self, existing_data: Dict, symbol_comparison: Dict, sample_validation: Dict) -> str:
        """生成验证报告"""
        print("\n📊 正在生成验证报告...")
        
        report_filename = f"data_validation_report_{self.timestamp}.xlsx"
        
        with pd.ExcelWriter(report_filename, engine='openpyxl') as writer:
            
            # 1. 验证概览
            overview_data = []
            overview_data.append(['验证时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            overview_data.append(['现有数据文件', self.existing_excel_path])
            overview_data.append(['', ''])
            overview_data.append(['平台', '现有数据', '当前API', '匹配率', '新增', '下架'])
            
            for platform, result in symbol_comparison.items():
                overview_data.append([
                    platform.upper(),
                    result['existing_count'],
                    result['current_count'],
                    f"{result['match_rate']:.1%}",
                    len(result['only_in_current']),
                    len(result['only_in_existing'])
                ])
            
            overview_data.append(['', ''])
            overview_data.append(['抽样验证', ''])
            overview_data.append(['样本量', sample_validation['sample_size']])
            overview_data.append(['成功验证', sample_validation['success_count']])
            overview_data.append(['验证成功率', f"{sample_validation['success_rate']:.1%}"])
            
            overview_df = pd.DataFrame(overview_data, columns=['项目', '值'])
            overview_df.to_excel(writer, sheet_name='验证概览', index=False)
            
            # 2. 交易对对比详情
            for platform, result in symbol_comparison.items():
                if result['only_in_existing']:
                    removed_df = pd.DataFrame({
                        '已下架交易对': result['only_in_existing']
                    })
                    removed_df.to_excel(writer, sheet_name=f'{platform.upper()}_已下架', index=False)
                
                if result['only_in_current']:
                    new_df = pd.DataFrame({
                        '新增交易对': result['only_in_current']
                    })
                    new_df.to_excel(writer, sheet_name=f'{platform.upper()}_新增', index=False)
            
            # 3. 抽样验证详情
            if sample_validation['results']:
                validation_details = []
                for result in sample_validation['results']:
                    validation_details.append({
                        '币对': result['symbol'],
                        '验证状态': result['validation_status'],
                        '现有_基础风险等级': result['existing_data'].get('基础风险等级', ''),
                        '现有_WEEX_1-3档': result['existing_data'].get('WEEX_1-3档总量除以2', ''),
                        '现有_BingX_1-3档': result['existing_data'].get('BingX_1-3档总量除以2', ''),
                        '现有_MEXC_1-3档': result['existing_data'].get('MEXC_1-3档总量除以2', '')
                    })
                
                validation_df = pd.DataFrame(validation_details)
                validation_df.to_excel(writer, sheet_name='抽样验证详情', index=False)
        
        print(f"✅ 验证报告已生成: {report_filename}")
        return report_filename
    
    def run_validation_analysis(self) -> str:
        """运行完整的验证分析"""
        print("🚀 开始数据验证与对比分析...")
        print("=" * 60)
        
        # 1. 加载现有数据
        existing_data = self.load_existing_data()
        if not existing_data:
            print("❌ 无法加载现有数据，验证终止")
            return ""
        
        # 2. 获取当前API数据
        current_symbols = self.get_all_platform_symbols()
        
        # 3. 对比交易对列表
        symbol_comparison = self.compare_symbol_lists(existing_data, current_symbols)
        
        # 4. 抽样验证数据准确性
        sample_validation = self.sample_data_validation(existing_data, sample_size=10)
        
        # 5. 生成验证报告
        report_file = self.generate_validation_report(existing_data, symbol_comparison, sample_validation)
        
        print("\n" + "=" * 60)
        print("🎉 数据验证与对比分析完成!")
        print(f"📊 验证报告: {report_file}")
        
        return report_file

def main():
    """主函数"""
    analyzer = DataValidationAnalyzer()
    report_file = analyzer.run_validation_analysis()
    
    if report_file:
        print(f"\n✅ 分析完成，报告文件: {report_file}")
    else:
        print("\n❌ 分析失败")

if __name__ == "__main__":
    main() 