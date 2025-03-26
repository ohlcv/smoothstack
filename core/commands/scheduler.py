#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调度命令模块

提供调度相关的命令，包括：
- 调度配置
- 调度监控
- 调度管理
- 调度日志
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


class SchedulerCommand(BaseCommand):
    """调度命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.scheduler_dir = self.project_root / "scheduler"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.scheduler_dir.mkdir(parents=True, exist_ok=True)

    def config(self, project_name: str, action: str, **kwargs):
        """调度配置"""
        try:
            self.info(f"调度配置: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查调度配置
            config_file = project_dir / "scheduler" / "config.yml"
            if not config_file.exists():
                config = {}
            else:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

            # 配置调度
            if action == "add":
                self._add_scheduler_config(config, **kwargs)
            elif action == "remove":
                self._remove_scheduler_config(config, **kwargs)
            elif action == "update":
                self._update_scheduler_config(config, **kwargs)
            elif action == "show":
                self._show_scheduler_config(config)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("调度配置已更新")

        except Exception as e:
            self.error(f"调度配置失败: {e}")
            raise

    def monitor(self, project_name: str):
        """调度监控"""
        try:
            self.info(f"调度监控: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查调度配置
            config_file = project_dir / "scheduler" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("调度配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 监控调度
            self._monitor_scheduler(config)

        except Exception as e:
            self.error(f"调度监控失败: {e}")
            raise

    def manage(
        self,
        project_name: str,
        action: str,
        scheduler_name: Optional[str] = None,
        **kwargs,
    ):
        """调度管理"""
        try:
            self.info(f"调度管理: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查调度配置
            config_file = project_dir / "scheduler" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("调度配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 管理调度
            if action == "start":
                self._start_scheduler(config, scheduler_name)
            elif action == "stop":
                self._stop_scheduler(config, scheduler_name)
            elif action == "restart":
                self._restart_scheduler(config, scheduler_name)
            elif action == "status":
                self._status_scheduler(config, scheduler_name)
            elif action == "trigger":
                self._trigger_scheduler(config, scheduler_name)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

        except Exception as e:
            self.error(f"调度管理失败: {e}")
            raise

    def log(self, project_name: str, scheduler_name: Optional[str] = None, **kwargs):
        """调度日志"""
        try:
            self.info(f"调度日志: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查调度配置
            config_file = project_dir / "scheduler" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("调度配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 查看日志
            self._view_scheduler_log(config, scheduler_name, **kwargs)

        except Exception as e:
            self.error(f"查看调度日志失败: {e}")
            raise

    def _add_scheduler_config(self, config: Dict[str, Any], **kwargs):
        """添加调度配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("调度名称不能为空")

            # 添加配置
            name = kwargs.pop("name")
            config[name] = kwargs

            self.success(f"添加调度配置成功: {name}")

        except Exception as e:
            self.error(f"添加调度配置失败: {e}")
            raise

    def _remove_scheduler_config(self, config: Dict[str, Any], **kwargs):
        """移除调度配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("调度名称不能为空")

            # 移除配置
            name = kwargs["name"]
            if name in config:
                del config[name]
                self.success(f"移除调度配置成功: {name}")
            else:
                self.warning(f"调度配置不存在: {name}")

        except Exception as e:
            self.error(f"移除调度配置失败: {e}")
            raise

    def _update_scheduler_config(self, config: Dict[str, Any], **kwargs):
        """更新调度配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("调度名称不能为空")

            # 更新配置
            name = kwargs.pop("name")
            if name in config:
                config[name].update(kwargs)
                self.success(f"更新调度配置成功: {name}")
            else:
                self.warning(f"调度配置不存在: {name}")

        except Exception as e:
            self.error(f"更新调度配置失败: {e}")
            raise

    def _show_scheduler_config(self, config: Dict[str, Any]):
        """显示调度配置"""
        try:
            if not config:
                self.info("未配置调度")
                return

            self.info("\n调度配置:")
            for name, scheduler in config.items():
                self.info(f"名称: {name}")
                for key, value in scheduler.items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"显示调度配置失败: {e}")
            raise

    def _monitor_scheduler(self, config: Dict[str, Any]):
        """监控调度"""
        try:
            # 获取系统资源
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            self.info("\n系统资源:")
            self.info(f"CPU使用率: {cpu_percent}%")
            self.info(f"内存使用率: {memory.percent}%")

            # 获取调度统计
            for name, scheduler in config.items():
                # 获取调度路径
                scheduler_path = Path(scheduler.get("path", ""))
                if not scheduler_path.exists():
                    self.warning(f"调度路径不存在: {scheduler_path}")
                    continue

                # 获取调度大小
                scheduler_size = self._get_dir_size(scheduler_path)
                self.info(f"\n调度 {name}:")
                self.info(f"路径: {scheduler_path}")
                self.info(f"大小: {scheduler_size}")

                # 获取调度统计
                if "type" in scheduler and scheduler["type"] == "apscheduler":
                    self._monitor_apscheduler_scheduler(scheduler)
                elif "type" in scheduler and scheduler["type"] == "celery":
                    self._monitor_celery_scheduler(scheduler)

        except Exception as e:
            self.error(f"监控调度失败: {e}")
            raise

    def _start_scheduler(
        self, config: Dict[str, Any], scheduler_name: Optional[str] = None
    ):
        """启动调度"""
        try:
            # 启动指定调度
            if scheduler_name:
                if scheduler_name in config:
                    self._start_single_scheduler(config[scheduler_name])
                else:
                    self.warning(f"调度配置不存在: {scheduler_name}")
            else:
                # 启动所有调度
                for name, scheduler in config.items():
                    self._start_single_scheduler(scheduler)

        except Exception as e:
            self.error(f"启动调度失败: {e}")
            raise

    def _stop_scheduler(
        self, config: Dict[str, Any], scheduler_name: Optional[str] = None
    ):
        """停止调度"""
        try:
            # 停止指定调度
            if scheduler_name:
                if scheduler_name in config:
                    self._stop_single_scheduler(config[scheduler_name])
                else:
                    self.warning(f"调度配置不存在: {scheduler_name}")
            else:
                # 停止所有调度
                for name, scheduler in config.items():
                    self._stop_single_scheduler(scheduler)

        except Exception as e:
            self.error(f"停止调度失败: {e}")
            raise

    def _restart_scheduler(
        self, config: Dict[str, Any], scheduler_name: Optional[str] = None
    ):
        """重启调度"""
        try:
            # 重启指定调度
            if scheduler_name:
                if scheduler_name in config:
                    self._restart_single_scheduler(config[scheduler_name])
                else:
                    self.warning(f"调度配置不存在: {scheduler_name}")
            else:
                # 重启所有调度
                for name, scheduler in config.items():
                    self._restart_single_scheduler(scheduler)

        except Exception as e:
            self.error(f"重启调度失败: {e}")
            raise

    def _status_scheduler(
        self, config: Dict[str, Any], scheduler_name: Optional[str] = None
    ):
        """调度状态"""
        try:
            # 获取指定调度状态
            if scheduler_name:
                if scheduler_name in config:
                    self._status_single_scheduler(config[scheduler_name])
                else:
                    self.warning(f"调度配置不存在: {scheduler_name}")
            else:
                # 获取所有调度状态
                for name, scheduler in config.items():
                    self._status_single_scheduler(scheduler)

        except Exception as e:
            self.error(f"获取调度状态失败: {e}")
            raise

    def _trigger_scheduler(
        self, config: Dict[str, Any], scheduler_name: Optional[str] = None
    ):
        """触发调度"""
        try:
            # 触发指定调度
            if scheduler_name:
                if scheduler_name in config:
                    self._trigger_single_scheduler(config[scheduler_name])
                else:
                    self.warning(f"调度配置不存在: {scheduler_name}")
            else:
                # 触发所有调度
                for name, scheduler in config.items():
                    self._trigger_single_scheduler(scheduler)

        except Exception as e:
            self.error(f"触发调度失败: {e}")
            raise

    def _view_scheduler_log(
        self, config: Dict[str, Any], scheduler_name: Optional[str] = None, **kwargs
    ):
        """查看调度日志"""
        try:
            # 查看指定调度日志
            if scheduler_name:
                if scheduler_name in config:
                    self._view_single_scheduler_log(config[scheduler_name], **kwargs)
                else:
                    self.warning(f"调度配置不存在: {scheduler_name}")
            else:
                # 查看所有调度日志
                for name, scheduler in config.items():
                    self._view_single_scheduler_log(scheduler, **kwargs)

        except Exception as e:
            self.error(f"查看调度日志失败: {e}")
            raise

    def _start_single_scheduler(self, scheduler: Dict[str, Any]):
        """启动单个调度"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 启动调度
            if "type" in scheduler:
                if scheduler["type"] == "apscheduler":
                    self._start_apscheduler_scheduler(scheduler)
                elif scheduler["type"] == "celery":
                    self._start_celery_scheduler(scheduler)
                else:
                    # 启动文件调度
                    self._start_file_scheduler(scheduler)

        except Exception as e:
            self.error(f"启动调度失败: {e}")
            raise

    def _stop_single_scheduler(self, scheduler: Dict[str, Any]):
        """停止单个调度"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 停止调度
            if "type" in scheduler:
                if scheduler["type"] == "apscheduler":
                    self._stop_apscheduler_scheduler(scheduler)
                elif scheduler["type"] == "celery":
                    self._stop_celery_scheduler(scheduler)
                else:
                    # 停止文件调度
                    self._stop_file_scheduler(scheduler)

        except Exception as e:
            self.error(f"停止调度失败: {e}")
            raise

    def _restart_single_scheduler(self, scheduler: Dict[str, Any]):
        """重启单个调度"""
        try:
            # 停止调度
            self._stop_single_scheduler(scheduler)

            # 启动调度
            self._start_single_scheduler(scheduler)

        except Exception as e:
            self.error(f"重启调度失败: {e}")
            raise

    def _status_single_scheduler(self, scheduler: Dict[str, Any]):
        """单个调度状态"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 获取调度状态
            if "type" in scheduler:
                if scheduler["type"] == "apscheduler":
                    self._status_apscheduler_scheduler(scheduler)
                elif scheduler["type"] == "celery":
                    self._status_celery_scheduler(scheduler)
                else:
                    # 获取文件调度状态
                    self._status_file_scheduler(scheduler)

        except Exception as e:
            self.error(f"获取调度状态失败: {e}")
            raise

    def _trigger_single_scheduler(self, scheduler: Dict[str, Any]):
        """触发单个调度"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 触发调度
            if "type" in scheduler:
                if scheduler["type"] == "apscheduler":
                    self._trigger_apscheduler_scheduler(scheduler)
                elif scheduler["type"] == "celery":
                    self._trigger_celery_scheduler(scheduler)
                else:
                    # 触发文件调度
                    self._trigger_file_scheduler(scheduler)

        except Exception as e:
            self.error(f"触发调度失败: {e}")
            raise

    def _view_single_scheduler_log(self, scheduler: Dict[str, Any], **kwargs):
        """查看单个调度日志"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 查看日志
            if "type" in scheduler:
                if scheduler["type"] == "apscheduler":
                    self._view_apscheduler_scheduler_log(scheduler, **kwargs)
                elif scheduler["type"] == "celery":
                    self._view_celery_scheduler_log(scheduler, **kwargs)
                else:
                    # 查看文件调度日志
                    self._view_file_scheduler_log(scheduler, **kwargs)

        except Exception as e:
            self.error(f"查看调度日志失败: {e}")
            raise

    def _monitor_apscheduler_scheduler(self, scheduler: Dict[str, Any]):
        """监控APScheduler调度"""
        try:
            # 获取APScheduler连接
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler_instance = BackgroundScheduler()
            scheduler_instance.start()

            # 获取调度信息
            self.info("\nAPScheduler调度信息:")
            self.info(f"调度器状态: {scheduler_instance.state}")
            self.info(f"任务数量: {len(scheduler_instance.get_jobs())}")

            # 关闭调度器
            scheduler_instance.shutdown()

        except Exception as e:
            self.error(f"监控APScheduler调度失败: {e}")
            raise

    def _monitor_celery_scheduler(self, scheduler: Dict[str, Any]):
        """监控Celery调度"""
        try:
            # 获取Celery连接
            from celery import Celery

            app = Celery(
                scheduler.get("name", "celery"),
                broker=scheduler.get("broker", "redis://localhost:6379/0"),
            )

            # 获取调度信息
            self.info("\nCelery调度信息:")
            self.info(f"调度器状态: {app.control.inspect().active()}")
            self.info(f"任务数量: {len(app.control.inspect().scheduled())}")

        except Exception as e:
            self.error(f"监控Celery调度失败: {e}")
            raise

    def _start_apscheduler_scheduler(self, scheduler: Dict[str, Any]):
        """启动APScheduler调度"""
        try:
            # 获取APScheduler连接
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler_instance = BackgroundScheduler()

            # 添加任务
            for job in scheduler.get("jobs", []):
                scheduler_instance.add_job(
                    job.get("func"),
                    job.get("trigger", "interval"),
                    **job.get("args", {}),
                )

            # 启动调度器
            scheduler_instance.start()

            self.success(f"启动APScheduler调度成功: {scheduler.get('name', '')}")

        except Exception as e:
            self.error(f"启动APScheduler调度失败: {e}")
            raise

    def _start_celery_scheduler(self, scheduler: Dict[str, Any]):
        """启动Celery调度"""
        try:
            # 获取Celery连接
            from celery import Celery

            app = Celery(
                scheduler.get("name", "celery"),
                broker=scheduler.get("broker", "redis://localhost:6379/0"),
            )

            # 启动调度器
            app.worker_main(["worker", "--loglevel=info"])

            self.success(f"启动Celery调度成功: {scheduler.get('name', '')}")

        except Exception as e:
            self.error(f"启动Celery调度失败: {e}")
            raise

    def _start_file_scheduler(self, scheduler: Dict[str, Any]):
        """启动文件调度"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                scheduler_path.mkdir(parents=True, exist_ok=True)

            self.success(f"启动文件调度成功: {scheduler_path}")

        except Exception as e:
            self.error(f"启动文件调度失败: {e}")
            raise

    def _stop_apscheduler_scheduler(self, scheduler: Dict[str, Any]):
        """停止APScheduler调度"""
        try:
            # 获取APScheduler连接
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler_instance = BackgroundScheduler()

            # 停止调度器
            scheduler_instance.shutdown()

            self.success(f"停止APScheduler调度成功: {scheduler.get('name', '')}")

        except Exception as e:
            self.error(f"停止APScheduler调度失败: {e}")
            raise

    def _stop_celery_scheduler(self, scheduler: Dict[str, Any]):
        """停止Celery调度"""
        try:
            # 获取Celery连接
            from celery import Celery

            app = Celery(
                scheduler.get("name", "celery"),
                broker=scheduler.get("broker", "redis://localhost:6379/0"),
            )

            # 停止调度器
            app.control.shutdown()

            self.success(f"停止Celery调度成功: {scheduler.get('name', '')}")

        except Exception as e:
            self.error(f"停止Celery调度失败: {e}")
            raise

    def _stop_file_scheduler(self, scheduler: Dict[str, Any]):
        """停止文件调度"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 停止调度
            for file in scheduler_path.glob("*"):
                if file.is_file():
                    file.unlink()

            self.success(f"停止文件调度成功: {scheduler_path}")

        except Exception as e:
            self.error(f"停止文件调度失败: {e}")
            raise

    def _status_apscheduler_scheduler(self, scheduler: Dict[str, Any]):
        """APScheduler调度状态"""
        try:
            # 获取APScheduler连接
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler_instance = BackgroundScheduler()
            scheduler_instance.start()

            # 获取调度状态
            self.info(f"\nAPScheduler调度 {scheduler.get('name', '')} 状态:")
            self.info(f"调度器状态: {scheduler_instance.state}")
            self.info(f"任务数量: {len(scheduler_instance.get_jobs())}")
            self.info(f"状态: 运行中")

            # 关闭调度器
            scheduler_instance.shutdown()

        except Exception as e:
            self.error(f"获取APScheduler调度状态失败: {e}")
            raise

    def _status_celery_scheduler(self, scheduler: Dict[str, Any]):
        """Celery调度状态"""
        try:
            # 获取Celery连接
            from celery import Celery

            app = Celery(
                scheduler.get("name", "celery"),
                broker=scheduler.get("broker", "redis://localhost:6379/0"),
            )

            # 获取调度状态
            self.info(f"\nCelery调度 {scheduler.get('name', '')} 状态:")
            self.info(f"调度器状态: {app.control.inspect().active()}")
            self.info(f"任务数量: {len(app.control.inspect().scheduled())}")
            self.info(f"状态: 运行中")

        except Exception as e:
            self.error(f"获取Celery调度状态失败: {e}")
            raise

    def _status_file_scheduler(self, scheduler: Dict[str, Any]):
        """文件调度状态"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 获取调度状态
            file_count = len(list(scheduler_path.glob("*")))
            self.info(f"\n文件调度 {scheduler_path} 状态:")
            self.info(f"文件数量: {file_count}")
            self.info(f"状态: 运行中")

        except Exception as e:
            self.error(f"获取文件调度状态失败: {e}")
            raise

    def _trigger_apscheduler_scheduler(self, scheduler: Dict[str, Any]):
        """触发APScheduler调度"""
        try:
            # 获取APScheduler连接
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler_instance = BackgroundScheduler()
            scheduler_instance.start()

            # 触发任务
            for job in scheduler.get("jobs", []):
                scheduler_instance.add_job(
                    job.get("func"),
                    job.get("trigger", "interval"),
                    **job.get("args", {}),
                )

            # 关闭调度器
            scheduler_instance.shutdown()

            self.success(f"触发APScheduler调度成功: {scheduler.get('name', '')}")

        except Exception as e:
            self.error(f"触发APScheduler调度失败: {e}")
            raise

    def _trigger_celery_scheduler(self, scheduler: Dict[str, Any]):
        """触发Celery调度"""
        try:
            # 获取Celery连接
            from celery import Celery

            app = Celery(
                scheduler.get("name", "celery"),
                broker=scheduler.get("broker", "redis://localhost:6379/0"),
            )

            # 触发任务
            for task in scheduler.get("tasks", []):
                app.send_task(task.get("name"), **task.get("args", {}))

            self.success(f"触发Celery调度成功: {scheduler.get('name', '')}")

        except Exception as e:
            self.error(f"触发Celery调度失败: {e}")
            raise

    def _trigger_file_scheduler(self, scheduler: Dict[str, Any]):
        """触发文件调度"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 触发调度
            for task in scheduler.get("tasks", []):
                task_file = scheduler_path / f"{task.get('name', '')}.txt"
                with open(task_file, "w", encoding="utf-8") as f:
                    f.write(str(task.get("args", {})))

            self.success(f"触发文件调度成功: {scheduler_path}")

        except Exception as e:
            self.error(f"触发文件调度失败: {e}")
            raise

    def _view_apscheduler_scheduler_log(self, scheduler: Dict[str, Any], **kwargs):
        """查看APScheduler调度日志"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 查看日志
            log_file = scheduler_path / "apscheduler.log"
            if not log_file.exists():
                self.warning(f"日志文件不存在: {log_file}")
                return

            # 读取日志
            with open(log_file, "r", encoding="utf-8") as f:
                logs = f.readlines()

            # 显示日志
            self.info(f"\nAPScheduler调度 {scheduler.get('name', '')} 日志:")
            for log in logs:
                self.info(log.strip())

        except Exception as e:
            self.error(f"查看APScheduler调度日志失败: {e}")
            raise

    def _view_celery_scheduler_log(self, scheduler: Dict[str, Any], **kwargs):
        """查看Celery调度日志"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 查看日志
            log_file = scheduler_path / "celery.log"
            if not log_file.exists():
                self.warning(f"日志文件不存在: {log_file}")
                return

            # 读取日志
            with open(log_file, "r", encoding="utf-8") as f:
                logs = f.readlines()

            # 显示日志
            self.info(f"\nCelery调度 {scheduler.get('name', '')} 日志:")
            for log in logs:
                self.info(log.strip())

        except Exception as e:
            self.error(f"查看Celery调度日志失败: {e}")
            raise

    def _view_file_scheduler_log(self, scheduler: Dict[str, Any], **kwargs):
        """查看文件调度日志"""
        try:
            # 获取调度路径
            scheduler_path = Path(scheduler.get("path", ""))
            if not scheduler_path.exists():
                self.warning(f"调度路径不存在: {scheduler_path}")
                return

            # 查看日志
            log_file = scheduler_path / "scheduler.log"
            if not log_file.exists():
                self.warning(f"日志文件不存在: {log_file}")
                return

            # 读取日志
            with open(log_file, "r", encoding="utf-8") as f:
                logs = f.readlines()

            # 显示日志
            self.info(f"\n文件调度 {scheduler_path} 日志:")
            for log in logs:
                self.info(log.strip())

        except Exception as e:
            self.error(f"查看文件调度日志失败: {e}")
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
def scheduler():
    """调度命令"""
    pass


@scheduler.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="调度名称")
@click.option("--type", "-t", help="调度类型")
@click.option("--path", "-p", help="调度路径")
@click.option("--broker", "-b", help="消息代理")
@click.option("--backend", "-B", help="结果后端")
@click.option("--jobs", "-j", help="任务列表")
@click.option("--tasks", "-T", help="任务列表")
def config(project_name: str, action: str, **kwargs):
    """调度配置"""
    cmd = SchedulerCommand()
    cmd.config(project_name, action, **kwargs)


@scheduler.command()
@click.argument("project_name")
def monitor(project_name: str):
    """调度监控"""
    cmd = SchedulerCommand()
    cmd.monitor(project_name)


@scheduler.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="调度名称")
def manage(project_name: str, action: str, name: Optional[str]):
    """调度管理"""
    cmd = SchedulerCommand()
    cmd.manage(project_name, action, name)


@scheduler.command()
@click.argument("project_name")
@click.option("--name", "-n", help="调度名称")
@click.option("--lines", "-l", help="日志行数")
def log(project_name: str, name: Optional[str], lines: Optional[int]):
    """调度日志"""
    cmd = SchedulerCommand()
    cmd.log(project_name, name, lines=lines)
