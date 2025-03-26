#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker管理器主类

提供统一的Docker管理接口，包括：
- 自动选择最佳实现方式（CLI命令或Python API）
- 容器和镜像的管理
- 美观的界面和详细的错误处理
"""

import os
import sys
import logging
import subprocess
from typing import List, Dict, Optional, Any, Union, Tuple
from enum import Enum, auto

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RunMode(Enum):
    """Docker运行模式"""

    CLI = auto()  # 使用Docker CLI命令
    PYTHON_API = auto()  # 使用Python Docker API
    AUTO = auto()  # 自动选择最佳实现


class OutputFormat(Enum):
    """输出格式"""

    PLAIN = auto()  # 纯文本输出
    RICH = auto()  # Rich格式化输出
    JSON = auto()  # JSON格式输出


class DockerManager:
    """Docker管理器主类"""

    def __init__(
        self,
        mode: RunMode = RunMode.AUTO,
        output_format: OutputFormat = OutputFormat.RICH,
        config_path: Optional[str] = None,
    ):
        self.mode = self._determine_run_mode(mode)
        self.output_format = output_format
        self.config_path = config_path
        self.docker_client = None

        # 初始化Rich输出
        self.rich_available = False
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.progress import Progress
            from rich.panel import Panel

            self.console = Console()
            self.rich_available = True
        except ImportError:
            if self.output_format == OutputFormat.RICH:
                logger.warning("Rich库不可用，将使用纯文本输出")
                self.output_format = OutputFormat.PLAIN

    def _determine_run_mode(self, mode: RunMode) -> RunMode:
        """确定实际运行模式"""
        if mode == RunMode.CLI:
            if not self._check_docker_installed():
                raise RuntimeError("Docker未安装或无法访问")
            return RunMode.CLI

        if mode == RunMode.PYTHON_API:
            if not self._init_docker_client():
                raise RuntimeError("Python Docker API不可用")
            return RunMode.PYTHON_API

        # 自动模式：优先使用Python API
        if self._init_docker_client():
            return RunMode.PYTHON_API

        if self._check_docker_installed():
            return RunMode.CLI

        raise RuntimeError("Docker未安装或无法访问")

    def _check_docker_installed(self) -> bool:
        """检查Docker是否已安装"""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _init_docker_client(self) -> bool:
        """初始化Docker客户端"""
        if self.docker_client is not None:
            return True

        try:
            import docker

            self.docker_client = docker.from_env()
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.debug(f"初始化Docker客户端失败: {e}")
            return False

    def _run_docker_command(
        self, cmd: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """运行Docker命令"""
        try:
            result = subprocess.run(
                ["docker"] + cmd, capture_output=capture_output, text=True, check=False
            )
            return result
        except Exception as e:
            raise RuntimeError(f"执行Docker命令失败: {e}")

    def print_message(self, message: str, style: str = "") -> None:
        """格式化输出消息"""
        if self.output_format == OutputFormat.RICH and self.rich_available:
            self.console.print(message)
        elif self.output_format == OutputFormat.JSON:
            import json

            print(json.dumps({"message": message}))
        else:
            # 去除Rich标记
            message = message.replace("[bold ", "").replace("[/]", "")
            message = message.replace("[green]", "").replace("[red]", "")
            message = message.replace("[yellow]", "").replace("[blue]", "")
            print(message)

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def format_time_ago(self, timestamp: str) -> str:
        """格式化时间差"""
        from datetime import datetime
        import pytz

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            now = datetime.now(pytz.UTC)
            diff = now - dt

            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60

            if days > 0:
                return f"{days}天前"
            elif hours > 0:
                return f"{hours}小时前"
            elif minutes > 0:
                return f"{minutes}分钟前"
            else:
                return "刚刚"
        except Exception:
            return timestamp
