#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试命令模块

提供测试相关的命令，包括：
- 单元测试
- 集成测试
- 测试覆盖率
- 测试报告生成
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


class TestCommand(BaseCommand):
    """测试命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def unit(self, project_name: str, test_path: Optional[str] = None):
        """运行单元测试"""
        try:
            self.info(f"运行单元测试: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查测试目录
            tests_dir = project_dir / "tests"
            if not tests_dir.exists():
                raise RuntimeError(f"测试目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 运行单元测试
            if test_path:
                if os.system(f"python -m pytest {test_path}") != 0:
                    raise RuntimeError("运行单元测试失败")
            else:
                if os.system("python -m pytest tests/unit") != 0:
                    raise RuntimeError("运行单元测试失败")

            self.success("单元测试通过")

        except Exception as e:
            self.error(f"运行单元测试失败: {e}")
            raise

    def integration(self, project_name: str, test_path: Optional[str] = None):
        """运行集成测试"""
        try:
            self.info(f"运行集成测试: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查测试目录
            tests_dir = project_dir / "tests"
            if not tests_dir.exists():
                raise RuntimeError(f"测试目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 运行集成测试
            if test_path:
                if os.system(f"python -m pytest {test_path}") != 0:
                    raise RuntimeError("运行集成测试失败")
            else:
                if os.system("python -m pytest tests/integration") != 0:
                    raise RuntimeError("运行集成测试失败")

            self.success("集成测试通过")

        except Exception as e:
            self.error(f"运行集成测试失败: {e}")
            raise

    def coverage(self, project_name: str, test_path: Optional[str] = None):
        """运行测试覆盖率"""
        try:
            self.info(f"运行测试覆盖率: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查测试目录
            tests_dir = project_dir / "tests"
            if not tests_dir.exists():
                raise RuntimeError(f"测试目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 运行测试覆盖率
            if test_path:
                if os.system(f"python -m pytest --cov=. {test_path}") != 0:
                    raise RuntimeError("运行测试覆盖率失败")
            else:
                if os.system("python -m pytest --cov=. tests/") != 0:
                    raise RuntimeError("运行测试覆盖率失败")

            self.success("测试覆盖率检查完成")

        except Exception as e:
            self.error(f"运行测试覆盖率失败: {e}")
            raise

    def report(self, project_name: str, output_dir: Optional[str] = None):
        """生成测试报告"""
        try:
            self.info(f"生成测试报告: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查测试目录
            tests_dir = project_dir / "tests"
            if not tests_dir.exists():
                raise RuntimeError(f"测试目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 创建报告目录
            if output_dir:
                report_dir = Path(output_dir)
            else:
                report_dir = project_dir / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)

            # 生成测试报告
            if (
                os.system(f"python -m pytest --html={report_dir}/report.html tests/")
                != 0
            ):
                raise RuntimeError("生成测试报告失败")

            self.success(f"测试报告已生成: {report_dir}/report.html")

        except Exception as e:
            self.error(f"生成测试报告失败: {e}")
            raise

    def clean(self, project_name: str):
        """清理测试文件"""
        try:
            self.info(f"清理测试文件: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 清理测试文件
            if os.system("find . -type d -name '__pycache__' -exec rm -r {} +") != 0:
                raise RuntimeError("清理__pycache__目录失败")

            if os.system("find . -type f -name '*.pyc' -delete") != 0:
                raise RuntimeError("清理.pyc文件失败")

            if os.system("find . -type f -name '.coverage' -delete") != 0:
                raise RuntimeError("清理.coverage文件失败")

            if os.system("find . -type d -name '.pytest_cache' -exec rm -r {} +") != 0:
                raise RuntimeError("清理.pytest_cache目录失败")

            self.success("测试文件清理完成")

        except Exception as e:
            self.error(f"清理测试文件失败: {e}")
            raise


# CLI命令
@click.group()
def test():
    """测试命令"""
    pass


@test.command()
@click.argument("project_name")
@click.option("--path", "-p", help="测试路径")
def unit(project_name: str, path: Optional[str]):
    """运行单元测试"""
    cmd = TestCommand()
    cmd.unit(project_name, path)


@test.command()
@click.argument("project_name")
@click.option("--path", "-p", help="测试路径")
def integration(project_name: str, path: Optional[str]):
    """运行集成测试"""
    cmd = TestCommand()
    cmd.integration(project_name, path)


@test.command()
@click.argument("project_name")
@click.option("--path", "-p", help="测试路径")
def coverage(project_name: str, path: Optional[str]):
    """运行测试覆盖率"""
    cmd = TestCommand()
    cmd.coverage(project_name, path)


@test.command()
@click.argument("project_name")
@click.option("--output", "-o", help="输出目录")
def report(project_name: str, output: Optional[str]):
    """生成测试报告"""
    cmd = TestCommand()
    cmd.report(project_name, output)


@test.command()
@click.argument("project_name")
def clean(project_name: str):
    """清理测试文件"""
    cmd = TestCommand()
    cmd.clean(project_name)
