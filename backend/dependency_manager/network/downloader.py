#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载器

实现文件下载和网络资源获取，支持断点续传、重试和超时设置
"""

import os
import time
import logging
import hashlib
import tempfile
import requests
from typing import Dict, Optional, Any, Callable, Tuple
from urllib.parse import urlparse

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.network")


class Downloader:
    """文件下载器"""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5,
        progress_callback: Optional[Callable[[float, float], None]] = None,
    ):
        """
        初始化下载器

        Args:
            timeout: 超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            progress_callback: 进度回调函数(当前大小, 总大小)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "smoothstack-dependency-manager/1.0"}
        )

    def download_file(
        self,
        url: str,
        destination: Optional[str] = None,
        overwrite: bool = False,
        validate_checksum: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str]:
        """
        下载文件

        Args:
            url: 文件URL
            destination: 目标路径，None则自动生成临时文件
            overwrite: 是否覆盖已存在的文件
            validate_checksum: 校验和信息，格式为{'algorithm': 'checksum'}

        Returns:
            (是否成功, 文件路径)
        """
        # 如果未指定目标路径，生成临时文件
        if destination is None:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = "download.tmp"
            temp_dir = tempfile.gettempdir()
            destination = os.path.join(temp_dir, filename)
            logger.debug(f"Generated temporary file path: {destination}")

        # 如果文件已存在且不覆盖，则直接返回
        if os.path.exists(destination) and not overwrite:
            logger.debug(f"File already exists and overwrite=False: {destination}")

            # 如果需要验证校验和
            if validate_checksum:
                if self._validate_file_checksum(destination, validate_checksum):
                    logger.debug(f"Existing file checksum validated: {destination}")
                    return True, destination
                else:
                    logger.warning(
                        f"Existing file failed checksum validation: {destination}"
                    )
                    if not overwrite:
                        return False, destination
            else:
                return True, destination

        # 创建目标目录
        os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)

        # 获取文件信息，支持断点续传
        file_size = 0
        headers = {}

        try:
            response = self.session.head(url, timeout=self.timeout)
            response.raise_for_status()

            if "content-length" in response.headers:
                file_size = int(response.headers["content-length"])

            # 检查是否支持断点续传
            accept_ranges = response.headers.get("accept-ranges", "")
            if accept_ranges == "bytes" and os.path.exists(destination) and overwrite:
                current_size = os.path.getsize(destination)
                if current_size < file_size:
                    headers["Range"] = f"bytes={current_size}-"
                    logger.debug(f"Resuming download from byte {current_size}")
                else:
                    # 文件已完整下载
                    logger.debug(f"File already fully downloaded: {destination}")

                    # 验证校验和
                    if validate_checksum:
                        if self._validate_file_checksum(destination, validate_checksum):
                            return True, destination
                        else:
                            logger.warning(
                                f"File failed checksum validation, redownloading: {destination}"
                            )
                            current_size = 0
                    else:
                        return True, destination
        except Exception as e:
            logger.warning(f"Failed to get file info: {e}")
            headers = {}

        # 下载文件
        retries = 0
        success = False

        while retries <= self.max_retries and not success:
            if retries > 0:
                logger.info(f"Retry #{retries} after {self.retry_delay}s delay")
                time.sleep(self.retry_delay)

            try:
                mode = "ab" if "Range" in headers else "wb"

                # 发送请求
                with self.session.get(
                    url, headers=headers, stream=True, timeout=self.timeout
                ) as response:
                    response.raise_for_status()

                    # 获取文件总大小
                    if "content-length" in response.headers:
                        file_size = int(response.headers["content-length"])

                        if "Range" in headers:
                            # 对于断点续传，需要加上已下载的大小
                            file_size += int(
                                headers["Range"].split("=")[1].split("-")[0]
                            )

                    # 写入文件
                    with open(destination, mode) as f:
                        downloaded_size = (
                            int(
                                headers.get("Range", "bytes=0-")
                                .split("=")[1]
                                .split("-")[0]
                            )
                            if "Range" in headers
                            else 0
                        )
                        chunk_size = 8192

                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)

                                # 调用进度回调
                                if self.progress_callback and file_size > 0:
                                    self.progress_callback(downloaded_size, file_size)

                # 下载成功
                success = True
                logger.info(f"Downloaded file: {url} -> {destination}")

                # 验证校验和
                if validate_checksum:
                    if not self._validate_file_checksum(destination, validate_checksum):
                        logger.error(f"File failed checksum validation: {destination}")
                        success = False

            except requests.RequestException as e:
                logger.warning(f"Download failed: {e}")
                retries += 1

                # 检查文件是否部分下载，以便断点续传
                if os.path.exists(destination):
                    current_size = os.path.getsize(destination)
                    if current_size > 0:
                        headers["Range"] = f"bytes={current_size}-"
                        logger.debug(f"Will resume from byte {current_size} on retry")

        return success, destination

    def _validate_file_checksum(
        self, file_path: str, checksum_info: Dict[str, str]
    ) -> bool:
        """
        验证文件校验和

        Args:
            file_path: 文件路径
            checksum_info: 校验和信息，格式为{'algorithm': 'checksum'}

        Returns:
            校验结果
        """
        for algorithm, expected_checksum in checksum_info.items():
            if algorithm not in hashlib.algorithms_available:
                logger.warning(f"Unsupported hash algorithm: {algorithm}")
                continue

            try:
                hash_obj = hashlib.new(algorithm)

                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_obj.update(chunk)

                actual_checksum = hash_obj.hexdigest()

                if actual_checksum.lower() != expected_checksum.lower():
                    logger.warning(
                        f"Checksum mismatch for {file_path} using {algorithm}: "
                        f"expected {expected_checksum}, got {actual_checksum}"
                    )
                    return False

                logger.debug(f"Checksum validated for {file_path} using {algorithm}")
                return True

            except Exception as e:
                logger.error(f"Error validating checksum: {e}")
                return False

        # 如果没有可用的校验算法
        logger.warning(f"No valid checksum algorithms provided for {file_path}")
        return False

    def fetch_url(self, url: str, as_json: bool = False) -> Tuple[bool, Any]:
        """
        获取URL内容

        Args:
            url: URL
            as_json: 是否解析为JSON

        Returns:
            (是否成功, 内容)
        """
        retries = 0

        while retries <= self.max_retries:
            if retries > 0:
                logger.info(f"Retry #{retries} after {self.retry_delay}s delay")
                time.sleep(self.retry_delay)

            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                if as_json:
                    return True, response.json()
                else:
                    return True, response.text

            except requests.RequestException as e:
                logger.warning(f"Failed to fetch URL {url}: {e}")
                retries += 1

        return False, None

    def check_url_availability(
        self, url: str, timeout: Optional[int] = None
    ) -> Tuple[bool, int]:
        """
        检查URL可用性

        Args:
            url: URL
            timeout: 超时时间，默认使用实例超时

        Returns:
            (是否可用, 响应时间(ms))
        """
        timeout = timeout or self.timeout

        try:
            start_time = time.time()
            response = self.session.head(url, timeout=timeout)
            end_time = time.time()

            response_time_ms = int((end_time - start_time) * 1000)

            if response.status_code < 400:
                logger.debug(
                    f"URL {url} is available, response time: {response_time_ms}ms"
                )
                return True, response_time_ms
            else:
                logger.debug(f"URL {url} returned status code {response.status_code}")
                return False, response_time_ms

        except requests.RequestException as e:
            logger.debug(f"URL {url} is not available: {e}")
            return False, 0
