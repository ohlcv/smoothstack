#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoothstack 配置管理模块

用于加载、验证和管理应用程序配置和环境变量
"""

from .config_manager import ConfigManager

# 导出 ConfigManager 的单例实例
config = ConfigManager()

# 导出供其他模块使用的符号
__all__ = ["config", "ConfigManager"]
