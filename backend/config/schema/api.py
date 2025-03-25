#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API配置验证

定义API配置的验证规则
"""

from typing import List, Optional, Union
from pydantic import Field, validator
import re

from .base import ConfigSchema


class ApiConfigSchema(ConfigSchema):
    """
    API配置验证模式

    验证API配置的类型和范围
    """

    host: str = Field(default="0.0.0.0", description="API服务器主机地址")

    port: int = Field(default=5000, ge=1, le=65535, description="API服务器端口")

    debug: bool = Field(default=False, description="是否启用API调试模式")

    cors_origins: List[str] = Field(default=["*"], description="允许的CORS源列表")

    rate_limit: int = Field(default=100, ge=1, description="API请求速率限制（每分钟）")

    @validator("host")
    def validate_host(cls, v):
        """验证主机地址格式"""
        # IP地址格式验证
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        # 主机名格式验证
        hostname_pattern = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"

        if (
            v != "0.0.0.0"
            and v != "localhost"
            and not re.match(ip_pattern, v)
            and not re.match(hostname_pattern, v)
        ):
            raise ValueError(
                "主机地址格式无效。应为IP地址、主机名、'localhost'或'0.0.0.0'"
            )

        return v

    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        """验证CORS源列表"""
        if "*" in v and len(v) > 1:
            raise ValueError("如果包含通配符'*'，则CORS源列表不应包含其他项")

        for origin in v:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"CORS源 '{origin}' 必须以 'http://' 或 'https://' 开头"
                )

        return v
