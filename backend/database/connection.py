#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接管理器

管理数据库连接、连接池和数据库配置
"""

import os
import time
import logging
import threading
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import QueuePool

from backend.config import config

# 配置日志
logger = logging.getLogger("smoothstack.database.connection")


class DatabaseConnection:
    """
    数据库连接管理器

    管理数据库连接、连接池和切换不同数据库
    """

    def __init__(self):
        """初始化数据库连接管理器"""
        # 数据库引擎缓存
        self._engines: Dict[str, Engine] = {}
        # 数据库连接URL缓存
        self._urls: Dict[str, str] = {}
        # 默认数据库名称
        self._default_db = "default"
        # 线程锁，确保线程安全
        self._lock = threading.RLock()
        # 最大重连尝试次数
        self._max_retries = 3
        # 重连等待时间（秒）
        self._retry_wait = 1.0
        # 是否已初始化
        self._initialized = False

    def init_engines(self) -> None:
        """初始化数据库引擎"""
        with self._lock:
            if self._initialized:
                return

            # 加载数据库配置
            db_config = config.get("database", {})

            # 处理默认连接
            url = db_config.get("url")
            if url:
                self._parse_and_create_engine(self._default_db, url, db_config)

            # 处理其他命名连接
            connections = db_config.get("connections", {})
            for name, conn_config in connections.items():
                if "url" in conn_config:
                    self._parse_and_create_engine(name, conn_config["url"], conn_config)

            # 确保至少有一个引擎
            if not self._engines:
                logger.warning("未配置任何数据库连接，使用默认的SQLite内存数据库")
                self._parse_and_create_engine(
                    self._default_db,
                    "sqlite:///:memory:",
                    {"echo": False, "pool_size": 1},
                )

            self._initialized = True
            logger.info(
                f"数据库引擎已初始化，可用的数据库：{', '.join(self._engines.keys())}"
            )

    def _parse_and_create_engine(
        self, name: str, url: str, config: Dict[str, Any]
    ) -> None:
        """
        解析连接URL并创建数据库引擎

        Args:
            name: 数据库连接名称
            url: 数据库连接URL
            config: 数据库配置项
        """
        # 保存连接URL
        self._urls[name] = url

        # 提取引擎选项
        engine_options = self._get_engine_options(url, config)

        # 使用重连包装器创建引擎
        self._engines[name] = self._create_engine_with_retry(url, engine_options)

        logger.debug(f"已创建数据库引擎: {name}, {url.split('@')[-1]}")

    def _get_engine_options(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取引擎选项配置

        Args:
            url: 数据库连接URL
            config: 数据库配置项

        Returns:
            引擎选项字典
        """
        # 基本选项
        options = {
            "echo": config.get("echo", False),
            "future": True,  # 使用SQLAlchemy 2.0风格API
        }

        # SQLite特殊处理
        if url.startswith("sqlite:"):
            options.update(
                {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": None if url == "sqlite:///:memory:" else QueuePool,
                }
            )
        else:
            # 非SQLite数据库的连接池配置
            options.update(
                {
                    "pool_size": config.get("pool_size", 5),
                    "max_overflow": config.get("max_overflow", 10),
                    "pool_timeout": config.get("pool_timeout", 30),
                    "pool_recycle": config.get("pool_recycle", 1800),  # 30分钟
                    "pool_pre_ping": config.get("pool_pre_ping", True),
                }
            )

        return options

    def _create_engine_with_retry(self, url: str, options: Dict[str, Any]) -> Engine:
        """
        创建数据库引擎，支持自动重试

        Args:
            url: 数据库连接URL
            options: 引擎选项

        Returns:
            创建的SQLAlchemy引擎对象
        """
        retries = 0
        last_error = None

        while retries < self._max_retries:
            try:
                # 创建引擎
                engine = create_engine(url, **options)

                # 测试连接
                if not url.startswith("sqlite:"):
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))

                return engine

            except (SQLAlchemyError, OperationalError) as e:
                last_error = e
                retries += 1

                if retries < self._max_retries:
                    wait_time = self._retry_wait * retries
                    logger.warning(
                        f"数据库连接失败，将在 {wait_time} 秒后重试 ({retries}/{self._max_retries}): {e}"
                    )
                    time.sleep(wait_time)

        # 如果所有尝试都失败，记录错误并抛出异常
        if last_error:
            logger.error(f"无法连接到数据库，已达到最大重试次数: {last_error}")
            raise last_error

        # 这应该不会发生，但为了类型检查完整性
        raise RuntimeError("创建数据库引擎时发生未知错误")

    def get_engine(self, db_name: Optional[str] = None) -> Engine:
        """
        获取数据库引擎

        Args:
            db_name: 数据库名称，默认使用默认数据库

        Returns:
            数据库引擎对象

        Raises:
            ValueError: 如果指定的数据库不存在
        """
        if not self._initialized:
            self.init_engines()

        name = db_name or self._default_db

        if name not in self._engines:
            raise ValueError(f"未找到名为 '{name}' 的数据库配置")

        return self._engines[name]

    def get_url(self, db_name: Optional[str] = None) -> str:
        """
        获取数据库连接URL

        Args:
            db_name: 数据库名称，默认使用默认数据库

        Returns:
            数据库连接URL

        Raises:
            ValueError: 如果指定的数据库不存在
        """
        if not self._initialized:
            self.init_engines()

        name = db_name or self._default_db

        if name not in self._urls:
            raise ValueError(f"未找到名为 '{name}' 的数据库URL")

        return self._urls[name]

    def refresh_engines(self) -> None:
        """
        刷新所有数据库引擎

        在配置变更后调用，重新创建所有数据库引擎
        """
        with self._lock:
            # 关闭现有引擎
            for engine in self._engines.values():
                engine.dispose()

            # 清空引擎和URL缓存
            self._engines.clear()
            self._urls.clear()

            # 重置初始化状态
            self._initialized = False

            # 重新初始化
            self.init_engines()

            logger.info("已刷新所有数据库引擎")

    def close_all(self) -> None:
        """关闭所有数据库连接"""
        with self._lock:
            if not self._initialized:
                return

            for name, engine in self._engines.items():
                try:
                    engine.dispose()
                    logger.debug(f"已关闭数据库连接: {name}")
                except Exception as e:
                    logger.error(f"关闭数据库连接 '{name}' 时出错: {e}")

            self._engines.clear()
            self._initialized = False

            logger.info("已关闭所有数据库连接")


# 创建全局数据库连接管理器
_connection_manager = DatabaseConnection()


def get_connection() -> DatabaseConnection:
    """
    获取数据库连接管理器实例

    Returns:
        数据库连接管理器实例
    """
    return _connection_manager
