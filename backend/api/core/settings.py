#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API设置模块

定义和管理API服务的配置选项
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

from backend.config import config

# 配置日志
logger = logging.getLogger("smoothstack.api.settings")


class CORSSettings(BaseModel):
    """CORS设置"""

    allow_origins: List[str] = Field(default=["*"], description="允许的源域名列表")
    allow_methods: List[str] = Field(default=["*"], description="允许的HTTP方法")
    allow_headers: List[str] = Field(default=["*"], description="允许的HTTP头")
    allow_credentials: bool = Field(default=False, description="是否允许携带凭证")
    max_age: int = Field(default=600, description="预检请求缓存时间(秒)")


class SecuritySettings(BaseModel):
    """安全设置"""

    secret_key: str = Field(..., description="用于JWT和加密的密钥")
    algorithm: str = Field(default="HS256", description="JWT算法")
    token_expire_minutes: int = Field(default=60 * 24, description="令牌过期时间(分钟)")
    password_bcrypt_rounds: int = Field(default=12, description="密码散列轮数")


class DocumentationSettings(BaseModel):
    """API文档设置"""

    title: str = Field(default="Smoothstack API", description="API标题")
    description: str = Field(
        default="Smoothstack量化交易平台API", description="API描述"
    )
    version: str = Field(default="0.1.0", description="API版本")
    docs_url: str = Field(default="/docs", description="文档URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc文档URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI模式URL")
    enable_docs: bool = Field(default=True, description="是否启用文档")


class RateLimitSettings(BaseModel):
    """速率限制设置"""

    enabled: bool = Field(default=True, description="是否启用速率限制")
    default_limit: int = Field(default=100, description="默认请求限制(每分钟)")
    default_window: int = Field(default=60, description="默认时间窗口(秒)")
    by_ip: bool = Field(default=True, description="是否按IP限制")


class APISettings(BaseModel):
    """API设置"""

    debug: bool = Field(default=False, description="是否为调试模式")
    host: str = Field(default="0.0.0.0", description="服务主机")
    port: int = Field(default=8000, description="服务端口")
    root_path: str = Field(default="", description="API根路径")
    prefix: str = Field(default="/api", description="API前缀")
    cors: CORSSettings = Field(default_factory=CORSSettings, description="CORS设置")
    security: SecuritySettings = Field(..., description="安全设置")
    docs: DocumentationSettings = Field(
        default_factory=DocumentationSettings, description="文档设置"
    )
    rate_limit: RateLimitSettings = Field(
        default_factory=RateLimitSettings, description="速率限制设置"
    )
    log_level: str = Field(default="INFO", description="日志级别")

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level. Must be one of: {', '.join(valid_levels)}"
            )
        return v.upper()


def get_settings() -> APISettings:
    """
    获取API设置

    从配置系统加载API设置

    Returns:
        API设置对象
    """
    # 从配置系统获取API配置
    api_config = config.get("api", {})

    # 处理安全设置
    security_config = api_config.get("security", {})
    if "secret_key" not in security_config:
        # 从环境变量获取密钥，如果不存在则使用配置文件中的默认值
        secret_key = config.get_secret("API_SECRET_KEY")
        if not secret_key:
            raise ValueError(
                "API secret key is not configured. Set API_SECRET_KEY environment variable."
            )
        security_config["secret_key"] = secret_key

    # 构建完整配置
    settings_data = {
        **api_config,
        "security": SecuritySettings(**security_config),
    }

    # 创建设置对象
    try:
        return APISettings(**settings_data)
    except Exception as e:
        logger.error(f"Failed to load API settings: {e}")
        raise
