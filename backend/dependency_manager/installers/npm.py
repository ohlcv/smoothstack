#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NPM安装器

实现通过npm管理Node.js包
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
logger = logging.getLogger("smoothstack.dependency_manager.installers.npm")


class NpmInstaller(BaseInstaller):
    """NPM安装器"""

    def __init__(self):
        """初始化NPM安装器"""
        super().__init__("npm")
        self.npm_executable = self._get_npm_executable()

    def _get_npm_executable(self) -> str:
        """
        获取npm可执行文件路径

        Returns:
            npm可执行文件路径
        """
        # 在Windows系统上添加.exe后缀
        if sys.platform.startswith("win"):
            return "npm.cmd"

        # 其他系统
        return "npm"

    def _run_npm_command(
        self, args: List[str], cwd: Optional[str] = None, capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        运行npm命令

        Args:
            args: 命令参数列表
            cwd: 工作目录
            capture_output: 是否捕获输出

        Returns:
            命令执行结果
        """
        cmd = [self.npm_executable] + args
        logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                check=False,
                cwd=cwd,
            )

            if result.returncode != 0:
                logger.error(f"NPM command failed: {result.stderr}")

            return result
        except Exception as e:
            logger.error(f"Error running npm command: {e}")
            raise

    def install(self, package: str, source: Optional[Source] = None, **kwargs) -> bool:
        """
        安装依赖包

        Args:
            package: 包名和版本
            source: 源对象
            **kwargs: 其他参数
                global: 是否全局安装
                save_dev: 是否保存为开发依赖
                cwd: 工作目录

        Returns:
            是否安装成功
        """
        args = ["install"]

        # 添加额外参数
        if kwargs.get("global"):
            args.append("-g")

        if kwargs.get("save_dev"):
            args.append("--save-dev")
        else:
            args.append("--save")

        # 添加包名和版本
        args.append(package)

        # 构建选项
        cwd = kwargs.get("cwd")

        # 运行安装命令
        result = self._run_npm_command(args, cwd=cwd)

        return result.returncode == 0

    def uninstall(self, package: str, **kwargs) -> bool:
        """
        卸载依赖包

        Args:
            package: 包名
            **kwargs: 其他参数
                global: 是否全局卸载
                cwd: 工作目录

        Returns:
            是否卸载成功
        """
        args = ["uninstall"]

        # 添加额外参数
        if kwargs.get("global"):
            args.append("-g")
        elif not kwargs.get("no_save"):
            args.append("--save")

        # 添加包名
        args.append(package)

        # 构建选项
        cwd = kwargs.get("cwd")

        # 运行卸载命令
        result = self._run_npm_command(args, cwd=cwd)

        return result.returncode == 0

    def update(self, package: str, source: Optional[Source] = None, **kwargs) -> bool:
        """
        更新依赖包

        Args:
            package: 包名
            source: 源对象
            **kwargs: 其他参数
                global: 是否全局更新
                cwd: 工作目录

        Returns:
            是否更新成功
        """
        logger.info(f"Updating npm package: {package}")
        try:
            # 使用npm update命令
            cmd = [self.npm_executable, "update", package]

            # 添加源URL
            if source:
                cmd.extend(["--registry", source.url])

            # 执行命令
            subprocess.check_call(cmd)
            logger.info(f"Successfully updated {package}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating {package}: {e}")
            return False

    def _parse_json_output(self, stdout: str) -> Dict:
        """
        解析JSON格式的输出

        Args:
            stdout: 命令输出

        Returns:
            解析后的数据
        """
        try:
            # 查找JSON内容的开始位置
            start_pos = stdout.find("{")
            if start_pos == -1:
                logger.error("No JSON content found in output")
                return {}

            # 提取JSON内容
            json_str = stdout[start_pos:]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {e}")
            return {}

    def list_packages(self, **kwargs) -> List[Dict[str, str]]:
        """
        列出已安装的依赖包

        Args:
            **kwargs: 其他参数
                global: 是否列出全局包
                cwd: 工作目录

        Returns:
            已安装的依赖包列表
        """
        logger.info("Listing installed npm packages")
        try:
            # 使用npm list命令获取已安装的包
            cmd = [self.npm_executable, "list", "--json", "--depth=0"]
            result = subprocess.check_output(cmd, text=True)
            data = json.loads(result)

            # 转换为标准格式
            packages = []
            if "dependencies" in data:
                for name, info in data["dependencies"].items():
                    packages.append(
                        {"name": name, "version": info.get("version", "unknown")}
                    )

            return packages
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Error listing packages: {e}")
            return []

    def check_updates(self, source: Optional[Source] = None, **kwargs) -> List[Dict]:
        """
        检查依赖包更新

        Args:
            source: 源对象
            **kwargs: 其他参数
                global: 是否检查全局包
                cwd: 工作目录

        Returns:
            可更新的依赖包列表
        """
        args = ["outdated", "--json"]

        # 添加额外参数
        if kwargs.get("global"):
            args.append("-g")

        # 构建选项
        cwd = kwargs.get("cwd")

        # 运行outdated命令
        result = self._run_npm_command(args, cwd=cwd)

        # npm outdated返回非0状态码表示有可更新的包
        if result.returncode != 0 and not result.stdout:
            logger.error("Failed to check package updates")
            return []

        try:
            data = self._parse_json_output(result.stdout)
            if not data:
                return []

            # 将依赖转换为列表格式
            outdated_packages = []
            for name, info in data.items():
                package_info = {
                    "name": name,
                    "current": info.get("current", "unknown"),
                    "wanted": info.get("wanted", "unknown"),
                    "latest": info.get("latest", "unknown"),
                    "location": info.get("location", ""),
                }
                outdated_packages.append(package_info)

            return outdated_packages
        except Exception as e:
            logger.error(f"Failed to parse npm outdated output: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """
        获取安装器状态

        Returns:
            状态信息
        """
        status = super().get_status()

        # 获取npm版本
        result = self._run_npm_command(["--version"])
        if result.returncode == 0:
            npm_version = result.stdout.strip()
        else:
            npm_version = "unknown"

        # 获取node版本
        node_result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=False
        )
        if node_result.returncode == 0:
            node_version = node_result.stdout.strip()
        else:
            node_version = "unknown"

        status.update(
            {
                "executable": self.npm_executable,
                "npm_version": npm_version,
                "node_version": node_version,
            }
        )

        return status

    def get_latest_version(self, package: str, source=None, **kwargs) -> Optional[str]:
        """获取依赖包的最新版本号"""
        logger.info(f"Getting latest version for npm package: {package}")
        try:
            # 使用npm view命令获取最新版本
            cmd = [self.npm_executable, "view", package, "version"]

            # 添加源URL
            if source:
                cmd.extend(["--registry", source.url])

            # 执行命令
            result = subprocess.check_output(cmd, text=True)

            # 结果通常是单行的版本号
            latest_version = result.strip()
            if latest_version:
                logger.info(f"Latest version of {package}: {latest_version}")
                return latest_version

            logger.warning(f"Could not get latest version for {package}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting latest version for {package}: {e}")
            return None
