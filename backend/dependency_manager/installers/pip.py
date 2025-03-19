#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PIP安装器

实现通过pip管理Python包
"""

import logging
import subprocess
import json
import os
import sys
from typing import Dict, List, Optional, Any

from ..sources.source import Source, SourceType
from .base import BaseInstaller

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.installers.pip")


class PipInstaller(BaseInstaller):
    """PIP安装器"""

    def __init__(self):
        """初始化PIP安装器"""
        super().__init__("pip")
        self.pip_executable = self._get_pip_executable()

    def _get_pip_executable(self) -> str:
        """
        获取pip可执行文件路径

        Returns:
            pip可执行文件路径
        """
        # 如果在虚拟环境中，使用虚拟环境的pip
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            if sys.platform.startswith("win"):
                return os.path.join(sys.prefix, "Scripts", "pip.exe")
            else:
                return os.path.join(sys.prefix, "bin", "pip")

        # 否则使用系统pip
        return "pip"

    def _run_pip_command(
        self, args: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        运行pip命令

        Args:
            args: 命令参数列表
            capture_output: 是否捕获输出

        Returns:
            命令执行结果
        """
        cmd = [self.pip_executable] + args
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error(f"Pip command failed: {result.stderr}")

            return result
        except Exception as e:
            logger.error(f"Error running pip command: {e}")
            raise

    def install(self, package: str, source: Optional[Source] = None, **kwargs) -> bool:
        """
        安装依赖包

        Args:
            package: 包名和版本
            source: 源对象
            **kwargs: 其他参数
                upgrade: 是否升级
                editable: 是否以可编辑模式安装
                extras: 额外功能

        Returns:
            是否安装成功
        """
        args = ["install"]

        # 添加额外参数
        if kwargs.get("upgrade"):
            args.append("--upgrade")

        if kwargs.get("editable"):
            args.append("-e")

        # 指定源
        if source and source.type == SourceType.PYPI:
            args.extend(["-i", source.url])

        # 添加包名和版本
        if kwargs.get("extras"):
            # 格式: package[extras]
            package_with_extras = f"{package}[{kwargs['extras']}]"
            args.append(package_with_extras)
        else:
            args.append(package)

        # 运行安装命令
        result = self._run_pip_command(args)

        return result.returncode == 0

    def uninstall(self, package: str, **kwargs) -> bool:
        """
        卸载依赖包

        Args:
            package: 包名
            **kwargs: 其他参数

        Returns:
            是否卸载成功
        """
        args = ["uninstall", "-y", package]
        result = self._run_pip_command(args)

        return result.returncode == 0

    def update(self, package: str, source: Optional[Source] = None, **kwargs) -> bool:
        """
        更新依赖包

        Args:
            package: 包名
            source: 源对象
            **kwargs: 其他参数

        Returns:
            是否更新成功
        """
        # 本质上就是带--upgrade参数的安装
        kwargs["upgrade"] = True
        return self.install(package, source, **kwargs)

    def list_packages(self, **kwargs) -> List[Dict]:
        """
        列出已安装的依赖包

        Args:
            **kwargs: 其他参数
                format: 输出格式，支持json

        Returns:
            已安装的依赖包列表
        """
        args = ["list", "--format=json"]

        result = self._run_pip_command(args)

        if result.returncode != 0:
            logger.error("Failed to list packages")
            return []

        try:
            packages = json.loads(result.stdout)
            return packages
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pip list output: {e}")
            return []

    def check_updates(self, source: Optional[Source] = None, **kwargs) -> List[Dict]:
        """
        检查依赖包更新

        Args:
            source: 源对象
            **kwargs: 其他参数

        Returns:
            可更新的依赖包列表
        """
        args = ["list", "--outdated", "--format=json"]

        # 指定源
        if source and source.type == SourceType.PYPI:
            args.extend(["-i", source.url])

        result = self._run_pip_command(args)

        if result.returncode != 0:
            logger.error("Failed to check package updates")
            return []

        try:
            outdated_packages = json.loads(result.stdout)
            return outdated_packages
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pip outdated output: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """
        获取安装器状态

        Returns:
            状态信息
        """
        status = super().get_status()

        # 获取pip版本
        result = self._run_pip_command(["--version"])
        if result.returncode == 0:
            pip_version = result.stdout.strip()
        else:
            pip_version = "unknown"

        status.update({"executable": self.pip_executable, "version": pip_version})

        return status
