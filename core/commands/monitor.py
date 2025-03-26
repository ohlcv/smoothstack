#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控命令模块

提供监控相关的命令，包括：
- 服务监控
- 资源监控
- 性能监控
- 告警管理
"""

import os
import sys
import yaml
import click
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MonitorCommand(BaseCommand):
    """监控命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def service(self, project_name: str, service: Optional[str] = None):
        """监控服务"""
        try:
            self.info(f"监控服务: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 监控服务
            if service:
                if os.system(f"docker-compose ps {service}") != 0:
                    raise RuntimeError(f"监控服务失败: {service}")
            else:
                if os.system("docker-compose ps") != 0:
                    raise RuntimeError("监控服务失败")

        except Exception as e:
            self.error(f"监控服务失败: {e}")
            raise

    def resource(self, project_name: str):
        """监控资源"""
        try:
            self.info(f"监控资源: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 监控容器资源
            if os.system("docker stats --no-stream") != 0:
                raise RuntimeError("监控容器资源失败")

            # 监控系统资源
            self._monitor_system_resources()

        except Exception as e:
            self.error(f"监控资源失败: {e}")
            raise

    def performance(self, project_name: str, duration: int = 60):
        """监控性能"""
        try:
            self.info(f"监控性能: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 监控容器性能
            if (
                os.system(
                    f"docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'"
                )
                != 0
            ):
                raise RuntimeError("监控容器性能失败")

            # 监控系统性能
            self._monitor_system_performance(duration)

        except Exception as e:
            self.error(f"监控性能失败: {e}")
            raise

    def alert(self, project_name: str, action: str, **kwargs):
        """管理告警"""
        try:
            self.info(f"管理告警: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查告警配置
            config_file = project_dir / "monitor" / "alerts.yml"
            if not config_file.exists():
                raise RuntimeError(f"告警配置不存在: {project_name}")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 管理告警
            if action == "add":
                self._add_alert(config, **kwargs)
            elif action == "remove":
                self._remove_alert(config, **kwargs)
            elif action == "list":
                self._list_alerts(config)
            elif action == "test":
                self._test_alert(config, **kwargs)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("告警配置已更新")

        except Exception as e:
            self.error(f"管理告警失败: {e}")
            raise

    def _monitor_system_resources(self):
        """监控系统资源"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.info(f"CPU使用率: {cpu_percent}%")

            # 内存使用率
            memory = psutil.virtual_memory()
            self.info(f"内存使用率: {memory.percent}%")

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            self.info(f"磁盘使用率: {disk.percent}%")

            # 网络使用率
            net_io = psutil.net_io_counters()
            self.info(f"网络发送: {net_io.bytes_sent / 1024 / 1024:.2f}MB")
            self.info(f"网络接收: {net_io.bytes_recv / 1024 / 1024:.2f}MB")

        except Exception as e:
            self.error(f"监控系统资源失败: {e}")
            raise

    def _monitor_system_performance(self, duration: int):
        """监控系统性能"""
        try:
            # 开始时间
            start_time = datetime.now()

            # 监控CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.info(f"CPU使用率: {cpu_percent}%")

            # 监控内存
            memory = psutil.virtual_memory()
            self.info(f"内存使用率: {memory.percent}%")

            # 监控磁盘
            disk = psutil.disk_usage("/")
            self.info(f"磁盘使用率: {disk.percent}%")

            # 监控网络
            net_io = psutil.net_io_counters()
            self.info(f"网络发送: {net_io.bytes_sent / 1024 / 1024:.2f}MB")
            self.info(f"网络接收: {net_io.bytes_recv / 1024 / 1024:.2f}MB")

            # 监控进程
            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent"]
            ):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # 按CPU使用率排序
            processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            self.info("\n进程列表:")
            for proc in processes[:10]:
                self.info(
                    f"PID: {proc['pid']}, 名称: {proc['name']}, CPU: {proc['cpu_percent']}%, 内存: {proc['memory_percent']:.1f}%"
                )

            # 结束时间
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.info(f"\n监控时长: {duration:.1f}秒")

        except Exception as e:
            self.error(f"监控系统性能失败: {e}")
            raise

    def _add_alert(self, config: Dict[str, Any], **kwargs):
        """添加告警"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("告警名称不能为空")

            # 添加告警
            name = kwargs.pop("name")
            config[name] = kwargs

            self.success(f"添加告警成功: {name}")

        except Exception as e:
            self.error(f"添加告警失败: {e}")
            raise

    def _remove_alert(self, config: Dict[str, Any], **kwargs):
        """移除告警"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("告警名称不能为空")

            # 移除告警
            name = kwargs["name"]
            if name in config:
                del config[name]
                self.success(f"移除告警成功: {name}")
            else:
                self.warning(f"告警不存在: {name}")

        except Exception as e:
            self.error(f"移除告警失败: {e}")
            raise

    def _list_alerts(self, config: Dict[str, Any]):
        """列出告警"""
        try:
            if not config:
                self.info("未配置告警")
                return

            self.info("\n告警列表:")
            for name, alert in config.items():
                self.info(f"名称: {name}")
                for key, value in alert.items():
                    self.info(f"  {key}: {value}")

        except Exception as e:
            self.error(f"列出告警失败: {e}")
            raise

    def _test_alert(self, config: Dict[str, Any], **kwargs):
        """测试告警"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("告警名称不能为空")

            # 测试告警
            name = kwargs["name"]
            if name in config:
                alert = config[name]
                self.info(f"测试告警: {name}")
                self.info(f"配置: {alert}")
                # TODO: 实现告警测试逻辑
            else:
                self.warning(f"告警不存在: {name}")

        except Exception as e:
            self.error(f"测试告警失败: {e}")
            raise


# CLI命令
@click.group()
def monitor():
    """监控命令"""
    pass


@monitor.command()
@click.argument("project_name")
@click.option("--service", "-s", help="服务名称")
def service(project_name: str, service: Optional[str]):
    """监控服务"""
    cmd = MonitorCommand()
    cmd.service(project_name, service)


@monitor.command()
@click.argument("project_name")
def resource(project_name: str):
    """监控资源"""
    cmd = MonitorCommand()
    cmd.resource(project_name)


@monitor.command()
@click.argument("project_name")
@click.option("--duration", "-d", default=60, help="监控时长(秒)")
def performance(project_name: str, duration: int):
    """监控性能"""
    cmd = MonitorCommand()
    cmd.performance(project_name, duration)


@monitor.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="告警名称")
@click.option("--type", "-t", help="告警类型")
@click.option("--threshold", "-v", help="告警阈值")
@click.option("--action", "-a", help="告警动作")
def alert(project_name: str, action: str, **kwargs):
    """管理告警"""
    cmd = MonitorCommand()
    cmd.alert(project_name, action, **kwargs)
