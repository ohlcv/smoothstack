"""
版本更新检查工具模块，提供CLI工具版本检查和更新通知
"""

__version__ = "1.0.0"  # 统一版本定义（自动同步到各子系统）

import re
import os
import sys
import json
import tempfile
import subprocess
from typing import Dict, Any, Optional, Tuple, List, cast
from pathlib import Path
from datetime import datetime, timedelta
import platform
import urllib.request
import urllib.error
from urllib.parse import urlparse
import ssl

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from .logger import get_logger
from .errors import UserError, NetworkError

# 创建日志记录器
logger = get_logger("version")

# 创建控制台实例
console = Console()

# 当前版本（从模块变量获取）


# 版本检查URL
VERSION_CHECK_URL = (
    "https://api.github.com/repos/smoothstack/smoothstack-cli/releases/latest"
)

# 备用版本检查URL
BACKUP_VERSION_CHECK_URL = (
    "https://gitee.com/api/v5/repos/smoothstack/smoothstack-cli/releases/latest"
)

# 版本检查缓存文件名
VERSION_CACHE_FILE = ".version_check"

# 缓存有效期（小时）
CACHE_VALID_HOURS = 24


class Version:
    """版本对象，用于版本比较"""

    def __init__(self, version_str: str):
        """
        初始化版本对象

        Args:
            version_str: 版本字符串，如"1.0.0"
        """
        self.version_str = version_str.strip()
        self.parts = self._parse_version(self.version_str)

    def _parse_version(self, version_str: str) -> List[int]:
        """
        解析版本字符串为数字列表

        Args:
            version_str: 版本字符串

        Returns:
            包含版本各部分的数字列表
        """
        # 去除前缀"v"（如果存在）
        if version_str.startswith("v"):
            version_str = version_str[1:]

        # 分割版本号，使用正则表达式兼容各种格式
        parts = re.findall(r"\d+", version_str)

        # 转换为整数列表，确保至少有三个部分
        result = [int(p) for p in parts] + [0, 0, 0]
        return result[:3]

    def __str__(self) -> str:
        """返回版本字符串"""
        return self.version_str

    def __eq__(self, other: object) -> bool:
        """判断版本是否相等"""
        if not isinstance(other, Version):
            return NotImplemented
        return self.parts == other.parts

    def __lt__(self, other: "Version") -> bool:
        """判断版本是否小于另一个版本"""
        for i in range(len(self.parts)):
            if self.parts[i] < other.parts[i]:
                return True
            elif self.parts[i] > other.parts[i]:
                return False
        return False

    def __gt__(self, other: "Version") -> bool:
        """判断版本是否大于另一个版本"""
        return other < self

    def __le__(self, other: "Version") -> bool:
        """判断版本是否小于等于另一个版本"""
        return self < other or self == other

    def __ge__(self, other: "Version") -> bool:
        """判断版本是否大于等于另一个版本"""
        return self > other or self == other


def _get_cache_file_path() -> Path:
    """
    获取版本缓存文件路径

    Returns:
        版本缓存文件路径
    """
    # 获取用户家目录
    home_dir = Path.home()
    # 创建.smoothstack目录（如果不存在）
    ss_dir = home_dir / ".smoothstack"
    ss_dir.mkdir(exist_ok=True)
    # 缓存文件
    return ss_dir / VERSION_CACHE_FILE


def _read_cache() -> Optional[Dict[str, Any]]:
    """
    读取版本缓存信息

    Returns:
        缓存信息字典，如果缓存不存在或无效则返回None
    """
    cache_file = _get_cache_file_path()
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))

        # 验证缓存数据格式
        if (
            not isinstance(data, dict)
            or "timestamp" not in data
            or "version" not in data
        ):
            logger.warning("缓存数据格式无效")
            return None

        # 检查缓存时间是否有效
        timestamp = datetime.fromisoformat(data["timestamp"])
        now = datetime.now()
        if now - timestamp > timedelta(hours=CACHE_VALID_HOURS):
            logger.debug("缓存已过期")
            return None

        return data
    except Exception as e:
        logger.warning(f"读取缓存文件失败: {e}")
        return None


def _write_cache(version_info: Dict[str, Any]) -> None:
    """
    写入版本缓存信息

    Args:
        version_info: 版本信息字典
    """
    cache_file = _get_cache_file_path()

    # 添加时间戳
    cache_data = version_info.copy()
    cache_data["timestamp"] = datetime.now().isoformat()

    try:
        cache_file.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.debug(f"版本信息已缓存到 {cache_file}")
    except Exception as e:
        logger.warning(f"写入缓存文件失败: {e}")


def _http_get(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    发送HTTP GET请求并返回JSON响应

    Args:
        url: API URL
        timeout: 超时时间（秒）

    Returns:
        JSON响应数据，请求失败则返回None
    """
    logger.debug(f"发送HTTP请求: {url}")

    headers = {
        "User-Agent": f"SmoothstackCLI/{__version__} ({platform.system()} {platform.version()})"
    }

    try:
        # 创建请求对象
        req = urllib.request.Request(url, headers=headers)

        # 设置SSL上下文
        ctx = ssl.create_default_context()

        # 发送请求
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            if response.status != 200:
                logger.warning(f"HTTP请求失败: 状态码 {response.status}")
                return None

            # 解析响应
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)

    except urllib.error.URLError as e:
        logger.warning(f"网络请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"解析JSON响应失败: {e}")
        return None
    except Exception as e:
        logger.warning(f"HTTP请求异常: {e}")
        return None


def _fetch_latest_version() -> Dict[str, Any]:
    """
    获取最新版本信息

    Returns:
        最新版本信息字典

    Raises:
        NetworkError: 网络请求失败
    """
    # 尝试从主要源获取
    data = _http_get(VERSION_CHECK_URL)

    # 主要源失败时，尝试备用源
    if data is None:
        logger.warning(f"从主要源获取版本信息失败，尝试备用源")
        data = _http_get(BACKUP_VERSION_CHECK_URL)

    if data is None:
        # 从缓存中读取
        cache_data = _read_cache()
        if cache_data:
            logger.info("使用缓存的版本信息")
            return cache_data

        # 如果无法获取版本信息，抛出异常
        raise NetworkError("无法获取版本信息", "请检查网络连接或稍后再试")

    # 解析版本信息
    version_info = {
        "version": data.get("tag_name", "").lstrip("v"),
        "name": data.get("name", ""),
        "url": data.get("html_url", ""),
        "published_at": data.get("published_at", ""),
        "body": data.get("body", ""),
    }

    # 写入缓存
    _write_cache(version_info)

    return version_info


def check_for_updates(
    show_current: bool = False, force: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    检查是否有更新可用

    Args:
        show_current: 是否显示当前版本信息（即使没有更新）
        force: 是否强制检查（忽略缓存）

    Returns:
        (是否有更新, 最新版本信息)

    Raises:
        NetworkError: 网络请求失败
    """
    try:
        # 获取当前版本
        current_version = Version(__version__)

        # 从缓存读取版本信息（如果不是强制检查）
        if not force:
            cache_data = _read_cache()
            if cache_data:
                latest_version = Version(cache_data["version"])
                if latest_version > current_version:
                    return True, cache_data
                elif show_current:
                    return False, cache_data

        # 获取最新版本信息
        latest_info = _fetch_latest_version()
        latest_version = Version(latest_info["version"])

        # 比较版本
        has_update = latest_version > current_version

        return has_update, latest_info

    except Exception as e:
        logger.error(f"检查更新失败: {e}")
        if isinstance(e, NetworkError):
            raise
        raise UserError("检查更新失败", f"发生错误: {str(e)}")


def display_update_info(version_info: Dict[str, Any], has_update: bool) -> None:
    """
    显示更新信息

    Args:
        version_info: 版本信息字典
        has_update: 是否有更新
    """
    # 解析发布日期
    published_at = version_info.get("published_at", "")
    if published_at:
        try:
            # 格式化日期
            published_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            published_str = published_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            published_str = published_at
    else:
        published_str = "未知"

    # 创建表格
    table = Table(title="版本信息")
    table.add_column("项目", style="cyan")
    table.add_column("内容", style="green")

    table.add_row("当前版本", __version__)
    table.add_row("最新版本", version_info.get("version", "未知"))
    table.add_row("发布时间", published_str)
    table.add_row("发布名称", version_info.get("name", ""))
    table.add_row("发布地址", version_info.get("url", ""))

    # 显示表格
    console.print(table)

    # 显示更新内容
    release_notes = version_info.get("body", "")
    if release_notes:
        console.print(Panel("更新内容", style="yellow"))
        console.print(Markdown(release_notes))

    # 显示更新提示
    if has_update:
        console.print(
            Panel(
                f"发现新版本 {version_info.get('version')}，请使用包管理器更新或访问发布地址下载最新版本",
                style="bold green",
            )
        )
    else:
        console.print(Panel(f"当前已是最新版本 {__version__}", style="bold blue"))
