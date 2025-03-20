#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务编排管理器

管理多容器服务组的部署、启动、停止和监控
"""

import os
import time
import logging
import yaml
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from pathlib import Path
import docker
from docker.errors import DockerException, APIError, NotFound

from backend.config import config
from .manager import ContainerManager
from .models.container import Container, ContainerStatus
from .models.service_group import (
    ServiceGroup,
    Service,
    ServiceNetwork,
    ServiceStatus,
    NetworkMode,
)

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.service_orchestrator")


class ServiceOrchestrator:
    """服务编排管理器"""

    def __init__(self, container_manager: Optional[ContainerManager] = None):
        """
        初始化服务编排管理器

        Args:
            container_manager: 容器管理器实例，如果未提供则创建新实例
        """
        logger.info("初始化服务编排管理器")

        # 初始化配置
        self._init_config()

        # 使用提供的容器管理器或创建新实例
        self.container_manager = container_manager or ContainerManager()

        # 初始化Docker客户端
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except DockerException as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            self.docker_client = None

        # 服务组缓存
        self.service_groups: Dict[str, ServiceGroup] = {}

        # 加载现有服务组
        self.load_service_groups()

        logger.info("服务编排管理器初始化完成")

    def _init_config(self):
        """初始化配置"""
        # 确保配置存在
        if "service_orchestrator" not in config:
            config.set_default(
                "service_orchestrator",
                {
                    "service_groups_dir": os.path.join(
                        os.path.expanduser("~"), ".smoothstack", "service_groups"
                    ),  # 服务组配置目录
                    "default_network": "bridge",  # 默认网络
                    "container_prefix": "sms_",  # 容器名称前缀
                    "default_timeout": 60,  # 默认超时时间（秒）
                },
            )

        # 创建服务组目录
        service_groups_dir = config.get("service_orchestrator.service_groups_dir")
        if service_groups_dir and not os.path.exists(service_groups_dir):
            os.makedirs(service_groups_dir, exist_ok=True)

    def load_service_groups(self):
        """加载所有服务组配置"""
        logger.info("加载服务组配置")

        self.service_groups = {}
        service_groups_dir = config.get("service_orchestrator.service_groups_dir")

        if not service_groups_dir or not os.path.exists(service_groups_dir):
            logger.warning(f"服务组目录不存在: {service_groups_dir}")
            return

        # 查找所有YAML文件
        yaml_files = list(Path(service_groups_dir).glob("*.yaml")) + list(
            Path(service_groups_dir).glob("*.yml")
        )

        for yaml_file in yaml_files:
            try:
                service_group = ServiceGroup.load_from_file(str(yaml_file))
                if service_group:
                    self.service_groups[service_group.name] = service_group
                    logger.debug(f"加载服务组: {service_group.name}")
            except Exception as e:
                logger.error(f"加载服务组配置失败 {yaml_file}: {e}")

        logger.info(f"已加载 {len(self.service_groups)} 个服务组")

    def get_service_group(self, name: str) -> Optional[ServiceGroup]:
        """
        获取服务组

        Args:
            name: 服务组名称

        Returns:
            服务组实例，如果不存在则返回None
        """
        return self.service_groups.get(name)

    def list_service_groups(self) -> List[ServiceGroup]:
        """
        列出所有服务组

        Returns:
            服务组列表
        """
        return list(self.service_groups.values())

    def save_service_group(self, service_group: ServiceGroup) -> bool:
        """
        保存服务组配置

        Args:
            service_group: 服务组实例

        Returns:
            是否保存成功
        """
        service_groups_dir = config.get("service_orchestrator.service_groups_dir")
        file_path = os.path.join(service_groups_dir, f"{service_group.name}.yaml")

        if service_group.save_to_file(file_path):
            # 更新缓存
            self.service_groups[service_group.name] = service_group
            return True
        return False

    def delete_service_group(self, name: str) -> bool:
        """
        删除服务组配置

        Args:
            name: 服务组名称

        Returns:
            是否删除成功
        """
        if name not in self.service_groups:
            logger.warning(f"尝试删除不存在的服务组: {name}")
            return False

        service_groups_dir = config.get("service_orchestrator.service_groups_dir")
        file_path = os.path.join(service_groups_dir, f"{name}.yaml")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)

            # 从缓存中移除
            del self.service_groups[name]
            logger.info(f"已删除服务组: {name}")
            return True
        except Exception as e:
            logger.error(f"删除服务组失败: {e}")
            return False

    def create_network(self, network: ServiceNetwork) -> Tuple[bool, str]:
        """
        创建Docker网络

        Args:
            network: 网络配置

        Returns:
            (是否成功, 消息)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 检查网络是否已存在
            try:
                existing_network = self.docker_client.networks.get(network.name)
                logger.info(f"网络已存在: {network.name}")
                return True, f"网络已存在: {network.name}"
            except NotFound:
                # 网络不存在，创建新网络
                pass

            # 准备网络配置
            ipam_config = None
            if network.subnet or network.gateway:
                ipam_pool = {}
                if network.subnet:
                    ipam_pool["subnet"] = network.subnet
                if network.gateway:
                    ipam_pool["gateway"] = network.gateway

                ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

            # 创建网络
            network_params = {
                "name": network.name,
                "driver": network.driver,
                "options": {},
                "ipam": ipam_config,
                "labels": network.labels,
                "enable_ipv6": network.enable_ipv6,
                "internal": network.internal,
            }

            created_network = self.docker_client.networks.create(**network_params)
            logger.info(f"已创建网络: {network.name}")
            return True, f"已创建网络: {network.name}"

        except Exception as e:
            logger.error(f"创建网络失败: {e}")
            return False, f"创建网络失败: {str(e)}"

    def delete_network(self, network_name: str) -> Tuple[bool, str]:
        """
        删除Docker网络

        Args:
            network_name: 网络名称

        Returns:
            (是否成功, 消息)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 检查网络是否存在
            try:
                network = self.docker_client.networks.get(network_name)
            except NotFound:
                logger.warning(f"网络不存在: {network_name}")
                return False, f"网络不存在: {network_name}"

            # 删除网络
            network.remove()
            logger.info(f"已删除网络: {network_name}")
            return True, f"已删除网络: {network_name}"

        except Exception as e:
            logger.error(f"删除网络失败: {e}")
            return False, f"删除网络失败: {str(e)}"

    def get_network_stats(self, network_name: str) -> Optional[Dict[str, Any]]:
        """
        获取网络状态

        Args:
            network_name: 网络名称

        Returns:
            网络状态信息，如果不存在则返回None
        """
        if not self.docker_client:
            return None

        try:
            # 获取网络
            try:
                network = self.docker_client.networks.get(network_name)
            except NotFound:
                logger.warning(f"网络不存在: {network_name}")
                return None

            # 获取网络信息
            containers = network.containers

            stats = {
                "name": network.name,
                "id": network.id,
                "driver": network.attrs["Driver"],
                "containers": len(containers),
                "subnet": network.attrs.get("IPAM", {})
                .get("Config", [{}])[0]
                .get("Subnet"),
                "gateway": network.attrs.get("IPAM", {})
                .get("Config", [{}])[0]
                .get("Gateway"),
            }

            return stats

        except Exception as e:
            logger.error(f"获取网络状态失败: {e}")
            return None

    def deploy_service_group(
        self, service_group: ServiceGroup
    ) -> Tuple[bool, List[str]]:
        """
        部署服务组

        Args:
            service_group: 服务组实例

        Returns:
            (是否成功, 消息列表)
        """
        if not self.docker_client:
            return False, ["Docker客户端未初始化"]

        messages = []
        success = True

        # 验证服务组配置
        valid, errors = service_group.validate()
        if not valid:
            return False, errors

        # 创建网络
        for network_name, network in service_group.networks.items():
            network_success, network_message = self.create_network(network)
            messages.append(network_message)
            if not network_success:
                success = False

        # 按依赖顺序创建服务
        try:
            service_order = service_group.get_startup_order()
            logger.info(f"服务启动顺序: {service_order}")

            # 按顺序创建服务
            for service_name in service_order:
                service = service_group.services[service_name]
                service_success, service_message = self._deploy_service(
                    service_group.name, service
                )
                messages.append(service_message)
                if not service_success:
                    success = False

            # 更新服务组状态
            service_group.status = ServiceStatus.CREATED
            self.save_service_group(service_group)

            return success, messages

        except Exception as e:
            logger.error(f"部署服务组失败: {e}")
            return False, [f"部署服务组失败: {str(e)}"]

    def _deploy_service(self, group_name: str, service: Service) -> Tuple[bool, str]:
        """
        部署单个服务

        Args:
            group_name: 服务组名称
            service: 服务配置

        Returns:
            (是否成功, 消息)
        """
        # 准备容器名称
        container_prefix = config.get("service_orchestrator.container_prefix", "sms_")
        container_name = service.container_name
        if not container_name:
            container_name = f"{container_prefix}{group_name}_{service.name}"

        # 检查是否已存在同名容器
        existing_container = self.container_manager.get_container(container_name)
        if existing_container:
            logger.info(f"容器已存在: {container_name}，将尝试停止并移除")
            self.container_manager.stop_container(container_name)
            try:
                self.docker_client.containers.get(container_name).remove()
                logger.info(f"已移除旧容器: {container_name}")
            except Exception as e:
                logger.error(f"移除旧容器失败: {e}")
                return False, f"移除旧容器失败: {str(e)}"

        # 准备容器配置
        container_config = {
            "name": container_name,
            "image": service.image,
            "detach": True,
            "labels": {
                "smoothstack.service_group": group_name,
                "smoothstack.service_name": service.name,
                **service.labels,
            },
        }

        # 设置命令和入口点
        if service.command:
            container_config["command"] = service.command
        if service.entrypoint:
            container_config["entrypoint"] = service.entrypoint

        # 设置工作目录和用户
        if service.working_dir:
            container_config["working_dir"] = service.working_dir
        if service.user:
            container_config["user"] = service.user

        # 设置环境变量
        if service.environment:
            container_config["environment"] = service.environment

        # 设置网络
        if service.networks:
            # 使用第一个网络作为主网络
            container_config["network"] = service.networks[0]

        # 设置端口映射
        if service.ports:
            ports = {}
            for container_port, host_port in service.ports.items():
                # 端口格式: "容器端口/协议": "主机端口"
                # 或者只有容器端口: "容器端口"
                if "/" not in container_port:
                    container_port = f"{container_port}/tcp"
                ports[container_port] = int(host_port) if host_port else None
            container_config["ports"] = ports

        # 设置卷挂载
        if service.volumes:
            volumes = {}
            for host_path, container_path in service.volumes.items():
                # 卷格式: "主机路径": "容器路径[:ro]"
                read_only = False
                mount_path = container_path
                if ":" in container_path:
                    parts = container_path.split(":")
                    mount_path = parts[0]
                    if len(parts) > 1 and parts[1].lower() == "ro":
                        read_only = True

                # 确保主机路径存在
                host_path = os.path.expanduser(host_path)
                if not os.path.exists(host_path):
                    os.makedirs(host_path, exist_ok=True)

                volumes[host_path] = {
                    "bind": mount_path,
                    "mode": "ro" if read_only else "rw",
                }
            container_config["volumes"] = volumes

        # 设置资源限制
        if service.cpu_limit is not None:
            container_config["nano_cpus"] = int(service.cpu_limit * 1e9)
        if service.memory_limit:
            container_config["mem_limit"] = service.memory_limit

        # 设置重启策略
        if service.restart:
            container_config["restart_policy"] = {"Name": service.restart}

        # 设置健康检查
        if service.healthcheck:
            container_config["healthcheck"] = service.healthcheck

        try:
            # 创建容器
            logger.info(f"创建容器: {container_name}, 镜像: {service.image}")
            container = self.docker_client.containers.create(**container_config)

            # 连接额外的网络
            if service.networks and len(service.networks) > 1:
                for network_name in service.networks[1:]:
                    try:
                        network = self.docker_client.networks.get(network_name)
                        network.connect(container)
                        logger.info(
                            f"容器 {container_name} 已连接到网络: {network_name}"
                        )
                    except Exception as e:
                        logger.error(f"连接网络失败: {e}")

            logger.info(f"服务 {service.name} 容器创建成功: {container_name}")
            return True, f"服务 {service.name} 容器创建成功: {container_name}"

        except Exception as e:
            logger.error(f"创建容器失败: {e}")
            return False, f"创建容器失败: {str(e)}"

    def start_service_group(self, name: str) -> Tuple[bool, List[str]]:
        """
        启动服务组

        Args:
            name: 服务组名称

        Returns:
            (是否成功, 消息列表)
        """
        service_group = self.get_service_group(name)
        if not service_group:
            return False, [f"服务组不存在: {name}"]

        messages = []
        success = True

        # 按依赖顺序启动服务
        try:
            service_order = service_group.get_startup_order()
            logger.info(f"服务启动顺序: {service_order}")

            # 按顺序启动服务
            for service_name in service_order:
                service = service_group.services[service_name]

                # 构建容器名称
                container_prefix = config.get(
                    "service_orchestrator.container_prefix", "sms_"
                )
                container_name = service.container_name
                if not container_name:
                    container_name = f"{container_prefix}{name}_{service.name}"

                # 启动容器
                start_success, start_message = self.container_manager.start_container(
                    container_name
                )
                messages.append(f"服务 {service.name}: {start_message}")
                if not start_success:
                    success = False

                # 如果有依赖条件是service_healthy，需要等待健康检查通过
                if service_name < len(service_order) - 1:
                    for i, next_service_name in enumerate(
                        service_order[service_order.index(service_name) + 1 :], 1
                    ):
                        next_service = service_group.services[next_service_name]
                        for dep in next_service.depends_on:
                            if (
                                dep.service_name == service_name
                                and dep.condition == "service_healthy"
                            ):
                                # 等待健康检查通过
                                if not self._wait_for_service_healthy(
                                    container_name, timeout=60
                                ):
                                    msg = f"服务 {service_name} 健康检查超时，依赖此服务的 {next_service_name} 可能无法正常启动"
                                    messages.append(msg)
                                    logger.warning(msg)
                                    if dep.required:
                                        success = False
                                break

            # 更新服务组状态
            if success:
                service_group.status = ServiceStatus.RUNNING
            else:
                service_group.status = ServiceStatus.PARTIALLY_RUNNING

            self.save_service_group(service_group)

            return success, messages

        except Exception as e:
            logger.error(f"启动服务组失败: {e}")
            return False, [f"启动服务组失败: {str(e)}"]

    def _wait_for_service_healthy(self, container_name: str, timeout: int = 60) -> bool:
        """
        等待服务健康检查通过

        Args:
            container_name: 容器名称
            timeout: 超时时间（秒）

        Returns:
            是否健康
        """
        if not self.docker_client:
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                container = self.docker_client.containers.get(container_name)
                if container.status != "running":
                    return False

                health = container.attrs.get("State", {}).get("Health", {})
                if health and health.get("Status") == "healthy":
                    logger.info(f"容器 {container_name} 健康检查通过")
                    return True

                time.sleep(1)
            except Exception as e:
                logger.error(f"检查容器健康状态失败: {e}")
                return False

        logger.warning(f"容器 {container_name} 健康检查超时")
        return False

    def stop_service_group(
        self, name: str, timeout: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        停止服务组

        Args:
            name: 服务组名称
            timeout: 停止超时时间（秒）

        Returns:
            (是否成功, 消息列表)
        """
        service_group = self.get_service_group(name)
        if not service_group:
            return False, [f"服务组不存在: {name}"]

        messages = []
        success = True

        # 按依赖顺序的反序停止服务
        try:
            service_order = service_group.get_startup_order()
            service_order.reverse()  # 反转顺序
            logger.info(f"服务停止顺序: {service_order}")

            # 按顺序停止服务
            for service_name in service_order:
                service = service_group.services[service_name]

                # 构建容器名称
                container_prefix = config.get(
                    "service_orchestrator.container_prefix", "sms_"
                )
                container_name = service.container_name
                if not container_name:
                    container_name = f"{container_prefix}{name}_{service.name}"

                # 停止容器
                stop_success, stop_message = self.container_manager.stop_container(
                    container_name, timeout=timeout
                )
                messages.append(f"服务 {service.name}: {stop_message}")
                if not stop_success:
                    success = False

            # 更新服务组状态
            service_group.status = ServiceStatus.STOPPED
            self.save_service_group(service_group)

            return success, messages

        except Exception as e:
            logger.error(f"停止服务组失败: {e}")
            return False, [f"停止服务组失败: {str(e)}"]

    def remove_service_group(
        self, name: str, remove_volumes: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        移除服务组

        Args:
            name: 服务组名称
            remove_volumes: 是否同时移除卷

        Returns:
            (是否成功, 消息列表)
        """
        service_group = self.get_service_group(name)
        if not service_group:
            return False, [f"服务组不存在: {name}"]

        messages = []
        success = True

        # 停止并移除容器
        stop_success, stop_messages = self.stop_service_group(name)
        messages.extend(stop_messages)
        if not stop_success:
            # 即使停止部分失败，仍继续尝试移除
            success = False

        # 移除容器
        container_prefix = config.get("service_orchestrator.container_prefix", "sms_")
        for service_name, service in service_group.services.items():
            container_name = service.container_name
            if not container_name:
                container_name = f"{container_prefix}{name}_{service.name}"

            try:
                # 获取容器
                try:
                    container = self.docker_client.containers.get(container_name)
                    # 移除容器
                    container.remove(v=remove_volumes)
                    messages.append(f"已移除容器: {container_name}")
                except NotFound:
                    messages.append(f"容器不存在，无需移除: {container_name}")
            except Exception as e:
                logger.error(f"移除容器失败: {e}")
                messages.append(f"移除容器失败: {str(e)}")
                success = False

        # 移除网络（只移除非默认网络）
        default_networks = ["bridge", "host", "none"]
        for network_name, network in service_group.networks.items():
            if network.name not in default_networks:
                try:
                    self.delete_network(network.name)
                    messages.append(f"已移除网络: {network.name}")
                except Exception as e:
                    logger.error(f"移除网络失败: {e}")
                    messages.append(f"移除网络失败: {str(e)}")
                    success = False

        return success, messages

    def get_service_group_status(
        self, name: str
    ) -> Tuple[ServiceStatus, Dict[str, str]]:
        """
        获取服务组状态

        Args:
            name: 服务组名称

        Returns:
            (服务组状态, 各服务状态字典)
        """
        service_group = self.get_service_group(name)
        if not service_group:
            return ServiceStatus.UNKNOWN, {}

        service_statuses = {}
        container_prefix = config.get("service_orchestrator.container_prefix", "sms_")

        # 获取各服务状态
        for service_name, service in service_group.services.items():
            container_name = service.container_name
            if not container_name:
                container_name = f"{container_prefix}{name}_{service.name}"

            container = self.container_manager.get_container(container_name)
            if not container:
                service_statuses[service_name] = "not_created"
            else:
                service_statuses[service_name] = container.status.name.lower()

        # 确定整体状态
        if not service_statuses:
            return ServiceStatus.UNKNOWN, {}

        # 检查是否所有服务都在运行
        all_running = all(status == "running" for status in service_statuses.values())
        any_running = any(status == "running" for status in service_statuses.values())
        all_stopped = all(
            status in ["exited", "stopped", "not_created"]
            for status in service_statuses.values()
        )

        if all_running:
            status = ServiceStatus.RUNNING
        elif any_running:
            status = ServiceStatus.PARTIALLY_RUNNING
        elif all_stopped:
            status = ServiceStatus.STOPPED
        else:
            status = ServiceStatus.UNKNOWN

        # 更新服务组状态
        if service_group.status != status:
            service_group.status = status
            self.save_service_group(service_group)

        return status, service_statuses

    def import_from_compose_file(
        self, file_path: str, group_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        从Docker Compose文件导入服务组

        Args:
            file_path: Compose文件路径
            group_name: 自定义服务组名称，如果未提供则使用目录名

        Returns:
            (是否成功, 消息)
        """
        try:
            # 加载Compose文件
            with open(file_path, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            if not compose_data:
                return False, "Compose文件为空或格式错误"

            # 确定服务组名称
            if not group_name:
                # 使用目录名作为服务组名称
                group_name = os.path.basename(
                    os.path.dirname(os.path.abspath(file_path))
                )

            # 创建服务组
            service_group = ServiceGroup(
                name=group_name,
                description=f"从Docker Compose文件导入: {file_path}",
                version=compose_data.get("version", "1.0"),
            )

            # 处理网络
            if "networks" in compose_data:
                for network_name, network_data in compose_data["networks"].items():
                    # 创建网络配置
                    network_config = {
                        "name": network_name,
                        "driver": network_data.get("driver", "bridge"),
                    }

                    # 处理IPAM配置
                    if "ipam" in network_data:
                        ipam = network_data["ipam"]
                        if "config" in ipam and ipam["config"]:
                            config = ipam["config"][0]
                            if "subnet" in config:
                                network_config["subnet"] = config["subnet"]
                            if "gateway" in config:
                                network_config["gateway"] = config["gateway"]

                    # 添加到服务组
                    service_group.networks[network_name] = ServiceNetwork.from_dict(
                        network_config
                    )

            # 处理服务
            if "services" in compose_data:
                for service_name, service_data in compose_data["services"].items():
                    # 创建服务配置
                    service_config = {
                        "name": service_name,
                        "image": service_data.get("image", ""),
                        "container_name": service_data.get("container_name"),
                        "command": service_data.get("command"),
                        "environment": self._parse_compose_environment(
                            service_data.get("environment", {})
                        ),
                        "working_dir": service_data.get("working_dir"),
                        "user": service_data.get("user"),
                        "restart": service_data.get("restart", "no"),
                    }

                    # 处理依赖
                    if "depends_on" in service_data:
                        service_config["depends_on"] = service_data["depends_on"]

                    # 处理端口映射
                    if "ports" in service_data:
                        ports = {}
                        for port_mapping in service_data["ports"]:
                            # 解析端口映射
                            if isinstance(port_mapping, str):
                                # 字符串格式: "主机端口:容器端口"
                                parts = port_mapping.split(":")
                                if len(parts) == 2:
                                    host_port, container_port = parts
                                    ports[container_port] = host_port
                                elif len(parts) == 1:
                                    container_port = parts[0]
                                    ports[container_port] = ""
                            elif isinstance(port_mapping, dict):
                                # 字典格式: {"target": 容器端口, "published": 主机端口}
                                container_port = str(port_mapping.get("target", ""))
                                host_port = str(port_mapping.get("published", ""))
                                if container_port:
                                    ports[container_port] = host_port

                        service_config["ports"] = ports

                    # 处理卷挂载
                    if "volumes" in service_data:
                        volumes = {}
                        for volume_mapping in service_data["volumes"]:
                            # 解析卷挂载
                            if isinstance(volume_mapping, str):
                                # 字符串格式: "主机路径:容器路径[:读写模式]"
                                parts = volume_mapping.split(":")
                                if len(parts) >= 2:
                                    host_path, container_path = parts[0], parts[1]
                                    if len(parts) == 3 and parts[2] == "ro":
                                        container_path = f"{container_path}:ro"
                                    volumes[host_path] = container_path
                            elif isinstance(volume_mapping, dict):
                                # 字典格式: {"source": 主机路径, "target": 容器路径, "read_only": 是否只读}
                                host_path = volume_mapping.get("source", "")
                                container_path = volume_mapping.get("target", "")
                                read_only = volume_mapping.get("read_only", False)
                                if host_path and container_path:
                                    if read_only:
                                        container_path = f"{container_path}:ro"
                                    volumes[host_path] = container_path

                        service_config["volumes"] = volumes

                    # 处理网络
                    if "networks" in service_data:
                        networks = []
                        if isinstance(service_data["networks"], list):
                            networks = service_data["networks"]
                        elif isinstance(service_data["networks"], dict):
                            networks = list(service_data["networks"].keys())

                        service_config["networks"] = networks

                    # 处理健康检查
                    if "healthcheck" in service_data:
                        healthcheck = service_data["healthcheck"]
                        if isinstance(healthcheck, dict):
                            service_config["healthcheck"] = {
                                "test": healthcheck.get("test"),
                                "interval": healthcheck.get("interval"),
                                "timeout": healthcheck.get("timeout"),
                                "retries": healthcheck.get("retries"),
                                "start_period": healthcheck.get("start_period"),
                            }

                    # 处理资源限制
                    if "deploy" in service_data:
                        deploy = service_data["deploy"]
                        if isinstance(deploy, dict) and "resources" in deploy:
                            resources = deploy["resources"]
                            limits = resources.get("limits", {})

                            if "cpus" in limits:
                                service_config["cpu_limit"] = float(limits["cpus"])
                            if "memory" in limits:
                                service_config["memory_limit"] = limits["memory"]

                    # 添加到服务组
                    service_group.services[service_name] = Service.from_dict(
                        service_config
                    )

            # 保存服务组
            if self.save_service_group(service_group):
                return True, f"从Compose文件导入服务组成功: {group_name}"
            else:
                return False, "保存服务组失败"

        except Exception as e:
            logger.error(f"从Compose文件导入服务组失败: {e}")
            return False, f"导入失败: {str(e)}"

    def _parse_compose_environment(
        self, env_data: Union[Dict, List, str]
    ) -> Dict[str, str]:
        """
        解析Docker Compose环境变量配置

        Args:
            env_data: 环境变量配置，可能是字典、列表或字符串

        Returns:
            环境变量字典
        """
        result = {}

        if isinstance(env_data, dict):
            # 字典格式: {"KEY": "VALUE"}
            result = env_data
        elif isinstance(env_data, list):
            # 列表格式: ["KEY=VALUE"]
            for item in env_data:
                if isinstance(item, str) and "=" in item:
                    key, value = item.split("=", 1)
                    result[key] = value
        elif isinstance(env_data, str):
            # 字符串格式: "KEY=VALUE\nKEY2=VALUE2"
            for line in env_data.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    result[key] = value

        return result
