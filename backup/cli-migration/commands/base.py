"""
基础命令类
"""

import os
import sys
import time
import signal
import threading
from pathlib import Path
from typing import Optional, Callable, Any
from functools import wraps
from ..logger import Logger


def timeout(seconds: int):
    """超时装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Windows 平台使用线程实现超时
            if sys.platform == "win32":
                result = [None]
                exception = [None]

                def worker():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=worker)
                thread.daemon = True
                thread.start()
                thread.join(seconds)

                if thread.is_alive():
                    raise TimeoutError(f"函数 {func.__name__} 执行超时")

                if exception[0]:
                    raise exception[0]

                return result[0]
            else:
                # Unix 平台使用信号实现超时
                def _handle_timeout(signum, frame):
                    raise TimeoutError(f"函数 {func.__name__} 执行超时")

                # 设置信号处理器
                original_handler = signal.signal(signal.SIGALRM, _handle_timeout)
                signal.alarm(seconds)
                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # 取消警报
                    return result
                finally:
                    signal.alarm(0)  # 确保取消警报
                    signal.signal(signal.SIGALRM, original_handler)  # 恢复原始处理器

        return wrapper

    return decorator


class BaseCommand:
    """基础命令类"""

    def __init__(self):
        """初始化命令"""
        self.project_root = Path(__file__).parent.parent.parent
        self.logger = Logger(self.__class__.__name__)

    def info(self, message: str):
        """输出信息"""
        self.logger.info(message)

    def success(self, message: str):
        """输出成功信息"""
        self.logger.info(f"SUCCESS: {message}")

    def warning(self, message: str):
        """输出警告信息"""
        self.logger.warning(message)

    def error(self, message: str):
        """输出错误信息"""
        self.logger.error(message)

    def debug(self, message: str):
        """输出调试信息"""
        self.logger.debug(message)

    def check_command(self, command: str) -> bool:
        """检查命令是否可用"""
        if sys.platform == "win32":
            # Windows平台使用where命令
            # 提取命令名称（如 'python -m venv' 只需要检查 'python'）
            cmd_name = command.split()[0]
            return os.system(f"where {cmd_name} >nul 2>&1") == 0
        else:
            # Unix/Linux平台使用command -v
            return os.system(f"command -v {command} >/dev/null 2>&1") == 0

    def check_directory(self, path: str) -> bool:
        """检查目录是否存在"""
        return os.path.isdir(path)

    def check_file(self, path: str) -> bool:
        """检查文件是否存在"""
        return os.path.isfile(path)

    def create_directory(self, path: str, parents: bool = True):
        """创建目录"""
        os.makedirs(path, exist_ok=parents)

    def copy_item(self, src: str, dst: str):
        """复制文件或目录"""
        if os.path.isfile(src):
            import shutil

            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            import shutil

            shutil.copytree(src, dst)

    def replace_text(self, file_path: str, old_text: str, new_text: str):
        """替换文件中的文本"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace(old_text, new_text)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_python_version(self) -> str:
        """获取Python版本"""
        return sys.version.split()[0]

    def check_python_version(self, required_version: str) -> bool:
        """检查Python版本是否满足要求"""
        from packaging import version

        current = version.parse(self.get_python_version())
        required = version.parse(required_version)
        return current >= required

    def activate_venv(self):
        """激活虚拟环境"""
        venv_path = self.project_root / ".venv"
        if not self.check_directory(str(venv_path)):
            raise RuntimeError("虚拟环境不存在")

        if sys.platform == "win32":
            activate_script = venv_path / "Scripts" / "activate.bat"
        else:
            activate_script = venv_path / "bin" / "activate"

        if not self.check_file(str(activate_script)):
            raise RuntimeError("虚拟环境激活脚本不存在")

        os.system(f"source {activate_script}")

    def install_dependencies(self, requirements_file: str):
        """安装依赖"""
        if not self.check_file(requirements_file):
            raise RuntimeError(f"依赖文件不存在: {requirements_file}")
        os.system(f"pip install -r {requirements_file}")

    def check_docker_service(self) -> bool:
        """检查Docker服务是否运行"""
        return os.system("docker info >/dev/null 2>&1") == 0

    @timeout(300)  # 10分钟超时
    def wait_for_service(self, host: str, port: int, timeout: int = 60):
        """等待服务就绪"""
        import socket

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return
            except:
                pass
            time.sleep(1)
        raise TimeoutError(f"服务 {host}:{port} 未就绪")

    def check_permissions(self, path: str, required_permissions: int = 0o755) -> bool:
        """检查文件或目录权限"""
        try:
            current_permissions = os.stat(path).st_mode & 0o777
            return (current_permissions & required_permissions) == required_permissions
        except OSError:
            return False

    def ensure_permissions(self, path: str, required_permissions: int = 0o755):
        """确保文件或目录具有所需权限"""
        try:
            current_permissions = os.stat(path).st_mode & 0o777
            if (current_permissions & required_permissions) != required_permissions:
                os.chmod(path, current_permissions | required_permissions)
        except OSError as e:
            raise RuntimeError(f"无法设置权限: {str(e)}")
