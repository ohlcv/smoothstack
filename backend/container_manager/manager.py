#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理器

管理Docker容器的生命周期，包括启动、停止、重启和监控
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple, Union
import docker
from docker.errors import DockerException, APIError, NotFound

from backend.config import config
from .models.container import Container, ContainerStatus

# 配置日志
logger = logging.getLogger("smoothstack.container_manager")


class ContainerManager:
    """容器管理器"""

    def __init__(self):
        """初始化容器管理器"""
        logger.info("Initializing container manager")

        # 初始化配置
        self._init_config()

        # 初始化Docker客户端
        self.client = self._init_docker_client()

        # 容器缓存
        self.containers: Dict[str, Container] = {}

        # 默认超时设置（秒）
        self.default_timeout = config.get("container_manager.default_timeout", 30)

        logger.info("Container manager initialized")

    def _init_config(self):
        """初始化配置"""
        try:
            # 确保配置存在
            if "container_manager" not in config:
                default_config = {
                    "default_timeout": 30,  # 默认超时时间（秒）
                    "auto_restart": True,  # 是否自动重启崩溃的容器
                    "max_restart_attempts": 3,  # 最大重启尝试次数
                    "compose_file_path": "./docker-compose.yml",  # Docker Compose配置文件路径
                    "container_log_dir": os.path.join(
                        os.path.expanduser("~"), ".smoothstack", "logs", "containers"
                    ),  # 容器日志目录
                    "volume_base_dir": os.path.join(
                        os.path.expanduser("~"), ".smoothstack", "volumes"
                    ),  # 容器卷基础目录
                }

                # 检查config是否有set_default方法
                if hasattr(config, "set_default"):
                    config.set_default("container_manager", default_config)
                else:
                    # 兼容不同的配置系统
                    config["container_manager"] = default_config

            # 创建日志目录
            log_dir = config.get("container_manager.container_log_dir")
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                logger.debug(f"Created container log directory: {log_dir}")

            # 创建卷目录
            volume_dir = config.get("container_manager.volume_base_dir")
            if volume_dir and not os.path.exists(volume_dir):
                os.makedirs(volume_dir, exist_ok=True)
                logger.debug(f"Created container volume directory: {volume_dir}")

        except Exception as e:
            logger.warning(f"Error during configuration initialization: {str(e)}")
            logger.warning("Using default configuration values")
            # 设置默认值以确保管理器仍能运行
            self.default_timeout = 30
            self.auto_restart = True
            self.max_restart_attempts = 3

    def _init_docker_client(self):
        """初始化Docker客户端"""
        try:
            # 尝试创建Docker客户端
            client = docker.from_env()
            # 测试连接
            client.ping()
            logger.info("Docker client initialized successfully")
            return client
        except (DockerException, ImportError) as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            logger.warning("Docker functionality will be limited")
            return None

    def _refresh_containers(self) -> None:
        """刷新容器缓存"""
        try:
            # 获取所有容器
            docker_containers = self.client.containers.list(all=True)

            # 更新缓存
            updated_containers = {}
            for container in docker_containers:
                container_obj = Container.from_docker_container(container)
                updated_containers[container_obj.id] = container_obj

            self.containers = updated_containers
            logger.debug(
                f"Refreshed containers cache: {len(self.containers)} containers"
            )
        except DockerException as e:
            logger.error(f"Failed to refresh containers: {e}")

    def get_container(self, container_id_or_name: str) -> Optional[Container]:
        """
        获取容器信息

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            容器对象，如果不存在则返回None
        """
        try:
            # 刷新容器缓存
            self._refresh_containers()

            # 先尝试按ID查找
            if container_id_or_name in self.containers:
                return self.containers[container_id_or_name]

            # 再尝试按名称查找
            for container in self.containers.values():
                if container.name == container_id_or_name:
                    return container

            # 找不到容器
            logger.warning(f"Container not found: {container_id_or_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting container {container_id_or_name}: {e}")
            return None

    def list_containers(
        self, all_containers: bool = True, filters: Optional[Dict[str, str]] = None
    ) -> List[Container]:
        """
        列出容器

        Args:
            all_containers: 是否包括停止的容器
            filters: 筛选条件

        Returns:
            容器列表
        """
        try:
            # 刷新容器缓存
            self._refresh_containers()

            # 获取容器列表
            containers = list(self.containers.values())

            # 如果不包括停止的容器，过滤掉非运行状态的容器
            if not all_containers:
                containers = [
                    c for c in containers if c.status == ContainerStatus.RUNNING
                ]

            # 应用过滤器
            if filters:
                filtered_containers = []
                for container in containers:
                    match = True
                    for key, value in filters.items():
                        # 对于标签，检查是否包含指定标签
                        if key == "label":
                            label_key, label_value = value.split("=")
                            if (
                                label_key not in container.labels
                                or container.labels[label_key] != label_value
                            ):
                                match = False
                                break
                        # 对于名称，检查是否包含指定字符串
                        elif key == "name":
                            if value not in container.name:
                                match = False
                                break
                        # 对于状态，检查是否匹配
                        elif key == "status":
                            if container.status.name.lower() != value.lower():
                                match = False
                                break
                    if match:
                        filtered_containers.append(container)
                containers = filtered_containers

            return containers
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def start_container(
        self, container_id_or_name: str, timeout: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        启动容器

        Args:
            container_id_or_name: 容器ID或名称
            timeout: 超时时间（秒）

        Returns:
            (成功状态, 消息)
        """
        timeout = timeout or self.default_timeout
        try:
            # 获取Docker容器对象
            container = self.client.containers.get(container_id_or_name)
            container.start()

            # 等待容器完全启动
            start_time = time.time()
            while time.time() - start_time < timeout:
                container.reload()
                if container.status.lower() == "running":
                    logger.info(
                        f"Container {container_id_or_name} started successfully"
                    )
                    return True, "Container started successfully"
                time.sleep(0.5)

            # 超时
            logger.warning(f"Container {container_id_or_name} start timed out")
            return False, f"Container start timed out after {timeout} seconds"
        except NotFound:
            logger.error(f"Container {container_id_or_name} not found")
            return False, "Container not found"
        except APIError as e:
            logger.error(f"API error starting container {container_id_or_name}: {e}")
            return False, f"API error: {str(e)}"
        except Exception as e:
            logger.error(f"Error starting container {container_id_or_name}: {e}")
            return False, f"Error: {str(e)}"

    def stop_container(
        self, container_id_or_name: str, timeout: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        停止容器

        Args:
            container_id_or_name: 容器ID或名称
            timeout: 超时时间（秒）

        Returns:
            (成功状态, 消息)
        """
        timeout = timeout or self.default_timeout
        try:
            # 获取Docker容器对象
            container = self.client.containers.get(container_id_or_name)
            container.stop(timeout=timeout)

            # 验证容器已停止
            container.reload()
            if container.status.lower() != "running":
                logger.info(f"Container {container_id_or_name} stopped successfully")
                return True, "Container stopped successfully"
            else:
                logger.warning(
                    f"Container {container_id_or_name} did not stop properly"
                )
                return False, "Container did not stop properly"
        except NotFound:
            logger.error(f"Container {container_id_or_name} not found")
            return False, "Container not found"
        except APIError as e:
            logger.error(f"API error stopping container {container_id_or_name}: {e}")
            return False, f"API error: {str(e)}"
        except Exception as e:
            logger.error(f"Error stopping container {container_id_or_name}: {e}")
            return False, f"Error: {str(e)}"

    def restart_container(
        self, container_id_or_name: str, timeout: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        重启容器

        Args:
            container_id_or_name: 容器ID或名称
            timeout: 超时时间（秒）

        Returns:
            (成功状态, 消息)
        """
        timeout = timeout or self.default_timeout
        try:
            # 获取Docker容器对象
            container = self.client.containers.get(container_id_or_name)
            container.restart(timeout=timeout)

            # 等待容器完全重启
            start_time = time.time()
            while time.time() - start_time < timeout:
                container.reload()
                if container.status.lower() == "running":
                    logger.info(
                        f"Container {container_id_or_name} restarted successfully"
                    )
                    return True, "Container restarted successfully"
                time.sleep(0.5)

            # 超时
            logger.warning(f"Container {container_id_or_name} restart timed out")
            return False, f"Container restart timed out after {timeout} seconds"
        except NotFound:
            logger.error(f"Container {container_id_or_name} not found")
            return False, "Container not found"
        except APIError as e:
            logger.error(f"API error restarting container {container_id_or_name}: {e}")
            return False, f"API error: {str(e)}"
        except Exception as e:
            logger.error(f"Error restarting container {container_id_or_name}: {e}")
            return False, f"Error: {str(e)}"

    def get_container_logs(
        self, container_id_or_name: str, tail: int = 100, since: Optional[int] = None
    ) -> Tuple[bool, Union[str, List[str]]]:
        """
        获取容器日志

        Args:
            container_id_or_name: 容器ID或名称
            tail: 返回的日志行数
            since: 从多少秒前开始获取日志

        Returns:
            (成功状态, 日志内容或错误消息)
        """
        try:
            # 获取Docker容器对象
            container = self.client.containers.get(container_id_or_name)

            # 获取日志
            logs = (
                container.logs(
                    tail=tail,
                    since=int(time.time()) - since if since else None,
                    timestamps=True,
                    stream=False,
                )
                .decode("utf-8")
                .splitlines()
            )

            return True, logs
        except NotFound:
            logger.error(f"Container {container_id_or_name} not found")
            return False, "Container not found"
        except APIError as e:
            logger.error(
                f"API error getting logs for container {container_id_or_name}: {e}"
            )
            return False, f"API error: {str(e)}"
        except Exception as e:
            logger.error(
                f"Error getting logs for container {container_id_or_name}: {e}"
            )
            return False, f"Error: {str(e)}"

    def get_container_stats(self, container_id_or_name: str) -> Tuple[bool, Dict]:
        """
        获取容器统计信息

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            (成功状态, 统计信息或错误消息)
        """
        try:
            # 获取Docker容器对象
            container = self.client.containers.get(container_id_or_name)

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
            logger.error(f"Container {container_id_or_name} not found")
            return False, {"error": "Container not found"}
        except APIError as e:
            logger.error(
                f"API error getting stats for container {container_id_or_name}: {e}"
            )
            return False, {"error": f"API error: {str(e)}"}
        except Exception as e:
            logger.error(
                f"Error getting stats for container {container_id_or_name}: {e}"
            )
            return False, {"error": f"Error: {str(e)}"}

    def check_docker_service(self) -> Tuple[bool, str]:
        """
        检查Docker服务状态

        Returns:
            (是否正常, 状态消息)
        """
        try:
            # 尝试ping Docker守护进程
            self.client.ping()
            version_info = self.client.version()

            # 提取版本信息
            docker_version = version_info.get("Version", "Unknown")
            api_version = version_info.get("ApiVersion", "Unknown")
            os = version_info.get("Os", "Unknown")
            arch = version_info.get("Arch", "Unknown")

            logger.info(
                f"Docker service is running. Version: {docker_version}, API: {api_version}"
            )
            return (
                True,
                f"Docker服务正常运行。版本: {docker_version}, API: {api_version}, OS: {os}, 架构: {arch}",
            )
        except DockerException as e:
            logger.error(f"Docker service check failed: {e}")
            return False, f"Docker服务异常: {str(e)}"
