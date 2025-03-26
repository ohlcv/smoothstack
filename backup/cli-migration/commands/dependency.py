"""
依赖管理命令类
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from .base import BaseCommand


class DependencyCommand(BaseCommand):
    """依赖管理命令类"""

    def __init__(self):
        super().__init__()
        self.frontend_dir = self.project_root / "frontend"
        self.backend_dir = self.project_root / "backend"

    def install(self, type: str, packages: List[str], registry: Optional[str] = None):
        """安装依赖

        Args:
            type: 依赖类型 (frontend/backend)
            packages: 包名列表
            registry: 包管理器源
        """
        self.info(f"安装{type}依赖: {', '.join(packages)}")
        try:
            if type == "frontend":
                os.chdir(str(self.frontend_dir))
                if registry:
                    # 设置npm源
                    os.system(f"npm config set registry {registry}")
                # 安装依赖
                os.system(f"npm install {' '.join(packages)}")

            elif type == "backend":
                os.chdir(str(self.backend_dir))
                if registry:
                    # 设置pip源
                    with open("pip.conf", "w") as f:
                        f.write(f"[global]\nindex-url = {registry}")
                # 安装依赖
                os.system(f"pip install {' '.join(packages)}")

            self.success(f"{type}依赖安装成功")
        except Exception as e:
            self.error(f"依赖安装失败: {str(e)}")
            raise

    def uninstall(self, type: str, packages: List[str]):
        """卸载依赖

        Args:
            type: 依赖类型 (frontend/backend)
            packages: 包名列表
        """
        self.info(f"卸载{type}依赖: {', '.join(packages)}")
        try:
            if type == "frontend":
                os.chdir(str(self.frontend_dir))
                os.system(f"npm uninstall {' '.join(packages)}")

            elif type == "backend":
                os.chdir(str(self.backend_dir))
                os.system(f"pip uninstall -y {' '.join(packages)}")

            self.success(f"{type}依赖卸载成功")
        except Exception as e:
            self.error(f"依赖卸载失败: {str(e)}")
            raise

    def update(self, type: str, packages: Optional[List[str]] = None):
        """更新依赖

        Args:
            type: 依赖类型 (frontend/backend)
            packages: 包名列表，如果为空则更新所有依赖
        """
        self.info(f"更新{type}依赖")
        try:
            if type == "frontend":
                os.chdir(str(self.frontend_dir))
                if packages:
                    os.system(f"npm update {' '.join(packages)}")
                else:
                    os.system("npm update")

            elif type == "backend":
                os.chdir(str(self.backend_dir))
                if packages:
                    os.system(f"pip install --upgrade {' '.join(packages)}")
                else:
                    # 更新所有依赖
                    os.system(
                        "pip list --outdated | cut -d ' ' -f1 | xargs -n1 pip install --upgrade"
                    )

            self.success(f"{type}依赖更新成功")
        except Exception as e:
            self.error(f"依赖更新失败: {str(e)}")
            raise

    def list(self, type: str):
        """列出依赖

        Args:
            type: 依赖类型 (frontend/backend)
        """
        self.info(f"列出{type}依赖")
        try:
            if type == "frontend":
                os.chdir(str(self.frontend_dir))
                os.system("npm list")

            elif type == "backend":
                os.chdir(str(self.backend_dir))
                os.system("pip list")

        except Exception as e:
            self.error(f"列出依赖失败: {str(e)}")
            raise

    def clean_cache(self, type: str):
        """清理依赖缓存

        Args:
            type: 依赖类型 (frontend/backend)
        """
        self.info(f"清理{type}依赖缓存")
        try:
            if type == "frontend":
                os.chdir(str(self.frontend_dir))
                os.system("npm cache clean --force")

            elif type == "backend":
                os.chdir(str(self.backend_dir))
                os.system("pip cache purge")

            self.success(f"{type}依赖缓存清理成功")
        except Exception as e:
            self.error(f"清理依赖缓存失败: {str(e)}")
            raise

    def set_registry(self, type: str, registry: str):
        """设置包管理器源

        Args:
            type: 依赖类型 (frontend/backend)
            registry: 源地址
        """
        self.info(f"设置{type}包管理器源: {registry}")
        try:
            if type == "frontend":
                os.system(f"npm config set registry {registry}")

            elif type == "backend":
                # 创建或更新pip配置文件
                pip_conf_dir = Path.home() / ".pip"
                pip_conf_dir.mkdir(exist_ok=True)

                with open(pip_conf_dir / "pip.conf", "w") as f:
                    f.write(f"[global]\nindex-url = {registry}")

            self.success(f"{type}包管理器源设置成功")
        except Exception as e:
            self.error(f"设置包管理器源失败: {str(e)}")
            raise
