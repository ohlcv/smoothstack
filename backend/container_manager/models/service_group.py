#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务组模型

定义了服务组的数据模型，用于在容器管理器中表示多容器服务组及其依赖关系
"""

import os
import enum
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime
import yaml

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.models.service_group")


class ServiceStatus(enum.Enum):
    """服务状态枚举"""

    UNKNOWN = enum.auto()  # 未知状态
    CREATED = enum.auto()  # 已创建但未启动
    RUNNING = enum.auto()  # 运行中
    PARTIALLY_RUNNING = enum.auto()  # 部分容器运行中
    STOPPED = enum.auto()  # 已停止
    FAILED = enum.auto()  # 启动失败或运行时失败


class NetworkMode(enum.Enum):
    """网络模式枚举"""

    BRIDGE = "bridge"  # 默认桥接网络
    HOST = "host"  # 共享主机网络
    NONE = "none"  # 无网络
    CUSTOM = "custom"  # 自定义网络


@dataclass
class ServiceNetwork:
    """服务网络配置"""

    name: str  # 网络名称
    mode: NetworkMode = NetworkMode.BRIDGE  # 网络模式
    subnet: Optional[str] = None  # 子网配置，如 "172.28.0.0/16"
    gateway: Optional[str] = None  # 网关配置，如 "172.28.0.1"
    driver: str = "bridge"  # 网络驱动类型
    enable_ipv6: bool = False  # 是否启用IPv6
    internal: bool = False  # 是否为内部网络
    aliases: List[str] = field(default_factory=list)  # 网络别名
    ipv4_address: Optional[str] = None  # IPv4地址
    ipv6_address: Optional[str] = None  # IPv6地址
    labels: Dict[str, str] = field(default_factory=dict)  # 网络标签

    def __str__(self) -> str:
        """字符串表示"""
        return f"Network({self.name}, {self.mode.value})"

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            包含网络信息的字典
        """
        result = {
            "name": self.name,
            "mode": self.mode.value,
            "driver": self.driver,
            "enable_ipv6": self.enable_ipv6,
            "internal": self.internal,
        }

        if self.subnet:
            result["subnet"] = self.subnet
        if self.gateway:
            result["gateway"] = self.gateway
        if self.aliases:
            result["aliases"] = self.aliases
        if self.ipv4_address:
            result["ipv4_address"] = self.ipv4_address
        if self.ipv6_address:
            result["ipv6_address"] = self.ipv6_address
        if self.labels:
            result["labels"] = self.labels

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceNetwork":
        """
        从字典创建网络配置

        Args:
            data: 包含网络配置的字典

        Returns:
            ServiceNetwork实例
        """
        mode = NetworkMode(data.get("mode", "bridge"))
        return cls(
            name=data.get("name", "default"),
            mode=mode,
            subnet=data.get("subnet"),
            gateway=data.get("gateway"),
            driver=data.get("driver", "bridge"),
            enable_ipv6=data.get("enable_ipv6", False),
            internal=data.get("internal", False),
            aliases=data.get("aliases", []),
            ipv4_address=data.get("ipv4_address"),
            ipv6_address=data.get("ipv6_address"),
            labels=data.get("labels", {}),
        )


@dataclass
class ServiceDependency:
    """服务依赖配置"""

    service_name: str  # 依赖的服务名称
    condition: str = (
        "service_started"  # 依赖条件，可选值：service_started, service_healthy, service_completed_successfully
    )
    required: bool = True  # 是否为必须依赖，如果为True则依赖不满足时不启动本服务

    def __str__(self) -> str:
        """字符串表示"""
        return f"Dependency({self.service_name}, {self.condition})"

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            包含依赖信息的字典
        """
        return {
            "service_name": self.service_name,
            "condition": self.condition,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceDependency":
        """
        从字典创建依赖配置

        Args:
            data: 包含依赖配置的字典

        Returns:
            ServiceDependency实例
        """
        return cls(
            service_name=data.get("service_name", ""),
            condition=data.get("condition", "service_started"),
            required=data.get("required", True),
        )


@dataclass
class Service:
    """服务配置"""

    name: str  # 服务名称
    image: str  # 容器镜像
    container_name: Optional[str] = None  # 容器名称，如果不指定则自动生成
    depends_on: List[ServiceDependency] = field(default_factory=list)  # 依赖的服务
    command: Optional[str] = None  # 容器启动命令
    entrypoint: Optional[List[str]] = None  # 容器入口点
    working_dir: Optional[str] = None  # 工作目录
    user: Optional[str] = None  # 用户
    restart: str = "no"  # 重启策略：no, always, on-failure, unless-stopped
    ports: Dict[str, str] = field(
        default_factory=dict
    )  # 端口映射，格式: {"容器端口/协议": "主机端口"}
    volumes: Dict[str, str] = field(
        default_factory=dict
    )  # 卷挂载，格式: {"主机路径": "容器路径"}
    environment: Dict[str, str] = field(default_factory=dict)  # 环境变量
    networks: List[str] = field(default_factory=list)  # 服务使用的网络
    labels: Dict[str, str] = field(default_factory=dict)  # 容器标签
    healthcheck: Optional[Dict[str, Any]] = None  # 健康检查配置
    cpu_limit: Optional[float] = None  # CPU限制
    memory_limit: Optional[str] = None  # 内存限制，如 "512m"
    stop_grace_period: str = "10s"  # 停止容器前等待的时间
    deploy: Optional[Dict[str, Any]] = None  # 部署配置

    def __str__(self) -> str:
        """字符串表示"""
        return f"Service({self.name}, {self.image})"

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            包含服务信息的字典
        """
        result = {
            "name": self.name,
            "image": self.image,
            "restart": self.restart,
        }

        if self.container_name:
            result["container_name"] = self.container_name
        if self.depends_on:
            result["depends_on"] = [d.to_dict() for d in self.depends_on]
        if self.command:
            result["command"] = self.command
        if self.entrypoint:
            result["entrypoint"] = self.entrypoint
        if self.working_dir:
            result["working_dir"] = self.working_dir
        if self.user:
            result["user"] = self.user
        if self.ports:
            result["ports"] = self.ports
        if self.volumes:
            result["volumes"] = self.volumes
        if self.environment:
            result["environment"] = self.environment
        if self.networks:
            result["networks"] = self.networks
        if self.labels:
            result["labels"] = self.labels
        if self.healthcheck:
            result["healthcheck"] = self.healthcheck
        if self.cpu_limit is not None:
            result["cpu_limit"] = self.cpu_limit
        if self.memory_limit:
            result["memory_limit"] = self.memory_limit
        if self.stop_grace_period:
            result["stop_grace_period"] = self.stop_grace_period
        if self.deploy:
            result["deploy"] = self.deploy

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Service":
        """
        从字典创建服务配置

        Args:
            data: 包含服务配置的字典

        Returns:
            Service实例
        """
        # 处理依赖关系
        depends_on = []
        if "depends_on" in data:
            if isinstance(data["depends_on"], list):
                for dep in data["depends_on"]:
                    if isinstance(dep, dict):
                        depends_on.append(ServiceDependency.from_dict(dep))
                    else:
                        depends_on.append(ServiceDependency(service_name=str(dep)))
            elif isinstance(data["depends_on"], dict):
                for service_name, condition in data["depends_on"].items():
                    depends_on.append(
                        ServiceDependency(
                            service_name=service_name, condition=condition
                        )
                    )
            else:
                # 假设是逗号分隔的字符串或单个服务名
                services = (
                    data["depends_on"].split(",")
                    if isinstance(data["depends_on"], str)
                    else [str(data["depends_on"])]
                )
                for service in services:
                    depends_on.append(ServiceDependency(service_name=service.strip()))

        return cls(
            name=data.get("name", ""),
            image=data.get("image", ""),
            container_name=data.get("container_name"),
            depends_on=depends_on,
            command=data.get("command"),
            entrypoint=data.get("entrypoint"),
            working_dir=data.get("working_dir"),
            user=data.get("user"),
            restart=data.get("restart", "no"),
            ports=data.get("ports", {}),
            volumes=data.get("volumes", {}),
            environment=data.get("environment", {}),
            networks=data.get("networks", []),
            labels=data.get("labels", {}),
            healthcheck=data.get("healthcheck"),
            cpu_limit=data.get("cpu_limit"),
            memory_limit=data.get("memory_limit"),
            stop_grace_period=data.get("stop_grace_period", "10s"),
            deploy=data.get("deploy"),
        )


@dataclass
class ServiceGroup:
    """服务组配置"""

    name: str  # 服务组名称
    description: Optional[str] = None  # 服务组描述
    version: str = "1.0"  # 配置版本
    services: Dict[str, Service] = field(default_factory=dict)  # 服务配置
    networks: Dict[str, ServiceNetwork] = field(default_factory=dict)  # 网络配置
    created_at: Optional[datetime] = None  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间
    status: ServiceStatus = ServiceStatus.UNKNOWN  # 服务组状态

    def __post_init__(self):
        """初始化后处理"""
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        """字符串表示"""
        return f"ServiceGroup({self.name}, {len(self.services)} services)"

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            包含服务组信息的字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "services": {
                name: service.to_dict() for name, service in self.services.items()
            },
            "networks": {
                name: network.to_dict() for name, network in self.networks.items()
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def save_to_file(self, file_path: str) -> bool:
        """
        保存到YAML文件

        Args:
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            # 保存数据
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.to_dict(), f, default_flow_style=False, allow_unicode=True
                )

            logger.info(f"服务组配置已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存服务组配置失败: {e}")
            return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceGroup":
        """
        从字典创建服务组配置

        Args:
            data: 包含服务组配置的字典

        Returns:
            ServiceGroup实例
        """
        services = {}
        if "services" in data:
            for name, service_data in data["services"].items():
                if "name" not in service_data:
                    service_data["name"] = name
                services[name] = Service.from_dict(service_data)

        networks = {}
        if "networks" in data:
            for name, network_data in data["networks"].items():
                if "name" not in network_data:
                    network_data["name"] = name
                networks[name] = ServiceNetwork.from_dict(network_data)

        created_at = None
        if "created_at" in data and data["created_at"]:
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                created_at = datetime.now()

        updated_at = None
        if "updated_at" in data and data["updated_at"]:
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                updated_at = datetime.now()

        return cls(
            name=data.get("name", "default"),
            description=data.get("description"),
            version=data.get("version", "1.0"),
            services=services,
            networks=networks,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["ServiceGroup"]:
        """
        从YAML文件加载

        Args:
            file_path: 文件路径

        Returns:
            ServiceGroup实例，如果加载失败则返回None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.error(f"文件为空或格式错误: {file_path}")
                return None

            logger.info(f"从文件加载服务组配置: {file_path}")
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"加载服务组配置失败: {e}")
            return None

    def get_service_dependencies(self, service_name: str) -> Set[str]:
        """
        获取服务的所有依赖服务

        Args:
            service_name: 服务名称

        Returns:
            依赖服务名称集合
        """
        if service_name not in self.services:
            return set()

        service = self.services[service_name]
        direct_deps = {dep.service_name for dep in service.depends_on}
        all_deps = direct_deps.copy()

        # 递归查找传递依赖
        for dep in direct_deps:
            if dep in self.services:
                all_deps.update(self.get_service_dependencies(dep))

        return all_deps

    def get_startup_order(self) -> List[str]:
        """
        获取服务启动顺序

        Returns:
            按启动顺序排序的服务名称列表
        """
        # 拓扑排序
        visited = set()
        temp_mark = set()
        order = []

        def visit(service_name):
            if service_name in temp_mark:
                # 发现循环依赖
                logger.warning(f"服务组 {self.name} 中发现循环依赖: {service_name}")
                return
            if service_name in visited:
                return

            temp_mark.add(service_name)

            # 遍历依赖
            if service_name in self.services:
                service = self.services[service_name]
                for dep in service.depends_on:
                    if dep.service_name in self.services:
                        visit(dep.service_name)

            temp_mark.remove(service_name)
            visited.add(service_name)
            order.append(service_name)

        # 对所有服务进行拓扑排序
        for service_name in self.services:
            if service_name not in visited:
                visit(service_name)

        # 反转顺序，确保依赖先启动
        order.reverse()
        return order

    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证服务组配置

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 检查服务名称是否唯一
        if len(self.services) != len({s.name for s in self.services.values()}):
            errors.append("服务名称必须唯一")

        # 检查网络名称是否唯一
        if len(self.networks) != len({n.name for n in self.networks.values()}):
            errors.append("网络名称必须唯一")

        # 检查依赖的服务是否存在
        for service_name, service in self.services.items():
            for dep in service.depends_on:
                if dep.service_name not in self.services:
                    errors.append(
                        f"服务 {service_name} 依赖不存在的服务: {dep.service_name}"
                    )

        # 检查服务使用的网络是否存在
        for service_name, service in self.services.items():
            for network_name in service.networks:
                if network_name not in self.networks:
                    errors.append(
                        f"服务 {service_name} 使用不存在的网络: {network_name}"
                    )

        # 检查是否存在循环依赖
        try:
            self.get_startup_order()
        except Exception as e:
            errors.append(f"服务组存在循环依赖: {str(e)}")

        return len(errors) == 0, errors
