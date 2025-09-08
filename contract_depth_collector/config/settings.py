#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Settings:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """初始化配置"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "exchanges": {
                "binance": {
                    "enabled": True,
                    "api_key": "",
                    "secret_key": "",
                    "base_url": "https://fapi.binance.com",
                    "ws_url": "wss://fstream.binance.com/ws",
                    "rate_limit": 1200,
                    "timeout": 30
                }
            },
            "data_collection": {
                "default_symbols": ["BTCUSDT", "ETHUSDT"],
                "depth_levels": 20,
                "update_interval": 1.0,
                "max_retries": 3,
                "retry_delay": 5.0
            },
            "logging": {
                "level": "INFO",
                "file": "logs/collector.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }
    
    def get_exchange_config(self, exchange_name: str) -> Dict[str, Any]:
        """获取指定交易所配置"""
        return self.config.get("exchanges", {}).get(exchange_name, {})
    
    def is_exchange_enabled(self, exchange_name: str) -> bool:
        """检查交易所是否启用"""
        return self.get_exchange_config(exchange_name).get("enabled", False)
    
    def get_data_collection_config(self) -> Dict[str, Any]:
        """获取数据收集配置"""
        return self.config.get("data_collection", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config.get("logging", {})
    
    def update_exchange_config(self, exchange_name: str, config: Dict[str, Any]):
        """更新交易所配置"""
        if "exchanges" not in self.config:
            self.config["exchanges"] = {}
        self.config["exchanges"][exchange_name] = config
        self._save_config()
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_api_credentials(self, exchange_name: str) -> Dict[str, str]:
        """获取API凭证"""
        exchange_config = self.get_exchange_config(exchange_name)
        return {
            "api_key": exchange_config.get("api_key", ""),
            "secret_key": exchange_config.get("secret_key", ""),
            "passphrase": exchange_config.get("passphrase", "")
        }
    
    def get_rate_limit(self, exchange_name: str) -> int:
        """获取API速率限制"""
        return self.get_exchange_config(exchange_name).get("rate_limit", 600)
    
    def get_timeout(self, exchange_name: str) -> int:
        """获取请求超时时间"""
        return self.get_exchange_config(exchange_name).get("timeout", 30)
