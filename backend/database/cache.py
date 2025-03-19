#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库缓存模块

提供模型缓存和查询结果缓存功能，减少数据库访问
"""

import functools
import hashlib
import inspect
import json
import logging
import pickle
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Query, Session

from .base import BaseModel

# 配置日志
logger = logging.getLogger("smoothstack.database.cache")

# 类型变量
T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")
V = TypeVar("V")


class CacheStrategy(str, Enum):
    """缓存策略枚举"""

    NONE = "none"  # 不缓存
    MEMORY = "memory"  # 内存缓存
    REDIS = "redis"  # Redis缓存（未实现）


class MemoryCache:
    """内存缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存项数量
            ttl: 默认过期时间（秒）
        """
        self._data: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
        self._default_ttl = ttl
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def get(self, key: str) -> Any:
        """
        获取缓存项

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        with self._lock:
            if key not in self._data:
                self._stats["misses"] += 1
                return None

            value, expire_time = self._data[key]

            # 检查是否过期
            if expire_time < time.time():
                del self._data[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存项

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认过期时间
        """
        with self._lock:
            # 检查是否需要淘汰
            if len(self._data) >= self._max_size and key not in self._data:
                # LRU淘汰：移除最先过期的项
                oldest_key = min(self._data.items(), key=lambda x: x[1][1])[0]
                del self._data[oldest_key]
                self._stats["evictions"] += 1

            # 设置过期时间
            expire_time = time.time() + (ttl if ttl is not None else self._default_ttl)

            # 存储数据
            self._data[key] = (value, expire_time)
            self._stats["sets"] += 1

    def delete(self, key: str) -> bool:
        """
        删除缓存项

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._data.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            return self._stats.copy()

    def get_size(self) -> int:
        """
        获取缓存大小

        Returns:
            缓存项数量
        """
        with self._lock:
            return len(self._data)


class CacheRegistry:
    """缓存注册表"""

    def __init__(self):
        """初始化缓存注册表"""
        self._caches: Dict[str, MemoryCache] = {}
        self._lock = threading.RLock()
        self._enabled = True
        self._strategy = CacheStrategy.MEMORY

    def get_cache(self, name: str) -> MemoryCache:
        """
        获取命名缓存

        Args:
            name: 缓存名称

        Returns:
            缓存对象
        """
        with self._lock:
            if name not in self._caches:
                self._caches[name] = MemoryCache()
            return self._caches[name]

    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()

    def set_enabled(self, enabled: bool) -> None:
        """
        设置缓存启用状态

        Args:
            enabled: 是否启用
        """
        with self._lock:
            self._enabled = enabled

    def is_enabled(self) -> bool:
        """
        获取缓存启用状态

        Returns:
            是否启用
        """
        return self._enabled

    def set_strategy(self, strategy: CacheStrategy) -> None:
        """
        设置缓存策略

        Args:
            strategy: 缓存策略
        """
        with self._lock:
            self._strategy = strategy

    def get_strategy(self) -> CacheStrategy:
        """
        获取缓存策略

        Returns:
            缓存策略
        """
        return self._strategy

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        获取所有缓存统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            return {name: cache.get_stats() for name, cache in self._caches.items()}


# 创建全局缓存注册表
_registry = CacheRegistry()


def get_registry() -> CacheRegistry:
    """
    获取缓存注册表

    Returns:
        缓存注册表
    """
    return _registry


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        prefix: 前缀
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键
    """
    # 序列化参数
    key_parts = [prefix]

    if args:
        args_repr = []
        for arg in args:
            if isinstance(arg, BaseModel):
                # 使用模型ID
                args_repr.append(
                    f"{arg.__class__.__name__}:{getattr(arg, arg.__id_column__)}"
                )
            elif hasattr(arg, "__name__"):
                # 使用类或函数名称
                args_repr.append(arg.__name__)
            else:
                # 使用字符串表示
                args_repr.append(str(arg))
        key_parts.append(",".join(args_repr))

    if kwargs:
        # 排序确保相同参数生成相同键
        kwargs_repr = [f"{k}:{v}" for k, v in sorted(kwargs.items())]
        key_parts.append(",".join(kwargs_repr))

    # 生成哈希
    key = ":".join(key_parts)
    if len(key) > 64:
        # 如果键太长，使用哈希
        key_hash = hashlib.md5(key.encode()).hexdigest()
        key = f"{prefix}:{key_hash}"

    return key


class QueryCache:
    """查询缓存"""

    def __init__(self, model_class: Type[T], session: Session, ttl: int = 60):
        """
        初始化查询缓存

        Args:
            model_class: 模型类
            session: 数据库会话
            ttl: 缓存过期时间（秒）
        """
        self._model_class = model_class
        self._session = session
        self._ttl = ttl
        self._cache = get_registry().get_cache("query")

    def get(self, query: Query) -> Optional[List[T]]:
        """
        获取查询结果缓存

        Args:
            query: 查询对象

        Returns:
            缓存的查询结果或None
        """
        if not get_registry().is_enabled():
            return None

        # 生成缓存键
        key = self._generate_query_cache_key(query)

        # 获取缓存
        return self._cache.get(key)

    def set(self, query: Query, result: List[T]) -> None:
        """
        设置查询结果缓存

        Args:
            query: 查询对象
            result: 查询结果
        """
        if not get_registry().is_enabled():
            return

        # 生成缓存键
        key = self._generate_query_cache_key(query)

        # 设置缓存
        self._cache.set(key, result, self._ttl)

    def invalidate(self, query: Query) -> None:
        """
        使查询结果缓存失效

        Args:
            query: 查询对象
        """
        if not get_registry().is_enabled():
            return

        # 生成缓存键
        key = self._generate_query_cache_key(query)

        # 删除缓存
        self._cache.delete(key)

    def invalidate_model(self, model_id: Any) -> None:
        """
        使模型缓存失效

        Args:
            model_id: 模型ID
        """
        if not get_registry().is_enabled():
            return

        # 获取模型缓存
        model_cache = get_registry().get_cache("model")

        # 构建缓存键
        key = f"{self._model_class.__name__}:{model_id}"

        # 删除缓存
        model_cache.delete(key)

    def _generate_query_cache_key(self, query: Query) -> str:
        """
        生成查询缓存键

        Args:
            query: 查询对象

        Returns:
            缓存键
        """
        # 获取查询语句
        query_str = str(query)

        # 生成缓存键
        return _generate_cache_key(f"query:{self._model_class.__name__}", query_str)


class ModelCache:
    """模型缓存"""

    def __init__(self, model_class: Type[T], ttl: int = 300):
        """
        初始化模型缓存

        Args:
            model_class: 模型类
            ttl: 缓存过期时间（秒）
        """
        self._model_class = model_class
        self._ttl = ttl
        self._cache = get_registry().get_cache("model")

    def get(self, model_id: Any) -> Optional[T]:
        """
        获取模型缓存

        Args:
            model_id: 模型ID

        Returns:
            缓存的模型或None
        """
        if not get_registry().is_enabled():
            return None

        # 生成缓存键
        key = self._generate_model_cache_key(model_id)

        # 获取缓存
        return self._cache.get(key)

    def set(self, model: T) -> None:
        """
        设置模型缓存

        Args:
            model: 模型对象
        """
        if not get_registry().is_enabled():
            return

        # 获取模型ID
        model_id = getattr(model, model.__id_column__)

        # 生成缓存键
        key = self._generate_model_cache_key(model_id)

        # 设置缓存
        self._cache.set(key, model, self._ttl)

    def invalidate(self, model_id: Any) -> None:
        """
        使模型缓存失效

        Args:
            model_id: 模型ID
        """
        if not get_registry().is_enabled():
            return

        # 生成缓存键
        key = self._generate_model_cache_key(model_id)

        # 删除缓存
        self._cache.delete(key)

    def _generate_model_cache_key(self, model_id: Any) -> str:
        """
        生成模型缓存键

        Args:
            model_id: 模型ID

        Returns:
            缓存键
        """
        return f"{self._model_class.__name__}:{model_id}"


def cached_query(ttl: int = 60):
    """
    查询结果缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        装饰器函数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 检查是否启用缓存
            if not get_registry().is_enabled():
                return func(*args, **kwargs)

            # 生成缓存键
            key = _generate_cache_key(f"cached_query:{func.__name__}", *args, **kwargs)

            # 获取缓存
            cache = get_registry().get_cache("query")
            result = cache.get(key)

            if result is not None:
                return result

            # 调用原函数
            result = func(*args, **kwargs)

            # 设置缓存
            cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_model_cache(model_class: Type[T], model_id: Any) -> None:
    """
    使模型缓存失效

    Args:
        model_class: 模型类
        model_id: 模型ID
    """
    if not get_registry().is_enabled():
        return

    # 获取模型缓存
    cache = ModelCache(model_class)

    # 使缓存失效
    cache.invalidate(model_id)


def cache_model(func: Optional[Callable] = None, ttl: int = 300):
    """
    模型缓存装饰器

    Args:
        func: 要装饰的函数
        ttl: 缓存过期时间（秒）

    Returns:
        装饰器函数或装饰后的函数
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(cls, session, id_value, *args, **kwargs):
            # 检查是否启用缓存
            if not get_registry().is_enabled():
                return f(cls, session, id_value, *args, **kwargs)

            # 获取模型缓存
            cache = ModelCache(cls, ttl)

            # 尝试从缓存获取
            model = cache.get(id_value)
            if model is not None:
                return model

            # 调用原函数
            model = f(cls, session, id_value, *args, **kwargs)

            # 缓存结果
            if model is not None:
                cache.set(model)

            return model

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
