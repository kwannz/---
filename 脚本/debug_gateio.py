#!/usr/bin/env python3
"""
Debug Gate.io API response format
"""

import requests
import json

def debug_gateio_depth():
    """Debug Gate.io深度数据格式"""
    url = "https://api.gateio.ws/api/v4/futures/usdt/order_book"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    params = {
        'contract': 'BTC_USDT',
        'limit': 5
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        depth_data = response.json()
        
        print("Gate.io API Response:")
        print(json.dumps(depth_data, indent=2))
        
        if 'asks' in depth_data:
            print(f"\nAsks format: {depth_data['asks'][:2]}")
        if 'bids' in depth_data:
            print(f"Bids format: {depth_data['bids'][:2]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_gateio_depth()