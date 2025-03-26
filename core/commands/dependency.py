#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖管理命令模块

提供依赖管理相关的命令，包括：
- 依赖安装和更新
- 依赖版本管理
- 依赖冲突检测
- 依赖清理
"""

import os
import sys
import yaml
import click
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DependencyCommand(BaseCommand):
    """依赖管理命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def install(self, project_name: str, packages: List[str], dev: bool = False):
        """安装依赖"""
        try:
            self.info(f"安装依赖: {', '.join(packages)}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查requirements文件
            requirements_file = project_dir / "requirements.txt"
            if not requirements_file.exists():
                raise RuntimeError(f"requirements.txt不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 安装依赖
            for package in packages:
                if os.system(f"pip install {package}") != 0:
                    raise RuntimeError(f"安装依赖失败: {package}")

            # 更新requirements.txt
            if os.system("pip freeze > requirements.txt") != 0:
                raise RuntimeError("更新requirements.txt失败")

            self.success(f"依赖安装成功: {', '.join(packages)}")

        except Exception as e:
            self.error(f"安装依赖失败: {e}")
            raise

    def update(self, project_name: str, packages: Optional[List[str]] = None):
        """更新依赖"""
        try:
            self.info(f"更新依赖: {', '.join(packages) if packages else '所有'}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查requirements文件
            requirements_file = project_dir / "requirements.txt"
            if not requirements_file.exists():
                raise RuntimeError(f"requirements.txt不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 更新依赖
            if packages:
                for package in packages:
                    if os.system(f"pip install --upgrade {package}") != 0:
                        raise RuntimeError(f"更新依赖失败: {package}")
            else:
                if os.system("pip install --upgrade -r requirements.txt") != 0:
                    raise RuntimeError("更新依赖失败")

            # 更新requirements.txt
            if os.system("pip freeze > requirements.txt") != 0:
                raise RuntimeError("更新requirements.txt失败")

            self.success(f"依赖更新成功: {', '.join(packages) if packages else '所有'}")

        except Exception as e:
            self.error(f"更新依赖失败: {e}")
            raise

    def remove(self, project_name: str, packages: List[str]):
        """移除依赖"""
        try:
            self.info(f"移除依赖: {', '.join(packages)}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查requirements文件
            requirements_file = project_dir / "requirements.txt"
            if not requirements_file.exists():
                raise RuntimeError(f"requirements.txt不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 移除依赖
            for package in packages:
                if os.system(f"pip uninstall -y {package}") != 0:
                    raise RuntimeError(f"移除依赖失败: {package}")

            # 更新requirements.txt
            if os.system("pip freeze > requirements.txt") != 0:
                raise RuntimeError("更新requirements.txt失败")

            self.success(f"依赖移除成功: {', '.join(packages)}")

        except Exception as e:
            self.error(f"移除依赖失败: {e}")
            raise

    def check(self, project_name: str):
        """检查依赖冲突"""
        try:
            self.info(f"检查依赖冲突: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查requirements文件
            requirements_file = project_dir / "requirements.txt"
            if not requirements_file.exists():
                raise RuntimeError(f"requirements.txt不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 检查依赖冲突
            if os.system("pip check") != 0:
                raise RuntimeError("发现依赖冲突")

            self.success("未发现依赖冲突")

        except Exception as e:
            self.error(f"检查依赖冲突失败: {e}")
            raise

    def clean(self, project_name: str):
        """清理依赖"""
        try:
            self.info(f"清理依赖: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查requirements文件
            requirements_file = project_dir / "requirements.txt"
            if not requirements_file.exists():
                raise RuntimeError(f"requirements.txt不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 清理依赖
            if os.system("pip uninstall -y -r requirements.txt") != 0:
                raise RuntimeError("清理依赖失败")

            # 重新安装依赖
            if os.system("pip install -r requirements.txt") != 0:
                raise RuntimeError("重新安装依赖失败")

            self.success("依赖清理成功")

        except Exception as e:
            self.error(f"清理依赖失败: {e}")
            raise

    def show(self, project_name: str):
        """显示依赖信息"""
        try:
            self.info(f"显示依赖信息: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查requirements文件
            requirements_file = project_dir / "requirements.txt"
            if not requirements_file.exists():
                raise RuntimeError(f"requirements.txt不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 显示依赖信息
            if os.system("pip list") != 0:
                raise RuntimeError("显示依赖信息失败")

        except Exception as e:
            self.error(f"显示依赖信息失败: {e}")
            raise


# CLI命令
@click.group()
def dependency():
    """依赖管理命令"""
    pass


@dependency.command()
@click.argument("project_name")
@click.argument("packages", nargs=-1)
@click.option("--dev", "-d", is_flag=True, help="安装开发依赖")
def install(project_name: str, packages: List[str], dev: bool):
    """安装依赖"""
    cmd = DependencyCommand()
    cmd.install(project_name, packages, dev)


@dependency.command()
@click.argument("project_name")
@click.argument("packages", nargs=-1, required=False)
def update(project_name: str, packages: Optional[List[str]]):
    """更新依赖"""
    cmd = DependencyCommand()
    cmd.update(project_name, packages)


@dependency.command()
@click.argument("project_name")
@click.argument("packages", nargs=-1)
def remove(project_name: str, packages: List[str]):
    """移除依赖"""
    cmd = DependencyCommand()
    cmd.remove(project_name, packages)


@dependency.command()
@click.argument("project_name")
def check(project_name: str):
    """检查依赖冲突"""
    cmd = DependencyCommand()
    cmd.check(project_name)


@dependency.command()
@click.argument("project_name")
def clean(project_name: str):
    """清理依赖"""
    cmd = DependencyCommand()
    cmd.clean(project_name)


@dependency.command()
@click.argument("project_name")
def show(project_name: str):
    """显示依赖信息"""
    cmd = DependencyCommand()
    cmd.show(project_name)
