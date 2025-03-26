#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志命令模块

提供日志相关的命令，包括：
- 日志查看
- 日志分析
- 日志清理
- 日志配置
"""

import os
import sys
import yaml
import click
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LogCommand(BaseCommand):
    """日志命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def view(self, project_name: str, service: Optional[str] = None, lines: int = 100):
        """查看日志"""
        try:
            self.info(f"查看日志: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查日志目录
            logs_dir = project_dir / "logs"
            if not logs_dir.exists():
                raise RuntimeError(f"日志目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 查看日志
            if service:
                log_file = logs_dir / f"{service}.log"
                if not log_file.exists():
                    raise RuntimeError(f"服务日志不存在: {service}")
                if os.system(f"tail -n {lines} {log_file}") != 0:
                    raise RuntimeError(f"查看服务日志失败: {service}")
            else:
                for log_file in logs_dir.glob("*.log"):
                    self.info(f"\n查看日志文件: {log_file.name}")
                    if os.system(f"tail -n {lines} {log_file}") != 0:
                        raise RuntimeError(f"查看日志文件失败: {log_file.name}")

        except Exception as e:
            self.error(f"查看日志失败: {e}")
            raise

    def analyze(self, project_name: str, service: Optional[str] = None, days: int = 7):
        """分析日志"""
        try:
            self.info(f"分析日志: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查日志目录
            logs_dir = project_dir / "logs"
            if not logs_dir.exists():
                raise RuntimeError(f"日志目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 分析日志
            if service:
                log_file = logs_dir / f"{service}.log"
                if not log_file.exists():
                    raise RuntimeError(f"服务日志不存在: {service}")
                self._analyze_log_file(log_file, days)
            else:
                for log_file in logs_dir.glob("*.log"):
                    self.info(f"\n分析日志文件: {log_file.name}")
                    self._analyze_log_file(log_file, days)

        except Exception as e:
            self.error(f"分析日志失败: {e}")
            raise

    def clean(self, project_name: str, days: int = 30):
        """清理日志"""
        try:
            self.info(f"清理日志: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查日志目录
            logs_dir = project_dir / "logs"
            if not logs_dir.exists():
                raise RuntimeError(f"日志目录不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 清理日志
            cutoff_date = datetime.now() - timedelta(days=days)
            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.info(f"删除日志文件: {log_file.name}")

            self.success("日志清理完成")

        except Exception as e:
            self.error(f"清理日志失败: {e}")
            raise

    def config(self, project_name: str, service: Optional[str] = None, **kwargs):
        """配置日志"""
        try:
            self.info(f"配置日志: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查日志目录
            logs_dir = project_dir / "logs"
            if not logs_dir.exists():
                raise RuntimeError(f"日志目录不存在: {project_name}")

            # 检查日志配置
            config_file = logs_dir / "config.yml"
            if not config_file.exists():
                raise RuntimeError(f"日志配置不存在: {project_name}")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新配置
            if service:
                if service not in config:
                    config[service] = {}
                config[service].update(kwargs)
            else:
                config.update(kwargs)

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("日志配置已更新")

        except Exception as e:
            self.error(f"配置日志失败: {e}")
            raise

    def _analyze_log_file(self, log_file: Path, days: int):
        """分析日志文件"""
        try:
            # 读取日志文件
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 统计信息
            total_lines = len(lines)
            error_lines = sum(1 for line in lines if "ERROR" in line)
            warning_lines = sum(1 for line in lines if "WARNING" in line)
            info_lines = sum(1 for line in lines if "INFO" in line)

            # 显示统计信息
            self.info(f"总行数: {total_lines}")
            self.info(f"错误数: {error_lines}")
            self.info(f"警告数: {warning_lines}")
            self.info(f"信息数: {info_lines}")

            # 显示错误信息
            if error_lines > 0:
                self.info("\n错误信息:")
                for line in lines:
                    if "ERROR" in line:
                        self.info(line.strip())

            # 显示警告信息
            if warning_lines > 0:
                self.info("\n警告信息:")
                for line in lines:
                    if "WARNING" in line:
                        self.info(line.strip())

        except Exception as e:
            self.error(f"分析日志文件失败: {e}")
            raise


# CLI命令
@click.group()
def log():
    """日志命令"""
    pass


@log.command()
@click.argument("project_name")
@click.option("--service", "-s", help="服务名称")
@click.option("--lines", "-n", default=100, help="显示行数")
def view(project_name: str, service: Optional[str], lines: int):
    """查看日志"""
    cmd = LogCommand()
    cmd.view(project_name, service, lines)


@log.command()
@click.argument("project_name")
@click.option("--service", "-s", help="服务名称")
@click.option("--days", "-d", default=7, help="分析天数")
def analyze(project_name: str, service: Optional[str], days: int):
    """分析日志"""
    cmd = LogCommand()
    cmd.analyze(project_name, service, days)


@log.command()
@click.argument("project_name")
@click.option("--days", "-d", default=30, help="保留天数")
def clean(project_name: str, days: int):
    """清理日志"""
    cmd = LogCommand()
    cmd.clean(project_name, days)


@log.command()
@click.argument("project_name")
@click.option("--service", "-s", help="服务名称")
@click.option("--level", "-l", help="日志级别")
@click.option("--format", "-f", help="日志格式")
@click.option("--file", "-o", help="日志文件")
def config(project_name: str, service: Optional[str], **kwargs):
    """配置日志"""
    cmd = LogCommand()
    cmd.config(project_name, service, **kwargs)
