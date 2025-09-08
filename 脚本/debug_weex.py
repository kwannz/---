#!/usr/bin/env python3
"""
调试WEEX API响应格式
"""

import requests
import json

def debug_weex_contracts():
    """调试WEEX合约API"""
    url = "https://api-contract.weex.com/capi/v2/market/contracts"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print("WEEX Contracts API Response:")
        print(json.dumps(data, indent=2)[:1000] + "..." if len(str(data)) > 1000 else json.dumps(data, indent=2))
        
        if isinstance(data, dict):
            print(f"\nResponse keys: {list(data.keys())}")
            if 'data' in data:
                print(f"Data type: {type(data['data'])}")
                if isinstance(data['data'], list) and len(data['data']) > 0:
                    print(f"First item: {data['data'][0]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def debug_weex_depth():
    """调试WEEX深度API"""
    url = "https://api-contract.weex.com/capi/v2/market/depth"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    params = {'symbol': 'BTCUSDT', 'limit': 5}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print("\nWEEX Depth API Response:")
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(f"❌ Depth Error: {e}")

if __name__ == "__main__":
    debug_weex_contracts()
    debug_weex_depth()