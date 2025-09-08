#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易所合约铺单量数据收集器启动脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import main

if __name__ == "__main__":
    print("=== 多交易所合约铺单量数据收集器 ===")
    print("支持交易所: Binance, MEXC, Gate.io, OKX, BingX, Bitunix, Blofin")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)
