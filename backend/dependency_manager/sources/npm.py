#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NPM源实现

实现对Node.js包管理器（NPM）的支持
"""

import logging
import time
import requests
from typing import Dict, Optional
from urllib.parse import urljoin

from .source import Source, SourceType, SourceStatus

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.sources.npm")


class NPMSource(Source):
    """NPM源"""

    def __init__(
        self,
        name: str,
        url: str,
        priority: int = 100,
        group: str = "global",
        enabled: bool = True,
        timeout: int = 30,
    ):
        """
        初始化NPM源

        Args:
            name: 源名称
            url: 源URL
            priority: 优先级（值越小优先级越高）
            group: 分组
            enabled: 是否启用
            timeout: 超时时间（秒）
        """
        super().__init__(name, url, SourceType.NPM, priority, group, enabled, timeout)

    def check_health(self) -> SourceStatus:
        """
        检查源的健康状态

        Returns:
            源状态
        """
        if not self.enabled:
            return SourceStatus.OFFLINE

        try:
            # 测试连接，使用a标签作为测试，它是一个很小的包
            start_time = time.time()
            test_url = urljoin(self.url, "react")
            response = requests.get(test_url, timeout=self.timeout)
            response_time = time.time() - start_time

            if response.status_code == 200:
                # 更新状态
                if response_time > 2.0:  # 如果响应时间超过2秒，认为是慢源
                    status = SourceStatus.SLOW
                else:
                    status = SourceStatus.ONLINE

                self.update_status(status, response_time)
                return status
            else:
                self.update_status(SourceStatus.ERROR)
                return SourceStatus.ERROR

        except requests.exceptions.Timeout:
            logger.warning(f"Source '{self.name}' timed out")
            self.update_status(SourceStatus.SLOW)
            return SourceStatus.SLOW

        except requests.exceptions.RequestException as e:
            logger.warning(f"Source '{self.name}' check failed: {e}")
            self.update_status(SourceStatus.OFFLINE)
            return SourceStatus.OFFLINE

    def get_package_url(self, package_name: str, version: Optional[str] = None) -> str:
        """
        获取包的URL

        Args:
            package_name: 包名
            version: 版本号

        Returns:
            包的URL
        """
        # 处理@开头的包名（作用域包）
        if package_name.startswith("@"):
            package_path = package_name.replace("@", "").replace("/", "%2F")
        else:
            package_path = package_name

        # 构建包URL
        base_url = urljoin(self.url, package_path)

        # 如果指定了版本，添加版本信息
        if version:
            return f"{base_url}/{version}"
        else:
            return base_url
