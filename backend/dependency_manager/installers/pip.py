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
import re
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
        """更新依赖包"""
        # 实现包更新逻辑
        logger.info(f"Updating pip package: {package}")
        try:
            # 使用pip安装新版本
            cmd = [self.pip_executable, "install", "--upgrade", package]

            # 添加源URL
            if source:
                cmd.extend(["-i", source.url])

            # 执行命令
            subprocess.check_call(cmd)
            logger.info(f"Successfully updated {package}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating {package}: {e}")
            return False

    def list_packages(self, **kwargs) -> List[Dict[str, str]]:
        """列出已安装的依赖包"""
        logger.info("Listing installed pip packages")
        try:
            # 使用pip list命令获取已安装的包
            cmd = [self.pip_executable, "list", "--format=json"]
            result = subprocess.check_output(cmd, text=True)
            packages = json.loads(result)

            # 转换为标准格式
            return [
                {"name": pkg["name"], "version": pkg["version"]} for pkg in packages
            ]
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Error listing packages: {e}")
            return []

    def get_latest_version(self, package: str, source=None, **kwargs) -> Optional[str]:
        """获取依赖包的最新版本号"""
        logger.info(f"Getting latest version for pip package: {package}")
        try:
            # 使用pip index命令获取最新版本
            cmd = [self.pip_executable, "index", "versions", package]

            # 添加源URL
            if source:
                cmd.extend(["-i", source.url])

            # 执行命令
            result = subprocess.check_output(cmd, text=True)

            # 解析结果
            # 格式通常是 "package (x.y.z)"
            match = re.search(r"\(([^)]+)\)", result)
            if match:
                latest_version = match.group(1).split(",")[0].strip()
                logger.info(f"Latest version of {package}: {latest_version}")
                return latest_version

            logger.warning(f"Could not parse latest version for {package}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting latest version for {package}: {e}")
            return None

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
