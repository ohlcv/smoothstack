"""
前端容器依赖管理模块

此模块提供了Docker容器内前端依赖的管理功能
"""

from .package_manager import PackageManager
from .container_env import ContainerEnvironment

__all__ = ["PackageManager", "ContainerEnvironment"]
