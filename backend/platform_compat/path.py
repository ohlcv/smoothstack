"""
路径处理模块

提供跨平台的路径处理功能，处理Windows和Unix系统的路径差异。
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Union, List


def normalize_path(path: Union[str, Path]) -> str:
    """
    标准化路径，确保路径分隔符在不同平台上一致

    Args:
        path: 需要标准化的路径

    Returns:
        标准化后的路径字符串
    """
    # 转换为Path对象
    if isinstance(path, str):
        path = Path(path)

    # 转换为标准形式
    normalized = str(path.resolve())

    # 在Windows上，将反斜杠转换为正斜杠
    if sys.platform == "win32":
        normalized = normalized.replace("\\", "/")

    return normalized


def get_executable_path(name: str) -> str:
    """
    获取可执行文件的完整路径，自动处理平台差异（如Windows上的.exe后缀）

    Args:
        name: 可执行文件名称

    Returns:
        可执行文件的完整路径
    """
    if sys.platform == "win32":
        # Windows上检查多个可能的后缀
        for ext in [".exe", ".cmd", ".bat", ".ps1"]:
            if name.lower().endswith(ext.lower()):
                return name

            # 在PATH中查找带后缀的可执行文件
            executable = _find_executable(name + ext)
            if executable:
                return executable

        # 如果没有找到带后缀的版本，返回原始名称
        return name
    else:
        # Unix系统直接返回名称
        return name


def _find_executable(name: str) -> Optional[str]:
    """
    在PATH环境变量中查找可执行文件

    Args:
        name: 可执行文件名称

    Returns:
        可执行文件的完整路径，如果未找到则返回None
    """
    # 获取PATH环境变量
    path_var = os.environ.get("PATH", "")

    # 获取路径分隔符（Windows使用分号，Unix使用冒号）
    path_sep = ";" if sys.platform == "win32" else ":"

    # 遍历PATH中的所有目录
    for directory in path_var.split(path_sep):
        # 构建可能的可执行文件路径
        executable = os.path.join(directory, name)

        # 检查文件是否存在且可执行
        if os.path.isfile(executable):
            if sys.platform == "win32":
                # Windows上不检查执行权限
                return executable
            else:
                # Unix系统上检查执行权限
                if os.access(executable, os.X_OK):
                    return executable

    return None


def get_home_dir() -> str:
    """
    获取用户主目录的路径，处理跨平台差异

    Returns:
        用户主目录的标准化路径
    """
    # 首先尝试使用标准的HOME环境变量
    home = os.environ.get("HOME")

    if not home:
        if sys.platform == "win32":
            # Windows上使用USERPROFILE
            home = os.environ.get("USERPROFILE")
            if not home:
                # 如果USERPROFILE也不存在，则组合HOMEDRIVE和HOMEPATH
                drive = os.environ.get("HOMEDRIVE", "")
                path = os.environ.get("HOMEPATH", "")
                home = os.path.join(drive, path)
        else:
            # 在Unix系统上，如果HOME不存在，使用pwd模块
            try:
                import pwd

                home = pwd.getpwuid(os.getuid()).pw_dir
            except ImportError:
                # 如果pwd模块不可用，使用当前目录
                home = os.getcwd()

    return normalize_path(home)


def get_temp_dir() -> str:
    """
    获取系统临时目录的路径，处理跨平台差异

    Returns:
        临时目录的标准化路径
    """
    import tempfile

    return normalize_path(tempfile.gettempdir())


def get_app_data_dir(app_name: str) -> str:
    """
    获取应用数据目录的路径，处理跨平台差异

    Args:
        app_name: 应用程序名称

    Returns:
        应用数据目录的标准化路径
    """
    if sys.platform == "win32":
        # Windows上使用APPDATA或LOCALAPPDATA
        base_dir = os.environ.get("APPDATA")
        if not base_dir:
            base_dir = os.environ.get("LOCALAPPDATA")
            if not base_dir:
                base_dir = os.path.join(get_home_dir(), "AppData", "Local")
    elif sys.platform == "darwin":
        # macOS上使用~/Library/Application Support
        base_dir = os.path.join(get_home_dir(), "Library", "Application Support")
    else:
        # Linux/Unix上使用~/.local/share
        base_dir = os.path.join(get_home_dir(), ".local", "share")

    app_dir = os.path.join(base_dir, app_name)
    os.makedirs(app_dir, exist_ok=True)
    return normalize_path(app_dir)


def is_symlink_supported() -> bool:
    """
    检查当前平台是否支持符号链接

    Returns:
        如果支持符号链接则返回True，否则返回False
    """
    if sys.platform == "win32":
        # Windows上需要管理员权限或开发者模式才能创建符号链接
        try:
            test_dir = os.path.join(get_temp_dir(), "symlink_test")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, "test_file")
            test_link = os.path.join(test_dir, "test_link")

            # 创建测试文件
            with open(test_file, "w") as f:
                f.write("test")

            # 尝试创建符号链接
            os.symlink(test_file, test_link)

            # 清理测试文件
            os.unlink(test_link)
            os.unlink(test_file)
            os.rmdir(test_dir)

            return True
        except (OSError, IOError):
            return False
    else:
        # Unix系统默认支持符号链接
        return True
