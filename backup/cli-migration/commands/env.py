"""
环境管理命令
"""

import os
import sys
from pathlib import Path
from typing import Optional
from .base import BaseCommand


class EnvCommand(BaseCommand):
    """环境管理命令类"""

    def check(self):
        """检查环境"""
        self.info("开始检查环境...")
        self.check_python()
        self.check_docker()
        self.check_venv()
        self.success("环境检查完成")

    def check_python(self):
        """检查Python环境"""
        self.info("检查Python环境...")

        # 检查Python版本
        if not self.check_python_version("3.8.0"):
            raise RuntimeError(
                f"需要 Python 3.8.0 或更高版本 (当前版本: {self.get_python_version()})"
            )

        # 检查pip
        if not self.check_command("pip"):
            raise RuntimeError("pip 未安装")

        # 检查虚拟环境
        if not self.check_command("python -m venv"):
            raise RuntimeError("venv 模块未安装")

        self.success("Python环境检查通过")

    def check_docker(self):
        """检查Docker环境"""
        self.info("检查Docker环境...")

        if not self.check_docker_service():
            raise RuntimeError("Docker服务未运行")

        # 检查Docker Compose
        if not self.check_command("docker-compose"):
            raise RuntimeError("Docker Compose未安装")

        self.success("Docker环境检查通过")

    def check_venv(self):
        """检查虚拟环境"""
        self.info("检查虚拟环境...")

        venv_path = self.project_root / ".venv"
        if not self.check_directory(str(venv_path)):
            self.warning("虚拟环境不存在")
            return

        # 检查虚拟环境权限
        if not self.check_permissions(str(venv_path)):
            self.warning("虚拟环境权限不正确")
            self.ensure_permissions(str(venv_path))

        # 检查pip是否可用
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"

        if not self.check_file(str(pip_path)):
            raise RuntimeError("虚拟环境pip不可用")

        self.success("虚拟环境检查通过")

    def setup(self):
        """设置开发环境"""
        self.info("开始设置开发环境...")

        # 创建必要的目录
        directories = ["logs", "data", "config", "tests", "docs"]

        for directory in directories:
            dir_path = self.project_root / directory
            if not self.check_directory(str(dir_path)):
                self.create_directory(str(dir_path))
                self.info(f"创建目录: {directory}")

        # 创建虚拟环境
        venv_path = self.project_root / ".venv"
        if not self.check_directory(str(venv_path)):
            self.info("创建虚拟环境...")
            import venv

            venv.create(venv_path, with_pip=True)

        # 安装依赖
        requirements_file = self.project_root / "requirements.txt"
        if self.check_file(str(requirements_file)):
            self.info("安装项目依赖...")
            self.install_dependencies(str(requirements_file))

        self.success("开发环境设置完成")

    def clean(self):
        """清理环境"""
        self.info("开始清理环境...")

        # 停止Docker容器
        self.info("停止Docker容器...")
        os.system("docker-compose down")

        # 清理Docker资源
        self.info("清理Docker资源...")
        os.system("docker system prune -f")

        # 删除虚拟环境
        venv_path = self.project_root / ".venv"
        if self.check_directory(str(venv_path)):
            self.info("删除虚拟环境...")
            import shutil

            shutil.rmtree(str(venv_path))

        # 清理日志文件
        logs_path = self.project_root / "logs"
        if self.check_directory(str(logs_path)):
            self.info("清理日志文件...")
            for log_file in logs_path.glob("*.log"):
                log_file.unlink()

        self.success("环境清理完成")
