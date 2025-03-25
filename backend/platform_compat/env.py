"""
环境变量管理模块

提供跨平台的环境变量管理功能，处理Windows和Unix系统的环境变量差异。
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, Union, List, Dict, Any


def get_env_path_separator() -> str:
    """
    获取环境变量PATH的分隔符

    Returns:
        PATH分隔符
    """
    return os.pathsep


def normalize_env_var(name: str, value: str) -> str:
    """
    标准化环境变量值，处理跨平台差异

    Args:
        name: 环境变量名称
        value: 环境变量值

    Returns:
        标准化后的环境变量值
    """
    if name.upper() == "PATH":
        # 处理PATH环境变量
        paths = value.split(os.pathsep)
        # 移除重复路径
        paths = list(dict.fromkeys(paths))
        # 移除空路径
        paths = [p for p in paths if p]
        # 标准化路径分隔符
        paths = [os.path.normpath(p) for p in paths]
        return os.pathsep.join(paths)
    else:
        # 其他环境变量保持不变
        return value


def get_env_dict(inherit: bool = True) -> Dict[str, str]:
    """
    获取标准化的环境变量字典

    Args:
        inherit: 是否继承当前进程的环境变量

    Returns:
        环境变量字典
    """
    env = {}
    if inherit:
        # 继承当前进程的环境变量
        env.update(os.environ)

    # 标准化所有环境变量
    for name, value in list(env.items()):
        env[name] = normalize_env_var(name, value)

    return env


def expand_env_vars(value: str) -> str:
    """
    展开环境变量，处理跨平台差异

    Args:
        value: 包含环境变量的字符串

    Returns:
        展开后的字符串
    """
    if sys.platform == "win32":
        # Windows风格的环境变量展开
        def replace(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, "")

        # 支持%VAR%和${VAR}两种格式
        value = re.sub(r"%([^%]+)%|\$\{([^}]+)\}", replace, value)
    else:
        # Unix风格的环境变量展开
        value = os.path.expandvars(value)

    return value


def set_env_var(name: str, value: str, system_wide: bool = False) -> bool:
    """
    设置环境变量，处理跨平台差异

    Args:
        name: 环境变量名称
        value: 环境变量值
        system_wide: 是否设置系统级环境变量

    Returns:
        是否设置成功
    """
    try:
        if sys.platform == "win32":
            # Windows上设置环境变量
            if system_wide:
                import winreg

                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    "System\\CurrentControlSet\\Control\\Session Manager\\Environment",
                    0,
                    winreg.KEY_ALL_ACCESS,
                ) as key:
                    winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)

                # 通知系统环境变量已更改
                import win32con
                import win32gui

                win32gui.SendMessageTimeout(
                    win32con.HWND_BROADCAST,
                    win32con.WM_SETTINGCHANGE,
                    0,
                    None,  # 使用None代替字符串参数
                    win32con.SMTO_ABORTIFHUNG,
                    5000,
                )
            else:
                # 设置用户级环境变量
                import winreg

                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
                ) as key:
                    winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
        else:
            # Unix系统上设置环境变量
            if system_wide:
                # 在/etc/environment中设置系统级环境变量
                with open("/etc/environment", "a") as f:
                    f.write(f'\n{name}="{value}"\n')
            else:
                # 在~/.profile中设置用户级环境变量
                profile_path = os.path.expanduser("~/.profile")
                with open(profile_path, "a") as f:
                    f.write(f'\nexport {name}="{value}"\n')

        # 更新当前进程的环境变量
        os.environ[name] = value
        return True
    except Exception as e:
        print(f"设置环境变量失败: {e}")
        return False


def get_path_var() -> List[str]:
    """
    获取PATH环境变量的路径列表

    Returns:
        路径列表
    """
    path = os.environ.get("PATH", "")
    return [os.path.normpath(p) for p in path.split(os.pathsep) if p]


def update_path_var(paths: List[str], prepend: bool = True) -> bool:
    """
    更新PATH环境变量

    Args:
        paths: 要添加的路径列表
        prepend: 是否添加到PATH的开头

    Returns:
        是否更新成功
    """
    try:
        current_paths = get_path_var()

        # 标准化新路径
        new_paths = [os.path.normpath(p) for p in paths]

        # 移除重复路径
        new_paths = [p for p in new_paths if p not in current_paths]

        if prepend:
            # 添加到PATH开头
            updated_paths = new_paths + current_paths
        else:
            # 添加到PATH末尾
            updated_paths = current_paths + new_paths

        # 更新PATH环境变量
        path_value = os.pathsep.join(updated_paths)
        return set_env_var("PATH", path_value)
    except Exception as e:
        print(f"更新PATH环境变量失败: {e}")
        return False
