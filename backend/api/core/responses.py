#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API响应模块

定义API响应的标准格式和处理方法
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """API响应基类"""

    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class ErrorResponse(APIResponse):
    """错误响应"""

    success: bool = False
    error_code: str = Field(default="UNKNOWN_ERROR", description="错误代码")
    detail: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    path: Optional[str] = Field(default=None, description="请求路径")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "操作失败",
                "error_code": "VALIDATION_ERROR",
                "detail": {"field": "username", "reason": "Value is required"},
                "timestamp": "2023-03-25T10:30:45.123456",
                "path": "/api/v1/users",
            }
        }


class DataResponse(APIResponse):
    """带数据的成功响应"""

    success: bool = True
    data: Any = Field(..., description="响应数据")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "获取成功",
                "data": {"id": 1, "name": "示例用户", "email": "user@example.com"},
                "timestamp": "2023-03-25T10:30:45.123456",
            }
        }


class PageInfo(BaseModel):
    """分页信息"""

    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")


class PageResponse(APIResponse):
    """分页响应"""

    success: bool = True
    data: List[Any] = Field(default_factory=list, description="分页数据")
    pagination: PageInfo = Field(..., description="分页信息")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "获取成功",
                "data": [{"id": 1, "name": "示例1"}, {"id": 2, "name": "示例2"}],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 50,
                    "total_pages": 5,
                },
                "timestamp": "2023-03-25T10:30:45.123456",
            }
        }


class SuccessResponse(APIResponse):
    """简单成功响应"""

    success: bool = True

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "timestamp": "2023-03-25T10:30:45.123456",
            }
        }


# 类型别名
ResponseType = Union[ErrorResponse, DataResponse, PageResponse, SuccessResponse]


def create_response(
    success: bool = True,
    message: str = "",
    data: Any = None,
    error_code: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
    pagination: Optional[Dict[str, int]] = None,
) -> ResponseType:
    """
    创建标准API响应

    Args:
        success: 是否成功
        message: 响应消息
        data: 响应数据
        error_code: 错误代码
        detail: 错误详情
        path: 请求路径
        pagination: 分页信息

    Returns:
        标准格式的API响应
    """
    if not success:
        return ErrorResponse(
            message=message,
            error_code=error_code or "UNKNOWN_ERROR",
            detail=detail,
            path=path,
        )

    if pagination is not None and isinstance(data, list):
        return PageResponse(
            message=message,
            data=data,
            pagination=PageInfo(**pagination),
        )

    if data is not None:
        return DataResponse(
            message=message,
            data=data,
        )

    return SuccessResponse(message=message)
