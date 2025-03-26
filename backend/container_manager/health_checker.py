#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器健康检查器

提供容器健康检查、状态监控和告警功能
"""

import os
import time
import logging
import threading
import json
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from datetime import datetime, timedelta
import docker
from docker.errors import NotFound, APIError

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.health_checker")


class HealthStatus:
    """健康状态常量"""

    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"


class HealthCheck:
    """健康检查配置"""

    def __init__(
        self,
        test: List[str],
        interval: int = 30,
        timeout: int = 30,
        retries: int = 3,
        start_period: int = 0,
    ):
        """
        初始化健康检查配置

        Args:
            test: 健康检查命令, 例如 ["CMD", "curl", "-f", "http://localhost"]
            interval: 健康检查间隔(秒)
            timeout: 超时时间(秒)
            retries: 重试次数
            start_period: 启动等待期(秒)
        """
        self.test = test
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self.start_period = start_period

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthCheck":
        """从字典创建健康检查配置"""
        return cls(
            test=data.get("test", ["CMD", "exit", "0"]),
            interval=data.get("interval", 30),
            timeout=data.get("timeout", 30),
            retries=data.get("retries", 3),
            start_period=data.get("start_period", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test": self.test,
            "interval": self.interval,
            "timeout": self.timeout,
            "retries": self.retries,
            "start_period": self.start_period,
        }


class HealthResult:
    """健康检查结果"""

    def __init__(
        self,
        status: str,
        container_id: str,
        container_name: str,
        check_time: datetime,
        details: Dict[str, Any] = None,
        message: str = "",
    ):
        """
        初始化健康检查结果

        Args:
            status: 健康状态
            container_id: 容器ID
            container_name: 容器名称
            check_time: 检查时间
            details: 详细信息
            message: 消息
        """
        self.status = status
        self.container_id = container_id
        self.container_name = container_name
        self.check_time = check_time
        self.details = details or {}
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "container_id": self.container_id,
            "container_name": self.container_name,
            "check_time": self.check_time.isoformat(),
            "details": self.details,
            "message": self.message,
        }


class ResourceThresholds:
    """资源阈值设置"""

    def __init__(
        self,
        cpu_warning: float = 80.0,
        cpu_critical: float = 95.0,
        memory_warning: float = 80.0,
        memory_critical: float = 95.0,
        disk_warning: float = 80.0,
        disk_critical: float = 95.0,
        restart_threshold: int = 3,
    ):
        """
        初始化资源阈值设置

        Args:
            cpu_warning: CPU使用率警告阈值
            cpu_critical: CPU使用率严重阈值
            memory_warning: 内存使用率警告阈值
            memory_critical: 内存使用率严重阈值
            disk_warning: 磁盘使用率警告阈值
            disk_critical: 磁盘使用率严重阈值
            restart_threshold: 重启次数阈值
        """
        self.cpu_warning = cpu_warning
        self.cpu_critical = cpu_critical
        self.memory_warning = memory_warning
        self.memory_critical = memory_critical
        self.disk_warning = disk_warning
        self.disk_critical = disk_critical
        self.restart_threshold = restart_threshold

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceThresholds":
        """从字典创建资源阈值设置"""
        return cls(
            cpu_warning=data.get("cpu_warning", 80.0),
            cpu_critical=data.get("cpu_critical", 95.0),
            memory_warning=data.get("memory_warning", 80.0),
            memory_critical=data.get("memory_critical", 95.0),
            disk_warning=data.get("disk_warning", 80.0),
            disk_critical=data.get("disk_critical", 95.0),
            restart_threshold=data.get("restart_threshold", 3),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cpu_warning": self.cpu_warning,
            "cpu_critical": self.cpu_critical,
            "memory_warning": self.memory_warning,
            "memory_critical": self.memory_critical,
            "disk_warning": self.disk_warning,
            "disk_critical": self.disk_critical,
            "restart_threshold": self.restart_threshold,
        }


class NotificationConfig:
    """通知配置"""

    def __init__(
        self,
        enabled: bool = True,
        notify_on_status_change: bool = True,
        notify_on_warning: bool = True,
        notify_on_critical: bool = True,
        notification_interval: int = 300,  # 10分钟
        notification_handlers: List[str] = None,
    ):
        """
        初始化通知配置

        Args:
            enabled: 是否启用通知
            notify_on_status_change: 状态变化时通知
            notify_on_warning: 警告状态时通知
            notify_on_critical: 严重状态时通知
            notification_interval: 通知间隔(秒)
            notification_handlers: 通知处理器列表
        """
        self.enabled = enabled
        self.notify_on_status_change = notify_on_status_change
        self.notify_on_warning = notify_on_warning
        self.notify_on_critical = notify_on_critical
        self.notification_interval = notification_interval
        self.notification_handlers = notification_handlers or ["console"]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationConfig":
        """从字典创建通知配置"""
        return cls(
            enabled=data.get("enabled", True),
            notify_on_status_change=data.get("notify_on_status_change", True),
            notify_on_warning=data.get("notify_on_warning", True),
            notify_on_critical=data.get("notify_on_critical", True),
            notification_interval=data.get("notification_interval", 300),
            notification_handlers=data.get("notification_handlers", ["console"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "notify_on_status_change": self.notify_on_status_change,
            "notify_on_warning": self.notify_on_warning,
            "notify_on_critical": self.notify_on_critical,
            "notification_interval": self.notification_interval,
            "notification_handlers": self.notification_handlers,
        }


class HealthChecker:
    """容器健康检查器"""

    def __init__(self, config_path: str = None):
        """
        初始化健康检查器

        Args:
            config_path: 配置文件路径
        """
        self.client = docker.from_env()
        self.config_path = config_path or os.path.expanduser(
            "~/.smoothstack/health_checker.json"
        )
        self.monitored_containers = set()
        self.check_results = {}  # 容器ID -> HealthResult
        self.previous_results = {}  # 容器ID -> HealthResult
        self.last_notification_time = {}  # 容器ID -> datetime
        self.thresholds = ResourceThresholds()
        self.notification_config = NotificationConfig()
        self.check_interval = 60  # 秒
        self.running = False
        self.check_thread = None
        self.notification_handlers = {
            "console": self._console_notification_handler,
            # 可以添加更多通知处理器: email, slack, webhook等
        }

        # 加载配置
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.thresholds = ResourceThresholds.from_dict(
                        config.get("thresholds", {})
                    )
                    self.notification_config = NotificationConfig.from_dict(
                        config.get("notification", {})
                    )
                    self.check_interval = config.get("check_interval", 60)
                logger.info(f"已从 {self.config_path} 加载健康检查配置")
            else:
                logger.info(f"配置文件 {self.config_path} 不存在，使用默认配置")
                self._save_config()  # 创建默认配置文件
        except Exception as e:
            logger.error(f"加载配置文件时出错: {e}")
            # 使用默认配置
            self.thresholds = ResourceThresholds()
            self.notification_config = NotificationConfig()
            self.check_interval = 60

    def _save_config(self):
        """保存配置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            config = {
                "thresholds": self.thresholds.to_dict(),
                "notification": self.notification_config.to_dict(),
                "check_interval": self.check_interval,
            }

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"已保存健康检查配置到 {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件时出错: {e}")

    def update_config(
        self,
        thresholds: Dict[str, Any] = None,
        notification: Dict[str, Any] = None,
        check_interval: int = None,
    ) -> bool:
        """
        更新配置

        Args:
            thresholds: 资源阈值设置
            notification: 通知配置
            check_interval: 检查间隔

        Returns:
            是否成功
        """
        try:
            if thresholds:
                self.thresholds = ResourceThresholds.from_dict(thresholds)
            if notification:
                self.notification_config = NotificationConfig.from_dict(notification)
            if check_interval is not None:
                self.check_interval = check_interval

            self._save_config()
            return True
        except Exception as e:
            logger.error(f"更新配置时出错: {e}")
            return False

    def add_container(self, container_id_or_name: str) -> bool:
        """
        添加容器到监控列表

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            是否成功
        """
        try:
            container = self.client.containers.get(container_id_or_name)
            self.monitored_containers.add(container.id)
            logger.info(f"已添加容器 {container.name} ({container.id[:12]}) 到监控列表")
            return True
        except Exception as e:
            logger.error(f"添加容器到监控列表时出错: {e}")
            return False

    def remove_container(self, container_id_or_name: str) -> bool:
        """
        从监控列表移除容器

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            是否成功
        """
        try:
            container = self.client.containers.get(container_id_or_name)
            if container.id in self.monitored_containers:
                self.monitored_containers.remove(container.id)
                logger.info(
                    f"已从监控列表移除容器 {container.name} ({container.id[:12]})"
                )
            return True
        except NotFound:
            # 容器不存在，尝试通过ID前缀移除
            removed = False
            for container_id in list(self.monitored_containers):
                if container_id.startswith(container_id_or_name):
                    self.monitored_containers.remove(container_id)
                    logger.info(f"已从监控列表移除容器ID {container_id[:12]}")
                    removed = True
            return removed
        except Exception as e:
            logger.error(f"从监控列表移除容器时出错: {e}")
            return False

    def list_monitored_containers(self) -> List[Dict[str, Any]]:
        """
        获取监控的容器列表

        Returns:
            容器信息列表
        """
        result = []
        for container_id in self.monitored_containers:
            try:
                container = self.client.containers.get(container_id)
                health_result = self.check_results.get(container_id)

                container_info = {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "health": (
                        health_result.status if health_result else HealthStatus.UNKNOWN
                    ),
                    "last_check": (
                        health_result.check_time.isoformat() if health_result else None
                    ),
                }
                result.append(container_info)
            except NotFound:
                # 容器已被移除，从监控列表中移除
                self.monitored_containers.remove(container_id)
            except Exception as e:
                logger.error(f"获取容器信息时出错: {e}")

        return result

    def get_health_report(self, container_id_or_name: str = None) -> Dict[str, Any]:
        """
        获取健康报告

        Args:
            container_id_or_name: 容器ID或名称，None表示获取所有监控容器的报告

        Returns:
            健康报告
        """
        if container_id_or_name:
            try:
                container = self.client.containers.get(container_id_or_name)
                report = self._generate_container_report(container.id)
                if report:
                    return report
                else:
                    return {"error": "容器未在监控列表中或尚未进行健康检查"}
            except NotFound:
                return {"error": "容器不存在"}
            except Exception as e:
                logger.error(f"获取容器健康报告时出错: {e}")
                return {"error": f"获取健康报告时出错: {str(e)}"}
        else:
            # 获取所有监控容器的报告
            reports = {}
            for container_id in self.monitored_containers:
                try:
                    report = self._generate_container_report(container_id)
                    if report:
                        reports[container_id] = report
                except Exception as e:
                    logger.error(f"获取容器健康报告时出错: {e}")

            return {
                "summary": {
                    "total": len(self.monitored_containers),
                    "healthy": sum(
                        1
                        for r in self.check_results.values()
                        if r.status == HealthStatus.HEALTHY
                    ),
                    "warning": sum(
                        1
                        for r in self.check_results.values()
                        if r.status == HealthStatus.WARNING
                    ),
                    "unhealthy": sum(
                        1
                        for r in self.check_results.values()
                        if r.status == HealthStatus.UNHEALTHY
                    ),
                    "unknown": sum(
                        1
                        for container_id in self.monitored_containers
                        if container_id not in self.check_results
                    ),
                },
                "reports": reports,
            }

    def _generate_container_report(self, container_id: str) -> Dict[str, Any]:
        """
        生成容器健康报告

        Args:
            container_id: 容器ID

        Returns:
            健康报告
        """
        if container_id not in self.monitored_containers:
            return None

        try:
            container = self.client.containers.get(container_id)
            health_result = self.check_results.get(container_id)

            if not health_result:
                # 尚未进行健康检查
                return {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "health": HealthStatus.UNKNOWN,
                    "message": "尚未进行健康检查",
                }

            # 构建详细报告
            report = health_result.to_dict()
            report["container_status"] = container.status

            # 添加历史趋势数据 (未实现)

            return report
        except NotFound:
            # 容器已被移除，从监控列表中移除
            self.monitored_containers.remove(container_id)
            return None
        except Exception as e:
            logger.error(f"生成容器健康报告时出错: {e}")
            return None

    def check_container_health(self, container_id_or_name: str) -> HealthResult:
        """
        检查单个容器的健康状态

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            健康检查结果
        """
        try:
            container = self.client.containers.get(container_id_or_name)

            # 检查容器是否在运行
            if container.status != "running":
                result = HealthResult(
                    status=HealthStatus.UNKNOWN,
                    container_id=container.id,
                    container_name=container.name,
                    check_time=datetime.now(),
                    message=f"容器状态为 {container.status}，未运行",
                )
                self.check_results[container.id] = result
                return result

            # 获取容器详细信息
            container.reload()
            attrs = container.attrs

            # 检查Docker内置健康检查状态
            docker_health_status = None
            if "State" in attrs and "Health" in attrs["State"]:
                health = attrs["State"]["Health"]
                docker_health_status = health.get("Status")

            # 获取资源使用统计
            success, stats = self._get_container_stats(container.id)

            if not success:
                result = HealthResult(
                    status=HealthStatus.UNKNOWN,
                    container_id=container.id,
                    container_name=container.name,
                    check_time=datetime.now(),
                    message=f"获取容器统计信息失败: {stats.get('error', '未知错误')}",
                )
                self.check_results[container.id] = result
                return result

            # 检查资源使用情况
            status = HealthStatus.HEALTHY
            messages = []
            details = {"docker_health_status": docker_health_status, "stats": stats}

            # 根据Docker健康检查状态设置状态
            if docker_health_status:
                if docker_health_status == "unhealthy":
                    status = HealthStatus.UNHEALTHY
                    messages.append("Docker健康检查失败")
                elif docker_health_status == "starting":
                    status = HealthStatus.STARTING
                    messages.append("Docker健康检查正在启动")

            # 检查CPU使用率
            cpu_percent = stats["cpu"]["usage_percent"]
            if cpu_percent >= self.thresholds.cpu_critical:
                status = (
                    HealthStatus.UNHEALTHY if status == HealthStatus.HEALTHY else status
                )
                messages.append(
                    f"CPU使用率 ({cpu_percent:.2f}%) 超过严重阈值 ({self.thresholds.cpu_critical}%)"
                )
            elif cpu_percent >= self.thresholds.cpu_warning:
                status = (
                    HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                )
                messages.append(
                    f"CPU使用率 ({cpu_percent:.2f}%) 超过警告阈值 ({self.thresholds.cpu_warning}%)"
                )

            # 检查内存使用率
            memory_percent = stats["memory"]["usage_percent"]
            if memory_percent >= self.thresholds.memory_critical:
                status = (
                    HealthStatus.UNHEALTHY if status == HealthStatus.HEALTHY else status
                )
                messages.append(
                    f"内存使用率 ({memory_percent:.2f}%) 超过严重阈值 ({self.thresholds.memory_critical}%)"
                )
            elif memory_percent >= self.thresholds.memory_warning:
                status = (
                    HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                )
                messages.append(
                    f"内存使用率 ({memory_percent:.2f}%) 超过警告阈值 ({self.thresholds.memory_warning}%)"
                )

            # 检查重启次数
            restart_count = attrs.get("RestartCount", 0)
            if restart_count >= self.thresholds.restart_threshold:
                status = (
                    HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                )
                messages.append(
                    f"容器重启次数 ({restart_count}) 超过阈值 ({self.thresholds.restart_threshold})"
                )

            # 组装结果
            message = "; ".join(messages) if messages else "容器健康状态正常"
            result = HealthResult(
                status=status,
                container_id=container.id,
                container_name=container.name,
                check_time=datetime.now(),
                details=details,
                message=message,
            )

            # 保存结果并检查是否需要发送通知
            self._update_check_result(container.id, result)

            return result

        except NotFound:
            logger.error(f"容器 {container_id_or_name} 不存在")
            return HealthResult(
                status=HealthStatus.UNKNOWN,
                container_id="unknown",
                container_name=container_id_or_name,
                check_time=datetime.now(),
                message="容器不存在",
            )
        except Exception as e:
            logger.error(f"检查容器健康状态时出错: {e}")
            return HealthResult(
                status=HealthStatus.UNKNOWN,
                container_id="unknown",
                container_name=container_id_or_name,
                check_time=datetime.now(),
                message=f"检查健康状态时出错: {str(e)}",
            )

    def _get_container_stats(self, container_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        获取容器统计信息

        Args:
            container_id: 容器ID

        Returns:
            (成功状态, 统计信息或错误消息)
        """
        try:
            container = self.client.containers.get(container_id)

            # 获取状态信息
            stats = container.stats(stream=False)

            # 提取关键信息
            cpu_stats = stats["cpu_stats"]
            memory_stats = stats["memory_stats"]
            network_stats = stats["networks"] if "networks" in stats else {}

            # 计算CPU使用率
            cpu_delta = (
                cpu_stats["cpu_usage"]["total_usage"]
                - cpu_stats["cpu_usage"].get("usage_in_kernelmode", 0)
                - cpu_stats["cpu_usage"].get("usage_in_usermode", 0)
            )
            system_delta = (
                cpu_stats["system_cpu_usage"] if "system_cpu_usage" in cpu_stats else 0
            )
            cpu_usage = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0

            # 计算内存使用率
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            )

            # 网络使用情况
            network_rx = sum(
                interface.get("rx_bytes", 0) for interface in network_stats.values()
            )
            network_tx = sum(
                interface.get("tx_bytes", 0) for interface in network_stats.values()
            )

            result = {
                "id": container.id,
                "name": container.name,
                "cpu": {
                    "usage_percent": round(cpu_usage, 2),
                    "online_cpus": cpu_stats.get("online_cpus", 0),
                },
                "memory": {
                    "usage": memory_usage,
                    "limit": memory_limit,
                    "usage_percent": round(memory_percent, 2),
                },
                "network": {
                    "rx_bytes": network_rx,
                    "tx_bytes": network_tx,
                },
                "pid": stats.get("pids_stats", {}).get("current", 0),
                "read_time": stats.get("read"),
            }

            return True, result
        except NotFound:
            logger.error(f"容器 {container_id} 不存在")
            return False, {"error": "Container not found"}
        except APIError as e:
            logger.error(f"API error getting stats for container {container_id}: {e}")
            return False, {"error": f"API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error getting stats for container {container_id}: {e}")
            return False, {"error": f"Error: {str(e)}"}

    def _update_check_result(self, container_id: str, result: HealthResult):
        """
        更新检查结果并处理通知

        Args:
            container_id: 容器ID
            result: 健康检查结果
        """
        # 保存上一次结果用于比较
        if container_id in self.check_results:
            self.previous_results[container_id] = self.check_results[container_id]

        # 更新当前结果
        self.check_results[container_id] = result

        # 检查是否需要发送通知
        self._check_and_send_notification(container_id, result)

    def _check_and_send_notification(self, container_id: str, result: HealthResult):
        """
        检查是否需要发送通知并发送

        Args:
            container_id: 容器ID
            result: 健康检查结果
        """
        if not self.notification_config.enabled:
            return

        should_notify = False

        # 检查状态变化
        if self.notification_config.notify_on_status_change:
            if container_id in self.previous_results:
                prev_result = self.previous_results[container_id]
                if prev_result.status != result.status:
                    should_notify = True
            else:
                # 首次检查
                should_notify = True

        # 检查警告状态
        if (
            self.notification_config.notify_on_warning
            and result.status == HealthStatus.WARNING
        ):
            should_notify = True

        # 检查严重状态
        if (
            self.notification_config.notify_on_critical
            and result.status == HealthStatus.UNHEALTHY
        ):
            should_notify = True

        if should_notify:
            # 检查通知间隔
            now = datetime.now()
            last_notification = self.last_notification_time.get(container_id)

            if (
                not last_notification
                or (now - last_notification).total_seconds()
                >= self.notification_config.notification_interval
            ):
                self._send_notification(result)
                self.last_notification_time[container_id] = now

    def _send_notification(self, result: HealthResult):
        """
        发送通知

        Args:
            result: 健康检查结果
        """
        for handler_name in self.notification_config.notification_handlers:
            handler = self.notification_handlers.get(handler_name)
            if handler:
                try:
                    handler(result)
                except Exception as e:
                    logger.error(f"发送通知时出错: {e}")

    def _console_notification_handler(self, result: HealthResult):
        """
        控制台通知处理器

        Args:
            result: 健康检查结果
        """
        status_display = {
            HealthStatus.HEALTHY: "健康",
            HealthStatus.WARNING: "警告",
            HealthStatus.UNHEALTHY: "不健康",
            HealthStatus.UNKNOWN: "未知",
            HealthStatus.STARTING: "启动中",
        }.get(result.status, result.status)

        logger.warning(
            f"容器健康状态通知: {result.container_name} ({result.container_id[:12]}) - "
            f"状态: {status_display}, 消息: {result.message}"
        )

    def start_monitoring(
        self,
        containers: List[str] = None,
        monitor_all: bool = False,
        use_existing: bool = True,
    ) -> bool:
        """
        启动监控服务

        Args:
            containers: 要监控的容器ID或名称列表
            monitor_all: 是否监控所有容器
            use_existing: 是否使用现有的监控容器列表

        Returns:
            是否成功启动
        """
        if self.running:
            logger.warning("监控服务已经在运行")
            return True

        try:
            if not use_existing:
                self.monitored_containers = set()

            # 添加指定的容器
            if containers:
                for container_id_or_name in containers:
                    self.add_container(container_id_or_name)

            # 添加所有运行容器
            if monitor_all:
                running_containers = self.client.containers.list()
                for container in running_containers:
                    self.monitored_containers.add(container.id)
                logger.info(
                    f"已添加 {len(running_containers)} 个运行中的容器到监控列表"
                )

            # 启动监控线程
            self.running = True
            self.check_thread = threading.Thread(target=self._monitoring_loop)
            self.check_thread.daemon = True
            self.check_thread.start()

            logger.info(f"已启动健康检查监控服务, 检查间隔: {self.check_interval}秒")
            return True
        except Exception as e:
            logger.error(f"启动监控服务时出错: {e}")
            self.running = False
            return False

    def stop_monitoring(self) -> bool:
        """
        停止监控服务

        Returns:
            是否成功停止
        """
        if not self.running:
            logger.warning("监控服务未在运行")
            return True

        try:
            self.running = False
            if self.check_thread:
                self.check_thread.join(timeout=5)
            logger.info("已停止健康检查监控服务")
            return True
        except Exception as e:
            logger.error(f"停止监控服务时出错: {e}")
            return False

    def is_monitoring(self) -> bool:
        """
        检查监控服务是否在运行

        Returns:
            是否在运行
        """
        return self.running

    def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 获取当前被监控的容器列表
                monitored = list(self.monitored_containers)

                # 检查每个容器的健康状态
                for container_id in monitored:
                    try:
                        if self.running:  # 再次检查，防止在循环中被停止
                            self.check_container_health(container_id)
                    except Exception as e:
                        logger.error(
                            f"检查容器 {container_id[:12]} 健康状态时出错: {e}"
                        )

                # 等待下一次检查
                if self.running:
                    # 分段等待，便于更快响应停止请求
                    for _ in range(self.check_interval):
                        if self.running:
                            time.sleep(1)
                        else:
                            break
            except Exception as e:
                logger.error(f"监控循环中出错: {e}")
                # 等待一段时间后重试
                time.sleep(5)

        logger.info("健康检查监控循环已退出")


# 单例实例
_health_checker = None


def get_health_checker() -> HealthChecker:
    """
    获取健康检查器实例

    Returns:
        健康检查器实例
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
