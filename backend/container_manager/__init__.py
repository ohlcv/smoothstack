#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理系统

提供Docker容器生命周期管理、日志监控、开发环境配置和多容器服务编排功能
"""

from .manager import ContainerManager
from .dev_environment_manager import DevEnvironmentManager

# 创建单例实例
container_manager = ContainerManager()
dev_environment_manager = DevEnvironmentManager()

# 定义公开的符号
__all__ = ["container_manager", "dev_environment_manager"]
