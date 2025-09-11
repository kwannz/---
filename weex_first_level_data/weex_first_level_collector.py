#!/usr/bin/env python3
"""
WEEX 第一档买卖深度数据收集器
专门收集WEEX交易所所有代币的第一档买卖价格和数量数据
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback
import os

class WeexFirstLevelCollector:
    def __init__(self, max_workers: int = 6, request_delay: float = 0.1):
        """初始化WEEX第一档深度数据收集器"""
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
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        # 统计计数器
        self.success_count = 0
        self.error_count = 0
        self.collected_data = []
        
        # 确保输出目录存在
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def log_message(self, message: str):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # 写入日志文件
        with open(f"logs/weex_collection_{self.timestamp}.log", "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def rate_limit_request(self):
        """API频率限制控制"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.request_delay:
                time.sleep(self.request_delay - time_since_last)
            self.last_request_time = time.time()
    
    def get_weex_symbols(self) -> List[str]:
        """获取WEEX所有可交易的合约符号"""
        try:
            self.log_message("🔍 正在获取WEEX交易对列表...")
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
                self.log_message(f"✅ 成功获取 {len(symbols)} 个WEEX交易对")
                return symbols
            return []
        except Exception as e:
            self.log_message(f"❌ 获取WEEX交易对失败: {e}")
            return []
    
    def get_weex_first_level_depth(self, symbol: str) -> Optional[Dict]:
        """获取WEEX第一档深度数据"""
        try:
            self.rate_limit_request()
            
            # 将标准格式转换为WEEX格式
            if '_USDT' in symbol:
                base = symbol.replace('_USDT', '').lower()
                weex_symbol = f"cmt_{base}usdt"
            else:
                weex_symbol = symbol.lower()
            
            # WEEX API不需要limit参数
            params = {'symbol': weex_symbol}
            response = requests.get(self.weex_depth_url, headers=self.weex_headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'asks' in data and 'bids' in data:
                asks = data['asks']
                bids = data['bids']
                
                if asks and bids:
                    # 获取第一档数据
                    first_ask = asks[0]  # [price, quantity]
                    first_bid = bids[0]  # [price, quantity]
                    
                    ask_price = float(first_ask[0])
                    ask_quantity = float(first_ask[1])
                    bid_price = float(first_bid[0])
                    bid_quantity = float(first_bid[1])
                    
                    # 计算第一档总金额
                    ask_amount = ask_price * ask_quantity
                    bid_amount = bid_price * bid_quantity
                    total_amount = ask_amount + bid_amount
                    
                    # 计算买卖比例
                    bid_ask_ratio = bid_amount / ask_amount if ask_amount > 0 else 0
                    
                    result = {
                        'symbol': symbol,
                        'timestamp': data.get('timestamp', int(time.time() * 1000)),
                        'first_ask_price': ask_price,
                        'first_ask_quantity': ask_quantity,
                        'first_ask_amount': ask_amount,
                        'first_bid_price': bid_price,
                        'first_bid_quantity': bid_quantity,
                        'first_bid_amount': bid_amount,
                        'total_first_level_amount': total_amount,
                        'bid_ask_ratio': bid_ask_ratio,
                        'spread': ask_price - bid_price,
                        'spread_percentage': ((ask_price - bid_price) / bid_price * 100) if bid_price > 0 else 0
                    }
                    
                    self.success_count += 1
                    return result
            
            self.error_count += 1
            return None
            
        except Exception as e:
            self.error_count += 1
            self.log_message(f"❌ 获取 {symbol} 深度数据失败: {e}")
            return None
    
    def collect_batch_data(self, symbols: List[str]) -> List[Dict]:
        """批量收集第一档深度数据"""
        self.log_message(f"🚀 开始收集 {len(symbols)} 个交易对的第一档深度数据")
        
        batch_data = []
        batch_size = 50
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(symbols) + batch_size - 1)//batch_size
            
            self.log_message(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch_symbols)} 个交易对)")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.get_weex_first_level_depth, symbol): symbol 
                    for symbol in batch_symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if result:
                            batch_data.append(result)
                            self.collected_data.append(result)
                    except Exception as e:
                        self.log_message(f"❌ 处理 {symbol} 时出错: {e}")
            
            # 批次间延迟
            if i + batch_size < len(symbols):
                time.sleep(0.5)
            
            # 显示进度
            success_rate = (self.success_count / (i + len(batch_symbols))) * 100
            self.log_message(f"📊 当前进度: {self.success_count}/{i + len(batch_symbols)} ({success_rate:.1f}%)")
        
        return batch_data
    
    def save_to_json(self, data: List[Dict]) -> str:
        """保存数据到JSON文件"""
        filename = f"data/weex_first_level_data_{self.timestamp}.json"
        
        try:
            # 创建输出数据结构
            output_data = {
                "collection_info": {
                    "timestamp": self.timestamp,
                    "collection_time": datetime.now().isoformat(),
                    "total_symbols": len(data),
                    "success_count": self.success_count,
                    "error_count": self.error_count,
                    "success_rate": f"{(self.success_count/(self.success_count+self.error_count)*100) if (self.success_count+self.error_count) > 0 else 0:.2f}%"
                },
                "data": data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"✅ JSON文件保存成功: {filename}")
            self.log_message(f"📂 文件位置: {os.path.abspath(filename)}")
            return filename
            
        except Exception as e:
            self.log_message(f"❌ 保存JSON文件失败: {e}")
            return ""
    
    def run_collection(self) -> str:
        """运行完整的数据收集流程"""
        self.log_message("=" * 60)
        self.log_message("🚀 WEEX第一档买卖深度数据收集器启动")
        self.log_message("🎯 专门收集所有代币的第一档买卖价格和数量")
        self.log_message("=" * 60)
        
        # 1. 获取交易对列表
        self.log_message("\n📊 第一步: 获取WEEX交易对列表")
        symbols = self.get_weex_symbols()
        
        if not symbols:
            self.log_message("❌ 无法获取交易对列表，程序退出")
            return ""
        
        # 2. 收集第一档深度数据
        self.log_message(f"\n📊 第二步: 收集 {len(symbols)} 个交易对的第一档深度数据")
        data = self.collect_batch_data(symbols)
        
        # 3. 保存到JSON文件
        self.log_message(f"\n📊 第三步: 保存数据到JSON文件")
        json_file = self.save_to_json(data)
        
        if json_file:
            self.log_message("\n" + "=" * 60)
            self.log_message("🎉 WEEX第一档深度数据收集完成!")
            self.log_message(f"📊 JSON文件: {json_file}")
            self.log_message(f"📈 数据统计:")
            self.log_message(f"   - 成功收集: {self.success_count} 个交易对")
            self.log_message(f"   - 失败: {self.error_count} 个交易对")
            
            if self.success_count + self.error_count > 0:
                success_rate = (self.success_count / (self.success_count + self.error_count)) * 100
                self.log_message(f"   - 成功率: {success_rate:.1f}%")
            
            self.log_message("=" * 60)
        
        return json_file

def main():
    """主函数"""
    print("🌟 WEEX第一档买卖深度数据收集器")
    print("专门收集所有USDT交易对的第一档买卖数据")
    print("=" * 50)
    
    # 进入weex_first_level_data目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    collector = WeexFirstLevelCollector()
    json_file = collector.run_collection()
    
    if json_file:
        print(f"\n🎉 数据收集成功完成！")
        print(f"📋 JSON文件: {json_file}")
        print(f"\n📊 数据包含内容:")
        print(f"   📈 第一档买价和买量")
        print(f"   📈 第一档卖价和卖量") 
        print(f"   📈 第一档买卖金额")
        print(f"   📈 买卖比例")
        print(f"   📈 价差和价差百分比")
        print(f"   📈 收集时间戳")
    else:
        print("\n❌ 数据收集失败")

if __name__ == "__main__":
    main()