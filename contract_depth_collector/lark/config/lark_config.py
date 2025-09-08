#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lark机器人配置文件
"""

import os
from typing import Dict, Any


class LarkConfig:
    """Lark机器人配置类"""
    
    def __init__(self):
        """初始化配置"""
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        return {
            # WebSocket服务器配置
            'websocket': {
                'host': os.getenv('LARK_WS_HOST', 'localhost'),
                'port': int(os.getenv('LARK_WS_PORT', '8765')),
                'timeout': int(os.getenv('LARK_WS_TIMEOUT', '30')),
                'max_connections': int(os.getenv('LARK_WS_MAX_CONNECTIONS', '100'))
            },
            
            # 数据收集配置
            'data_collection': {
                'cache_timeout': int(os.getenv('LARK_CACHE_TIMEOUT', '30')),  # 秒
                'max_cache_size': int(os.getenv('LARK_MAX_CACHE_SIZE', '1000')),
                'rate_limit': float(os.getenv('LARK_RATE_LIMIT', '1.0')),  # 秒
                'timeout': int(os.getenv('LARK_TIMEOUT', '30'))
            },
            
            # 交易所配置
            'exchanges': {
                'enabled': [
                    'binance', 'gate', 'okx', 'bingx', 
                    'bybit', 'bitunix', 'weex', 'kucoin'
                ],
                'priority': [
                    'binance', 'bybit', 'okx', 'gate', 
                    'bingx', 'bitunix', 'weex', 'kucoin'
                ]
            },
            
            # 消息配置
            'message': {
                'max_length': int(os.getenv('LARK_MAX_MESSAGE_LENGTH', '4000')),
                'format': 'markdown',
                'include_timestamp': True,
                'include_exchange_details': True
            },
            
            # 日志配置
            'logging': {
                'level': os.getenv('LARK_LOG_LEVEL', 'INFO'),
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': os.getenv('LARK_LOG_FILE', 'lark_bot.log')
            },
            
            # 安全配置
            'security': {
                'allowed_tokens': os.getenv('LARK_ALLOWED_TOKENS', '').split(','),
                'rate_limit_per_user': int(os.getenv('LARK_RATE_LIMIT_PER_USER', '10')),  # 每分钟
                'max_requests_per_minute': int(os.getenv('LARK_MAX_REQUESTS_PER_MINUTE', '100'))
            },
            
            # 性能配置
            'performance': {
                'max_concurrent_requests': int(os.getenv('LARK_MAX_CONCURRENT_REQUESTS', '20')),
                'request_timeout': int(os.getenv('LARK_REQUEST_TIMEOUT', '10')),
                'retry_attempts': int(os.getenv('LARK_RETRY_ATTEMPTS', '3')),
                'retry_delay': float(os.getenv('LARK_RETRY_DELAY', '1.0'))
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_websocket_config(self) -> Dict[str, Any]:
        """获取WebSocket配置"""
        return self.config['websocket']
    
    def get_data_collection_config(self) -> Dict[str, Any]:
        """获取数据收集配置"""
        return self.config['data_collection']
    
    def get_exchanges_config(self) -> Dict[str, Any]:
        """获取交易所配置"""
        return self.config['exchanges']
    
    def get_message_config(self) -> Dict[str, Any]:
        """获取消息配置"""
        return self.config['message']
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config['logging']
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.config['security']
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.config['performance']
    
    def is_token_allowed(self, token: str) -> bool:
        """检查代币是否被允许"""
        allowed_tokens = self.get('security.allowed_tokens', [])
        if not allowed_tokens or not allowed_tokens[0]:  # 空列表或空字符串
            return True  # 如果没有限制，允许所有代币
        return token.upper() in [t.upper() for t in allowed_tokens]
    
    def get_enabled_exchanges(self) -> list:
        """获取启用的交易所列表"""
        return self.get('exchanges.enabled', [])
    
    def get_exchange_priority(self) -> list:
        """获取交易所优先级列表"""
        return self.get('exchanges.priority', [])


# 全局配置实例
config = LarkConfig()
