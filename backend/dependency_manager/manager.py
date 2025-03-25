#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖管理器

提供依赖管理的核心功能，包括安装、卸载、更新和监控
"""

import logging
import os
from typing import Dict, List, Optional, Union, Any

from backend.config import config
from .sources.manager import SourceManager
from .installers.base import BaseInstaller
from .cache.manager import CacheManager

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager")


class DependencyManager:
    """依赖管理器"""

    def __init__(self):
        """初始化依赖管理器"""
        logger.info("Initializing dependency manager")

        # 初始化配置
        self._init_config()

        # 初始化组件
        self.source_manager = SourceManager()
        self.cache_manager = CacheManager()
        self.installers: Dict[str, BaseInstaller] = {}

        # 加载已注册的安装器
        self._load_installers()

        logger.info("Dependency manager initialized")

    def _init_config(self):
        """初始化配置"""
        # 确保配置存在
        if "dependency_manager" not in config:
            config["dependency_manager"] = {
                "default_source_group": "global",
                "use_cache": True,
                "cache_dir": os.path.join(
                    os.path.expanduser("~"), ".smoothstack", "cache", "dependencies"
                ),
                "timeout": 30,
                "retries": 3,
                "network": {
                    "concurrent_downloads": 3,
                    "chunk_size": 1024 * 1024,  # 1MB
                    "proxy": None,
                },
            }

        # 创建缓存目录
        cache_dir = config.get("dependency_manager.cache_dir")
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

    def _load_installers(self):
        """加载已注册的安装器"""
        # 这里会动态加载所有安装器
        # 在MVP阶段，我们将直接导入内置安装器
        from .installers.pip import PipInstaller
        from .installers.npm import NpmInstaller

        self.installers["pip"] = PipInstaller()
        self.installers["npm"] = NpmInstaller()

    def install(self, package: str, installer_type: str = "pip", **kwargs) -> bool:
        """
        安装依赖包

        Args:
            package: 包名和版本，例如：'django==3.2.0'或'@angular/cli@13.0.0'
            installer_type: 安装器类型，如'pip'、'npm'等
            **kwargs: 其他安装参数

        Returns:
            安装是否成功
        """
        if installer_type not in self.installers:
            logger.error(f"Installer '{installer_type}' not found")
            return False

        # 获取源
        source = self.source_manager.get_best_source(installer_type)
        if not source:
            logger.error(f"No available source for '{installer_type}'")
            return False

        # 执行安装
        try:
            installer = self.installers[installer_type]
            return installer.install(package, source=source, **kwargs)
        except Exception as e:
            logger.error(f"Failed to install '{package}': {e}")
            return False

    def uninstall(self, package: str, installer_type: str = "pip", **kwargs) -> bool:
        """
        卸载依赖包

        Args:
            package: 包名
            installer_type: 安装器类型
            **kwargs: 其他卸载参数

        Returns:
            卸载是否成功
        """
        if installer_type not in self.installers:
            logger.error(f"Installer '{installer_type}' not found")
            return False

        try:
            installer = self.installers[installer_type]
            return installer.uninstall(package, **kwargs)
        except Exception as e:
            logger.error(f"Failed to uninstall '{package}': {e}")
            return False

    def update(self, package: str, installer_type: str = "pip", **kwargs) -> bool:
        """
        更新依赖包

        Args:
            package: 包名
            installer_type: 安装器类型
            **kwargs: 其他更新参数

        Returns:
            更新是否成功
        """
        if installer_type not in self.installers:
            logger.error(f"Installer '{installer_type}' not found")
            return False

        # 获取源
        source = self.source_manager.get_best_source(installer_type)
        if not source:
            logger.error(f"No available source for '{installer_type}'")
            return False

        try:
            installer = self.installers[installer_type]
            return installer.update(package, source=source, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update '{package}': {e}")
            return False

    def list_packages(
        self, installer_type: str = "pip", **kwargs
    ) -> List[Dict[str, str]]:
        """
        列出已安装的依赖包

        Args:
            installer_type: 安装器类型
            **kwargs: 其他参数

        Returns:
            已安装的包列表
        """
        if installer_type not in self.installers:
            logger.error(f"Installer '{installer_type}' not found")
            return []

        try:
            installer = self.installers[installer_type]
            return installer.list_packages(**kwargs)
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            return []

    def check_updates(
        self, installer_type: str = "pip", **kwargs
    ) -> List[Dict[str, str]]:
        """
        检查可更新的依赖包

        Args:
            installer_type: 安装器类型
            **kwargs: 其他参数

        Returns:
            可更新的包列表
        """
        if installer_type not in self.installers:
            logger.error(f"Installer '{installer_type}' not found")
            return []

        # 获取源
        source = self.source_manager.get_best_source(installer_type)
        if not source:
            logger.error(f"No available source for '{installer_type}'")
            return []

        try:
            # 获取已安装的包
            packages = self.list_packages(installer_type=installer_type, **kwargs)
            if not packages:
                return []

            # 初始化更新列表
            updates = []

            # 检查每个包的更新
            installer = self.installers[installer_type]
            for pkg in packages:
                try:
                    # 获取最新版本
                    latest_version = installer.get_latest_version(
                        pkg["name"], source=source
                    )
                    if latest_version and latest_version != pkg.get("version"):
                        updates.append(
                            {
                                "name": pkg["name"],
                                "current": pkg.get("version"),
                                "latest": latest_version,
                            }
                        )
                except Exception as e:
                    logger.debug(f"Failed to check updates for '{pkg['name']}': {e}")

            return updates
        except Exception as e:
            logger.error(f"Failed to check updates: {e}")
            return []

    def switch_source(
        self, source_name: str, installer_type: Optional[str] = None
    ) -> bool:
        """
        切换依赖源

        Args:
            source_name: 源名称
            installer_type: 安装器类型，如果为None则对所有支持该源的安装器生效

        Returns:
            切换是否成功
        """
        return self.source_manager.switch_source(source_name, installer_type)

    def get_status(self) -> Dict[str, Any]:
        """
        获取依赖管理系统状态

        Returns:
            状态信息
        """
        return {
            "installers": {
                name: installer.get_info()
                for name, installer in self.installers.items()
            },
            "sources": self.source_manager.get_status(),
            "cache": {
                "enabled": self.cache_manager.cache_enabled,
                "size": self.cache_manager.get_cache_size(),
                "items": self.cache_manager.get_cache_info(),
            },
        }
