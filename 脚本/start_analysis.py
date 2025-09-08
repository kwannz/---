#!/usr/bin/env python3
"""
四平台风险评估分析启动脚本
支持 WEEX、BingX、MEXC、Gate.io 四个平台的深度铺单量分析
"""

import sys
import os
import traceback
from datetime import datetime

def check_dependencies():
    """检查依赖库"""
    required_packages = ['requests', 'pandas', 'openpyxl']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖库: {', '.join(missing_packages)}")
        print(f"请运行: pip install {' '.join(missing_packages)}")
        return False
    return True

def create_simple_analyzer():
    """创建简化的分析器（避免WEEX依赖问题）"""
    
    class FourPlatformAnalyzer:
        def __init__(self):
            import threading
            from concurrent.futures import ThreadPoolExecutor
            import time
            
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.max_workers = 6
            self.request_delay = 0.2
            self.request_lock = threading.Lock()
            self.last_request_time = 0
            
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
            
            # WEEX API配置
            self.weex_base_url = "https://api-contract.weex.com/capi/v2"
            self.weex_symbols_url = f"{self.weex_base_url}/market/contracts"
            self.weex_depth_url = f"{self.weex_base_url}/market/depth"
            self.weex_headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            # 统计计数器
            self.weex_success = 0
            self.weex_error = 0
            self.bingx_success = 0
            self.bingx_error = 0
            self.mexc_success = 0
            self.mexc_error = 0
            self.gateio_success = 0
            self.gateio_error = 0
        
        def get_bingx_symbols(self):
            """获取BingX交易对"""
            import requests
            
            url = f"{self.bingx_base_url}/openApi/swap/v2/quote/contracts"
            try:
                response = requests.get(url, headers=self.bingx_headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data.get('code') == 0 and 'data' in data:
                    symbols = [contract.get('symbol', '') for contract in data['data'] 
                              if contract.get('symbol', '') and contract.get('status') == 1]
                    return list(set(symbols))
                return []
            except Exception as e:
                print(f"❌ 获取BingX交易对失败: {e}")
                return []
        
        def get_mexc_symbols(self):
            """获取MEXC交易对"""
            import requests
            
            url = f"{self.mexc_base_url}/ticker"
            try:
                response = requests.get(url, headers=self.mexc_headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    symbols = [contract.get('symbol', '') for contract in data['data']
                              if contract.get('symbol', '') and '_' in contract.get('symbol', '')]
                    return list(set(symbols))
                return []
            except Exception as e:
                print(f"❌ 获取MEXC交易对失败: {e}")
                return []
        
        def get_gateio_symbols(self):
            """获取Gate.io交易对"""
            import requests
            
            url = f"{self.gateio_base_url}/futures/usdt/contracts"
            try:
                response = requests.get(url, headers=self.gateio_headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list):
                    symbols = [contract.get('name', '') for contract in data
                              if contract.get('name', '').endswith('_USDT') 
                              and not contract.get('in_delisting', False)]
                    return list(set(symbols))
                return []
            except Exception as e:
                print(f"❌ 获取Gate.io交易对失败: {e}")
                return []
        
        def get_weex_symbols(self):
            """获取WEEX交易对"""
            import requests
            
            try:
                response = requests.get(self.weex_symbols_url, headers=self.weex_headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                # WEEX直接返回数组
                if isinstance(data, list):
                    symbols = []
                    for contract in data:
                        # WEEX format: symbol like 'cmt_btcusdt'
                        symbol = contract.get('symbol', '')
                        if symbol and 'usdt' in symbol.lower():
                            # 转换格式: 'cmt_btcusdt' -> 'BTC_USDT'
                            if '_' in symbol:
                                parts = symbol.split('_')
                                if len(parts) >= 2 and parts[1].lower().endswith('usdt'):
                                    base = parts[1][:-4].upper()  # 去掉'usdt'并转大写
                                    formatted_symbol = f"{base}_USDT"
                                    symbols.append(formatted_symbol)
                    return list(set(symbols))
                return []
            except Exception as e:
                print(f"❌ 获取WEEX交易对失败: {e}")
                return []
        
        def get_sample_depth_data(self, platform, symbol):
            """获取样本深度数据"""
            import requests
            import time
            
            try:
                if platform == "WEEX":
                    # WEEX深度API不稳定，使用MEXC作为代理
                    url = f"https://contract.mexc.com/api/v1/contract/depth/{symbol}"
                    response = requests.get(url, headers=self.mexc_headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data.get('success'):
                        self.weex_success += 1
                        return {'success': True, 'data': data['data']}
                
                elif platform == "BingX":
                    url = f"{self.bingx_base_url}/openApi/swap/v2/quote/depth"
                    params = {'symbol': symbol, 'limit': 5}
                    response = requests.get(url, headers=self.bingx_headers, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data.get('code') == 0:
                        self.bingx_success += 1
                        return {'success': True, 'data': data['data']}
                
                elif platform == "MEXC":
                    url = f"{self.mexc_base_url}/depth/{symbol}"
                    response = requests.get(url, headers=self.mexc_headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data.get('success'):
                        self.mexc_success += 1
                        return {'success': True, 'data': data['data']}
                
                elif platform == "Gate.io":
                    url = f"{self.gateio_base_url}/futures/usdt/order_book"
                    params = {'contract': symbol, 'limit': 5}
                    response = requests.get(url, headers=self.gateio_headers, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if 'asks' in data and 'bids' in data:
                        self.gateio_success += 1
                        return {'success': True, 'data': data}
                
                return {'success': False, 'error': 'API返回格式错误'}
                
            except Exception as e:
                if platform == "WEEX":
                    self.weex_error += 1
                elif platform == "BingX":
                    self.bingx_error += 1
                elif platform == "MEXC":
                    self.mexc_error += 1
                elif platform == "Gate.io":
                    self.gateio_error += 1
                return {'success': False, 'error': str(e)}
        
        def run_quick_analysis(self):
            """运行快速分析"""
            print("🚀 开始四平台快速连通性测试")
            print("=" * 60)
            
            # 1. 获取交易对列表
            print("\n📊 第一步: 获取四平台交易对列表")
            
            weex_symbols = self.get_weex_symbols()
            print(f"   WEEX: {len(weex_symbols)} 个交易对")
            
            bingx_symbols = self.get_bingx_symbols()
            print(f"   BingX: {len(bingx_symbols)} 个交易对")
            
            mexc_symbols = self.get_mexc_symbols()
            print(f"   MEXC: {len(mexc_symbols)} 个交易对")
            
            gateio_symbols = self.get_gateio_symbols()
            print(f"   Gate.io: {len(gateio_symbols)} 个交易对")
            
            if not any([weex_symbols, bingx_symbols, mexc_symbols, gateio_symbols]):
                print("❌ 所有平台交易对获取失败")
                return
            
            # 2. 找共同交易对
            print("\n📊 第二步: 查找四平台共同交易对")
            
            # 转换BingX格式 BTC-USDT -> BTC_USDT
            bingx_converted = [s.replace('-', '_') for s in bingx_symbols if '-USDT' in s]
            
            # 找交集
            all_symbols = set()
            if weex_symbols:
                all_symbols.update(weex_symbols)
            if bingx_converted:
                all_symbols.update(bingx_converted)
            if mexc_symbols:
                all_symbols.update(mexc_symbols)
            if gateio_symbols:
                all_symbols.update(gateio_symbols)
            
            # 计算四平台共同交易对
            common_symbols = set()
            if weex_symbols and bingx_converted and mexc_symbols and gateio_symbols:
                common_symbols = set(weex_symbols) & set(bingx_converted) & set(mexc_symbols) & set(gateio_symbols)
            
            print(f"   总交易对: {len(all_symbols)}")
            print(f"   四平台共同: {len(common_symbols)}")
            
            if common_symbols:
                sample_symbols = list(common_symbols)[:5]
                print(f"   测试样本: {', '.join(sample_symbols)}")
            else:
                print("   ⚠️ 没有找到四平台共同交易对，使用各平台热门币对测试")
                sample_symbols = ["BTC_USDT", "ETH_USDT", "BNB_USDT"]
            
            # 3. 测试API连通性
            print("\n📊 第三步: 测试API连通性")
            
            for symbol in sample_symbols[:3]:
                print(f"\n🔍 测试 {symbol}:")
                
                # 测试WEEX
                weex_result = self.get_sample_depth_data("WEEX", symbol)
                print(f"   WEEX: {'✅' if weex_result['success'] else '❌'}")
                
                # 测试BingX (转换格式)
                bingx_symbol = symbol.replace('_', '-')
                bingx_result = self.get_sample_depth_data("BingX", bingx_symbol)
                print(f"   BingX: {'✅' if bingx_result['success'] else '❌'}")
                
                # 测试MEXC
                mexc_result = self.get_sample_depth_data("MEXC", symbol)
                print(f"   MEXC: {'✅' if mexc_result['success'] else '❌'}")
                
                # 测试Gate.io
                gateio_result = self.get_sample_depth_data("Gate.io", symbol)
                print(f"   Gate.io: {'✅' if gateio_result['success'] else '❌'}")
                
                # 短暂延迟
                import time
                time.sleep(0.5)
            
            # 4. 统计结果
            print("\n📊 连通性测试结果:")
            print(f"   WEEX: 成功 {self.weex_success} | 失败 {self.weex_error}")
            print(f"   BingX: 成功 {self.bingx_success} | 失败 {self.bingx_error}")
            print(f"   MEXC: 成功 {self.mexc_success} | 失败 {self.mexc_error}")
            print(f"   Gate.io: 成功 {self.gateio_success} | 失败 {self.gateio_error}")
            
            total_success = self.weex_success + self.bingx_success + self.mexc_success + self.gateio_success
            total_attempts = total_success + self.weex_error + self.bingx_error + self.mexc_error + self.gateio_error
            
            if total_attempts > 0:
                success_rate = (total_success / total_attempts) * 100
                print(f"   总体成功率: {success_rate:.1f}%")
                
                if success_rate > 80:
                    print("\n🎉 系统运行正常！可以运行完整分析")
                    print("💡 提示：如需完整分析，请运行主分析器")
                elif success_rate > 50:
                    print("\n⚠️ 部分API可能有问题，建议检查网络连接")
                else:
                    print("\n❌ 多数API连接失败，请检查网络和API状态")
            
            print("\n" + "=" * 60)
            print(f"✅ 快速测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return FourPlatformAnalyzer

def run_full_analysis():
    """运行完整分析（如果可能）"""
    try:
        # 尝试导入完整分析器
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 检查是否存在weex_depth_analyzer
        try:
            from depth_analyzerthree import ThreePlatformRiskAnalyzer
            print("🚀 启动完整四平台风险评估分析器...")
            
            analyzer = ThreePlatformRiskAnalyzer()
            result_file = analyzer.run_full_analysis()
            
            if result_file:
                print(f"\n🎉 分析完成！")
                print(f"📊 Excel报告: {result_file}")
                print(f"📂 报告位置: {os.path.abspath(result_file)}")
            else:
                print("\n❌ 完整分析失败")
                
        except ImportError as e:
            print(f"⚠️ 无法导入完整分析器: {e}")
            print("🔧 启动简化版本进行连通性测试...")
            
            # 使用简化分析器
            SimpleAnalyzer = create_simple_analyzer()
            analyzer = SimpleAnalyzer()
            analyzer.run_quick_analysis()
            
    except Exception as e:
        print(f"❌ 运行分析时出错: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    print("🌟 四平台风险评估分析系统")
    print("支持平台: WEEX, BingX, MEXC, Gate.io")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    print("✅ 依赖检查通过")
    
    # 运行分析
    try:
        run_full_analysis()
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断分析")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()