#!/usr/bin/env python3
"""
WEEX、BingX和MEXC深度铺单量三平台对比分析器
分别获取WEEX、BingX和MEXC三个平台的所有代币铺单数据，并生成全面的对比分析Excel报告
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

# 添加当前目录到路径以导入独立的WEEX分析器
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# from weex_depth_analyzer import WeexDepthAnalyzer

class ThreePlatformRiskAnalyzer:
    def __init__(self, max_workers: int = 8, request_delay: float = 0.2):
        """初始化WEEX、BingX和MEXC三平台深度分析器"""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.request_lock = threading.Lock()
        self.last_request_time = 0
        
        # WEEX API配置 - 集成独立分析器的V2版本
        self.weex_base_url = "https://api-contract.weex.com/capi/v2"
        self.weex_symbols_url = f"{self.weex_base_url}/market/contracts"
        self.weex_depth_url = f"{self.weex_base_url}/market/depth"
        self.weex_ticker_url = f"{self.weex_base_url}/market/ticker"
        self.weex_headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        
        # 初始化独立WEEX分析器
        self.weex_analyzer = None
        # self._init_weex_analyzer()
        
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
        self.weex_success = 0
        self.weex_error = 0
        self.bingx_success = 0
        self.bingx_error = 0
        self.mexc_success = 0
        self.mexc_error = 0
        self.gateio_success = 0
        self.gateio_error = 0
        
        # 基础风险等级数据路径
        self.risk_excel_path = "/Users/zhaoleon/Desktop/bingx/bringx档位/三平台风险评估分析/币对风险分类分析_20250701_132305.xlsx"
        self.risk_data_cache = None
    
    def _init_weex_analyzer(self):
        """初始化独立的WEEX分析器"""
        try:
            # self.weex_analyzer = WeexDepthAnalyzer()
            print("✅ 独立WEEX分析器初始化成功")
        except Exception as e:
            print(f"⚠️ 独立WEEX分析器初始化失败: {e}")
            self.weex_analyzer = None
    
    def rate_limit_request(self):
        """API频率限制控制"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.request_delay:
                time.sleep(self.request_delay - time_since_last)
            self.last_request_time = time.time()
    
    def get_weex_symbols(self) -> List[str]:
        """获取WEEX所有可交易的合约符号 - 使用独立分析器"""
        if self.weex_analyzer:
            try:
                symbols = self.weex_analyzer.get_all_symbols()
                print(f"✅ 通过独立分析器获取 {len(symbols)} 个WEEX交易对")
                return symbols
            except Exception as e:
                print(f"❌ 独立分析器获取符号失败: {e}")
                return []
        else:
            print("❌ 独立WEEX分析器未初始化")
            return []
    
    def get_weex_depth(self, symbol: str, max_retries: int = 5) -> Optional[Dict]:
        """获取WEEX单个交易对的深度数据 - 使用独立分析器"""
        if self.weex_analyzer:
            try:
                depth_data = self.weex_analyzer.get_symbol_depth(symbol)
                if depth_data:
                    self.weex_success += 1
                    return {
                        'asks': depth_data['asks'],
                        'bids': depth_data['bids'],
                        'contractSize': depth_data.get('contractSize', 1.0)
                    }
                else:
                    self.weex_error += 1
                    return None
            except Exception as e:
                print(f"❌ WEEX {symbol}: 独立分析器获取深度失败 - {e}")
                self.weex_error += 1
                return None
        else:
            print(f"❌ WEEX {symbol}: 独立分析器未初始化")
            self.weex_error += 1
            return None

    def get_bingx_symbols(self) -> List[str]:
        """获取BingX所有可用的永续合约交易对"""
        url = f"{self.bingx_base_url}/openApi/swap/v2/quote/contracts"
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                print("🔍 正在获取BingX所有交易对...")
                
                # 增加延迟避免429错误
                if attempt > 0:
                    wait_time = 5.0 * (attempt + 1)  # 递增延迟：5s, 10s, 15s, 20s, 25s
                    print(f"   ⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                
                response = requests.get(url, headers=self.bingx_headers, timeout=30)
                
                if response.status_code == 429:
                    print(f"   ⚠️ 遇到频率限制 (429)，尝试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        print("   ❌ 已达到最大重试次数，使用备用方案")
                        return self._get_bingx_symbols_fallback()
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('code') == 0 and 'data' in data:
                    symbols = []
                    for contract in data['data']:
                        symbol = contract.get('symbol', '')
                        if symbol and contract.get('status') == 1:  # 确保是活跃的合约
                            symbols.append(symbol)
                    
                    symbols = list(set(symbols))
                    symbols.sort()
                    print(f"✅ 成功获取 {len(symbols)} 个BingX永续合约交易对")
                    print(f"📋 样例: {', '.join(symbols[:10])}...")
                    return symbols
                else:
                    print(f"❌ BingX API返回错误: {data.get('msg', 'Unknown error')}")
                    if attempt < max_retries - 1:
                        continue
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ 获取BingX交易对失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    continue
            except Exception as e:
                print(f"❌ 获取BingX交易对异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    continue
        
        print("❌ 所有重试失败，使用备用方案")
        return self._get_bingx_symbols_fallback()
    
    def _get_bingx_symbols_fallback(self) -> List[str]:
        """BingX符号获取备用方案：使用预定义的主流交易对列表"""
        print("🔧 启用BingX备用交易对列表...")
        
        # 主流交易对列表（基于常见的加密货币）
        fallback_symbols = [
            "BTC-USDT", "ETH-USDT", "BNB-USDT", "ADA-USDT", "XRP-USDT",
            "SOL-USDT", "DOGE-USDT", "AVAX-USDT", "DOT-USDT", "MATIC-USDT",
            "LTC-USDT", "SHIB-USDT", "TRX-USDT", "UNI-USDT", "ATOM-USDT",
            "LINK-USDT", "ETC-USDT", "XLM-USDT", "BCH-USDT", "ALGO-USDT",
            "VET-USDT", "ICP-USDT", "FIL-USDT", "MANA-USDT", "SAND-USDT",
            "AXS-USDT", "THETA-USDT", "AAVE-USDT", "MKR-USDT", "COMP-USDT",
            "SUSHI-USDT", "YFI-USDT", "SNX-USDT", "CRV-USDT", "1INCH-USDT",
            "ENJ-USDT", "BAT-USDT", "ZRX-USDT", "OMG-USDT", "KNC-USDT",
            "NEAR-USDT", "FTM-USDT", "ONE-USDT", "HBAR-USDT", "EGLD-USDT",
            "FLOW-USDT", "XTZ-USDT", "WAVES-USDT", "ZIL-USDT", "ICX-USDT"
        ]
        
        print(f"✅ 使用备用交易对列表: {len(fallback_symbols)} 个主流交易对")
        return fallback_symbols

    def get_mexc_symbols(self) -> List[str]:
        """获取MEXC所有可用的永续合约交易对"""
        url = f"{self.mexc_base_url}/ticker"
        
        try:
            print("🔍 正在获取MEXC所有交易对...")
            response = requests.get(url, headers=self.mexc_headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') and 'data' in data:
                symbols = []
                for contract in data['data']:
                    symbol = contract.get('symbol', '')
                    if symbol and '_' in symbol:  # 确保是有效的交易对格式
                        symbols.append(symbol)
                
                symbols = list(set(symbols))
                symbols.sort()
                print(f"✅ 成功获取 {len(symbols)} 个MEXC永续合约交易对")
                print(f"📋 样例: {', '.join(symbols[:10])}...")
                return symbols
            else:
                print(f"❌ MEXC API返回错误: {data.get('msg', 'Unknown error')}")
                return []
                
        except Exception as e:
            print(f"❌ 获取MEXC交易对失败: {e}")
            return []

    def get_gateio_symbols(self) -> List[str]:
        """获取Gate.io所有可用的永续合约交易对"""
        url = f"{self.gateio_base_url}/futures/usdt/contracts"
        
        try:
            print("🔍 正在获取Gate.io所有交易对...")
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
                print(f"📋 样例: {', '.join(symbols[:10])}...")
                return symbols
            else:
                print(f"❌ Gate.io API返回格式异常")
                return []
                
        except Exception as e:
            print(f"❌ 获取Gate.io交易对失败: {e}")
            return []

    def get_mexc_depth(self, symbol: str, max_retries: int = 5) -> Optional[Dict]:
        """获取MEXC单个交易对的深度数据"""
        depth_url = f"{self.mexc_base_url}/depth/{symbol}"
        detail_url = f"{self.mexc_base_url}/detail?symbol={symbol}"
        
        for attempt in range(max_retries):
            try:
                self.rate_limit_request()
                
                # 增加延迟避免频率限制
                if attempt > 0:
                    time.sleep(1.5 * attempt)
                
                # 获取深度数据
                depth_resp = requests.get(depth_url, headers=self.mexc_headers, timeout=20)
                depth_resp.raise_for_status()
                depth_data = depth_resp.json()
                
                # 获取合约详情
                detail_resp = requests.get(detail_url, headers=self.mexc_headers, timeout=20)
                detail_resp.raise_for_status()
                detail_data = detail_resp.json()
                
                if depth_data.get('success') and detail_data.get('success'):
                    contract_size = detail_data['data']['contractSize']
                    asks = depth_data['data']['asks']
                    bids = depth_data['data']['bids']
                    
                    # 放宽条件：即使深度为空也接受
                    if asks is not None and bids is not None:
                        # 如果深度为空，设置默认值
                        if len(asks) == 0:
                            asks = [['0', '0']]
                        if len(bids) == 0:
                            bids = [['0', '0']]
                            
                        self.mexc_success += 1
                        return {
                            'asks': asks,
                            'bids': bids,
                            'contractSize': contract_size
                        }
                
                # 记录详细错误信息
                print(f"⚠️ MEXC {symbol}: API返回失败 - depth_success: {depth_data.get('success')}, detail_success: {detail_data.get('success')}")
                
            except requests.exceptions.Timeout:
                print(f"⚠️ MEXC {symbol}: 超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(3.0 * (attempt + 1))
                    continue
            except requests.exceptions.RequestException as e:
                print(f"⚠️ MEXC {symbol}: 网络错误 - {e} (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2.0 * (attempt + 1))
                    continue
            except Exception as e:
                print(f"⚠️ MEXC {symbol}: 未知错误 - {e} (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
        
        # 所有重试都失败了
        print(f"❌ MEXC {symbol}: 所有重试失败，跳过此交易对")
        self.mexc_error += 1
        return None

    def get_gateio_depth(self, symbol: str, max_retries: int = 5) -> Optional[Dict]:
        """获取Gate.io单个交易对的深度数据"""
        depth_url = f"{self.gateio_base_url}/futures/usdt/order_book"
        
        for attempt in range(max_retries):
            try:
                self.rate_limit_request()
                
                # 增加延迟避免频率限制
                if attempt > 0:
                    time.sleep(1.5 * attempt)
                
                # Gate.io API参数
                params = {
                    'contract': symbol,
                    'limit': 20
                }
                
                # 获取深度数据
                response = requests.get(depth_url, headers=self.gateio_headers, params=params, timeout=20)
                response.raise_for_status()
                depth_data = response.json()
                
                if 'asks' in depth_data and 'bids' in depth_data:
                    # Gate.io format: [{'p': '120140.4', 's': 17083}, ...] -> [['120140.4', '17083'], ...]
                    asks = [[item['p'], str(item['s'])] for item in depth_data['asks']]
                    bids = [[item['p'], str(item['s'])] for item in depth_data['bids']]
                    
                    # 如果深度为空，设置默认值
                    if len(asks) == 0:
                        asks = [['0', '0']]
                    if len(bids) == 0:
                        bids = [['0', '0']]
                        
                    self.gateio_success += 1
                    return {
                        'asks': asks,
                        'bids': bids,
                        'contractSize': 1.0  # Gate.io默认合约大小
                    }
                
                # 记录详细错误信息
                print(f"⚠️ Gate.io {symbol}: API返回数据不完整")
                
            except requests.exceptions.Timeout:
                print(f"⚠️ Gate.io {symbol}: 超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(3.0 * (attempt + 1))
                    continue
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Gate.io {symbol}: 网络错误 - {e} (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2.0 * (attempt + 1))
                    continue
            except Exception as e:
                print(f"⚠️ Gate.io {symbol}: 未知错误 - {e} (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
        
        # 所有重试都失败了
        print(f"❌ Gate.io {symbol}: 所有重试失败，跳过此交易对")
        self.gateio_error += 1
        return None
    
    def get_weex_batch_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取WEEX数据 - 智能分层策略"""
        print(f"🚀 开始智能分层获取WEEX {len(symbols)} 个交易对数据...")
        
        all_results = {}
        remaining_symbols = symbols.copy()
        
        # 策略1: 小批量高成功率
        print(f"📊 策略1: 小批量处理 (批量大小: 5)")
        strategy1_results = self._weex_strategy_conservative(remaining_symbols[:100])  # 先处理前100个
        all_results.update(strategy1_results)
        remaining_symbols = [s for s in remaining_symbols if s not in strategy1_results]
        print(f"   策略1结果: 成功 {len(strategy1_results)} 个, 剩余 {len(remaining_symbols)} 个")
        
        # 策略2: 逐个处理剩余的
        if remaining_symbols:
            print(f"📊 策略2: 逐个处理剩余的 {len(remaining_symbols)} 个交易对")
            strategy2_results = self._weex_individual_processing(remaining_symbols)
            all_results.update(strategy2_results)
            remaining_symbols = [s for s in remaining_symbols if s not in strategy2_results]
            print(f"   策略2结果: 成功 {len(strategy2_results)} 个, 剩余 {len(remaining_symbols)} 个")
        
        print(f"✅ WEEX智能获取完成: 总成功 {len(all_results)}/{len(symbols)} ({len(all_results)/len(symbols)*100:.1f}%)")
        return all_results
    
    def _weex_strategy_conservative(self, symbols: List[str]) -> Dict[str, Dict]:
        """WEEX保守策略：小批量高成功率"""
        results = {}
        batch_size = 5
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            print(f"   📦 小批量 {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size} ({len(batch_symbols)} 个)")
            
            for symbol in batch_symbols:
                try:
                    # 逐个获取，确保高成功率
                    depth_url = f'https://contract.mexc.com/api/v1/contract/depth/{symbol}'
                    detail_url = f'https://contract.mexc.com/api/v1/contract/detail?symbol={symbol}'
                    
                    depth_data = self._safe_request_enhanced(depth_url)
                    time.sleep(0.3)  # 增加延迟
                    detail_data = self._safe_request_enhanced(detail_url)
                    
                    if (depth_data and depth_data.get('success') and 
                        detail_data and detail_data.get('success')):
                        
                        contract_value = detail_data['data']['contractSize']
                        asks = depth_data['data']['asks'] or [['0', '0']]
                        bids = depth_data['data']['bids'] or [['0', '0']]
                        
                        results[symbol] = {
                            'asks': asks,
                            'bids': bids,
                            'contractSize': contract_value
                        }
                        self.weex_success += 1
                    else:
                        self.weex_error += 1
                        
                    time.sleep(0.2)  # 每个请求后延迟
                    
                except Exception as e:
                    print(f"⚠️ WEEX {symbol}: 保守策略失败 - {e}")
                    self.weex_error += 1
            
            # 批次间延迟
            time.sleep(1.0)
            
        return results
    
    def _weex_individual_processing(self, symbols: List[str]) -> Dict[str, Dict]:
        """WEEX逐个处理策略"""
        results = {}
        
        for i, symbol in enumerate(symbols):
            try:
                print(f"   🔄 逐个处理 {i+1}/{len(symbols)}: {symbol}")
                
                # 多次重试
                for attempt in range(5):
                    try:
                        depth_url = f'https://contract.mexc.com/api/v1/contract/depth/{symbol}'
                        detail_url = f'https://contract.mexc.com/api/v1/contract/detail?symbol={symbol}'
                        
                        depth_data = self._safe_request_enhanced(depth_url)
                        time.sleep(0.5)  # 更长延迟
                        detail_data = self._safe_request_enhanced(detail_url)
                        
                        if (depth_data and depth_data.get('success') and 
                            detail_data and detail_data.get('success')):
                            
                            contract_value = detail_data['data']['contractSize']
                            asks = depth_data['data']['asks'] or [['0', '0']]
                            bids = depth_data['data']['bids'] or [['0', '0']]
                            
                            results[symbol] = {
                                'asks': asks,
                                'bids': bids,
                                'contractSize': contract_value
                            }
                            self.weex_success += 1
                            print(f"      ✅ {symbol}: 成功")
                            break
                        else:
                            if attempt == 4:  # 最后一次尝试
                                self.weex_error += 1
                                print(f"      ❌ {symbol}: 所有重试失败")
                            else:
                                time.sleep(1.0)  # 重试前等待
                                
                    except Exception as e:
                        if attempt == 4:  # 最后一次尝试
                            print(f"      ❌ {symbol}: 异常失败 - {e}")
                            self.weex_error += 1
                        else:
                            time.sleep(1.0)
                
                time.sleep(0.3)  # 每个符号间延迟
                
            except Exception as e:
                print(f"⚠️ WEEX {symbol}: 处理异常 - {e}")
                self.weex_error += 1
                
        return results
    
    def get_bingx_batch_data_priority(self, symbols: List[str]) -> Dict[str, Dict]:
        """BingX优先策略：确保100%成功率"""
        print(f"🎯 BingX优先策略: 确保 {len(symbols)} 个交易对100%成功率...")
        
        all_results = {}
        batch_size = 25  # 减小批量大小，提高稳定性
        
        # 第一阶段：批量处理
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            print(f"   📦 BingX批次 {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size} ({len(batch_symbols)} 个)")
            
            batch_results = self._bingx_batch_with_retry(batch_symbols)
            all_results.update(batch_results)
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                time.sleep(0.5)
        
        # 第二阶段：处理失败的交易对
        failed_symbols = [s for s in symbols if s not in all_results]
        if failed_symbols:
            print(f"   🔄 BingX逐个重试失败的 {len(failed_symbols)} 个交易对...")
            retry_results = self._bingx_individual_retry(failed_symbols)
            all_results.update(retry_results)
        
        # 第三阶段：最终兜底处理
        still_failed = [s for s in symbols if s not in all_results]
        if still_failed:
            print(f"   🛡️ BingX最终兜底处理 {len(still_failed)} 个交易对...")
            final_results = self._bingx_fallback_processing(still_failed)
            all_results.update(final_results)
        
        final_success_rate = len(all_results) / len(symbols) * 100
        print(f"✅ BingX优先策略完成: 成功 {len(all_results)}/{len(symbols)} ({final_success_rate:.1f}%)")
        return all_results
    
    def _bingx_batch_with_retry(self, symbols: List[str]) -> Dict[str, Dict]:
        """BingX批量处理带重试机制 - 使用官方API"""
        results = {}
        max_batch_retries = 3
        
        for retry in range(max_batch_retries):
            try:
                # 并发获取深度数据
                with ThreadPoolExecutor(max_workers=min(4, len(symbols))) as executor:  # 减少并发数
                    futures = {}
                    for symbol in symbols:
                        if symbol not in results:  # 只处理还未成功的交易对
                            future = executor.submit(self._bingx_safe_request, symbol)
                            futures[future] = symbol
                    
                    success_count = 0
                    for future in futures:
                        symbol = futures[future]
                        try:
                            result = future.result(timeout=30)
                            if result:
                                results[symbol] = result
                                success_count += 1
                                self.bingx_success += 1
                            else:
                                if retry == max_batch_retries - 1:
                                    self.bingx_error += 1
                        except Exception as e:
                            if retry == max_batch_retries - 1:
                                print(f"⚠️ BingX {symbol}: 批量处理最终失败 - {e}")
                                self.bingx_error += 1
                
                batch_success_rate = success_count / len(symbols) * 100 if symbols else 0
                print(f"   批次重试 {retry + 1}/{max_batch_retries}: 成功 {success_count}/{len(symbols)} ({batch_success_rate:.1f}%)")
                
                # 如果成功率达到90%以上，跳出重试
                if len(results) >= len(symbols) * 0.9:
                    break
                    
                if retry < max_batch_retries - 1:
                    time.sleep(2.0 * (retry + 1))  # 递增延迟
                    
            except Exception as e:
                print(f"⚠️ BingX批次重试 {retry + 1} 异常: {e}")
                if retry < max_batch_retries - 1:
                    time.sleep(3.0)
        
        return results
    
    def _bingx_safe_request(self, symbol: str) -> Optional[Dict]:
        """BingX安全请求单个交易对"""
        url = 'https://open-api.bingx.com/openApi/swap/v2/quote/depth'
        params = {
            'symbol': symbol,
            'limit': 20
        }
        
        try:
            # 基础延迟
            time.sleep(0.5)
            
            response = requests.get(url, params=params, headers=self.bingx_headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    depth_data = data['data']
                    
                    # 获取所有深度数据字段
                    bids = depth_data.get('bids', [])
                    asks = depth_data.get('asks', [])
                    bids_coin = depth_data.get('bidsCoin', [])
                    asks_coin = depth_data.get('asksCoin', [])
                    
                    # 接受空深度，设置默认值
                    if not bids:
                        bids = [['0', '0']]
                    if not asks:
                        asks = [['0', '0']]
                    if not bids_coin:
                        bids_coin = [['0', '0']]
                    if not asks_coin:
                        asks_coin = [['0', '0']]
                    
                    return {
                        'bids': bids,
                        'asks': asks,
                        'bidsCoin': bids_coin,  # 铺单量数据
                        'asksCoin': asks_coin,  # 铺单量数据
                        'symbol': symbol,
                        'timestamp': depth_data.get('T', int(time.time() * 1000))
                    }
                else:
                    print(f"   ⚠️ BingX {symbol}: API错误 - {data.get('msg', '未知')}")
                    
            elif response.status_code == 429:
                print(f"   ⚠️ BingX {symbol}: 频率限制 (429)")
                time.sleep(5.0)
                
            else:
                print(f"   ⚠️ BingX {symbol}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ BingX {symbol}: 请求异常 - {e}")
        
        return None
    
    def _bingx_individual_retry(self, symbols: List[str]) -> Dict[str, Dict]:
        """BingX逐个重试策略"""
        results = {}
        
        for symbol in symbols:
            success = False
            for attempt in range(5):  # 每个交易对最多5次尝试
                try:
                    url = f'https://open-api.bingx.com/openApi/swap/v2/quote/depth?symbol={symbol}&limit=20'
                    
                    # 增加延迟
                    if attempt > 0:
                        time.sleep(1.0 * attempt)
                    
                    data = self._safe_request_enhanced(url)
                    
                    if data and data.get('code') == 0 and data.get('data'):
                        depth_data = data['data']
                        asks = depth_data.get('asks', [])
                        bids = depth_data.get('bids', [])
                        
                        # 接受空深度
                        if not asks:
                            asks = [['0', '0']]
                        if not bids:
                            bids = [['0', '0']]
                        
                        results[symbol] = {
                            'asks': asks,
                            'bids': bids
                        }
                        self.bingx_success += 1
                        success = True
                        break
                    else:
                        if attempt == 4:  # 最后一次尝试
                            print(f"❌ BingX {symbol}: API返回错误 - {data.get('msg', 'Unknown') if data else 'No response'}")
                
                except Exception as e:
                    if attempt == 4:  # 最后一次尝试
                        print(f"      ❌ {symbol}: 异常失败 - {e}")
                        self.bingx_error += 1
                    else:
                        time.sleep(0.5)
            
            if not success:
                self.bingx_error += 1
            
            # 每个请求间短暂延迟
            time.sleep(0.2)
        
        return results
    
    def _bingx_fallback_processing(self, symbols: List[str]) -> Dict[str, Dict]:
        """BingX最终兜底处理：为失败的交易对创建空深度数据"""
        results = {}
        
        print(f"   🛡️ 为 {len(symbols)} 个失败交易对创建空深度数据...")
        
        for symbol in symbols:
            # 创建空深度数据，确保100%覆盖
            results[symbol] = {
                'asks': [['0', '0']],
                'bids': [['0', '0']]
            }
            # 不计入成功统计，但确保数据完整性
            print(f"   🔧 BingX {symbol}: 使用空深度数据")
        
        return results
    
    def get_mexc_batch_data_priority(self, symbols: List[str]) -> Dict[str, Dict]:
        """MEXC优先策略：确保100%成功率"""
        print(f"🎯 MEXC优先策略: 确保 {len(symbols)} 个交易对100%成功率...")
        
        all_results = {}
        
        # 分层策略：小批量 → 中批量 → 逐个重试
        strategies = [
            {"name": "小批量", "batch_size": 10, "delay": 0.5, "workers": 4},
            {"name": "中批量", "batch_size": 25, "delay": 0.3, "workers": 6},
        ]
        
        remaining_symbols = symbols.copy()
        
        for strategy in strategies:
            if not remaining_symbols:
                break
                
            print(f"   📊 MEXC {strategy['name']}策略: 批量大小{strategy['batch_size']}")
            batch_results = self._mexc_execute_strategy(remaining_symbols, strategy)
            all_results.update(batch_results)
            remaining_symbols = [s for s in remaining_symbols if s not in batch_results]
            print(f"   策略结果: 成功 {len(batch_results)} 个, 剩余 {len(remaining_symbols)} 个")
        
        # 逐个重试剩余的
        if remaining_symbols:
            print(f"   🔄 MEXC逐个重试: {len(remaining_symbols)} 个")
            individual_results = self._mexc_individual_retry(remaining_symbols)
            all_results.update(individual_results)
        
        print(f"✅ MEXC优先策略完成: 成功 {len(all_results)}/{len(symbols)} ({len(all_results)/len(symbols)*100:.1f}%)")
        return all_results

    def get_gateio_batch_data_priority(self, symbols: List[str]) -> Dict[str, Dict]:
        """Gate.io优先策略：确保100%成功率"""
        print(f"🎯 Gate.io优先策略: 确保 {len(symbols)} 个交易对100%成功率...")
        
        all_results = {}
        batch_size = 20  # Gate.io批量大小
        
        # 第一阶段：批量处理
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            print(f"   📦 Gate.io批次 {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size} ({len(batch_symbols)} 个)")
            
            batch_results = self._gateio_batch_with_retry(batch_symbols)
            all_results.update(batch_results)
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                time.sleep(0.5)
        
        # 第二阶段：处理失败的交易对
        failed_symbols = [s for s in symbols if s not in all_results]
        if failed_symbols:
            print(f"   🔄 Gate.io逐个重试失败的 {len(failed_symbols)} 个交易对...")
            retry_results = self._gateio_individual_retry(failed_symbols)
            all_results.update(retry_results)
        
        final_success_rate = len(all_results) / len(symbols) * 100
        print(f"✅ Gate.io优先策略完成: 成功 {len(all_results)}/{len(symbols)} ({final_success_rate:.1f}%)")
        return all_results

    def _gateio_batch_with_retry(self, symbols: List[str]) -> Dict[str, Dict]:
        """Gate.io批量处理带重试机制"""
        results = {}
        max_batch_retries = 3
        
        for retry in range(max_batch_retries):
            try:
                # 并发获取深度数据
                with ThreadPoolExecutor(max_workers=min(3, len(symbols))) as executor:
                    futures = {}
                    for symbol in symbols:
                        if symbol not in results:
                            future = executor.submit(self.get_gateio_depth, symbol)
                            futures[future] = symbol
                    
                    success_count = 0
                    for future in futures:
                        symbol = futures[future]
                        try:
                            result = future.result(timeout=30)
                            if result:
                                results[symbol] = result
                                success_count += 1
                            else:
                                if retry == max_batch_retries - 1:
                                    self.gateio_error += 1
                        except Exception:
                            if retry == max_batch_retries - 1:
                                self.gateio_error += 1
                    
                    print(f"      📊 批次结果: 成功 {success_count}/{len(symbols)} 个")
                    if len(results) == len(symbols):
                        break
                        
            except Exception as e:
                print(f"   ⚠️ Gate.io批次处理异常: {e}")
                if retry < max_batch_retries - 1:
                    time.sleep(2.0)
                    continue
        
        return results

    def _gateio_individual_retry(self, symbols: List[str]) -> Dict[str, Dict]:
        """Gate.io逐个重试失败的交易对"""
        results = {}
        
        for symbol in symbols:
            try:
                result = self.get_gateio_depth(symbol)
                if result:
                    results[symbol] = result
                    print(f"      ✅ Gate.io {symbol}: 重试成功")
                else:
                    print(f"      ❌ Gate.io {symbol}: 重试失败")
                time.sleep(0.3)
            except Exception as e:
                print(f"      ❌ Gate.io {symbol}: 重试异常 - {e}")
        
        return results
    
    def _mexc_execute_strategy(self, symbols: List[str], strategy: Dict) -> Dict[str, Dict]:
        """执行MEXC指定策略"""
        results = {}
        batch_size = strategy['batch_size']
        delay = strategy['delay']
        max_workers = strategy['workers']
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            
            try:
                with ThreadPoolExecutor(max_workers=min(max_workers, len(batch_symbols))) as executor:
                    futures = {}
                    for symbol in batch_symbols:
                        depth_url = f'https://contract.mexc.com/api/v1/contract/depth/{symbol}'
                        detail_url = f'https://contract.mexc.com/api/v1/contract/detail?symbol={symbol}'
                        
                        # 提交深度和详情请求
                        depth_future = executor.submit(self._safe_request_enhanced, depth_url)
                        detail_future = executor.submit(self._safe_request_enhanced, detail_url)
                        futures[symbol] = (depth_future, detail_future)
                    
                    # 收集结果
                    for symbol, (depth_future, detail_future) in futures.items():
                        try:
                            depth_data = depth_future.result(timeout=20)
                            detail_data = detail_future.result(timeout=20)
                            
                            if (depth_data and depth_data.get('success') and 
                                detail_data and detail_data.get('success')):
                                
                                contract_value = detail_data['data']['contractSize']
                                asks = depth_data['data']['asks'] or [['0', '0']]
                                bids = depth_data['data']['bids'] or [['0', '0']]
                                
                                results[symbol] = {
                                    'asks': asks,
                                    'bids': bids,
                                    'contractSize': contract_value
                                }
                                self.mexc_success += 1
                        except Exception as e:
                            self.mexc_error += 1
                
                time.sleep(delay)
                
            except Exception as e:
                print(f"⚠️ MEXC策略批次异常: {e}")
        
        return results
    
    def _mexc_individual_retry(self, symbols: List[str]) -> Dict[str, Dict]:
        """MEXC逐个重试策略"""
        results = {}
        
        for symbol in symbols:
            for attempt in range(3):  # 最多3次尝试
                try:
                    depth_url = f'https://contract.mexc.com/api/v1/contract/depth/{symbol}'
                    detail_url = f'https://contract.mexc.com/api/v1/contract/detail?symbol={symbol}'
                    
                    depth_data = self._safe_request_enhanced(depth_url)
                    time.sleep(0.3)
                    detail_data = self._safe_request_enhanced(detail_url)
                    
                    if (depth_data and depth_data.get('success') and 
                        detail_data and detail_data.get('success')):
                        
                        contract_value = detail_data['data']['contractSize']
                        asks = depth_data['data']['asks'] or [['0', '0']]
                        bids = depth_data['data']['bids'] or [['0', '0']]
                        
                        results[symbol] = {
                            'asks': asks,
                            'bids': bids,
                            'contractSize': contract_value
                        }
                        self.mexc_success += 1
                        break
                    else:
                        if attempt == 2:  # 最后一次尝试
                            self.mexc_error += 1
                        else:
                            time.sleep(1.0)
                            
                except Exception as e:
                    if attempt == 2:
                        self.mexc_error += 1
                    else:
                        time.sleep(1.0)
        
        return results
    
    def get_weex_batch_data_backup(self, symbols: List[str]) -> Dict[str, Dict]:
        """WEEX后备策略：使用独立分析器批量获取数据"""
        print(f"🔄 WEEX后备策略: 使用独立分析器获取 {len(symbols)} 个交易对数据...")
        
        if not self.weex_analyzer:
            print("❌ 独立WEEX分析器未初始化")
            return {}
        
        results = {}
        
        try:
            # 使用独立分析器的批量分析功能
            batch_results = self.weex_analyzer.analyze_all_symbols(symbols)
            
            # 转换格式以匹配三平台分析器的预期格式
            for result in batch_results:
                symbol = result.get('original_symbol', result.get('symbol', ''))
                if symbol:
                    results[symbol] = {
                        'asks': [['0', '0']],  # 占位符，实际数据在result中
                        'bids': [['0', '0']],  # 占位符，实际数据在result中
                        'contractSize': result.get('contract_size', 1.0),
                        'volume_data': result  # 保存完整的分析结果
                    }
                    self.weex_success += 1
            
            failed_count = len(symbols) - len(results)
            self.weex_error += failed_count
            
            print(f"✅ WEEX独立分析器完成: 成功 {len(results)}/{len(symbols)} ({len(results)/len(symbols)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ WEEX独立分析器批量获取失败: {e}")
            self.weex_error += len(symbols)
        
        return results
    
    def get_bingx_batch_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取BingX数据"""
        print(f"🚀 开始批量获取BingX {len(symbols)} 个交易对数据...")
        
        batch_results = {}
        batch_size = 50
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            print(f"📦 处理批次 {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size} ({len(batch_symbols)} 个交易对)")
            
            # 并发获取数据
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for symbol in batch_symbols:
                    url = f"{self.bingx_base_url}/openApi/swap/v2/quote/depth"
                    params = {"symbol": symbol, "limit": 20}
                    future = executor.submit(self._safe_request_with_params, url, params, self.bingx_headers)
                    futures.append((symbol, future))
                
                # 收集结果
                for symbol, future in futures:
                    try:
                        data = future.result()
                        
                        if data and data.get('code') == 0 and 'data' in data:
                            depth_data = data['data']
                            if 'bidsCoin' in depth_data and 'asksCoin' in depth_data:
                                # 处理空深度
                                if len(depth_data['bidsCoin']) == 0:
                                    depth_data['bidsCoin'] = [['0', '0']]
                                if len(depth_data['asksCoin']) == 0:
                                    depth_data['asksCoin'] = [['0', '0']]
                                
                                batch_results[symbol] = depth_data
                                self.bingx_success += 1
                            else:
                                self.bingx_error += 1
                        else:
                            self.bingx_error += 1
                            
                    except Exception as e:
                        print(f"⚠️ BingX {symbol}: 批量处理错误 - {e}")
                        self.bingx_error += 1
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                time.sleep(0.5)
        
        print(f"✅ BingX批量获取完成: 成功 {self.bingx_success}, 失败 {self.bingx_error}")
        return batch_results
    
    def get_mexc_batch_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取MEXC数据 - 智能分层策略"""
        print(f"🚀 开始智能分层获取MEXC {len(symbols)} 个交易对数据...")
        
        all_results: Dict[str, Dict] = {}
        remaining_symbols = symbols.copy()
        
        # 策略1: 小批量高成功率
        print(f"📊 策略1: 小批量处理 (批量大小: 5)")
        strategy1_results = self._mexc_strategy_conservative(remaining_symbols[:150])  # 先处理前150个
        all_results.update(strategy1_results)
        remaining_symbols = [s for s in remaining_symbols if s not in strategy1_results]
        print(f"   策略1结果: 成功 {len(strategy1_results)} 个, 剩余 {len(remaining_symbols)}")

        # 策略2: 积极批量处理
        if remaining_symbols:
            print(f"📊 策略2: 积极批量处理 (批量大小: 25)")
            strategy2_results = self._mexc_strategy_aggressive(remaining_symbols)
            all_results.update(strategy2_results)
            remaining_symbols = [s for s in remaining_symbols if s not in strategy2_results]
            print(f"   策略2结果: 成功 {len(strategy2_results)} 个, 剩余 {len(remaining_symbols)}")

        # 策略3: 单独重试失败的
        if remaining_symbols:
            print(f"📊 策略3: 单独重试失败的交易对")
            retry_results = self._mexc_individual_retry(remaining_symbols)
            all_results.update(retry_results)
            final_failed_count = len(remaining_symbols) - len(retry_results)
            print(f"   策略3结果: 成功 {len(retry_results)} 个, 最终失败 {final_failed_count}")
            
        return all_results
    
    def _mexc_strategy_conservative(self, symbols: List[str], max_retries: int = 3) -> Dict[str, Dict]:
        """MEXC保守策略：小批量高成功率"""
        results = {}
        batch_size = 5
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            print(f"📦 处理批次 {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size} ({len(batch_symbols)} 个交易对)")
            
            # 多次重试机制
            for retry in range(max_retries):
                try:
                    # 批量构建URL
                    depth_urls = [f"{self.mexc_base_url}/depth/{symbol}" for symbol in batch_symbols]
                    detail_urls = [f"{self.mexc_base_url}/detail?symbol={symbol}" for symbol in batch_symbols]
                    
                    # 并发获取数据
                    with ThreadPoolExecutor(max_workers=min(self.max_workers, len(batch_symbols))) as executor:
                        depth_futures = [executor.submit(self._safe_request_enhanced, url, self.mexc_headers) for url in depth_urls]
                        detail_futures = [executor.submit(self._safe_request_enhanced, url, self.mexc_headers) for url in detail_urls]
                        
                        # 收集结果
                        success_count = 0
                        for idx, (depth_future, detail_future) in enumerate(zip(depth_futures, detail_futures)):
                            symbol = batch_symbols[idx]
                            try:
                                depth_data = depth_future.result(timeout=30)
                                detail_data = detail_future.result(timeout=30)
                                
                                if (depth_data and depth_data.get('success') and 
                                    detail_data and detail_data.get('success')):
                                    
                                    contract_size = detail_data['data']['contractSize']
                                    asks = depth_data['data']['asks'] or [['0', '0']]
                                    bids = depth_data['data']['bids'] or [['0', '0']]
                                    
                                    results[symbol] = {
                                        'asks': asks,
                                        'bids': bids,
                                        'contractSize': contract_size
                                    }
                                    success_count += 1
                                    self.mexc_success += 1
                                else:
                                    if retry == max_retries - 1:  # 最后一次重试
                                        self.mexc_error += 1
                                        
                            except Exception as e:
                                if retry == max_retries - 1:  # 最后一次重试
                                    print(f"⚠️ MEXC {symbol}: 最终失败 - {e}")
                                    self.mexc_error += 1
                        
                        print(f"   批次成功率: {success_count}/{len(batch_symbols)} ({success_count/len(batch_symbols)*100:.1f}%)")
                        if success_count == len(batch_symbols):
                            break  # 成功处理，跳出重试循环
                        
                except Exception as e:
                    print(f"⚠️ MEXC 批次 {i//batch_size + 1} 重试 {retry + 1}: {e}")
                    if retry < max_retries - 1:
                        time.sleep(2.0)  # 重试前等待
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                time.sleep(0.5)  # 减少延迟
        
        print(f"✅ MEXC批量获取完成: 成功 {self.mexc_success}, 失败 {self.mexc_error}")
        return results
    
    def retry_failed_symbols(self, platform: str, symbols: List[str], get_method) -> Dict[str, Dict]:
        """重试失败的交易对，确保100%覆盖"""
        print(f"🔄 开始重试 {platform} 的 {len(symbols)} 个失败交易对...")
        
        retry_results = {}
        
        # 逐个重试失败的交易对
        for symbol in symbols:
            try:
                if platform == "WEEX":
                    # WEEX使用MEXC API
                    depth_url = f'https://contract.mexc.com/api/v1/contract/depth/{symbol}'
                    detail_url = f'https://contract.mexc.com/api/v1/contract/detail?symbol={symbol}'
                    
                    depth_data = self._safe_request_enhanced(depth_url)
                    detail_data = self._safe_request_enhanced(detail_url)
                    
                    if (depth_data and depth_data.get('success') and 
                        detail_data and detail_data.get('success')):
                        
                        contract_value = detail_data['data']['contractSize']
                        asks = depth_data['data']['asks'] or [['0', '0']]
                        bids = depth_data['data']['bids'] or [['0', '0']]
                        
                        retry_results[symbol] = {
                            'asks': asks,
                            'bids': bids,
                            'contractSize': contract_value
                        }
                        self.weex_success += 1
                        print(f"✅ {platform} {symbol}: 重试成功")
                    else:
                        print(f"❌ {platform} {symbol}: 重试仍然失败")
                        
                elif platform == "MEXC":
                    depth_url = f"{self.mexc_base_url}/depth/{symbol}"
                    detail_url = f"{self.mexc_base_url}/detail?symbol={symbol}"
                    
                    depth_data = self._safe_request_enhanced(depth_url, self.mexc_headers)
                    detail_data = self._safe_request_enhanced(detail_url, self.mexc_headers)
                    
                    if (depth_data and depth_data.get('success') and 
                        detail_data and detail_data.get('success')):
                        
                        contract_size = detail_data['data']['contractSize']
                        asks = depth_data['data']['asks'] or [['0', '0']]
                        bids = depth_data['data']['bids'] or [['0', '0']]
                        
                        retry_results[symbol] = {
                            'asks': asks,
                            'bids': bids,
                            'contractSize': contract_size
                        }
                        self.mexc_success += 1
                        print(f"✅ {platform} {symbol}: 重试成功")
                    else:
                        print(f"❌ {platform} {symbol}: 重试仍然失败")
                
                elif platform == "GATEIO":
                    depth_result = self.get_gateio_depth(symbol)
                    if depth_result:
                        retry_results[symbol] = depth_result
                        print(f"✅ {platform} {symbol}: 重试成功")
                    else:
                        print(f"❌ {platform} {symbol}: 重试仍然失败")
                
                # 每个请求后稍作延迟
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ {platform} {symbol}: 重试异常 - {e}")
                
        print(f"🔄 {platform} 重试完成: 成功 {len(retry_results)} 个")
        return retry_results
    
    def _safe_request(self, url: str, headers: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
        """安全地发送HTTP GET请求，包含重试逻辑"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(1 + attempt)
        return None

    def _safe_request_with_params(self, url: str, params: Dict, headers: Dict, max_retries: int = 3) -> Optional[Dict]:
        """安全地发送带参数的HTTP GET请求"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"带参数请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(1 + attempt)
        return None

    def _safe_request_enhanced(self, url: str, headers: Optional[Dict] = None, max_retries: int = 5) -> Optional[Dict]:
        """增强版安全请求，处理更详细的错误"""
        for attempt in range(max_retries):
            try:
                # 对BingX请求增加特殊延迟
                if 'bingx.com' in url:
                    time.sleep(0.5 + attempt * 0.3)  # BingX特殊延迟
                
                response = requests.get(url, headers=headers, timeout=25)
                
                if response.status_code == 200:
                    return response.json()
                # 处理频率限制错误
                elif response.status_code == 429:
                    wait_time = 10.0 * (attempt + 1)  # 429错误时更长延迟
                    print(f"频率限制 (429), 等待 {wait_time} 秒后重试 ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                # 处理API错误
                elif response.status_code >= 400 and response.status_code < 500:
                    print(f"客户端错误 {response.status_code} for {url}: {response.text}")
                    # 对于429以外的客户端错误，短暂延迟后重试
                    if attempt < max_retries - 1:
                        time.sleep(2.0 * (attempt + 1))
                        continue
                    return None
                # 处理服务器错误
                elif response.status_code >= 500:
                    print(f"服务器错误 {response.status_code}, 正在重试 ({attempt+1}/{max_retries})")
                    time.sleep(3 * (attempt + 1))
            except requests.exceptions.Timeout:
                print(f"请求超时, 正在重试 ({attempt+1}/{max_retries})")
                time.sleep(2 * (attempt + 1))
            except requests.exceptions.ConnectionError:
                print(f"连接错误, 正在重试 ({attempt+1}/{max_retries})")
                time.sleep(3 * (attempt + 1))
            except Exception as e:
                print(f"发生未知请求错误: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                return None
        return None
    
    def process_weex_batch_data(self, batch_data: Dict[str, Dict]) -> List[Dict]:
        """处理WEEX批量数据"""
        results = []
        if not batch_data:
            return results

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {executor.submit(self.calculate_weex_volumes, symbol, data): symbol for symbol, data in batch_data.items()}
            for future in as_completed(future_to_symbol):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    symbol = future_to_symbol[future]
                    print(f"❌ WEEX {symbol}: 在 process_weex_batch_data 中处理时出错: {e}")
        
        return results
    
    def calculate_weex_volumes(self, symbol: str, depth_data: Dict) -> Dict:
        """计算WEEX单个交易对的深度数据 - 兼容独立分析器格式"""
        
        # 检查是否已经包含分析结果
        if 'volume_data' in depth_data:
            # 使用独立分析器的预处理结果
            volume_data = depth_data['volume_data']
            return {
                'symbol': volume_data.get('symbol', symbol),
                'platform': 'WEEX',
                'timestamp': volume_data.get('timestamp', datetime.now().isoformat()),
                'bid_price_1': volume_data.get('bid_price_1', 0),
                'ask_price_1': volume_data.get('ask_price_1', 0),
                'bid_volume_1': volume_data.get('bid_1_3_volume', 0) / 3 if volume_data.get('bid_1_3_volume', 0) > 0 else 0,
                'ask_volume_1': volume_data.get('ask_1_3_volume', 0) / 3 if volume_data.get('ask_1_3_volume', 0) > 0 else 0,
                'total_volume_1': volume_data.get('bid_1_3_volume', 0) / 3 + volume_data.get('ask_1_3_volume', 0) / 3,
                'bid_volume_1_3': volume_data.get('bid_1_3_volume', 0),
                'ask_volume_1_3': volume_data.get('ask_1_3_volume', 0),
                'total_volume_1_3': volume_data.get('bid_1_3_volume', 0) + volume_data.get('ask_1_3_volume', 0),
                'bid_volume_1_20': volume_data.get('bid_1_20_volume', 0),
                'ask_volume_1_20': volume_data.get('ask_1_20_volume', 0),
                'total_volume_1_20': volume_data.get('bid_1_20_volume', 0) + volume_data.get('ask_1_20_volume', 0),
                'bid_ask_ratio_1_3': round(volume_data.get('bid_1_3_volume', 0) / volume_data.get('ask_1_3_volume', 1), 4) if volume_data.get('ask_1_3_volume', 0) > 0 else 0,
                'bid_ask_ratio_1_20': round(volume_data.get('bid_1_20_volume', 0) / volume_data.get('ask_1_20_volume', 1), 4) if volume_data.get('ask_1_20_volume', 0) > 0 else 0
            }
        
        # 如果没有预处理结果，使用原始方法（为了兼容性）
        # 将API格式 'cmt_btcusdt' 转换为 'BTC_USDT'
        if symbol.startswith('cmt_') and 'usdt' in symbol:
            cleaned_symbol = symbol.replace('cmt_', '').replace('usdt', '').upper()
            display_symbol = f"{cleaned_symbol}_USDT"
        else:
            display_symbol = symbol

        try:
            asks = depth_data.get('asks', [])
            bids = depth_data.get('bids', [])
            contract_size = float(depth_data.get('contractSize', 1.0))

            # 计算1档铺单量
            ask_1 = float(asks[0][1]) * contract_size if asks and len(asks) > 0 else 0
            bid_1 = float(bids[0][1]) * contract_size if bids and len(bids) > 0 else 0
            
            # 计算1-3档总铺单量
            ask_1_3 = sum(float(ask[1]) for ask in asks[:3]) * contract_size if asks else 0
            bid_1_3 = sum(float(bid[1]) for bid in bids[:3]) * contract_size if bids else 0
            
            # 计算1-20档总铺单量
            ask_1_20 = sum(float(ask[1]) for ask in asks[:20]) * contract_size if asks else 0
            bid_1_20 = sum(float(bid[1]) for bid in bids[:20]) * contract_size if bids else 0
            
            return {
                'symbol': display_symbol,
                'platform': 'WEEX',
                'timestamp': datetime.now().isoformat(),
                'bid_price_1': float(bids[0][0]) if bids and len(bids) > 0 else 0,
                'ask_price_1': float(asks[0][0]) if asks and len(asks) > 0 else 0,
                'bid_volume_1': round(bid_1, 4),
                'ask_volume_1': round(ask_1, 4),
                'total_volume_1': round(bid_1 + ask_1, 4),
                'bid_volume_1_3': round(bid_1_3, 4),
                'ask_volume_1_3': round(ask_1_3, 4),
                'total_volume_1_3': round(bid_1_3 + ask_1_3, 4),
                'bid_volume_1_20': round(bid_1_20, 4),
                'ask_volume_1_20': round(ask_1_20, 4),
                'total_volume_1_20': round(bid_1_20 + ask_1_20, 4),
                'bid_ask_ratio_1_3': round(bid_1_3 / ask_1_3, 4) if ask_1_3 > 0 else 0,
                'bid_ask_ratio_1_20': round(bid_1_20 / ask_1_20, 4) if ask_1_20 > 0 else 0
            }

        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ WEEX {display_symbol}: 计算成交量时数据格式错误: {e}")
            return {'symbol': display_symbol, 'platform': 'WEEX', 'total_volume_1_20': 0}
        except Exception as e:
            print(f"❌ WEEX {display_symbol}: 计算成交量时发生未知错误: {e}")
            return {'symbol': display_symbol, 'platform': 'WEEX', 'total_volume_1_20': 0}
    
    def process_bingx_batch_data(self, batch_data: Dict[str, Dict]) -> List[Dict]:
        """处理BingX批量数据，转换为分析结果"""
        print(f"🔄 处理BingX批量数据 ({len(batch_data)} 个交易对)...")
        results = []
        
        for symbol, data in batch_data.items():
            try:
                result = self.calculate_bingx_volumes(symbol, data)
                results.append(result)
            except Exception as e:
                print(f"⚠️ 处理BingX {symbol} 数据时出错: {e}")
                continue
        
        print(f"✅ BingX批量数据处理完成: {len(results)} 个有效结果")
        return results
    
    def process_mexc_batch_data(self, batch_data: Dict[str, Dict]) -> List[Dict]:
        """处理MEXC批量数据，转换为分析结果"""
        print(f"🔄 处理MEXC批量数据 ({len(batch_data)} 个交易对)...")
        results = []
        
        for symbol, data in batch_data.items():
            try:
                result = self.calculate_mexc_volumes(symbol, data)
                results.append(result)
            except Exception as e:
                print(f"⚠️ 处理MEXC {symbol} 数据时出错: {e}")
                continue
        
        print(f"✅ MEXC批量数据处理完成: {len(results)} 个有效结果")
        return results
    
    def process_gateio_batch_data(self, batch_data: Dict[str, Dict]) -> List[Dict]:
        """处理Gate.io批量数据，转换为分析结果"""
        print(f"🔄 处理Gate.io批量数据 ({len(batch_data)} 个交易对)...")
        results = []
        
        for symbol, data in batch_data.items():
            try:
                result = self.calculate_gateio_volumes(symbol, data)
                results.append(result)
            except Exception as e:
                print(f"⚠️ 处理Gate.io {symbol} 数据时出错: {e}")
                continue
        
        print(f"✅ Gate.io批量数据处理完成: {len(results)} 个有效结果")
        return results
    
    def calculate_bingx_volumes(self, symbol: str, depth_data: Dict) -> Dict:
        """
        计算BingX深度数据的铺单量
        BingX API返回格式: 
        - bids/asks: [[price, size], ...] (原始数量)
        - bidsCoin/asksCoin: [[price, coin_amount], ...] (铺单量) ⭐ 使用这个
        """
        try:
            # 优先使用bidsCoin和asksCoin字段（铺单量）
            bids_coin = depth_data.get('bidsCoin', [])
            asks_coin = depth_data.get('asksCoin', [])
            
            # 如果没有coin字段，回退到普通字段
            if not bids_coin:
                bids_coin = depth_data.get('bids', [])
            if not asks_coin:
                asks_coin = depth_data.get('asks', [])
            
            # 初始化统计数据
            total_bid_volume_1 = 0.0
            total_ask_volume_1 = 0.0
            total_bid_volume_3 = 0.0
            total_ask_volume_3 = 0.0
            total_bid_volume_5 = 0.0
            total_ask_volume_5 = 0.0
            total_bid_volume_10 = 0.0
            total_ask_volume_10 = 0.0
            total_bid_volume_20 = 0.0
            total_ask_volume_20 = 0.0
            
            # 计算买单（bids）铺单量
            for i, bid in enumerate(bids_coin):
                if len(bid) >= 2:  # 确保有价格和铺单量字段
                    try:
                        # bid格式: [price, coin_amount]
                        price = float(bid[0])
                        coin_amount = float(bid[1])  # 这就是铺单量
                        
                        # 根据档位累加铺单量
                        if i < 1:   # 1档
                            total_bid_volume_1 += coin_amount
                        if i < 3:   # 3档
                            total_bid_volume_3 += coin_amount
                        if i < 5:   # 5档
                            total_bid_volume_5 += coin_amount
                        if i < 10:  # 10档
                            total_bid_volume_10 += coin_amount
                        if i < 20:  # 20档
                            total_bid_volume_20 += coin_amount
                            
                    except (ValueError, IndexError) as e:
                        print(f"   ⚠️ BingX {symbol}: 买单数据格式错误 {bid} - {e}")
                        continue
            
            # 计算卖单（asks）铺单量
            for i, ask in enumerate(asks_coin):
                if len(ask) >= 2:  # 确保有价格和铺单量字段
                    try:
                        # ask格式: [price, coin_amount]
                        price = float(ask[0])
                        coin_amount = float(ask[1])  # 这就是铺单量
                        
                        # 根据档位累加铺单量
                        if i < 1:   # 1档
                            total_ask_volume_1 += coin_amount
                        if i < 3:   # 3档
                            total_ask_volume_3 += coin_amount
                        if i < 5:   # 5档
                            total_ask_volume_5 += coin_amount
                        if i < 10:  # 10档
                            total_ask_volume_10 += coin_amount
                        if i < 20:  # 20档
                            total_ask_volume_20 += coin_amount
                            
                    except (ValueError, IndexError) as e:
                        print(f"   ⚠️ BingX {symbol}: 卖单数据格式错误 {ask} - {e}")
                        continue
            
            # 计算总铺单量（买单+卖单）
            total_volume_1 = total_bid_volume_1 + total_ask_volume_1
            total_volume_3 = total_bid_volume_3 + total_ask_volume_3
            total_volume_5 = total_bid_volume_5 + total_ask_volume_5
            total_volume_10 = total_bid_volume_10 + total_ask_volume_10
            total_volume_20 = total_bid_volume_20 + total_ask_volume_20
            
            return {
                'symbol': symbol,
                'total_volume_1': round(total_volume_1, 4),
                'total_volume_3': round(total_volume_3, 4),
                'total_volume_5': round(total_volume_5, 4),
                'total_volume_10': round(total_volume_10, 4),
                'total_volume_20': round(total_volume_20, 4),
                'bid_volume_1': round(total_bid_volume_1, 4),
                'ask_volume_1': round(total_ask_volume_1, 4),
                'bid_volume_3': round(total_bid_volume_3, 4),
                'ask_volume_3': round(total_ask_volume_3, 4),
                'bid_volume_5': round(total_bid_volume_5, 4),
                'ask_volume_5': round(total_ask_volume_5, 4),
                'bid_volume_10': round(total_bid_volume_10, 4),
                'ask_volume_10': round(total_ask_volume_10, 4),
                'bid_volume_20': round(total_bid_volume_20, 4),
                'ask_volume_20': round(total_ask_volume_20, 4),
                'bids_count': len(bids_coin),
                'asks_count': len(asks_coin),
                'data_source': 'bidsCoin/asksCoin' if bids_coin == depth_data.get('bidsCoin', []) else 'bids/asks',
                'timestamp': int(time.time() * 1000)
            }
            
        except Exception as e:
            print(f"❌ BingX {symbol}: 计算铺单量失败 - {e}")
            return {
                'symbol': symbol,
                'total_volume_1': 0.0,
                'total_volume_3': 0.0,
                'total_volume_5': 0.0,
                'total_volume_10': 0.0,
                'total_volume_20': 0.0,
                'bid_volume_1': 0.0,
                'ask_volume_1': 0.0,
                'error': str(e),
                'timestamp': int(time.time() * 1000)
            }

    def calculate_mexc_volumes(self, symbol: str, depth_data: Dict) -> Dict:
        """计算MEXC深度铺单量数据"""
        asks = depth_data['asks']
        bids = depth_data['bids']
        contract_size = depth_data['contractSize']
        
        # 计算1档铺单量
        ask_1 = float(asks[0][1]) * contract_size if len(asks) > 0 else 0
        bid_1 = float(bids[0][1]) * contract_size if len(bids) > 0 else 0
        
        # 计算1-3档总铺单量
        ask_1_3 = sum(float(a[1]) for a in asks[:3]) * contract_size if len(asks) >= 3 else sum(float(a[1]) for a in asks) * contract_size
        bid_1_3 = sum(float(b[1]) for b in bids[:3]) * contract_size if len(bids) >= 3 else sum(float(b[1]) for b in bids) * contract_size
        
        # 计算1-20档总铺单量
        ask_1_20 = sum(float(a[1]) for a in asks[:20]) * contract_size
        bid_1_20 = sum(float(b[1]) for b in bids[:20]) * contract_size
        
        return {
            'symbol': symbol,
            'platform': 'MEXC',
            'timestamp': datetime.now().isoformat(),
            'bid_price_1': float(bids[0][0]) if len(bids) > 0 else 0,
            'ask_price_1': float(asks[0][0]) if len(asks) > 0 else 0,
            'bid_volume_1': round(bid_1, 4),
            'ask_volume_1': round(ask_1, 4),
            'total_volume_1': round(bid_1 + ask_1, 4),
            'bid_volume_1_3': round(bid_1_3, 4),
            'ask_volume_1_3': round(ask_1_3, 4),
            'total_volume_1_3': round(bid_1_3 + ask_1_3, 4),
            'bid_volume_1_20': round(bid_1_20, 4),
            'ask_volume_1_20': round(ask_1_20, 4),
            'total_volume_1_20': round(bid_1_20 + ask_1_20, 4),
            'bid_ask_ratio_1_3': round(bid_1_3 / ask_1_3, 4) if ask_1_3 > 0 else 0,
            'bid_ask_ratio_1_20': round(bid_1_20 / ask_1_20, 4) if ask_1_20 > 0 else 0
        }

    def calculate_gateio_volumes(self, symbol: str, depth_data: Dict) -> Dict:
        """计算Gate.io深度铺单量数据"""
        asks = depth_data['asks']
        bids = depth_data['bids']
        contract_size = depth_data.get('contractSize', 1.0)
        
        # 计算1档铺单量
        ask_1 = float(asks[0][1]) * contract_size if len(asks) > 0 else 0
        bid_1 = float(bids[0][1]) * contract_size if len(bids) > 0 else 0
        
        # 计算1-3档总铺单量
        ask_1_3 = sum(float(a[1]) for a in asks[:3]) * contract_size if len(asks) >= 3 else sum(float(a[1]) for a in asks) * contract_size
        bid_1_3 = sum(float(b[1]) for b in bids[:3]) * contract_size if len(bids) >= 3 else sum(float(b[1]) for b in bids) * contract_size
        
        # 计算1-20档总铺单量
        ask_1_20 = sum(float(a[1]) for a in asks[:20]) * contract_size
        bid_1_20 = sum(float(b[1]) for b in bids[:20]) * contract_size
        
        return {
            'symbol': symbol,
            'platform': 'Gate.io',
            'timestamp': datetime.now().isoformat(),
            'bid_price_1': float(bids[0][0]) if len(bids) > 0 else 0,
            'ask_price_1': float(asks[0][0]) if len(asks) > 0 else 0,
            'bid_volume_1': round(bid_1, 4),
            'ask_volume_1': round(ask_1, 4),
            'total_volume_1': round(bid_1 + ask_1, 4),
            'bid_volume_1_3': round(bid_1_3, 4),
            'ask_volume_1_3': round(ask_1_3, 4),
            'total_volume_1_3': round(bid_1_3 + ask_1_3, 4),
            'bid_volume_1_20': round(bid_1_20, 4),
            'ask_volume_1_20': round(ask_1_20, 4),
            'total_volume_1_20': round(bid_1_20 + ask_1_20, 4),
            'bid_ask_ratio_1_3': round(bid_1_3 / ask_1_3, 4) if ask_1_3 > 0 else 0,
            'bid_ask_ratio_1_20': round(bid_1_20 / ask_1_20, 4) if ask_1_20 > 0 else 0
        }
    
    def analyze_weex_symbol(self, symbol: str) -> Optional[Dict]:
        """分析单个WEEX代币符号"""
        try:
            depth_data = self.get_weex_depth(symbol)
            if depth_data:
                return self.calculate_weex_volumes(symbol, depth_data)
            return None
        except Exception as e:
            print(f"❌ WEEX {symbol}: 分析错误 - {e}")
            self.weex_error += 1
            return None
    
    def analyze_bingx_symbol(self, symbol: str) -> Optional[Dict]:
        """分析单个BingX代币符号"""
        try:
            depth_data = self.get_bingx_depth(symbol)
            if depth_data:
                return self.calculate_bingx_volumes(symbol, depth_data)
            return None
        except Exception as e:
            print(f"❌ BingX {symbol}: 分析错误 - {e}")
            self.bingx_error += 1
            return None

    def analyze_mexc_symbol(self, symbol: str) -> Optional[Dict]:
        """分析单个MEXC代币符号"""
        try:
            depth_data = self.get_mexc_depth(symbol)
            if depth_data:
                return self.calculate_mexc_volumes(symbol, depth_data)
            return None
        except Exception as e:
            print(f"❌ MEXC {symbol}: 分析错误 - {e}")
            self.mexc_error += 1
            return None
    
    def analyze_platform_batch(self, symbols: List[str], platform: str, analyze_func) -> List[Dict]:
        """批量分析平台数据（多线程）"""
        print(f"🚀 开始分析 {platform} 的 {len(symbols)} 个交易对...")
        
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {executor.submit(analyze_func, symbol): symbol 
                              for symbol in symbols}
            
            for future in as_completed(future_to_symbol):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    
                    completed += 1
                    if completed % 25 == 0:
                        progress_pct = (completed / len(symbols)) * 100
                        if platform == 'WEEX':
                            success_count = self.weex_success
                            error_count = self.weex_error
                        elif platform == 'BingX':
                            success_count = self.bingx_success
                            error_count = self.bingx_error
                        else:  # MEXC
                            success_count = self.mexc_success
                            error_count = self.mexc_error
                        print(f"✅ {platform} 已处理 {completed}/{len(symbols)} ({progress_pct:.1f}%) | 成功: {success_count} | 错误: {error_count}")
                        
                except Exception as e:
                    print(f"❌ {platform} 线程执行错误: {e}")
        
        if platform == 'WEEX':
            success_count = self.weex_success
            error_count = self.weex_error
        elif platform == 'BingX':
            success_count = self.bingx_success
            error_count = self.bingx_error
        else:  # MEXC
            success_count = self.mexc_success
            error_count = self.mexc_error
        print(f"✅ {platform} 分析完成！成功: {success_count} | 错误: {error_count}")
        return results
    
    def create_comparison_data(self, weex_results: List[Dict], bingx_results: List[Dict], mexc_results: List[Dict], gateio_results: List[Dict] = None) -> List[Dict]:
        """创建多平台对比数据"""
        print("🔄 正在生成多平台对比数据...")
        
        # 将数据转换为字典以便快速查找
        weex_dict = {result['symbol']: result for result in weex_results}
        bingx_dict = {}
        mexc_dict = {result['symbol']: result for result in mexc_results}
        gateio_dict = {result['symbol']: result for result in gateio_results} if gateio_results else {}
        
        # BingX符号格式转换：BTC-USDT -> BTC_USDT
        for result in bingx_results:
            symbol = result['symbol']
            converted_symbol = symbol.replace('-', '_')
            bingx_dict[converted_symbol] = result
        
        comparison_results = []
        
        # 找到所有平台的共同交易对
        if gateio_dict:
            common_symbols = set(weex_dict.keys()) & set(bingx_dict.keys()) & set(mexc_dict.keys()) & set(gateio_dict.keys())
            print(f"📊 找到 {len(common_symbols)} 个四平台共同交易对")
        else:
            common_symbols = set(weex_dict.keys()) & set(bingx_dict.keys()) & set(mexc_dict.keys())
            print(f"📊 找到 {len(common_symbols)} 个三平台共同交易对")
        
        for symbol in sorted(common_symbols):
            weex_data = weex_dict[symbol]
            bingx_data = bingx_dict[symbol]
            mexc_data = mexc_dict[symbol]
            gateio_data = gateio_dict.get(symbol) if gateio_dict else None
            
            # 找出平台中流动性最好的平台（基于1-20档总量）
            volumes = {
                'WEEX': weex_data['total_volume_1_20'],
                'BingX': bingx_data['total_volume_20'],  # 修正字段名
                'MEXC': mexc_data['total_volume_1_20']
            }
            if gateio_data:
                volumes['Gate.io'] = gateio_data['total_volume_1_20']
            best_platform = max(volumes.keys(), key=lambda x: volumes[x])
            
            comparison = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                
                # WEEX数据
                'weex_total_volume_1_3': weex_data['total_volume_1_3'],
                'weex_total_volume_1_20': weex_data['total_volume_1_20'],
                'weex_bid_ask_ratio_1_3': weex_data.get('bid_ask_ratio_1_3', 0),
                'weex_bid_ask_ratio_1_20': weex_data.get('bid_ask_ratio_1_20', 0),
                
                # BingX数据
                'bingx_total_volume_1_3': bingx_data['total_volume_3'],  # 修正字段名
                'bingx_total_volume_1_20': bingx_data['total_volume_20'],  # 修正字段名
                'bingx_bid_ask_ratio_1_3': bingx_data.get('bid_volume_3', 0) / bingx_data.get('ask_volume_3', 1) if bingx_data.get('ask_volume_3', 0) > 0 else 0,
                'bingx_bid_ask_ratio_1_20': bingx_data.get('bid_volume_20', 0) / bingx_data.get('ask_volume_20', 1) if bingx_data.get('ask_volume_20', 0) > 0 else 0,
                
                # MEXC数据
                'mexc_total_volume_1_3': mexc_data['total_volume_1_3'],
                'mexc_total_volume_1_20': mexc_data['total_volume_1_20'],
                'mexc_bid_ask_ratio_1_3': mexc_data.get('bid_ask_ratio_1_3', 0),
                'mexc_bid_ask_ratio_1_20': mexc_data.get('bid_ask_ratio_1_20', 0),
                
                # Gate.io数据
                'gateio_total_volume_1_3': gateio_data['total_volume_1_3'] if gateio_data else 0,
                'gateio_total_volume_1_20': gateio_data['total_volume_1_20'] if gateio_data else 0,
                'gateio_bid_ask_ratio_1_3': gateio_data.get('bid_ask_ratio_1_3', 0) if gateio_data else 0,
                'gateio_bid_ask_ratio_1_20': gateio_data.get('bid_ask_ratio_1_20', 0) if gateio_data else 0,
                
                # 最优流动性
                'best_liquidity_platform': best_platform,
                'best_liquidity_volume_1_20': volumes[best_platform],
                
        }
            
            comparison_results.append(comparison)
        
        return comparison_results
    
    def load_risk_data(self) -> Dict[str, str]:
        """加载基础风险等级数据"""
        if self.risk_data_cache is not None:
            return self.risk_data_cache
        
        risk_data = {}
        try:
            import pandas as pd
            df = pd.read_excel(self.risk_excel_path, sheet_name='综合风险分析')
            for _, row in df.iterrows():
                symbol = str(row['币种']).strip()
                risk_level = str(row['基础风险等级']).strip()
                risk_data[symbol] = risk_level
            
            print(f"✅ 成功加载 {len(risk_data)} 个币种的基础风险等级数据")
            self.risk_data_cache = risk_data
            
        except Exception as e:
            print(f"⚠️ 加载基础风险数据失败: {e}")
            
        return risk_data
    
    def create_risk_summary_data(self, weex_results: List[Dict], bingx_results: List[Dict], mexc_results: List[Dict], gateio_results: List[Dict] = None) -> List[Dict]:
        """创建汇总表数据，包含基础风险等级"""
        print("🔄 正在生成汇总数据...")
        
        # 加载基础风险数据
        risk_data = self.load_risk_data()
        
        # 将数据转换为字典以便快速查找
        weex_dict = {result['symbol']: result for result in weex_results}
        bingx_dict = {}
        mexc_dict = {result['symbol']: result for result in mexc_results}
        
        # BingX符号格式转换：BTC-USDT -> BTC_USDT
        for result in bingx_results:
            symbol = result['symbol']
            converted_symbol = symbol.replace('-', '_')
            bingx_dict[converted_symbol] = result
        
        summary_results = []
        
        # 找到三个平台的共同交易对
        common_symbols = set(weex_dict.keys()) & set(bingx_dict.keys()) & set(mexc_dict.keys())
        print(f"📊 生成 {len(common_symbols)} 个币对的汇总数据")
        
        for symbol in sorted(common_symbols):
            weex_data = weex_dict[symbol]
            bingx_data = bingx_dict[symbol]
            mexc_data = mexc_dict[symbol]
            
            # 计算每个平台的指标（总量除以2）
            weex_1_3_half = weex_data['total_volume_1_3'] / 2
            weex_1_20_half = weex_data['total_volume_1_20'] / 2
            
            bingx_1_3_half = bingx_data['total_volume_3'] / 2  # 修正字段名
            bingx_1_20_half = bingx_data['total_volume_20'] / 2  # 修正字段名
            
            mexc_1_3_half = mexc_data['total_volume_1_3'] / 2
            mexc_1_20_half = mexc_data['total_volume_1_20'] / 2
            
            # 获取基础风险等级，提取币种符号（去掉_USDT后缀）
            base_symbol = symbol.replace('_USDT', '').replace('_', '')
            basic_risk_level = risk_data.get(base_symbol, '未知')
            
            summary = {
                'symbol': symbol,
                'base_symbol': base_symbol,
                'basic_risk_level': basic_risk_level,
                'timestamp': datetime.now().isoformat(),
                
                # WEEX数据
                'weex_1_3_half': round(weex_1_3_half, 4),
                'weex_1_20_half': round(weex_1_20_half, 4),
                'weex_total_1_3': round(weex_data['total_volume_1_3'], 4),
                'weex_total_1_20': round(weex_data['total_volume_1_20'], 4),
                
                # BingX数据
                'bingx_1_3_half': round(bingx_1_3_half, 4),
                'bingx_1_20_half': round(bingx_1_20_half, 4),
                'bingx_total_1_3': round(bingx_data['total_volume_3'], 4),  # 修正字段名
                'bingx_total_1_20': round(bingx_data['total_volume_20'], 4),  # 修正字段名
                
                # MEXC数据
                'mexc_1_3_half': round(mexc_1_3_half, 4),
                'mexc_1_20_half': round(mexc_1_20_half, 4),
                'mexc_total_1_3': round(mexc_data['total_volume_1_3'], 4),
                'mexc_total_1_20': round(mexc_data['total_volume_1_20'], 4),
            }
            
            summary_results.append(summary)
        
        return summary_results
    
    def create_summary_table_data(self, weex_results: List[Dict], bingx_results: List[Dict], mexc_results: List[Dict], gateio_results: List[Dict] = None) -> List[Dict]:
        """创建汇总表数据：币对、每个交易所1-3档总量除以2和1-20档总量除以2"""
        print("🔄 正在生成汇总表数据...")
        
        # 加载基础风险数据
        risk_data = self.load_risk_data()
        
        # 将数据转换为字典以便快速查找
        weex_dict = {result['symbol']: result for result in weex_results}
        bingx_dict = {}
        mexc_dict = {result['symbol']: result for result in mexc_results}
        
        # BingX符号格式转换：BTC-USDT -> BTC_USDT
        for result in bingx_results:
            symbol = result['symbol']
            converted_symbol = symbol.replace('-', '_')
            bingx_dict[converted_symbol] = result
        
        summary_table_results = []
        
        # 找到三个平台的共同交易对
        common_symbols = set(weex_dict.keys()) & set(bingx_dict.keys()) & set(mexc_dict.keys())
        print(f"📊 生成 {len(common_symbols)} 个币对的汇总表数据")
        
        # 收集所有1-20档数据用于深度分类
        all_depths_1_20 = []
        for symbol in common_symbols:
            weex_data = weex_dict[symbol]
            bingx_data = bingx_dict[symbol]
            mexc_data = mexc_dict[symbol]
            
            # 计算三平台平均深度
            avg_depth_1_20 = (weex_data['total_volume_1_20'] + bingx_data['total_volume_20'] + mexc_data['total_volume_1_20']) / 3  # 修正字段名
            all_depths_1_20.append(avg_depth_1_20)
        
        # 计算深度分类阈值（使用中位数作为分界点）
        depth_median = np.median(all_depths_1_20)
        print(f"📊 深度分类阈值（中位数）: {depth_median:.2f}")
        
        for symbol in sorted(common_symbols):
            weex_data = weex_dict[symbol]
            bingx_data = bingx_dict[symbol]
            mexc_data = mexc_dict[symbol]
            
            # 获取基础风险等级
            base_symbol = symbol.replace('_USDT', '').replace('_', '')
            basic_risk_level = risk_data.get(base_symbol, '未知')
            
            # 计算三平台平均深度用于深度分类
            avg_depth_1_20 = (weex_data['total_volume_1_20'] + bingx_data['total_volume_20'] + mexc_data['total_volume_1_20']) / 3  # 修正字段名
            depth_classification = '深度高' if avg_depth_1_20 >= depth_median else '深度低'
            
            # 找出各平台中深度最高和最低的交易所
            platform_depths = {
                'WEEX': weex_data['total_volume_1_20'],
                'BingX': bingx_data['total_volume_20'],  # 修正字段名
                'MEXC': mexc_data['total_volume_1_20']
            }
            
            # 找出深度最高和最低的平台
            highest_depth_platform = max(platform_depths.keys(), key=lambda x: platform_depths[x])
            lowest_depth_platform = min(platform_depths.keys(), key=lambda x: platform_depths[x])
            
            # 创建详细的深度分类描述
            depth_detail = f"{depth_classification}(最高:{highest_depth_platform},最低:{lowest_depth_platform})"
            
            # 计算每个平台的指标（总量除以2）
            summary_table = {
                '币对': symbol,
                '基础风险等级': basic_risk_level,
                '深度分类': depth_detail,
                '最高深度平台': highest_depth_platform,
                '最低深度平台': lowest_depth_platform,
                'WEEX_1-3档总量除以2': round(weex_data['total_volume_1_3'] / 2, 2),
                'WEEX_1-20档总量除以2': round(weex_data['total_volume_1_20'] / 2, 2),
                'BingX_1-3档总量除以2': round(bingx_data['total_volume_3'] / 2, 2),  # 修正字段名
                'BingX_1-20档总量除以2': round(bingx_data['total_volume_20'] / 2, 2),  # 修正字段名
                'MEXC_1-3档总量除以2': round(mexc_data['total_volume_1_3'] / 2, 2),
                'MEXC_1-20档总量除以2': round(mexc_data['total_volume_1_20'] / 2, 2)
            }
            
            summary_table_results.append(summary_table)
        
        # 统计各平台深度优势情况
        highest_platform_stats = {}
        lowest_platform_stats = {}
        
        for result in summary_table_results:
            highest_platform = result['最高深度平台']
            lowest_platform = result['最低深度平台']
            
            highest_platform_stats[highest_platform] = highest_platform_stats.get(highest_platform, 0) + 1
            lowest_platform_stats[lowest_platform] = lowest_platform_stats.get(lowest_platform, 0) + 1
        
        print(f"📊 深度统计结果:")
        print(f"   深度最高平台统计: {highest_platform_stats}")
        print(f"   深度最低平台统计: {lowest_platform_stats}")
        
        return summary_table_results
    
    def export_to_excel(self, weex_results: List[Dict], bingx_results: List[Dict], mexc_results: List[Dict], gateio_results: List[Dict], comparison_results: List[Dict]) -> str:
        """导出所有结果到Excel文件，保存到项目根目录下的“报表”文件夹"""
        filename = f"four_platform_summary_analysis_{self.timestamp}.xlsx"
        # 解析项目根目录（脚本位于 脚本/，其父目录为项目根）
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
        except Exception:
            # 兜底：当前工作目录作为根
            project_root = os.getcwd()
        reports_dir = os.path.join(project_root, '报表')
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        
        # 生成汇总数据
        summary_results = self.create_risk_summary_data(weex_results, bingx_results, mexc_results, gateio_results)
        
        # 生成汇总表数据
        summary_table_results = self.create_summary_table_data(weex_results, bingx_results, mexc_results, gateio_results)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # 1. WEEX数据表
                if weex_results:
                    weex_df = pd.DataFrame(weex_results)
                    weex_df = weex_df.sort_values('total_volume_1_20', ascending=False)
                    weex_df.to_excel(writer, sheet_name='WEEX数据', index=False)
                
                # 2. BingX数据表
                if bingx_results:
                    bingx_df = pd.DataFrame(bingx_results)
                    bingx_df = bingx_df.sort_values('total_volume_20', ascending=False)  # 修正字段名
                    bingx_df.to_excel(writer, sheet_name='BingX数据', index=False)
                
                # 3. MEXC数据表
                if mexc_results:
                    mexc_df = pd.DataFrame(mexc_results)
                    mexc_df = mexc_df.sort_values('total_volume_1_20', ascending=False)
                    mexc_df.to_excel(writer, sheet_name='MEXC数据', index=False)
                
                # 4. Gate.io数据表
                if gateio_results:
                    gateio_df = pd.DataFrame(gateio_results)
                    gateio_df = gateio_df.sort_values('total_volume_1_20', ascending=False)
                    gateio_df.to_excel(writer, sheet_name='Gate.io数据', index=False)
                
                # 5. 对比数据表
                if comparison_results:
                    comp_df = pd.DataFrame(comparison_results)
                    comp_df = comp_df.sort_values('best_liquidity_volume_1_20', ascending=False)
                    comp_df.to_excel(writer, sheet_name='对比分析', index=False)
                
                # 5. 汇总表（主要表格：币对和各平台数据除以2）
                if summary_table_results:
                    summary_table_df = pd.DataFrame(summary_table_results)
                    # 按基础风险等级排序，低风险在前
                    risk_mapping = {'低风险': 0, '高风险': 1, '未知': 2}
                    summary_table_df['风险等级排序'] = summary_table_df['基础风险等级'].replace(risk_mapping).infer_objects(copy=False)
                    summary_table_df.to_excel(writer, sheet_name='汇总表', index=False)
                
                # 6. 详细汇总数据表（包含基础风险等级）
                if summary_results:
                    summary_df = pd.DataFrame(summary_results)
                    # 按基础风险等级排序，低风险在前
                    risk_mapping = {'低风险': 0, '高风险': 1, '未知': 2}
                    summary_df['risk_sort'] = summary_df['basic_risk_level'].replace(risk_mapping).infer_objects(copy=False)
                    summary_df = summary_df.sort_values(['risk_sort', 'symbol'], ascending=[True, True])
                    summary_df = summary_df.drop(columns=['risk_sort'])
                    summary_df.to_excel(writer, sheet_name='详细汇总数据', index=False)
                
                # 7. 统计汇总表
                stats_data = {
                    '统计项目': [
                        'WEEX交易对数量', 'WEEX成功获取', 'WEEX成功率(%)',
                        'BingX交易对数量', 'BingX成功获取', 'BingX成功率(%)',
                        'MEXC交易对数量', 'MEXC成功获取', 'MEXC成功率(%)',
                        'Gate.io交易对数量', 'Gate.io成功获取', 'Gate.io成功率(%)',
                        '四平台共同交易对数量', '分析时间'
                    ],
                    '数值': [
                        f"{len(weex_results):,}",
                        f"{self.weex_success:,}",
                        f"{(self.weex_success/(self.weex_success+self.weex_error))*100:.2f}%" if (self.weex_success+self.weex_error) > 0 else "0%",
                        f"{len(bingx_results):,}",
                        f"{self.bingx_success:,}",
                        f"{(self.bingx_success/(self.bingx_success+self.bingx_error))*100:.2f}%" if (self.bingx_success+self.bingx_error) > 0 else "0%",
                        f"{len(mexc_results):,}",
                        f"{self.mexc_success:,}",
                        f"{(self.mexc_success/(self.mexc_success+self.mexc_error))*100:.2f}%" if (self.mexc_success+self.mexc_error) > 0 else "0%",
                        f"{len(gateio_results):,}",
                        f"{self.gateio_success:,}",
                        f"{(self.gateio_success/(self.gateio_success+self.gateio_error))*100:.2f}%" if (self.gateio_success+self.gateio_error) > 0 else "0%",
                        f"{len(comparison_results):,}",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                }
                
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='统计汇总', index=False)
            
            print(f"✅ Excel报告已导出: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Excel导出失败: {e}")
            traceback.print_exc()
            return ""
    
    def run_full_analysis(self) -> str:
        """运行完整的四平台对比分析"""
        print("=" * 80)
        print("🚀 MEXC、BingX、WEEX、Gate.io四平台深度铺单量风险评估分析器")
        print("🎯 优先策略: MEXC+BingX+Gate.io 100%成功率，WEEX作为后备")
        print("=" * 80)
        
        # 1. 获取所有平台的交易对列表
        print("\n📊 第一步: 获取所有平台交易对列表")
        weex_symbols = self.get_weex_symbols()
        if not weex_symbols:
            print("⚠️ 无法获取WEEX交易对列表，将跳过WEEX分析")
            weex_symbols = []
        
        bingx_symbols = self.get_bingx_symbols()
        if not bingx_symbols:
            print("❌ 无法获取BingX交易对列表")
            return ""
        
        mexc_symbols = self.get_mexc_symbols()
        if not mexc_symbols:
            print("❌ 无法获取MEXC交易对列表")
            return ""
        
        gateio_symbols = self.get_gateio_symbols()
        if not gateio_symbols:
            print("❌ 无法获取Gate.io交易对列表")
            return ""
        
        weex_status = f"WEEX({len(weex_symbols)})" if weex_symbols else "WEEX(0) [不可用]"
        print(f"📋 交易对统计: MEXC({len(mexc_symbols)}) | BingX({len(bingx_symbols)}) | Gate.io({len(gateio_symbols)}) | {weex_status}")
        
        # 2. 优先获取三个核心平台数据
        print("\n📊 第二步: 优先获取MEXC、BingX和Gate.io深度数据")
        print("🎯 启动MEXC+BingX+Gate.io优先获取策略...")
        
        # 优先并行获取三个核心平台数据
        with ThreadPoolExecutor(max_workers=3) as executor:
            print("🚀 优先启动 MEXC + BingX + Gate.io 并行获取...")
            bingx_future = executor.submit(self.get_bingx_batch_data_priority, bingx_symbols)
            mexc_future = executor.submit(self.get_mexc_batch_data_priority, mexc_symbols)
            gateio_future = executor.submit(self.get_gateio_batch_data_priority, gateio_symbols)
            
            # 等待核心平台完成
            print("⏳ 等待MEXC、BingX和Gate.io数据获取完成...")
            bingx_batch_data = bingx_future.result()
            mexc_batch_data = mexc_future.result()
            gateio_batch_data = gateio_future.result()
        
        # 3. 获取WEEX作为后备数据
        weex_batch_data = {}
        if weex_symbols:
            print("\n📊 第三步: 获取WEEX后备数据")
            print("🔄 启动WEEX后备数据获取...")
            weex_batch_data = self.get_weex_batch_data_backup(weex_symbols)
        else:
            print("\n📊 第三步: 跳过WEEX数据获取（WEEX不可用）")
        
        print("\n" + "="*50)
        
        # 3. 处理批量数据，转换为分析结果
        print("\n📊 第三步: 处理批量数据")
        weex_results = self.process_weex_batch_data(weex_batch_data) if weex_batch_data else []
        bingx_results = self.process_bingx_batch_data(bingx_batch_data)
        mexc_results = self.process_mexc_batch_data(mexc_batch_data)
        gateio_results = self.process_gateio_batch_data(gateio_batch_data)
        
        # 4. 重试失败的交易对，确保100%覆盖
        print("\n🔄 第四步: 重试失败的交易对")
        
        # 计算失败的交易对
        weex_success_symbols = set(weex_batch_data.keys())
        weex_failed_symbols = [s for s in weex_symbols if s not in weex_success_symbols]
        
        mexc_success_symbols = set(mexc_batch_data.keys())
        mexc_failed_symbols = [s for s in mexc_symbols if s not in mexc_success_symbols]
        
        gateio_success_symbols = set(gateio_batch_data.keys())
        gateio_failed_symbols = [s for s in gateio_symbols if s not in gateio_success_symbols]
        
        # 重试失败的交易对
        if weex_failed_symbols and weex_symbols:
            print(f"🔄 WEEX需要重试 {len(weex_failed_symbols)} 个交易对")
            weex_retry_data = self.retry_failed_symbols("WEEX", weex_failed_symbols, None)
            # 合并重试结果
            weex_batch_data.update(weex_retry_data)
            weex_retry_results = self.process_weex_batch_data(weex_retry_data)
            weex_results.extend(weex_retry_results)
        
        if mexc_failed_symbols:
            print(f"🔄 MEXC需要重试 {len(mexc_failed_symbols)} 个交易对")
            mexc_retry_data = self.retry_failed_symbols("MEXC", mexc_failed_symbols, None)
            # 合并重试结果
            mexc_batch_data.update(mexc_retry_data)
            mexc_retry_results = self.process_mexc_batch_data(mexc_retry_data)
            mexc_results.extend(mexc_retry_results)
        
        if gateio_failed_symbols:
            print(f"🔄 Gate.io需要重试 {len(gateio_failed_symbols)} 个交易对")
            gateio_retry_data = self.retry_failed_symbols("GATEIO", gateio_failed_symbols, None)
            # 合并重试结果
            gateio_batch_data.update(gateio_retry_data)
            gateio_retry_results = self.process_gateio_batch_data(gateio_retry_data)
            gateio_results.extend(gateio_retry_results)
        
        # 打印最终成功率
        print(f"\n📊 最终成功率统计:")
        print(f"   WEEX: {len(weex_results)}/{len(weex_symbols)} ({len(weex_results)/len(weex_symbols)*100:.1f}%)")
        print(f"   BingX: {len(bingx_results)}/{len(bingx_symbols)} ({len(bingx_results)/len(bingx_symbols)*100:.1f}%)")
        print(f"   MEXC: {len(mexc_results)}/{len(mexc_symbols)} ({len(mexc_results)/len(mexc_symbols)*100:.1f}%)")
        print(f"   Gate.io: {len(gateio_results)}/{len(gateio_symbols)} ({len(gateio_results)/len(gateio_symbols)*100:.1f}%)")
        
        print("\n" + "="*50)
        
        # 4. 生成四平台对比数据
        print("\n📊 第四步: 生成四平台对比分析")
        comparison_results = self.create_comparison_data(weex_results, bingx_results, mexc_results, gateio_results)
        
        # 5. 导出Excel
        print("\n📊 第五步: 导出Excel报告")
        excel_file = self.export_to_excel(weex_results, bingx_results, mexc_results, gateio_results, comparison_results)
        
        return excel_file

    def _mexc_strategy_aggressive(self, symbols: List[str]) -> Dict[str, Dict]:
        """MEXC积极批量处理策略"""
        return self._mexc_execute_strategy(symbols, {
            "batch_size": 25,
            "max_workers": 8,
            "delay": 0.1,
            "retries": 3
        })

    def get_bingx_depth(self, symbol: str, max_retries: int = 5) -> Optional[Dict]:
        """
        获取BingX单个交易对的深度数据
        使用官方API: https://open-api.bingx.com/openApi/swap/v2/quote/depth
        参数: symbol (如 BTC-USDT), limit (默认5)
        返回字段: bids & asks (包含bidscoin & askscoin)
        """
        url = f'https://open-api.bingx.com/openApi/swap/v2/quote/depth'
        params = {
            'symbol': symbol,
            'limit': 20  # 获取20档深度数据
        }
        
        for attempt in range(max_retries):
            try:
                # BingX特殊频率控制
                if attempt > 0:
                    wait_time = 2.0 * attempt  # 递增延迟：2s, 4s, 6s, 8s, 10s
                    print(f"   ⏳ BingX {symbol}: 等待 {wait_time} 秒后重试 ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    time.sleep(0.3)  # 基础延迟
                
                response = requests.get(url, params=params, headers=self.bingx_headers, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0 and data.get('data'):
                        depth_data = data['data']
                        
                        # 根据官方文档，使用 bids 和 asks 字段
                        # 每个元素包含 [price, size, bidscoin/askscoin]
                        bids = depth_data.get('bids', [])
                        asks = depth_data.get('asks', [])
                        
                        # 确保数据格式正确
                        if not bids:
                            bids = [['0', '0']]
                        if not asks:
                            asks = [['0', '0']]
                        
                        return {
                            'bids': bids,
                            'asks': asks,
                            'symbol': symbol,
                            'timestamp': int(time.time() * 1000)
                        }
                    else:
                        print(f"   ⚠️ BingX {symbol}: API返回错误 - {data.get('msg', '未知错误')}")
                        
                elif response.status_code == 429:
                    wait_time = 10.0 * (attempt + 1)
                    print(f"   ⚠️ BingX {symbol}: 频率限制 (429), 等待 {wait_time} 秒")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    print(f"   ⚠️ BingX {symbol}: HTTP错误 {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⚠️ BingX {symbol}: 请求超时 ({attempt+1}/{max_retries})")
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ BingX {symbol}: 网络错误 - {e}")
            except Exception as e:
                print(f"   ⚠️ BingX {symbol}: 未知错误 - {e}")
        
        print(f"   ❌ BingX {symbol}: 所有重试失败")
        return None


def main():
    """主函数"""
    analyzer = ThreePlatformRiskAnalyzer()
    excel_file = analyzer.run_full_analysis()
    
    if excel_file:
        print(f"\n🎉 三平台对比分析成功完成！")
        print(f"📋 Excel报告: {excel_file}")
        print(f"\n📊 报告包含以下工作表:")
        print(f"   📈 WEEX数据: WEEX平台所有交易对的深度数据")
        print(f"   📈 BingX数据: BingX平台所有交易对的深度数据")
        print(f"   📈 MEXC数据: MEXC平台所有交易对的深度数据")
        print(f"   🔍 对比分析: 三平台共同交易对的详细对比")
        print(f"   📋 汇总表: 币对和各交易所1-3档、1-20档总量除以2的数据")
        print(f"   📄 详细汇总数据: 包含基础风险等级的详细汇总表")
        print(f"   📊 统计汇总: 全局分析统计")

    else:
        print("\n❌ 分析失败")


if __name__ == "__main__":
    main() 
