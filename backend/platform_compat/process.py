"""
进程管理模块

提供跨平台的进程管理功能，处理Windows和Unix系统的进程管理差异。
"""

import os
import sys
import signal
import ctypes
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    print("请安装psutil: pip install psutil")
    HAS_PSUTIL = False

# Windows进程访问权限常量
PROCESS_ALL_ACCESS = 0x1F0FFF


def is_admin() -> bool:
    """
    检查当前进程是否具有管理员权限

    Returns:
        如果具有管理员权限则返回True，否则返回False
    """
    try:
        if sys.platform == "win32":
            # Windows上检查管理员权限
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # Unix系统检查root权限
            return os.geteuid() == 0
    except:
        return False


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """
    获取进程信息，处理跨平台差异

    Args:
        pid: 进程ID

    Returns:
        进程信息字典，如果获取失败则返回None
    """
    if not HAS_PSUTIL:
        return None

    try:
        process = psutil.Process(pid)
        return {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "create_time": process.create_time(),
            "cmdline": process.cmdline(),
            "cwd": process.cwd(),
            "username": process.username(),
            "num_threads": process.num_threads(),
            "connections": len(process.connections()),
            "open_files": len(process.open_files()),
        }
    except Exception as e:
        print(f"获取进程信息失败: {e}")
        return None


def list_processes() -> List[Dict[str, Any]]:
    """
    列出所有进程，处理跨平台差异

    Returns:
        进程信息列表
    """
    if not HAS_PSUTIL:
        return []

    try:
        processes = []
        for proc in psutil.process_iter(["pid", "name", "status"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    except Exception as e:
        print(f"列出进程失败: {e}")
        return []


def is_process_running(pid: int) -> bool:
    """
    检查进程是否在运行，处理跨平台差异

    Args:
        pid: 进程ID

    Returns:
        进程是否在运行
    """
    if not HAS_PSUTIL:
        try:
            # 尝试发送空信号来检查进程是否存在
            if sys.platform == "win32":
                import win32api

                win32api.OpenProcess(1, False, pid)
            else:
                os.kill(pid, 0)
            return True
        except:
            return False

    try:
        return psutil.pid_exists(pid)
    except Exception as e:
        print(f"检查进程状态失败: {e}")
        return False


def kill_process(pid: int, force: bool = False) -> bool:
    """
    终止进程，处理跨平台差异

    Args:
        pid: 进程ID
        force: 是否强制终止

    Returns:
        是否成功终止进程
    """
    if not HAS_PSUTIL:
        try:
            if sys.platform == "win32":
                import subprocess

                if force:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)], capture_output=True
                    )
                else:
                    subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGKILL if force else signal.SIGTERM)
            return True
        except:
            return False

    try:
        process = psutil.Process(pid)
        if force:
            process.kill()
        else:
            process.terminate()
            try:
                process.wait(timeout=3)
            except psutil.TimeoutExpired:
                process.kill()
        return True
    except Exception as e:
        print(f"终止进程失败: {e}")
        return False


def get_process_children(pid: int) -> List[int]:
    """
    获取进程的子进程列表，处理跨平台差异

    Args:
        pid: 进程ID

    Returns:
        子进程ID列表
    """
    if not HAS_PSUTIL:
        return []

    try:
        process = psutil.Process(pid)
        return [child.pid for child in process.children(recursive=True)]
    except Exception as e:
        print(f"获取子进程失败: {e}")
        return []


def set_process_priority(pid: int, priority: int) -> bool:
    """
    设置进程优先级，处理跨平台差异

    Args:
        pid: 进程ID
        priority: 优先级（-20到19，-20最高，19最低）

    Returns:
        是否设置成功
    """
    if not HAS_PSUTIL:
        try:
            if sys.platform == "win32":
                import win32api
                import win32process

                handle = win32api.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                win32process.SetPriorityClass(handle, priority)
            else:
                os.setpriority(os.PRIO_PROCESS, pid, priority)
            return True
        except:
            return False

    try:
        process = psutil.Process(pid)
        process.nice(priority)
        return True
    except Exception as e:
        print(f"设置进程优先级失败: {e}")
        return False


def get_process_environment(pid: int) -> Dict[str, str]:
    """
    获取进程的环境变量，处理跨平台差异

    Args:
        pid: 进程ID

    Returns:
        环境变量字典
    """
    if not HAS_PSUTIL:
        return {}

    try:
        process = psutil.Process(pid)
        return process.environ()
    except Exception as e:
        print(f"获取进程环境变量失败: {e}")
        return {}
