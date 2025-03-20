"""
平台相关的工具函数
"""

import os
import sys
from pathlib import Path
from typing import Optional


def is_windows() -> bool:
    """
    检查是否为Windows系统。

    Returns:
        bool: 如果是Windows系统则返回True
    """
    return sys.platform == "win32"


def is_macos() -> bool:
    """
    检查是否为macOS系统。

    Returns:
        bool: 如果是macOS系统则返回True
    """
    return sys.platform == "darwin"


def is_linux() -> bool:
    """
    检查是否为Linux系统。

    Returns:
        bool: 如果是Linux系统则返回True
    """
    return sys.platform.startswith("linux")


def is_wsl() -> bool:
    """
    检查是否在WSL环境中运行。

    Returns:
        bool: 如果在WSL中运行则返回True
    """
    if not is_linux():
        return False

    # 检查/proc/version文件内容
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except:
        return False


def get_home_dir() -> Path:
    """
    获取用户主目录路径。

    Returns:
        Path: 用户主目录的路径
    """
    # 首先尝试使用标准环境变量
    home = os.environ.get("HOME")
    if home:
        return Path(home)

    # Windows系统使用USERPROFILE
    if is_windows():
        home = os.environ.get("USERPROFILE")
        if home:
            return Path(home)

    # 如果都失败了，使用当前用户的主目录
    return Path.home()


def get_config_dir() -> Path:
    """
    获取配置文件目录路径。

    Returns:
        Path: 配置文件目录的路径
    """
    if is_windows():
        # Windows: %APPDATA%\smoothstack
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "smoothstack"
        return get_home_dir() / "AppData" / "Roaming" / "smoothstack"

    # Unix-like系统: ~/.config/smoothstack
    return get_home_dir() / ".config" / "smoothstack"


def get_cache_dir() -> Path:
    """
    获取缓存目录路径。

    Returns:
        Path: 缓存目录的路径
    """
    if is_windows():
        # Windows: %LOCALAPPDATA%\smoothstack\cache
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / "smoothstack" / "cache"
        return get_home_dir() / "AppData" / "Local" / "smoothstack" / "cache"

    # Unix-like系统: ~/.cache/smoothstack
    return get_home_dir() / ".cache" / "smoothstack"


def get_data_dir() -> Path:
    """
    获取数据目录路径。

    Returns:
        Path: 数据目录的路径
    """
    if is_windows():
        # Windows: %LOCALAPPDATA%\smoothstack\data
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / "smoothstack" / "data"
        return get_home_dir() / "AppData" / "Local" / "smoothstack" / "data"

    # Unix-like系统: ~/.local/share/smoothstack
    return get_home_dir() / ".local" / "share" / "smoothstack"


def get_temp_dir() -> Path:
    """
    获取临时目录路径。

    Returns:
        Path: 临时目录的路径
    """
    import tempfile

    return Path(tempfile.gettempdir()) / "smoothstack"


def ensure_dir(path: Path) -> None:
    """
    确保目录存在，如果不存在则创建。

    Args:
        path: 要确保存在的目录路径
    """
    path.mkdir(parents=True, exist_ok=True)


def get_executable_suffix() -> str:
    """
    获取可执行文件后缀。

    Returns:
        str: Windows返回'.exe'，其他系统返回空字符串
    """
    return ".exe" if is_windows() else ""
