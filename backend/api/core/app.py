#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API应用模块

创建和配置FastAPI应用实例
"""

import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.database.errors import DatabaseError
from .settings import APISettings, get_settings
from .errors import APIError, handle_api_error

# 配置日志
logger = logging.getLogger("smoothstack.api.app")

# 全局应用实例
_app: Optional[FastAPI] = None


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例

    Returns:
        FastAPI应用实例
    """
    global _app
    if _app is not None:
        return _app

    # 获取API设置
    settings = get_settings()

    # 创建FastAPI实例
    app = FastAPI(
        debug=settings.debug,
        title=settings.docs.title,
        description=settings.docs.description,
        version=settings.docs.version,
        docs_url=settings.docs.docs_url if settings.docs.enable_docs else None,
        redoc_url=settings.docs.redoc_url if settings.docs.enable_docs else None,
        openapi_url=settings.docs.openapi_url if settings.docs.enable_docs else None,
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
        allow_credentials=settings.cors.allow_credentials,
        max_age=settings.cors.max_age,
    )

    # 注册错误处理器
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return await handle_api_error(request, exc)

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return await handle_api_error(request, exc)

    @app.exception_handler(DatabaseError)
    async def database_error_handler(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        return await handle_api_error(request, exc)

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return await handle_api_error(request, exc)

    # 注册启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行"""
        logger.info(
            "Starting API server",
            extra={
                "host": settings.host,
                "port": settings.port,
                "debug": settings.debug,
            },
        )

    # 注册关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行"""
        logger.info("Shutting down API server")

    # 保存全局实例
    _app = app
    return app


def get_app() -> FastAPI:
    """
    获取FastAPI应用实例

    如果应用实例不存在，则创建新实例

    Returns:
        FastAPI应用实例
    """
    if _app is None:
        return create_app()
    return _app
