#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人工具函数
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging


class TokenValidator:
    """代币验证器"""
    
    # 常见的代币符号模式
    TOKEN_PATTERNS = [
        r'^[A-Z]{2,10}$',  # 2-10个大写字母
        r'^[A-Z]{2,10}[0-9]{1,3}$',  # 字母+数字
    ]
    
    # 常见的代币名称
    COMMON_TOKENS = [
        'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'DOGE', 'AVAX', 'MATIC',
        'LINK', 'UNI', 'LTC', 'BCH', 'ATOM', 'FTM', 'NEAR', 'ALGO', 'VET', 'ICP',
        'RIF', 'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'GUSD'
    ]
    
    @classmethod
    def is_valid_token(cls, token: str) -> bool:
        """验证代币符号是否有效"""
        if not token or not isinstance(token, str):
            return False
        
        token = token.upper().strip()
        
        # 检查长度
        if len(token) < 2 or len(token) > 15:
            return False
        
        # 检查模式
        for pattern in cls.TOKEN_PATTERNS:
            if re.match(pattern, token):
                return True
        
        # 检查是否在常见代币列表中
        return token in cls.COMMON_TOKENS
    
    @classmethod
    def normalize_token(cls, token: str) -> str:
        """标准化代币符号"""
        if not token:
            return ''
        
        # 转换为大写并去除空格
        token = token.upper().strip()
        
        # 去除特殊字符
        token = re.sub(r'[^A-Z0-9]', '', token)
        
        return token


class MessageFormatter:
    """消息格式化器"""
    
    @staticmethod
    def format_price(price: float, decimals: int = 6) -> str:
        """格式化价格"""
        if price == 0:
            return "0.000000"
        return f"{price:.{decimals}f}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 6) -> str:
        """格式化百分比"""
        if value == 0:
            return "0.000000%"
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def format_volume(volume: float, decimals: int = 6) -> str:
        """格式化交易量"""
        if volume == 0:
            return "0.000000"
        
        if volume >= 1_000_000:
            return f"{volume/1_000_000:.{decimals-6}f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.{decimals-3}f}K"
        else:
            return f"{volume:.{decimals}f}"
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """格式化时间戳"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return str(timestamp)
        except:
            return str(timestamp)
    
    @staticmethod
    def truncate_message(message: str, max_length: int = 4000) -> str:
        """截断消息"""
        if len(message) <= max_length:
            return message
        
        # 保留前80%和后20%的内容
        keep_length = int(max_length * 0.8)
        return message[:keep_length] + "\n\n... (消息过长，已截断) ...\n\n" + message[-keep_length:]


class DataProcessor:
    """数据处理器"""
    
    @staticmethod
    def calculate_rankings(data: Dict[str, Any], metric: str) -> Dict[str, int]:
        """计算排名"""
        if not data:
            return {}
        
        # 提取指标值
        values = {}
        for exchange, exchange_data in data.items():
            if isinstance(exchange_data, dict) and metric in exchange_data:
                values[exchange] = exchange_data[metric]
        
        # 排序并分配排名
        sorted_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
        rankings = {}
        
        for rank, (exchange, value) in enumerate(sorted_items, 1):
            rankings[exchange] = rank
        
        return rankings
    
    @staticmethod
    def find_best_exchange(data: Dict[str, Any], metric: str, reverse: bool = False) -> Optional[str]:
        """找到最佳交易所"""
        if not data:
            return None
        
        best_exchange = None
        best_value = None
        
        for exchange, exchange_data in data.items():
            if isinstance(exchange_data, dict) and metric in exchange_data:
                value = exchange_data[metric]
                
                if best_value is None:
                    best_value = value
                    best_exchange = exchange
                elif reverse:
                    if value < best_value:
                        best_value = value
                        best_exchange = exchange
                else:
                    if value > best_value:
                        best_value = value
                        best_exchange = exchange
        
        return best_exchange
    
    @staticmethod
    def calculate_statistics(data: List[float]) -> Dict[str, float]:
        """计算统计信息"""
        if not data:
            return {}
        
        data = [x for x in data if x is not None and x != 0]
        
        if not data:
            return {}
        
        return {
            'mean': sum(data) / len(data),
            'min': min(data),
            'max': max(data),
            'count': len(data)
        }


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int, time_window: int):
        """初始化速率限制器"""
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def is_allowed(self) -> bool:
        """检查是否允许请求"""
        now = time.time()
        
        # 清理过期的请求记录
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # 检查是否超过限制
        if len(self.requests) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests.append(now)
        return True
    
    def get_wait_time(self) -> float:
        """获取需要等待的时间"""
        if not self.requests:
            return 0
        
        now = time.time()
        oldest_request = min(self.requests)
        wait_time = self.time_window - (now - oldest_request)
        
        return max(0, wait_time)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, max_size: int = 1000, timeout: int = 30):
        """初始化缓存管理器"""
        self.max_size = max_size
        self.timeout = timeout
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None
        
        # 检查是否过期
        if time.time() - self.timestamps[key] > self.timeout:
            self.delete(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # 删除最旧的条目
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.delete(oldest_key)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """删除缓存值"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """设置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def validate_config(config: Dict[str, Any]) -> bool:
    """验证配置"""
    required_keys = [
        'websocket.host',
        'websocket.port',
        'data_collection.cache_timeout',
        'exchanges.enabled'
    ]
    
    for key in required_keys:
        keys = key.split('.')
        value = config
        
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return False
            value = value[k]
    
    return True
