#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理系统

提供Docker容器生命周期管理、日志监控、开发环境配置和多容器服务编排功能
"""

import logging
import importlib
from typing import Optional, Any

# 配置日志
logger = logging.getLogger("smoothstack.container_manager")

# 首先导出模型，避免循环导入
from .models import ContainerStatus, Container

# 单例实例
_container_manager_instance = None
_dev_environment_manager_instance = None
_consistency_manager_instance = None


def get_container_manager():
    """获取容器管理器单例实例"""
    global _container_manager_instance
    if _container_manager_instance is None:
        try:
            # 惰性导入以避免循环
            from .manager import ContainerManager

            _container_manager_instance = ContainerManager()
        except (ImportError, Exception) as e:
            logger.error(f"无法初始化容器管理器: {e}")
            return None
    return _container_manager_instance


def get_dev_environment_manager():
    """获取开发环境管理器单例实例"""
    global _dev_environment_manager_instance
    if _dev_environment_manager_instance is None:
        try:
            # 惰性导入以避免循环
            from .dev_environment_manager import DevEnvironmentManager

            _dev_environment_manager_instance = DevEnvironmentManager()
        except (ImportError, Exception) as e:
            logger.error(f"无法初始化开发环境管理器: {e}")
            return None
    return _dev_environment_manager_instance


def get_consistency_manager():
    """获取一致性管理器单例实例"""
    global _consistency_manager_instance
    if _consistency_manager_instance is None:
        try:
            # 惰性导入以避免循环
            from .consistency_manager import ConsistencyManager

            _consistency_manager_instance = ConsistencyManager()
        except (ImportError, Exception) as e:
            logger.error(f"无法初始化一致性管理器: {e}")
            return None
    return _consistency_manager_instance


# 定义公开的符号
__all__ = [
    "ContainerStatus",
    "Container",
    "get_container_manager",
    "get_dev_environment_manager",
    "get_consistency_manager",
]
