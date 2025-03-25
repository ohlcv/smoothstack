#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用配置验证

定义应用基本配置的验证规则
"""

from typing import Optional
from enum import Enum
from pydantic import Field, validator

from .base import ConfigSchema


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppConfigSchema(ConfigSchema):
    """
    应用配置验证模式

    验证应用基本配置的类型和范围
    """

    name: str = Field(default="smoothstack", description="应用名称")

    version: str = Field(default="0.1.0", description="应用版本")

    debug: bool = Field(default=False, description="是否启用调试模式")

    log_level: LogLevel = Field(default=LogLevel.INFO, description="应用日志级别")

    @validator("name")
    def validate_name(cls, v):
        """验证应用名称"""
        if not v or not v.strip():
            raise ValueError("应用名称不能为空")
        return v

    @validator("version")
    def validate_version(cls, v):
        """验证应用版本"""
        import re

        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("应用版本必须符合语义化版本格式（例如：1.0.0）")
        return v
