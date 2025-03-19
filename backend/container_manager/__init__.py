#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理系统

管理Docker容器的生命周期、配置和监控
"""

from .manager import ContainerManager

# 导出单例实例
container_manager = ContainerManager()

# 导出公共符号
__all__ = [
    "container_manager",
    "ContainerManager",
]
