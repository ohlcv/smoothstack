#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库错误处理模块

定义数据库相关的异常类和错误处理机制
"""

import logging
import traceback
from typing import Any, Dict, Optional, Type, Union

from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logger = logging.getLogger("smoothstack.database.errors")


class DatabaseError(Exception):
    """数据库错误基类"""

    def __init__(
        self,
        message: str,
        code: str = "DB_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        初始化数据库错误

        Args:
            message: 错误消息
            code: 错误代码
            details: 错误详情
            cause: 原始异常
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示

        Returns:
            错误信息字典
        """
        result: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "type": self.__class__.__name__,
        }

        if self.details:
            result["details"] = self.details

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def __str__(self) -> str:
        """字符串表示"""
        parts = [f"{self.code}: {self.message}"]

        if self.details:
            parts.append(f"Details: {self.details}")

        if self.cause:
            parts.append(f"Caused by: {self.cause}")

        return " | ".join(parts)


class ConnectionError(DatabaseError):
    """数据库连接错误"""

    def __init__(
        self,
        message: str = "Database connection error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, code="DB_CONNECTION_ERROR", details=details, cause=cause
        )


class QueryError(DatabaseError):
    """查询错误"""

    def __init__(
        self,
        message: str = "Query execution error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, code="DB_QUERY_ERROR", details=details, cause=cause
        )


class ValidationError(DatabaseError):
    """数据验证错误"""

    def __init__(
        self,
        message: str = "Data validation error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, code="DB_VALIDATION_ERROR", details=details, cause=cause
        )


class TransactionError(DatabaseError):
    """事务错误"""

    def __init__(
        self,
        message: str = "Transaction error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, code="DB_TRANSACTION_ERROR", details=details, cause=cause
        )


class CacheError(DatabaseError):
    """缓存错误"""

    def __init__(
        self,
        message: str = "Cache operation error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message, code="DB_CACHE_ERROR", details=details, cause=cause
        )


def handle_database_error(
    error: Exception,
    error_class: Optional[Type[DatabaseError]] = None,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    log_level: int = logging.ERROR,
) -> DatabaseError:
    """
    处理数据库错误

    Args:
        error: 原始错误
        error_class: 自定义错误类
        message: 自定义错误消息
        details: 错误详情
        log_level: 日志级别

    Returns:
        处理后的错误
    """
    # 如果已经是DatabaseError，直接返回
    if isinstance(error, DatabaseError):
        return error

    # 确定错误类型
    if error_class is None:
        error_class = DatabaseError

    # 创建错误详情
    error_details = details or {}
    error_details.update(
        {
            "traceback": traceback.format_exc(),
            "original_error": str(error),
        }
    )

    # 创建错误实例
    db_error = error_class(
        message=message or str(error), details=error_details, cause=error
    )

    # 记录日志
    logger.log(
        log_level,
        f"Database error occurred: {db_error}",
        exc_info=True,
        extra={"error_details": error_details},
    )

    return db_error


def safe_operation(operation_name: str):
    """
    安全操作装饰器

    用于包装数据库操作，提供统一的错误处理

    Args:
        operation_name: 操作名称

    Returns:
        装饰器函数
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                raise handle_database_error(
                    e,
                    message=f"Error during {operation_name}",
                    details={"operation": operation_name},
                )
            except DatabaseError:
                raise
            except Exception as e:
                raise handle_database_error(
                    e,
                    message=f"Unexpected error during {operation_name}",
                    details={"operation": operation_name},
                )

        return wrapper

    return decorator
