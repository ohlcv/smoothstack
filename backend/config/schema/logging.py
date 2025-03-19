#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志配置验证

定义日志配置的验证规则
"""

from typing import Optional
from enum import Enum
from pydantic import Field, validator
import os

from .base import ConfigSchema


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfigSchema(ConfigSchema):
    """
    日志配置验证模式

    验证日志配置的类型和范围
    """

    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")

    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式",
    )

    file: Optional[str] = Field(default=None, description="日志文件路径")

    max_size: int = Field(
        default=10485760,  # 10MB
        ge=1024,  # 至少1KB
        description="日志文件最大大小（字节）",
    )

    backup_count: int = Field(
        default=5, ge=0, le=100, description="保留的日志文件备份数量"
    )

    @validator("file")
    def validate_log_file(cls, v):
        """验证日志文件路径"""
        if not v:
            return v

        # 检查目录是否存在或可创建
        log_dir = os.path.dirname(v)
        if log_dir and not os.path.exists(log_dir):
            try:
                # 尝试创建日志目录
                os.makedirs(log_dir, exist_ok=True)
            except (IOError, OSError) as e:
                raise ValueError(f"无法创建日志目录 '{log_dir}': {str(e)}")

        # 检查文件是否可写
        try:
            if os.path.exists(v):
                # 文件已存在，检查是否可写
                if not os.access(v, os.W_OK):
                    raise ValueError(f"日志文件 '{v}' 不可写")
            else:
                # 文件不存在，尝试创建
                with open(v, "a"):
                    pass
                # 创建成功后删除空文件
                os.remove(v)
        except (IOError, OSError) as e:
            raise ValueError(f"无法写入日志文件 '{v}': {str(e)}")

        return v
