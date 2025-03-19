#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyPI源实现

实现对Python包索引（PyPI）的支持
"""

import logging
import time
import requests
from typing import Dict, Optional
from urllib.parse import urljoin

from .source import Source, SourceType, SourceStatus

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.sources.pypi")


class PyPISource(Source):
    """PyPI源"""

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
        初始化PyPI源

        Args:
            name: 源名称
            url: 源URL
            priority: 优先级（值越小优先级越高）
            group: 分组
            enabled: 是否启用
            timeout: 超时时间（秒）
        """
        super().__init__(name, url, SourceType.PYPI, priority, group, enabled, timeout)

    def check_health(self) -> SourceStatus:
        """
        检查源的健康状态

        Returns:
            源状态
        """
        if not self.enabled:
            return SourceStatus.OFFLINE

        try:
            # 测试连接
            start_time = time.time()
            test_url = urljoin(self.url, "pip")  # 使用pip包作为测试
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
        # 构建包URL
        base_url = urljoin(self.url, package_name)

        # 如果指定了版本，添加版本信息
        if version:
            return f"{base_url}/{package_name}-{version}.tar.gz"
        else:
            return base_url
