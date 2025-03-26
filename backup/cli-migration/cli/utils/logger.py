"""
日志工具模块，提供统一的日志记录接口
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union, cast

from rich.console import Console
from rich.logging import RichHandler

from .platform import get_data_dir, ensure_dir


# 定义日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# 简单日志格式（用于控制台输出）
SIMPLE_FORMAT = "%(message)s"

# 控制台实例
console = Console()


class Logger:
    """
    日志管理类，提供统一的日志记录接口
    """

    _loggers: Dict[str, logging.Logger] = {}
    _initialized: bool = False

    @classmethod
    def init(
        cls,
        log_dir: Optional[Path] = None,
        console_level: Union[str, int] = "info",
        file_level: Union[str, int] = "debug",
        max_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format_str: Optional[str] = None,
    ) -> None:
        """
        初始化日志系统

        Args:
            log_dir: 日志目录，默认为数据目录下的logs目录
            console_level: 控制台日志级别
            file_level: 文件日志级别
            max_size: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件数量
            format_str: 日志格式字符串
        """
        if cls._initialized:
            return

        # 确保日志目录存在
        if log_dir is None:
            log_dir = get_data_dir() / "logs"
        ensure_dir(log_dir)

        # 设置根日志配置
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 创建控制台处理器
        console_log_level = (
            LOG_LEVELS.get(cast(str, console_level).lower(), logging.INFO)
            if isinstance(console_level, str)
            else console_level
        )
        console_handler = RichHandler(
            console=console,
            show_path=False,
            enable_link_path=False,
            markup=True,
            rich_tracebacks=True,
            level=console_log_level,
        )
        console_formatter = logging.Formatter(SIMPLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 创建文件处理器
        file_log_level = (
            LOG_LEVELS.get(cast(str, file_level).lower(), logging.DEBUG)
            if isinstance(file_level, str)
            else file_level
        )
        format_str = format_str or DEFAULT_FORMAT

        # 使用日期作为日志文件名
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"smoothstack_{date_str}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(file_log_level)
        file_formatter = logging.Formatter(format_str)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志器

        Args:
            name: 日志器名称

        Returns:
            对应名称的日志器实例
        """
        if not cls._initialized:
            cls.init()

        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)

        return cls._loggers[name]

    @classmethod
    def set_level(
        cls, level: Union[str, int], logger_name: Optional[str] = None
    ) -> None:
        """
        设置日志级别

        Args:
            level: 日志级别，可以是字符串或整数
            logger_name: 日志器名称，None表示设置根日志器
        """
        if isinstance(level, str):
            level = LOG_LEVELS.get(level.lower(), logging.INFO)

        if logger_name:
            logger = cls.get_logger(logger_name)
            logger.setLevel(level)
        else:
            logging.getLogger().setLevel(level)

    @classmethod
    def disable_file_logging(cls) -> None:
        """
        禁用文件日志记录，只保留控制台输出
        """
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, RotatingFileHandler):
                root_logger.removeHandler(handler)

    @classmethod
    def disable_console_logging(cls) -> None:
        """
        禁用控制台日志记录，只保留文件输出
        """
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, RichHandler):
                root_logger.removeHandler(handler)


# 快捷函数
def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器

    Args:
        name: 日志器名称

    Returns:
        对应名称的日志器实例
    """
    return Logger.get_logger(name)


def init_logging(**kwargs: Any) -> None:
    """
    初始化日志系统

    Args:
        **kwargs: 传递给Logger.init的参数
    """
    Logger.init(**kwargs)


def set_log_level(level: Union[str, int], logger_name: Optional[str] = None) -> None:
    """
    设置日志级别

    Args:
        level: 日志级别，可以是字符串或整数
        logger_name: 日志器名称，None表示设置根日志器
    """
    Logger.set_level(level, logger_name)
