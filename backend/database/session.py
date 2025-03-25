#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库会话管理器

管理 SQLAlchemy 会话和事务
"""

import logging
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, Optional, TypeVar, cast

from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.scoping import scoped_session

from .connection import get_connection

# 配置日志
logger = logging.getLogger("smoothstack.database.session")

# 线程本地存储，用于存储当前活动的会话
_thread_local = threading.local()

# 类型变量，用于上下文管理器的返回类型
T = TypeVar("T")


class SessionManager:
    """
    数据库会话管理器

    管理数据库会话生命周期和事务范围
    """

    def __init__(self):
        """初始化会话管理器"""
        # 会话工厂缓存
        self._session_factories: Dict[str, scoped_session] = {}
        # 线程锁，确保线程安全
        self._lock = threading.RLock()
        # 是否已初始化
        self._initialized = False

    def init_sessions(self):
        """初始化会话工厂"""
        with self._lock:
            if self._initialized:
                return

            # 获取数据库连接管理器
            connection = get_connection()

            # 创建默认会话工厂
            self._create_session_factory("default", connection.get_engine())

            # 同步认为已经初始化
            self._initialized = True
            logger.info("数据库会话工厂已初始化")

    def _create_session_factory(self, name: str, engine: Any):
        """
        创建会话工厂

        Args:
            name: 会话工厂名称
            engine: 数据库引擎
        """
        # 创建会话工厂
        factory = sessionmaker(
            bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
        )

        # 创建线程安全的会话工厂
        scoped_factory = scoped_session(factory)

        # 缓存会话工厂
        self._session_factories[name] = scoped_factory

        logger.debug(f"已创建会话工厂: {name}")

    def get_session(self, db_name: Optional[str] = None) -> Session:
        """
        获取数据库会话

        该方法返回的会话对象需要手动关闭

        Args:
            db_name: 数据库名称，默认使用默认数据库

        Returns:
            会话对象

        Raises:
            ValueError: 如果指定的数据库不存在
        """
        if not self._initialized:
            self.init_sessions()

        name = db_name or "default"

        if name not in self._session_factories:
            # 如果会话工厂不存在，尝试为指定数据库创建
            connection = get_connection()
            try:
                engine = connection.get_engine(name)
                self._create_session_factory(name, engine)
            except ValueError as e:
                raise ValueError(f"无法获取数据库会话: {e}")

        return self._session_factories[name]()

    def close_sessions(self):
        """关闭所有会话"""
        with self._lock:
            if not self._initialized:
                return

            for name, factory in self._session_factories.items():
                try:
                    factory.remove()
                    logger.debug(f"已关闭会话工厂: {name}")
                except Exception as e:
                    logger.error(f"关闭会话工厂 '{name}' 时出错: {e}")

            self._session_factories.clear()
            self._initialized = False

            logger.info("已关闭所有会话工厂")


# 创建全局会话管理器
_session_manager = SessionManager()


def get_session(db_name: Optional[str] = None) -> Session:
    """
    获取数据库会话

    该函数返回的会话对象需要手动关闭

    Args:
        db_name: 数据库名称，默认使用默认数据库

    Returns:
        会话对象
    """
    return _session_manager.get_session(db_name)


@contextmanager
def session_scope(db_name: Optional[str] = None) -> Iterator[Session]:
    """
    会话上下文管理器

    提供自动提交和回滚的会话上下文

    Args:
        db_name: 数据库名称，默认使用默认数据库

    Yields:
        会话对象

    Example:
        with session_scope() as session:
            user = session.query(User).filter_by(id=1).first()
            user.name = "New Name"
            # 自动提交并关闭会话
    """
    session = get_session(db_name)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"会话操作失败，已回滚: {e}")
        raise
    finally:
        session.close()


class TransactionContext:
    """
    事务上下文

    提供可嵌套的事务支持，自动处理提交和回滚
    """

    def __init__(
        self, session: Optional[Session] = None, db_name: Optional[str] = None
    ):
        """
        初始化事务上下文

        Args:
            session: 会话对象，如果不提供则自动创建
            db_name: 数据库名称，默认使用默认数据库
        """
        self._db_name = db_name
        self._session = session
        self._should_close = session is None
        self._active = False

    def __enter__(self) -> Session:
        """进入事务上下文"""
        if not self._session:
            self._session = get_session(self._db_name)

        self._active = True
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出事务上下文"""
        if not self._session or not self._active:
            return

        try:
            if exc_type is not None:
                # 如果有异常，回滚事务
                self._session.rollback()
                logger.debug(f"事务已回滚: {exc_val}")
            else:
                # 否则提交事务
                self._session.commit()
                logger.debug("事务已提交")
        except Exception as e:
            # 处理提交或回滚时的异常
            self._session.rollback()
            logger.exception(f"事务操作失败: {e}")
        finally:
            # 如果是自动创建的会话，需要关闭
            if self._should_close:
                self._session.close()

            self._active = False


def transaction(func: Optional[Callable] = None, db_name: Optional[str] = None):
    """
    事务装饰器

    为函数提供事务支持

    Args:
        func: 要装饰的函数
        db_name: 数据库名称，默认使用默认数据库

    Returns:
        装饰后的函数

    Example:
        @transaction
        def update_user(user_id, name):
            session = get_current_session()
            user = session.query(User).filter_by(id=user_id).first()
            user.name = name
            # 函数返回时自动提交事务
    """

    def decorator(f):
        def wrapper(*args, **kwargs):
            with TransactionContext(db_name=db_name) as session:
                # 保存当前会话到线程本地存储
                _thread_local.current_session = session
                try:
                    result = f(*args, **kwargs)
                    return result
                finally:
                    # 清理线程本地存储
                    if hasattr(_thread_local, "current_session"):
                        delattr(_thread_local, "current_session")

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def get_current_session() -> Session:
    """
    获取当前线程的活动会话

    Returns:
        当前活动的会话对象

    Raises:
        RuntimeError: 如果没有活动的会话
    """
    if not hasattr(_thread_local, "current_session"):
        raise RuntimeError("没有活动的会话，请在事务上下文中调用此函数")

    return cast(Session, _thread_local.current_session)
