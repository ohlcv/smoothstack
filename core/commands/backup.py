#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
备份命令模块

提供备份相关的命令，包括：
- 项目备份
- 数据备份
- 配置备份
- 备份恢复
"""

import os
import sys
import yaml
import click
import shutil
import tarfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BackupCommand(BaseCommand):
    """备份命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.backups_dir = self.project_root / "backups"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def project(self, project_name: str, backup_name: Optional[str] = None):
        """备份项目"""
        try:
            self.info(f"备份项目: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 生成备份名称
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{project_name}_{timestamp}"

            # 创建备份目录
            backup_dir = self.backups_dir / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 备份项目文件
            self._backup_project_files(project_dir, backup_dir)

            # 备份项目配置
            self._backup_project_config(project_dir, backup_dir)

            # 备份项目数据
            self._backup_project_data(project_dir, backup_dir)

            # 创建备份信息
            self._create_backup_info(backup_dir, project_name, backup_name)

            # 压缩备份
            self._compress_backup(backup_dir)

            self.success(f"项目备份成功: {backup_name}")

        except Exception as e:
            self.error(f"项目备份失败: {e}")
            raise

    def data(self, project_name: str, backup_name: Optional[str] = None):
        """备份数据"""
        try:
            self.info(f"备份数据: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 生成备份名称
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{project_name}_data_{timestamp}"

            # 创建备份目录
            backup_dir = self.backups_dir / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 备份数据
            self._backup_project_data(project_dir, backup_dir)

            # 创建备份信息
            self._create_backup_info(backup_dir, project_name, backup_name)

            # 压缩备份
            self._compress_backup(backup_dir)

            self.success(f"数据备份成功: {backup_name}")

        except Exception as e:
            self.error(f"数据备份失败: {e}")
            raise

    def config(self, project_name: str, backup_name: Optional[str] = None):
        """备份配置"""
        try:
            self.info(f"备份配置: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 生成备份名称
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{project_name}_config_{timestamp}"

            # 创建备份目录
            backup_dir = self.backups_dir / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 备份配置
            self._backup_project_config(project_dir, backup_dir)

            # 创建备份信息
            self._create_backup_info(backup_dir, project_name, backup_name)

            # 压缩备份
            self._compress_backup(backup_dir)

            self.success(f"配置备份成功: {backup_name}")

        except Exception as e:
            self.error(f"配置备份失败: {e}")
            raise

    def restore(self, backup_name: str, project_name: Optional[str] = None):
        """恢复备份"""
        try:
            self.info(f"恢复备份: {backup_name}")

            # 检查备份文件
            backup_file = self.backups_dir / f"{backup_name}.tar.gz"
            if not backup_file.exists():
                raise RuntimeError(f"备份文件不存在: {backup_name}")

            # 创建临时目录
            temp_dir = self.backups_dir / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 解压备份
            self._extract_backup(backup_file, temp_dir)

            # 读取备份信息
            info_file = temp_dir / "backup_info.yml"
            with open(info_file, "r", encoding="utf-8") as f:
                info = yaml.safe_load(f)

            # 确定项目名称
            if not project_name:
                project_name = info["project_name"]

            # 恢复项目
            project_dir = self.projects_dir / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            # 恢复文件
            self._restore_project_files(temp_dir, project_dir)

            # 恢复配置
            self._restore_project_config(temp_dir, project_dir)

            # 恢复数据
            self._restore_project_data(temp_dir, project_dir)

            # 清理临时目录
            shutil.rmtree(temp_dir)

            self.success(f"备份恢复成功: {project_name}")

        except Exception as e:
            self.error(f"备份恢复失败: {e}")
            raise

    def list(self, project_name: Optional[str] = None):
        """列出备份"""
        try:
            self.info("列出备份:")

            # 获取备份列表
            backups = []
            for backup_file in self.backups_dir.glob("*.tar.gz"):
                backup_name = backup_file.stem
                backup_info = self._get_backup_info(backup_name)
                if not project_name or backup_info["project_name"] == project_name:
                    backups.append(backup_info)

            # 按时间排序
            backups.sort(key=lambda x: x["timestamp"], reverse=True)

            # 显示备份列表
            if not backups:
                self.info("未找到备份")
                return

            self.info("\n备份列表:")
            for backup in backups:
                self.info(f"名称: {backup['backup_name']}")
                self.info(f"项目: {backup['project_name']}")
                self.info(f"时间: {backup['timestamp']}")
                self.info(f"大小: {backup['size']}")
                self.info("")

        except Exception as e:
            self.error(f"列出备份失败: {e}")
            raise

    def delete(self, backup_name: str):
        """删除备份"""
        try:
            self.info(f"删除备份: {backup_name}")

            # 检查备份文件
            backup_file = self.backups_dir / f"{backup_name}.tar.gz"
            if not backup_file.exists():
                raise RuntimeError(f"备份文件不存在: {backup_name}")

            # 删除备份文件
            backup_file.unlink()

            self.success(f"备份删除成功: {backup_name}")

        except Exception as e:
            self.error(f"删除备份失败: {e}")
            raise

    def _backup_project_files(self, project_dir: Path, backup_dir: Path):
        """备份项目文件"""
        try:
            # 复制项目文件
            for item in project_dir.glob("*"):
                if item.is_file() and item.name not in ["backup_info.yml"]:
                    shutil.copy2(item, backup_dir / item.name)
                elif item.is_dir() and item.name not in [
                    "__pycache__",
                    ".git",
                    "venv",
                    "env",
                ]:
                    shutil.copytree(item, backup_dir / item.name)

        except Exception as e:
            self.error(f"备份项目文件失败: {e}")
            raise

    def _backup_project_config(self, project_dir: Path, backup_dir: Path):
        """备份项目配置"""
        try:
            # 复制配置文件
            config_dir = project_dir / "config"
            if config_dir.exists():
                shutil.copytree(config_dir, backup_dir / "config", dirs_exist_ok=True)

        except Exception as e:
            self.error(f"备份项目配置失败: {e}")
            raise

    def _backup_project_data(self, project_dir: Path, backup_dir: Path):
        """备份项目数据"""
        try:
            # 复制数据文件
            data_dir = project_dir / "data"
            if data_dir.exists():
                shutil.copytree(data_dir, backup_dir / "data", dirs_exist_ok=True)

        except Exception as e:
            self.error(f"备份项目数据失败: {e}")
            raise

    def _create_backup_info(
        self, backup_dir: Path, project_name: str, backup_name: str
    ):
        """创建备份信息"""
        try:
            # 创建备份信息
            info = {
                "project_name": project_name,
                "backup_name": backup_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "size": self._get_dir_size(backup_dir),
            }

            # 保存备份信息
            info_file = backup_dir / "backup_info.yml"
            with open(info_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(info, f, default_flow_style=False)

        except Exception as e:
            self.error(f"创建备份信息失败: {e}")
            raise

    def _compress_backup(self, backup_dir: Path):
        """压缩备份"""
        try:
            # 创建压缩文件
            backup_file = self.backups_dir / f"{backup_dir.name}.tar.gz"
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(backup_dir, arcname=backup_dir.name)

            # 删除备份目录
            shutil.rmtree(backup_dir)

        except Exception as e:
            self.error(f"压缩备份失败: {e}")
            raise

    def _extract_backup(self, backup_file: Path, extract_dir: Path):
        """解压备份"""
        try:
            # 解压备份文件
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(extract_dir)

        except Exception as e:
            self.error(f"解压备份失败: {e}")
            raise

    def _restore_project_files(self, backup_dir: Path, project_dir: Path):
        """恢复项目文件"""
        try:
            # 复制项目文件
            for item in backup_dir.glob("*"):
                if item.is_file() and item.name not in ["backup_info.yml"]:
                    shutil.copy2(item, project_dir / item.name)
                elif item.is_dir() and item.name not in ["config", "data"]:
                    shutil.copytree(item, project_dir / item.name, dirs_exist_ok=True)

        except Exception as e:
            self.error(f"恢复项目文件失败: {e}")
            raise

    def _restore_project_config(self, backup_dir: Path, project_dir: Path):
        """恢复项目配置"""
        try:
            # 复制配置文件
            config_dir = backup_dir / "config"
            if config_dir.exists():
                shutil.copytree(config_dir, project_dir / "config", dirs_exist_ok=True)

        except Exception as e:
            self.error(f"恢复项目配置失败: {e}")
            raise

    def _restore_project_data(self, backup_dir: Path, project_dir: Path):
        """恢复项目数据"""
        try:
            # 复制数据文件
            data_dir = backup_dir / "data"
            if data_dir.exists():
                shutil.copytree(data_dir, project_dir / "data", dirs_exist_ok=True)

        except Exception as e:
            self.error(f"恢复项目数据失败: {e}")
            raise

    def _get_backup_info(self, backup_name: str) -> Dict[str, Any]:
        """获取备份信息"""
        try:
            # 创建临时目录
            temp_dir = self.backups_dir / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 解压备份
            backup_file = self.backups_dir / f"{backup_name}.tar.gz"
            self._extract_backup(backup_file, temp_dir)

            # 读取备份信息
            info_file = temp_dir / "backup_info.yml"
            with open(info_file, "r", encoding="utf-8") as f:
                info = yaml.safe_load(f)

            # 清理临时目录
            shutil.rmtree(temp_dir)

            return info

        except Exception as e:
            self.error(f"获取备份信息失败: {e}")
            raise

    def _get_dir_size(self, directory: Path) -> str:
        """获取目录大小"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)

            # 转换为可读格式
            for unit in ["B", "KB", "MB", "GB"]:
                if total_size < 1024:
                    return f"{total_size:.2f}{unit}"
                total_size /= 1024

            return f"{total_size:.2f}TB"

        except Exception as e:
            self.error(f"获取目录大小失败: {e}")
            raise


# CLI命令
@click.group()
def backup():
    """备份命令"""
    pass


@backup.command()
@click.argument("project_name")
@click.option("--name", "-n", help="备份名称")
def project(project_name: str, name: Optional[str]):
    """备份项目"""
    cmd = BackupCommand()
    cmd.project(project_name, name)


@backup.command()
@click.argument("project_name")
@click.option("--name", "-n", help="备份名称")
def data(project_name: str, name: Optional[str]):
    """备份数据"""
    cmd = BackupCommand()
    cmd.data(project_name, name)


@backup.command()
@click.argument("project_name")
@click.option("--name", "-n", help="备份名称")
def config(project_name: str, name: Optional[str]):
    """备份配置"""
    cmd = BackupCommand()
    cmd.config(project_name, name)


@backup.command()
@click.argument("backup_name")
@click.option("--project", "-p", help="项目名称")
def restore(backup_name: str, project: Optional[str]):
    """恢复备份"""
    cmd = BackupCommand()
    cmd.restore(backup_name, project)


@backup.command()
@click.option("--project", "-p", help="项目名称")
def list(project: Optional[str]):
    """列出备份"""
    cmd = BackupCommand()
    cmd.list(project)


@backup.command()
@click.argument("backup_name")
def delete(backup_name: str):
    """删除备份"""
    cmd = BackupCommand()
    cmd.delete(backup_name)
