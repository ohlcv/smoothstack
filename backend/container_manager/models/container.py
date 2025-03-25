#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器模型

定义了容器的数据模型，用于在容器管理器中表示Docker容器
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class ContainerStatus(Enum):
    """容器状态枚举"""

    UNKNOWN = auto()
    CREATED = auto()
    RUNNING = auto()
    PAUSED = auto()
    RESTARTING = auto()
    REMOVING = auto()  # 添加REMOVING状态以匹配命令行工具中使用的状态
    EXITED = auto()
    DEAD = auto()
    STOPPED = auto()

    @classmethod
    def from_docker_status(cls, status: str) -> "ContainerStatus":
        """
        将Docker容器状态字符串转换为枚举值

        Args:
            status: Docker容器状态字符串

        Returns:
            容器状态枚举值
        """
        status_map = {
            "created": cls.CREATED,
            "running": cls.RUNNING,
            "paused": cls.PAUSED,
            "restarting": cls.RESTARTING,
            "removing": cls.REMOVING,
            "exited": cls.EXITED,
            "dead": cls.DEAD,
        }
        return status_map.get(status.lower(), cls.UNKNOWN)


@dataclass
class Container:
    """容器数据模型"""

    # 基本信息
    id: Optional[str] = None
    name: Optional[str] = None
    image: Optional[str] = None
    status: ContainerStatus = ContainerStatus.UNKNOWN

    # 创建信息
    created_at: Optional[datetime] = None

    # 网络配置
    ports: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)

    # 标签和环境变量
    labels: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)

    # 命令和工作目录
    command: Optional[str] = None
    entrypoint: Optional[List[str]] = None
    working_dir: Optional[str] = None

    # 资源限制
    cpu_limit: Optional[float] = None
    memory_limit: Optional[int] = None

    # 网络设置
    network_mode: Optional[str] = None
    ip_address: Optional[str] = None

    # 健康状态
    health_status: Optional[str] = None
    restart_count: Optional[int] = None

    def __str__(self) -> str:
        """字符串表示"""
        if self.name:
            return f"Container({self.name})"
        elif self.id:
            return f"Container({self.id[:12]})"
        else:
            return "Container(unknown)"

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            包含容器信息的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "status": self.status.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ports": self.ports,
            "volumes": self.volumes,
            "labels": self.labels,
            "environment": self.environment,
            "command": self.command,
            "entrypoint": self.entrypoint,
            "working_dir": self.working_dir,
            "cpu_limit": self.cpu_limit,
            "memory_limit": self.memory_limit,
            "network_mode": self.network_mode,
            "ip_address": self.ip_address,
            "health_status": self.health_status,
            "restart_count": self.restart_count,
        }

    @classmethod
    def from_docker_container(cls, docker_container) -> "Container":
        """
        从Docker容器对象创建Container实例

        Args:
            docker_container: Docker容器对象

        Returns:
            Container实例
        """
        # 获取容器属性
        attrs = docker_container.attrs

        # 获取端口映射
        ports = {}
        if "HostConfig" in attrs and "PortBindings" in attrs["HostConfig"]:
            port_bindings = attrs["HostConfig"]["PortBindings"]
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        host_port = binding.get("HostPort", "")
                        ports[host_port] = container_port.split("/")[0]

        # 获取卷映射
        volumes = {}
        if "Mounts" in attrs:
            for mount in attrs["Mounts"]:
                source = mount.get("Source", "")
                destination = mount.get("Destination", "")
                if source and destination:
                    volumes[source] = destination

        # 获取网络信息
        ip_address = None
        if "NetworkSettings" in attrs and "Networks" in attrs["NetworkSettings"]:
            for network in attrs["NetworkSettings"]["Networks"].values():
                if "IPAddress" in network and network["IPAddress"]:
                    ip_address = network["IPAddress"]
                    break

        # 获取健康状态
        health_status = None
        if "State" in attrs and "Health" in attrs["State"]:
            health = attrs["State"]["Health"]
            if "Status" in health:
                health_status = health["Status"]

        # 创建容器对象
        return cls(
            id=docker_container.id,
            name=docker_container.name,
            image=(
                docker_container.image.tags[0]
                if hasattr(docker_container, "image") and docker_container.image.tags
                else None
            ),
            status=ContainerStatus.from_docker_status(docker_container.status),
            created_at=(
                datetime.fromisoformat(attrs["Created"].replace("Z", "+00:00"))
                if "Created" in attrs
                else None
            ),
            ports=ports,
            volumes=volumes,
            labels=(
                attrs.get("Config", {}).get("Labels", {}) if "Config" in attrs else {}
            ),
            environment=(
                {
                    env.split("=")[0]: env.split("=")[1]
                    for env in attrs.get("Config", {}).get("Env", [])
                    if "=" in env
                }
                if "Config" in attrs
                else {}
            ),
            command=(
                attrs.get("Config", {}).get("Cmd", None) if "Config" in attrs else None
            ),
            entrypoint=(
                attrs.get("Config", {}).get("Entrypoint", None)
                if "Config" in attrs
                else None
            ),
            working_dir=(
                attrs.get("Config", {}).get("WorkingDir", None)
                if "Config" in attrs
                else None
            ),
            cpu_limit=(
                attrs.get("HostConfig", {}).get("NanoCpus", None) / 1e9
                if "HostConfig" in attrs and attrs["HostConfig"].get("NanoCpus")
                else None
            ),
            memory_limit=(
                attrs.get("HostConfig", {}).get("Memory", None)
                if "HostConfig" in attrs
                else None
            ),
            network_mode=(
                attrs.get("HostConfig", {}).get("NetworkMode", None)
                if "HostConfig" in attrs
                else None
            ),
            ip_address=ip_address,
            health_status=health_status,
            restart_count=(
                attrs.get("RestartCount", None) if "RestartCount" in attrs else None
            ),
        )
