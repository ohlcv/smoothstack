"""
容器依赖管理模块

此模块提供了管理Docker容器内依赖的功能，包括：
1. 前端容器依赖管理
2. 后端容器依赖管理
3. Dockerfile模板管理
4. 容器构建与发布
"""

from .base import ContainerDepsManager

__all__ = ["ContainerDepsManager"]
