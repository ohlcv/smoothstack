#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖源模型

定义依赖源的基本接口和属性
"""

import logging
import time
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.sources")


class SourceType(Enum):
    """源类型"""

    PYPI = auto()  # Python包索引
    NPM = auto()  # Node.js包管理器
    MAVEN = auto()  # Java包管理器
    CUSTOM = auto()  # 自定义源


class SourceStatus(Enum):
    """源状态"""

    UNKNOWN = auto()  # 未知状态
    ONLINE = auto()  # 在线可用
    OFFLINE = auto()  # 离线不可用
    SLOW = auto()  # 响应缓慢
    ERROR = auto()  # 出错状态


class Source(ABC):
    """依赖源抽象基类"""

    def __init__(
        self,
        name: str,
        url: str,
        source_type: SourceType,
        priority: int = 100,
        group: str = "global",
        enabled: bool = True,
        timeout: int = 30,
    ):
        """
        初始化源

        Args:
            name: 源名称
            url: 源URL
            source_type: 源类型
            priority: 优先级（值越小优先级越高）
            group: 分组
            enabled: 是否启用
            timeout: 超时时间（秒）
        """
        self.name = name
        self.url = url
        self.type = source_type
        self.priority = priority
        self.group = group
        self.enabled = enabled
        self.timeout = timeout

        # 状态信息
        self.status = SourceStatus.UNKNOWN
        self.last_check_time = 0
        self.last_response_time = 0
        self.error_count = 0
        self.success_count = 0

    def __str__(self) -> str:
        return f"{self.name} ({self.url})"

    def __repr__(self) -> str:
        return f"Source(name='{self.name}', url='{self.url}', type={self.type}, enabled={self.enabled})"

    @abstractmethod
    def check_health(self) -> SourceStatus:
        """
        检查源的健康状态

        Returns:
            源状态
        """
        pass

    @abstractmethod
    def get_package_url(self, package_name: str, version: Optional[str] = None) -> str:
        """
        获取包的URL

        Args:
            package_name: 包名
            version: 版本号

        Returns:
            包的URL
        """
        pass

    def update_status(self, status: SourceStatus, response_time: float = 0):
        """
        更新源状态

        Args:
            status: 新状态
            response_time: 响应时间(秒)
        """
        self.status = status
        self.last_check_time = time.time()

        if response_time > 0:
            self.last_response_time = response_time

        if status == SourceStatus.ONLINE:
            self.success_count += 1
        elif status in (SourceStatus.OFFLINE, SourceStatus.ERROR):
            self.error_count += 1

        logger.debug(f"Source '{self.name}' status updated to {status.name}")

    def get_status_dict(self) -> Dict[str, Any]:
        """
        获取源的状态信息

        Returns:
            状态信息字典
        """
        return {
            "name": self.name,
            "url": self.url,
            "type": self.type.name,
            "status": self.status.name,
            "priority": self.priority,
            "group": self.group,
            "enabled": self.enabled,
            "last_check_time": self.last_check_time,
            "last_response_time": self.last_response_time,
            "error_count": self.error_count,
            "success_count": self.success_count,
        }

    def is_available(self) -> bool:
        """
        检查源是否可用

        Returns:
            是否可用
        """
        if not self.enabled:
            return False

        # 如果状态未知或最后检查时间超过1小时，重新检查健康状态
        if (
            self.status == SourceStatus.UNKNOWN
            or time.time() - self.last_check_time > 3600
        ):
            self.check_health()

        return self.status == SourceStatus.ONLINE

    def enable(self):
        """启用源"""
        self.enabled = True
        logger.info(f"Source '{self.name}' enabled")

    def disable(self):
        """禁用源"""
        self.enabled = False
        logger.info(f"Source '{self.name}' disabled")
