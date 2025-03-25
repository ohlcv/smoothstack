#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安装器基类

定义依赖安装器的基本接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ..sources.source import Source

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.installers")


class BaseInstaller(ABC):
    """安装器基类"""

    def __init__(self, name: str):
        """
        初始化安装器

        Args:
            name: 安装器名称
        """
        self.name = name
        self.status = "initialized"

    @abstractmethod
    def install(self, package: str, source: Optional[Source] = None, **kwargs) -> bool:
        """
        安装依赖包

        Args:
            package: 包名和版本
            source: 源对象
            **kwargs: 其他参数

        Returns:
            是否安装成功
        """
        pass

    @abstractmethod
    def uninstall(self, package: str, **kwargs) -> bool:
        """
        卸载依赖包

        Args:
            package: 包名
            **kwargs: 其他参数

        Returns:
            是否卸载成功
        """
        pass

    @abstractmethod
    def update(self, package: str, **kwargs) -> bool:
        """
        更新依赖包

        Args:
            package: 包名
            **kwargs: 其他参数

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    def list_packages(self, **kwargs) -> List[Dict[str, str]]:
        """
        列出已安装的依赖包

        Args:
            **kwargs: 其他参数

        Returns:
            已安装的依赖包列表
        """
        pass

    @abstractmethod
    def check_updates(self, source: Optional[Source] = None, **kwargs) -> List[Dict]:
        """
        检查依赖包更新

        Args:
            source: 源对象
            **kwargs: 其他参数

        Returns:
            可更新的依赖包列表
        """
        pass

    @abstractmethod
    def get_latest_version(self, package: str, source=None, **kwargs) -> Optional[str]:
        """
        获取依赖包的最新版本号

        Args:
            package: 包名
            source: 源对象
            **kwargs: 其他参数

        Returns:
            最新版本号
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        获取安装器信息

        Returns:
            安装器信息
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        获取安装器状态

        Returns:
            状态信息
        """
        return {
            "name": self.name,
            "status": self.status,
        }
