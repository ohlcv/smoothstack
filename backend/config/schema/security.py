#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全配置验证

定义安全相关配置的验证规则
"""

from typing import List, Optional, Union
from enum import Enum
from pydantic import Field, validator
import re

from .base import ConfigSchema


class PasswordHashAlgorithm(str, Enum):
    """密码哈希算法枚举"""

    BCRYPT = "bcrypt"
    PBKDF2 = "pbkdf2"
    ARGON2 = "argon2"


class SecurityConfigSchema(ConfigSchema):
    """
    安全配置验证模式

    验证安全相关配置的类型和范围
    """

    secret_key: str = Field(..., description="应用密钥，用于签名和加密")  # 必填字段

    token_expire: int = Field(
        default=3600,  # 1小时
        ge=60,  # 至少1分钟
        le=86400 * 30,  # 最多30天
        description="令牌过期时间（秒）",
    )

    password_hash_algorithm: PasswordHashAlgorithm = Field(
        default=PasswordHashAlgorithm.BCRYPT, description="密码哈希算法"
    )

    allowed_hosts: List[str] = Field(default=["*"], description="允许的主机名列表")

    @validator("secret_key")
    def validate_secret_key(cls, v):
        """验证密钥强度"""
        if v == "your-secret-key-here":
            raise ValueError("请更改默认的密钥！此设置不适合生产环境。")

        if len(v) < 16:
            raise ValueError("密钥长度至少需要16个字符")

        return v

    @validator("allowed_hosts")
    def validate_allowed_hosts(cls, v):
        """验证允许的主机名列表"""
        if not v:
            raise ValueError("允许的主机名列表不能为空")

        # 如果包含通配符，不需要进一步验证
        if "*" in v:
            return v

        hostname_pattern = r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"

        for host in v:
            if (
                not re.match(hostname_pattern, host)
                and not re.match(ip_pattern, host)
                and host != "localhost"
            ):
                raise ValueError(f"主机名 '{host}' 格式无效")

        return v
