#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖管理系统

管理项目依赖，支持多源切换、版本控制和网络优化
"""

from .manager import DependencyManager
from .sources.source import Source, SourceType, SourceStatus
from .sources.manager import SourceManager

# 导出单例实例
dependency_manager = DependencyManager()

# 导出公共符号
__all__ = [
    "dependency_manager",
    "DependencyManager",
    "Source",
    "SourceType",
    "SourceStatus",
    "SourceManager",
]
