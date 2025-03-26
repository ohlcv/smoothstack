#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
存储命令模块

提供存储相关的命令，包括：
- 存储配置
- 存储监控
- 存储备份
- 存储恢复
"""

import os
import sys
import yaml
import click
import shutil
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StorageCommand(BaseCommand):
    """存储命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.storage_dir = self.project_root / "storage"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def config(self, project_name: str, action: str, **kwargs):
        """存储配置"""
        try:
            self.info(f"存储配置: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查存储配置
            config_file = project_dir / "storage" / "config.yml"
            if not config_file.exists():
                config = {}
            else:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

            # 配置存储
            if action == "add":
                self._add_storage_config(config, **kwargs)
            elif action == "remove":
                self._remove_storage_config(config, **kwargs)
            elif action == "update":
                self._update_storage_config(config, **kwargs)
            elif action == "show":
                self._show_storage_config(config)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("存储配置已更新")

        except Exception as e:
            self.error(f"存储配置失败: {e}")
            raise

    def monitor(self, project_name: str):
        """存储监控"""
        try:
            self.info(f"存储监控: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查存储配置
            config_file = project_dir / "storage" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("存储配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 监控存储
            self._monitor_storage(config)

        except Exception as e:
            self.error(f"存储监控失败: {e}")
            raise

    def backup(self, project_name: str, backup_name: Optional[str] = None):
        """存储备份"""
        try:
            self.info(f"存储备份: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查存储配置
            config_file = project_dir / "storage" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("存储配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 生成备份名称
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{project_name}_storage_{timestamp}"

            # 创建备份目录
            backup_dir = self.storage_dir / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 备份存储
            self._backup_storage(config, backup_dir)

            # 创建备份信息
            self._create_backup_info(backup_dir, project_name, backup_name)

            # 压缩备份
            self._compress_backup(backup_dir)

            self.success(f"存储备份成功: {backup_name}")

        except Exception as e:
            self.error(f"存储备份失败: {e}")
            raise

    def restore(self, backup_name: str, project_name: Optional[str] = None):
        """存储恢复"""
        try:
            self.info(f"存储恢复: {backup_name}")

            # 检查备份文件
            backup_file = self.storage_dir / f"{backup_name}.tar.gz"
            if not backup_file.exists():
                raise RuntimeError(f"备份文件不存在: {backup_name}")

            # 创建临时目录
            temp_dir = self.storage_dir / "temp"
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

            # 恢复存储
            self._restore_storage(temp_dir, project_dir)

            # 清理临时目录
            shutil.rmtree(temp_dir)

            self.success(f"存储恢复成功: {project_name}")

        except Exception as e:
            self.error(f"存储恢复失败: {e}")
            raise

    def _add_storage_config(self, config: Dict[str, Any], **kwargs):
        """添加存储配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("存储名称不能为空")

            # 添加配置
            name = kwargs.pop("name")
            config[name] = kwargs

            self.success(f"添加存储配置成功: {name}")

        except Exception as e:
            self.error(f"添加存储配置失败: {e}")
            raise

    def _remove_storage_config(self, config: Dict[str, Any], **kwargs):
        """移除存储配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("存储名称不能为空")

            # 移除配置
            name = kwargs["name"]
            if name in config:
                del config[name]
                self.success(f"移除存储配置成功: {name}")
            else:
                self.warning(f"存储配置不存在: {name}")

        except Exception as e:
            self.error(f"移除存储配置失败: {e}")
            raise

    def _update_storage_config(self, config: Dict[str, Any], **kwargs):
        """更新存储配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("存储名称不能为空")

            # 更新配置
            name = kwargs.pop("name")
            if name in config:
                config[name].update(kwargs)
                self.success(f"更新存储配置成功: {name}")
            else:
                self.warning(f"存储配置不存在: {name}")

        except Exception as e:
            self.error(f"更新存储配置失败: {e}")
            raise

    def _show_storage_config(self, config: Dict[str, Any]):
        """显示存储配置"""
        try:
            if not config:
                self.info("未配置存储")
                return

            self.info("\n存储配置:")
            for name, storage in config.items():
                self.info(f"名称: {name}")
                for key, value in storage.items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"显示存储配置失败: {e}")
            raise

    def _monitor_storage(self, config: Dict[str, Any]):
        """监控存储"""
        try:
            # 获取磁盘分区
            partitions = psutil.disk_partitions()

            self.info("\n磁盘分区:")
            for partition in partitions:
                # 获取使用情况
                usage = psutil.disk_usage(partition.mountpoint)
                self.info(f"设备: {partition.device}")
                self.info(f"挂载点: {partition.mountpoint}")
                self.info(f"文件系统: {partition.fstype}")
                self.info(f"总空间: {usage.total / 1024 / 1024 / 1024:.2f}GB")
                self.info(f"已用空间: {usage.used / 1024 / 1024 / 1024:.2f}GB")
                self.info(f"可用空间: {usage.free / 1024 / 1024 / 1024:.2f}GB")
                self.info(f"使用率: {usage.percent}%")
                self.info("")

            # 获取IO统计
            io_counters = psutil.disk_io_counters()
            self.info("\nIO统计:")
            self.info(f"读取字节数: {io_counters.read_bytes / 1024 / 1024:.2f}MB")
            self.info(f"写入字节数: {io_counters.write_bytes / 1024 / 1024:.2f}MB")
            self.info(f"读取次数: {io_counters.read_count}")
            self.info(f"写入次数: {io_counters.write_count}")

        except Exception as e:
            self.error(f"监控存储失败: {e}")
            raise

    def _backup_storage(self, config: Dict[str, Any], backup_dir: Path):
        """备份存储"""
        try:
            # 备份存储配置
            config_file = backup_dir / "config.yml"
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            # 备份存储数据
            for name, storage in config.items():
                # 获取存储路径
                storage_path = Path(storage.get("path", ""))
                if not storage_path.exists():
                    self.warning(f"存储路径不存在: {storage_path}")
                    continue

                # 创建备份目录
                storage_backup_dir = backup_dir / name
                storage_backup_dir.mkdir(parents=True, exist_ok=True)

                # 复制存储数据
                if storage_path.is_file():
                    shutil.copy2(storage_path, storage_backup_dir / storage_path.name)
                else:
                    shutil.copytree(
                        storage_path, storage_backup_dir / storage_path.name
                    )

        except Exception as e:
            self.error(f"备份存储失败: {e}")
            raise

    def _restore_storage(self, backup_dir: Path, project_dir: Path):
        """恢复存储"""
        try:
            # 恢复存储配置
            config_file = backup_dir / "config.yml"
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 恢复存储数据
            for name, storage in config.items():
                # 获取存储路径
                storage_path = project_dir / storage.get("path", "")
                storage_path.parent.mkdir(parents=True, exist_ok=True)

                # 获取备份路径
                storage_backup_dir = backup_dir / name
                if not storage_backup_dir.exists():
                    self.warning(f"备份路径不存在: {storage_backup_dir}")
                    continue

                # 复制存储数据
                if storage_path.is_file():
                    shutil.copy2(storage_backup_dir / storage_path.name, storage_path)
                else:
                    shutil.copytree(
                        storage_backup_dir / storage_path.name, storage_path
                    )

        except Exception as e:
            self.error(f"恢复存储失败: {e}")
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
            backup_file = self.storage_dir / f"{backup_dir.name}.tar.gz"
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
def storage():
    """存储命令"""
    pass


@storage.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="存储名称")
@click.option("--type", "-t", help="存储类型")
@click.option("--path", "-p", help="存储路径")
@click.option("--size", "-s", help="存储大小")
def config(project_name: str, action: str, **kwargs):
    """存储配置"""
    cmd = StorageCommand()
    cmd.config(project_name, action, **kwargs)


@storage.command()
@click.argument("project_name")
def monitor(project_name: str):
    """存储监控"""
    cmd = StorageCommand()
    cmd.monitor(project_name)


@storage.command()
@click.argument("project_name")
@click.option("--name", "-n", help="备份名称")
def backup(project_name: str, name: Optional[str]):
    """存储备份"""
    cmd = StorageCommand()
    cmd.backup(project_name, name)


@storage.command()
@click.argument("backup_name")
@click.option("--project", "-p", help="项目名称")
def restore(backup_name: str, project: Optional[str]):
    """存储恢复"""
    cmd = StorageCommand()
    cmd.restore(backup_name, project)
