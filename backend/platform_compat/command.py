"""
命令执行模块

提供跨平台的命令执行功能，处理Windows和Unix系统的命令执行差异。
"""

import os
import sys
import signal
import subprocess
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple


def execute_command(
    command: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
    shell: bool = False,
    timeout: Optional[float] = None,
    encoding: str = "utf-8",
) -> Tuple[int, str, str]:
    """
    执行命令，处理跨平台差异

    Args:
        command: 要执行的命令，可以是字符串或命令参数列表
        cwd: 工作目录
        env: 环境变量
        shell: 是否使用shell执行
        timeout: 超时时间（秒）
        encoding: 输出编码

    Returns:
        (返回码, 标准输出, 标准错误)的元组
    """
    try:
        # 处理命令格式
        if isinstance(command, str) and not shell:
            command = command.split()

        # 在Windows上处理可执行文件扩展名
        if sys.platform == "win32" and not shell:
            command = _resolve_windows_command(command)

        # 执行命令
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding=encoding,
        )

        # 等待命令完成
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr

    except subprocess.TimeoutExpired:
        _kill_process(process)
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def execute_command_async(
    command: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
    shell: bool = False,
) -> subprocess.Popen:
    """
    异步执行命令，处理跨平台差异

    Args:
        command: 要执行的命令，可以是字符串或命令参数列表
        cwd: 工作目录
        env: 环境变量
        shell: 是否使用shell执行

    Returns:
        subprocess.Popen对象
    """
    # 处理命令格式
    if isinstance(command, str) and not shell:
        command = command.split()

    # 在Windows上处理可执行文件扩展名
    if sys.platform == "win32" and not shell:
        command = _resolve_windows_command(command)

    # 异步执行命令
    return subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _resolve_windows_command(command: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    解析Windows命令，添加必要的扩展名

    Args:
        command: 原始命令

    Returns:
        处理后的命令
    """
    if sys.platform != "win32":
        return command

    if isinstance(command, str):
        return command

    cmd = command[0]
    if os.path.isfile(cmd):
        return command

    # 检查常见的可执行文件扩展名
    for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
        cmd_with_ext = cmd + ext.lower()
        if os.path.isfile(cmd_with_ext):
            command[0] = cmd_with_ext
            return command

    # 在PATH中查找可执行文件
    for path in os.environ.get("PATH", "").split(os.pathsep):
        cmd_path = os.path.join(path, cmd)
        if os.path.isfile(cmd_path):
            command[0] = cmd_path
            return command
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            cmd_with_ext = cmd_path + ext.lower()
            if os.path.isfile(cmd_with_ext):
                command[0] = cmd_with_ext
                return command

    return command


def _kill_process(process: subprocess.Popen) -> None:
    """
    终止进程，处理跨平台差异

    Args:
        process: 要终止的进程
    """
    try:
        if sys.platform == "win32":
            # Windows上使用taskkill强制终止进程树
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True
            )
        else:
            # Unix系统上发送SIGTERM信号
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)

            # 等待进程结束
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # 如果进程没有响应SIGTERM，发送SIGKILL
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except Exception as e:
        print(f"终止进程失败: {e}")


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """
    获取进程信息，处理跨平台差异

    Args:
        pid: 进程ID

    Returns:
        进程信息字典，如果获取失败则返回None
    """
    try:
        import psutil

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
    try:
        import psutil

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
    try:
        import psutil

        return psutil.pid_exists(pid)
    except Exception as e:
        print(f"检查进程状态失败: {e}")
        return False
