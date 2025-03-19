#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库配置验证

定义数据库配置的验证规则
"""

from typing import Optional, Union
from pydantic import Field, validator
import re

from .base import ConfigSchema


class DatabaseConfigSchema(ConfigSchema):
    """
    数据库配置验证模式

    验证数据库配置的类型和范围
    """

    url: str = Field(..., description="数据库连接URL")  # 必填字段

    pool_size: int = Field(default=5, ge=1, le=100, description="连接池大小")

    max_overflow: int = Field(
        default=10, ge=0, le=200, description="允许的最大连接数超出"
    )

    echo: bool = Field(default=False, description="是否回显SQL语句")

    @validator("url")
    def validate_url(cls, v):
        """验证数据库URL格式"""
        # SQLite URL格式验证
        if v.startswith("sqlite:"):
            return v

        # 其他数据库URL格式验证（PostgreSQL、MySQL等）
        valid_db_url = re.match(
            r"^(postgresql|mysql|oracle|mssql)(\+[a-z]+)?://([^:]+)(:[^@]+)?@[^/]+(:[0-9]+)?/[^?]+(\\?.+)?$",
            v,
        )

        if not valid_db_url:
            raise ValueError(
                "数据库URL格式无效。正确格式示例：\n"
                "- sqlite:///path/to/db.sqlite\n"
                "- postgresql://user:password@localhost:5432/dbname\n"
                "- mysql://user:password@localhost:3306/dbname"
            )

        return v
