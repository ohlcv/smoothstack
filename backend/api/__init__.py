#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API服务模块

提供RESTful API接口、请求处理和响应格式化
"""

from .core.app import create_app, get_app
from .core.settings import APISettings, get_settings
from .core.responses import APIResponse, ErrorResponse, SuccessResponse
from .core.errors import APIError, handle_api_error

# 导出公共符号
__all__ = [
    "create_app",
    "get_app",
    "APISettings",
    "get_settings",
    "APIResponse",
    "ErrorResponse",
    "SuccessResponse",
    "APIError",
    "handle_api_error",
]
