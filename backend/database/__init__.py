#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库模块

管理数据库连接、会话和ORM模型
"""

from .connection import DatabaseConnection, get_connection
from .session import (
    SessionManager,
    get_session,
    session_scope,
    transaction,
    get_current_session,
)
from .base import Base, BaseModel, UUIDModel
from .query import QueryBuilder, query, SortDirection
from .cache import (
    ModelCache,
    QueryCache,
    cached_query,
    cache_model,
    invalidate_model_cache,
    get_registry,
    CacheStrategy,
)
from .errors import (
    DatabaseError,
    ConnectionError,
    QueryError,
    ValidationError,
    TransactionError,
    CacheError,
    handle_database_error,
    safe_operation,
)

# 导入所有模型，确保模型被加载到元数据中
from .models import *

# 导出公共符号
__all__ = [
    "DatabaseConnection",
    "get_connection",
    "SessionManager",
    "get_session",
    "session_scope",
    "transaction",
    "get_current_session",
    "Base",
    "BaseModel",
    "UUIDModel",
    "QueryBuilder",
    "query",
    "SortDirection",
    "ModelCache",
    "QueryCache",
    "cached_query",
    "cache_model",
    "invalidate_model_cache",
    "get_registry",
    "CacheStrategy",
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "ValidationError",
    "TransactionError",
    "CacheError",
    "handle_database_error",
    "safe_operation",
]
