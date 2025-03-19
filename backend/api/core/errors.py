#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API错误处理模块

定义API错误类型和处理方法
"""

import logging
from typing import Any, Dict, Optional, Type, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.database.errors import DatabaseError
from .responses import ErrorResponse

# 配置日志
logger = logging.getLogger("smoothstack.api.errors")


class APIError(Exception):
    """API错误基类"""

    def __init__(
        self,
        message: str,
        error_code: str = "API_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class ValidationAPIError(APIError):
    """验证错误"""

    def __init__(
        self,
        message: str = "数据验证失败",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class AuthenticationError(APIError):
    """认证错误"""

    def __init__(
        self,
        message: str = "认证失败",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class AuthorizationError(APIError):
    """授权错误"""

    def __init__(
        self,
        message: str = "权限不足",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundError(APIError):
    """资源不存在错误"""

    def __init__(
        self,
        message: str = "资源不存在",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class RateLimitError(APIError):
    """速率限制错误"""

    def __init__(
        self,
        message: str = "请求过于频繁",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


async def handle_api_error(
    request: Request,
    exc: Union[APIError, HTTPException, ValidationError, DatabaseError, Exception],
) -> JSONResponse:
    """
    统一API错误处理

    Args:
        request: FastAPI请求对象
        exc: 异常对象

    Returns:
        JSON格式的错误响应
    """
    # 获取请求路径
    path = request.url.path

    # 处理不同类型的错误
    if isinstance(exc, APIError):
        response = ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
            detail=exc.detail,
            path=path,
        )
        status_code = exc.status_code

    elif isinstance(exc, HTTPException):
        response = ErrorResponse(
            message=str(exc.detail),
            error_code="HTTP_ERROR",
            detail={"status_code": exc.status_code},
            path=path,
        )
        status_code = exc.status_code

    elif isinstance(exc, ValidationError):
        response = ErrorResponse(
            message="数据验证失败",
            error_code="VALIDATION_ERROR",
            detail={"errors": exc.errors()},
            path=path,
        )
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    elif isinstance(exc, DatabaseError):
        response = ErrorResponse(
            message=str(exc),
            error_code="DATABASE_ERROR",
            detail=getattr(exc, "detail", None),
            path=path,
        )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    else:
        # 处理未预期的错误
        logger.exception("Unexpected error occurred")
        response = ErrorResponse(
            message="服务器内部错误",
            error_code="INTERNAL_SERVER_ERROR",
            detail={"type": type(exc).__name__},
            path=path,
        )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # 记录错误日志
    logger.error(
        f"API Error: {response.error_code} - {response.message}",
        extra={
            "path": path,
            "status_code": status_code,
            "detail": response.detail,
        },
    )

    return JSONResponse(
        status_code=status_code,
        content=response.dict(),
    )
