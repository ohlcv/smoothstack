"""
日志系统
"""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """日志记录器类"""

    def __init__(self, name: str, log_dir: Optional[Path] = None):
        """初始化日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志文件目录
        """
        self.name = name
        self.log_dir = log_dir or Path(__file__).parent.parent / "logs"
        self.log_file = self.log_dir / f"{name}.log"

        # 创建日志目录
        os.makedirs(str(self.log_dir), exist_ok=True)

        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 创建文件处理器
        file_handler = RotatingFileHandler(
            str(self.log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message: str):
        """记录普通信息"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)

    def critical(self, message: str):
        """记录严重错误信息"""
        self.logger.critical(message)

    def set_level(self, level: str):
        """设置日志级别"""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        self.logger.setLevel(level_map.get(level.lower(), logging.INFO))

    def get_log_file(self) -> Path:
        """获取日志文件路径"""
        return self.log_file
