#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档命令模块

提供文档相关的命令，包括：
- 文档生成
- 文档预览
- 文档更新
- 文档清理
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


class DocCommand(BaseCommand):
    """文档命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, project_name: str, output_dir: Optional[str] = None):
        """生成文档"""
        try:
            self.info(f"生成文档: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查文档目录
            docs_dir = project_dir / "docs"
            if not docs_dir.exists():
                raise RuntimeError(f"文档目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 创建输出目录
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = docs_dir / "build"
            output_path.mkdir(parents=True, exist_ok=True)

            # 生成文档
            if os.system(f"sphinx-build -b html {docs_dir} {output_path}") != 0:
                raise RuntimeError("生成文档失败")

            self.success(f"文档生成成功: {output_path}")

        except Exception as e:
            self.error(f"生成文档失败: {e}")
            raise

    def preview(self, project_name: str, port: int = 8000):
        """预览文档"""
        try:
            self.info(f"预览文档: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查文档目录
            docs_dir = project_dir / "docs"
            if not docs_dir.exists():
                raise RuntimeError(f"文档目录不存在: {project_name}")

            # 检查构建目录
            build_dir = docs_dir / "build"
            if not build_dir.exists():
                raise RuntimeError(f"文档未构建: {project_name}")

            # 切换到构建目录
            os.chdir(str(build_dir))

            # 启动预览服务器
            if os.system(f"python -m http.server {port}") != 0:
                raise RuntimeError("启动预览服务器失败")

        except Exception as e:
            self.error(f"预览文档失败: {e}")
            raise

    def update(self, project_name: str):
        """更新文档"""
        try:
            self.info(f"更新文档: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查文档目录
            docs_dir = project_dir / "docs"
            if not docs_dir.exists():
                raise RuntimeError(f"文档目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 更新API文档
            if os.system("sphinx-apidoc -o docs/api app") != 0:
                raise RuntimeError("更新API文档失败")

            # 更新配置文档
            if os.system("sphinx-apidoc -o docs/config config") != 0:
                raise RuntimeError("更新配置文档失败")

            # 更新测试文档
            if os.system("sphinx-apidoc -o docs/tests tests") != 0:
                raise RuntimeError("更新测试文档失败")

            self.success("文档更新成功")

        except Exception as e:
            self.error(f"更新文档失败: {e}")
            raise

    def clean(self, project_name: str):
        """清理文档"""
        try:
            self.info(f"清理文档: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查文档目录
            docs_dir = project_dir / "docs"
            if not docs_dir.exists():
                raise RuntimeError(f"文档目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 清理构建目录
            build_dir = docs_dir / "build"
            if build_dir.exists():
                import shutil

                shutil.rmtree(build_dir)

            # 清理API文档
            api_dir = docs_dir / "api"
            if api_dir.exists():
                shutil.rmtree(api_dir)

            # 清理配置文档
            config_dir = docs_dir / "config"
            if config_dir.exists():
                shutil.rmtree(config_dir)

            # 清理测试文档
            tests_dir = docs_dir / "tests"
            if tests_dir.exists():
                shutil.rmtree(tests_dir)

            self.success("文档清理成功")

        except Exception as e:
            self.error(f"清理文档失败: {e}")
            raise


# CLI命令
@click.group()
def doc():
    """文档命令"""
    pass


@doc.command()
@click.argument("project_name")
@click.option("--output", "-o", help="输出目录")
def generate(project_name: str, output: Optional[str]):
    """生成文档"""
    cmd = DocCommand()
    cmd.generate(project_name, output)


@doc.command()
@click.argument("project_name")
@click.option("--port", "-p", default=8000, help="预览端口")
def preview(project_name: str, port: int):
    """预览文档"""
    cmd = DocCommand()
    cmd.preview(project_name, port)


@doc.command()
@click.argument("project_name")
def update(project_name: str):
    """更新文档"""
    cmd = DocCommand()
    cmd.update(project_name)


@doc.command()
@click.argument("project_name")
def clean(project_name: str):
    """清理文档"""
    cmd = DocCommand()
    cmd.clean(project_name)
