#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器网络管理器

提供Docker容器网络的创建、配置和管理功能
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import docker
from docker.errors import DockerException, APIError, NotFound

from backend.config import config
from .models.service_group import ServiceNetwork, NetworkMode

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.network_manager")


class NetworkManager:
    """容器网络管理器"""

    def __init__(self):
        """初始化网络管理器"""
        logger.info("初始化容器网络管理器")

        # 初始化配置
        self._init_config()

        # 初始化Docker客户端
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except DockerException as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            self.docker_client = None

        # 网络模板缓存
        self.network_templates: Dict[str, Dict[str, Any]] = {}

        # 加载网络模板
        self.load_network_templates()

        logger.info("容器网络管理器初始化完成")

    def _init_config(self):
        """初始化配置"""
        # 确保配置存在
        if "network_manager" not in config:
            config.update_config(
                "network_manager",
                {
                    "templates_dir": os.path.join(
                        os.path.expanduser("~"), ".smoothstack", "network_templates"
                    ),  # 网络模板目录
                    "default_subnet": "172.20.0.0/16",  # 默认子网
                    "default_gateway": "172.20.0.1",  # 默认网关
                },
            )

        # 创建网络模板目录
        templates_dir = config.get("network_manager.templates_dir")
        if templates_dir and not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)

        # 创建默认模板
        self._create_default_templates()

    def _create_default_templates(self):
        """创建默认网络模板"""
        templates_dir = config.get("network_manager.templates_dir")
        if not templates_dir:
            return

        default_templates = {
            "isolated": {
                "name": "isolated",
                "description": "隔离网络，容器间可以通信，但无法访问外部网络",
                "driver": "bridge",
                "internal": True,
                "subnet": "172.21.0.0/16",
                "gateway": "172.21.0.1",
                "enable_ipv6": False,
                "options": {},
                "labels": {
                    "smoothstack.network_type": "isolated",
                    "smoothstack.description": "隔离网络，容器间可以通信，但无法访问外部网络",
                },
            },
            "web_app": {
                "name": "web_app",
                "description": "Web应用网络，适合前后端分离应用",
                "driver": "bridge",
                "subnet": "172.22.0.0/16",
                "gateway": "172.22.0.1",
                "enable_ipv6": False,
                "options": {},
                "labels": {
                    "smoothstack.network_type": "web_app",
                    "smoothstack.description": "Web应用网络，适合前后端分离应用",
                },
            },
            "high_performance": {
                "name": "high_performance",
                "description": "高性能网络，适合需要高吞吐量的应用",
                "driver": "bridge",
                "subnet": "172.23.0.0/16",
                "gateway": "172.23.0.1",
                "enable_ipv6": False,
                "options": {
                    "com.docker.network.driver.mtu": "9000"  # 使用大MTU提高性能
                },
                "labels": {
                    "smoothstack.network_type": "high_performance",
                    "smoothstack.description": "高性能网络，适合需要高吞吐量的应用",
                },
            },
            "database": {
                "name": "database",
                "description": "数据库网络，适合数据库集群",
                "driver": "bridge",
                "subnet": "172.24.0.0/16",
                "gateway": "172.24.0.1",
                "enable_ipv6": False,
                "internal": True,  # 内部网络，增加安全性
                "options": {},
                "labels": {
                    "smoothstack.network_type": "database",
                    "smoothstack.description": "数据库网络，适合数据库集群",
                },
            },
            "micro_services": {
                "name": "micro_services",
                "description": "微服务网络，适合微服务架构应用",
                "driver": "bridge",
                "subnet": "172.25.0.0/16",
                "gateway": "172.25.0.1",
                "enable_ipv6": False,
                "options": {},
                "labels": {
                    "smoothstack.network_type": "micro_services",
                    "smoothstack.description": "微服务网络，适合微服务架构应用",
                },
            },
        }

        # 创建默认模板文件
        for template_name, template_data in default_templates.items():
            template_path = os.path.join(templates_dir, f"{template_name}.json")
            if not os.path.exists(template_path):
                try:
                    with open(template_path, "w", encoding="utf-8") as f:
                        json.dump(template_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"已创建默认网络模板: {template_name}")
                except Exception as e:
                    logger.error(f"创建默认网络模板失败 {template_name}: {e}")

    def load_network_templates(self):
        """加载网络模板"""
        logger.info("加载网络模板")

        self.network_templates = {}
        templates_dir = config.get("network_manager.templates_dir")

        if not templates_dir or not os.path.exists(templates_dir):
            logger.warning(f"网络模板目录不存在: {templates_dir}")
            return

        # 加载所有JSON模板文件
        for file_name in os.listdir(templates_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(templates_dir, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        template_data = json.load(f)

                    template_name = template_data.get(
                        "name", os.path.splitext(file_name)[0]
                    )
                    self.network_templates[template_name] = template_data
                    logger.debug(f"加载网络模板: {template_name}")
                except Exception as e:
                    logger.error(f"加载网络模板失败 {file_path}: {e}")

        logger.info(f"已加载 {len(self.network_templates)} 个网络模板")

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取网络模板

        Args:
            name: 模板名称

        Returns:
            模板数据，如果不存在则返回None
        """
        return self.network_templates.get(name)

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        列出所有网络模板

        Returns:
            模板列表
        """
        return list(self.network_templates.values())

    def save_template(self, template_data: Dict[str, Any]) -> bool:
        """
        保存网络模板

        Args:
            template_data: 模板数据

        Returns:
            是否保存成功
        """
        templates_dir = config.get("network_manager.templates_dir")
        if not templates_dir:
            logger.error("未配置网络模板目录")
            return False

        template_name = template_data.get("name")
        if not template_name:
            logger.error("模板数据缺少名称")
            return False

        file_path = os.path.join(templates_dir, f"{template_name}.json")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)

            # 更新缓存
            self.network_templates[template_name] = template_data
            logger.info(f"已保存网络模板: {template_name}")
            return True
        except Exception as e:
            logger.error(f"保存网络模板失败: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """
        删除网络模板

        Args:
            name: 模板名称

        Returns:
            是否删除成功
        """
        if name not in self.network_templates:
            logger.warning(f"尝试删除不存在的网络模板: {name}")
            return False

        templates_dir = config.get("network_manager.templates_dir")
        if not templates_dir:
            return False

        file_path = os.path.join(templates_dir, f"{name}.json")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)

            # 从缓存中移除
            del self.network_templates[name]
            logger.info(f"已删除网络模板: {name}")
            return True
        except Exception as e:
            logger.error(f"删除网络模板失败: {e}")
            return False

    def create_network_from_template(
        self,
        template_name: str,
        network_name: Optional[str] = None,
        subnet: Optional[str] = None,
        gateway: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        从模板创建网络

        Args:
            template_name: 模板名称
            network_name: 网络名称，如果不提供则使用生成的名称
            subnet: 自定义子网，覆盖模板中的子网
            gateway: 自定义网关，覆盖模板中的网关
            custom_options: 自定义选项，覆盖或扩展模板中的选项

        Returns:
            (是否成功, 消息, 网络ID)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化", None

        # 获取模板
        template = self.get_template(template_name)
        if not template:
            return False, f"网络模板不存在: {template_name}", None

        # 准备网络配置
        network_config = template.copy()

        # 自定义网络名称
        if network_name:
            network_config["name"] = network_name
        else:
            network_name = network_config["name"]
            # 添加随机后缀避免冲突
            import uuid

            short_uuid = str(uuid.uuid4())[:8]
            network_name = f"{network_name}_{short_uuid}"
            network_config["name"] = network_name

        # 自定义子网和网关
        if subnet:
            network_config["subnet"] = subnet
        if gateway:
            network_config["gateway"] = gateway

        # 自定义选项
        if custom_options:
            if "options" not in network_config:
                network_config["options"] = {}
            network_config["options"].update(custom_options)

        # 创建网络
        try:
            # 检查网络是否已存在
            try:
                self.docker_client.networks.get(network_name)
                return False, f"网络已存在: {network_name}", None
            except NotFound:
                # 网络不存在，继续创建
                pass

            # 准备IPAM配置
            ipam_config = None
            if "subnet" in network_config or "gateway" in network_config:
                ipam_pool = {}
                if "subnet" in network_config:
                    ipam_pool["subnet"] = network_config["subnet"]
                if "gateway" in network_config:
                    ipam_pool["gateway"] = network_config["gateway"]

                ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

            # 创建网络
            create_params = {
                "name": network_name,
                "driver": network_config.get("driver", "bridge"),
                "options": network_config.get("options", {}),
                "ipam": ipam_config,
                "labels": network_config.get("labels", {}),
                "enable_ipv6": network_config.get("enable_ipv6", False),
                "internal": network_config.get("internal", False),
            }

            # 创建网络
            network = self.docker_client.networks.create(**create_params)
            logger.info(f"已从模板 '{template_name}' 创建网络: {network_name}")
            return (
                True,
                f"已从模板 '{template_name}' 创建网络: {network_name}",
                network.id,
            )

        except Exception as e:
            logger.error(f"从模板创建网络失败: {e}")
            return False, f"创建网络失败: {str(e)}", None

    def create_network(
        self, network: ServiceNetwork
    ) -> Tuple[bool, str, Optional[str]]:
        """
        创建网络

        Args:
            network: 网络配置

        Returns:
            (是否成功, 消息, 网络ID)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化", None

        try:
            # 检查网络是否已存在
            try:
                existing_network = self.docker_client.networks.get(network.name)
                logger.info(f"网络已存在: {network.name}")
                return True, f"网络已存在: {network.name}", existing_network.id
            except NotFound:
                # 网络不存在，创建新网络
                pass

            # 准备IPAM配置
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
            return True, f"已创建网络: {network.name}", created_network.id

        except Exception as e:
            logger.error(f"创建网络失败: {e}")
            return False, f"创建网络失败: {str(e)}", None

    def delete_network(self, network_name: str) -> Tuple[bool, str]:
        """
        删除网络

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

    def list_networks(
        self, filter_labels: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        列出网络

        Args:
            filter_labels: 过滤标签

        Returns:
            网络列表
        """
        if not self.docker_client:
            return []

        try:
            filters = {}
            if filter_labels:
                filters["label"] = [f"{k}={v}" for k, v in filter_labels.items()]

            networks = self.docker_client.networks.list(filters=filters)

            result = []
            for network in networks:
                # 跳过默认网络
                if network.name in ["bridge", "host", "none"]:
                    continue

                network_info = {
                    "id": network.id,
                    "name": network.name,
                    "driver": network.attrs.get("Driver", ""),
                    "scope": network.attrs.get("Scope", ""),
                    "internal": network.attrs.get("Internal", False),
                    "ipam": network.attrs.get("IPAM", {}),
                    "containers": len(network.containers),
                    "labels": network.attrs.get("Labels", {}),
                }

                result.append(network_info)

            return result

        except Exception as e:
            logger.error(f"列出网络失败: {e}")
            return []

    def get_network_details(self, network_name: str) -> Optional[Dict[str, Any]]:
        """
        获取网络详情

        Args:
            network_name: 网络名称

        Returns:
            网络详情，如果不存在则返回None
        """
        if not self.docker_client:
            return None

        try:
            try:
                network = self.docker_client.networks.get(network_name)
            except NotFound:
                logger.warning(f"网络不存在: {network_name}")
                return None

            # 获取基本信息
            details = {
                "id": network.id,
                "name": network.name,
                "driver": network.attrs.get("Driver", ""),
                "scope": network.attrs.get("Scope", ""),
                "internal": network.attrs.get("Internal", False),
                "labels": network.attrs.get("Labels", {}),
                "options": network.attrs.get("Options", {}),
                "created": network.attrs.get("Created", ""),
            }

            # IPAM配置
            ipam = network.attrs.get("IPAM", {})
            ipam_config = ipam.get("Config", [])
            if ipam_config:
                details["subnet"] = ipam_config[0].get("Subnet", "")
                details["gateway"] = ipam_config[0].get("Gateway", "")

            # 连接的容器
            connected_containers = {}
            for container_id, container_config in network.attrs.get(
                "Containers", {}
            ).items():
                container_name = container_config.get("Name", container_id)
                connected_containers[container_name] = {
                    "id": container_id,
                    "mac_address": container_config.get("MacAddress", ""),
                    "ipv4_address": container_config.get("IPv4Address", ""),
                    "ipv6_address": container_config.get("IPv6Address", ""),
                }

            details["connected_containers"] = connected_containers
            details["container_count"] = len(connected_containers)

            return details

        except Exception as e:
            logger.error(f"获取网络详情失败: {e}")
            return None

    def connect_container(
        self,
        network_name: str,
        container_name: str,
        ipv4_address: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        将容器连接到网络

        Args:
            network_name: 网络名称
            container_name: 容器名称
            ipv4_address: IPv4地址
            aliases: 网络别名

        Returns:
            (是否成功, 消息)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 获取网络
            try:
                network = self.docker_client.networks.get(network_name)
            except NotFound:
                return False, f"网络不存在: {network_name}"

            # 获取容器
            try:
                container = self.docker_client.containers.get(container_name)
            except NotFound:
                return False, f"容器不存在: {container_name}"

            # 准备连接参数
            connect_params = {}
            if ipv4_address:
                connect_params["ipv4_address"] = ipv4_address
            if aliases:
                connect_params["aliases"] = aliases

            # 连接容器到网络
            network.connect(container, **connect_params)
            logger.info(f"已将容器 {container_name} 连接到网络 {network_name}")
            return True, f"已将容器 {container_name} 连接到网络 {network_name}"

        except Exception as e:
            logger.error(f"连接容器到网络失败: {e}")
            return False, f"连接容器到网络失败: {str(e)}"

    def disconnect_container(
        self, network_name: str, container_name: str
    ) -> Tuple[bool, str]:
        """
        从网络断开容器

        Args:
            network_name: 网络名称
            container_name: 容器名称

        Returns:
            (是否成功, 消息)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 获取网络
            try:
                network = self.docker_client.networks.get(network_name)
            except NotFound:
                return False, f"网络不存在: {network_name}"

            # 获取容器
            try:
                container = self.docker_client.containers.get(container_name)
            except NotFound:
                return False, f"容器不存在: {container_name}"

            # 断开容器与网络的连接
            network.disconnect(container)
            logger.info(f"已断开容器 {container_name} 与网络 {network_name} 的连接")
            return True, f"已断开容器 {container_name} 与网络 {network_name} 的连接"

        except Exception as e:
            logger.error(f"断开容器与网络的连接失败: {e}")
            return False, f"断开容器与网络的连接失败: {str(e)}"

    def generate_network_config(self, template_name: str, **kwargs) -> ServiceNetwork:
        """
        生成网络配置

        Args:
            template_name: 模板名称
            **kwargs: 自定义配置

        Returns:
            ServiceNetwork实例
        """
        # 获取模板
        template = self.get_template(template_name)
        if not template:
            # 使用默认配置
            return ServiceNetwork(
                name=kwargs.get("name", "default"),
                driver=kwargs.get("driver", "bridge"),
                subnet=kwargs.get(
                    "subnet", config.get("network_manager.default_subnet")
                ),
                gateway=kwargs.get(
                    "gateway", config.get("network_manager.default_gateway")
                ),
                enable_ipv6=kwargs.get("enable_ipv6", False),
                internal=kwargs.get("internal", False),
                labels=kwargs.get("labels", {}),
            )

        # 基于模板创建，覆盖自定义配置
        return ServiceNetwork(
            name=kwargs.get("name", template.get("name", "default")),
            driver=kwargs.get("driver", template.get("driver", "bridge")),
            subnet=kwargs.get("subnet", template.get("subnet")),
            gateway=kwargs.get("gateway", template.get("gateway")),
            enable_ipv6=kwargs.get("enable_ipv6", template.get("enable_ipv6", False)),
            internal=kwargs.get("internal", template.get("internal", False)),
            labels={**template.get("labels", {}), **kwargs.get("labels", {})},
            aliases=kwargs.get("aliases", []),
        )

    def check_network_connectivity(
        self, source_container: str, target_container: str
    ) -> Tuple[bool, str]:
        """
        检查容器间的网络连接

        Args:
            source_container: 源容器名称
            target_container: 目标容器名称

        Returns:
            (是否可连接, 消息)
        """
        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 获取源容器
            try:
                source = self.docker_client.containers.get(source_container)
            except NotFound:
                return False, f"源容器不存在: {source_container}"

            # 获取目标容器
            try:
                target = self.docker_client.containers.get(target_container)
                # 检查目标容器是否在运行
                if target.status != "running":
                    return False, f"目标容器未运行: {target_container}"
            except NotFound:
                return False, f"目标容器不存在: {target_container}"

            # 获取目标容器IP地址
            target_networks = target.attrs.get("NetworkSettings", {}).get(
                "Networks", {}
            )
            if not target_networks:
                return False, f"目标容器未连接到任何网络: {target_container}"

            # 从各网络中尝试连接
            for network_name, network_config in target_networks.items():
                target_ip = network_config.get("IPAddress", "")
                if not target_ip:
                    continue

                # 尝试ping目标IP
                exit_code, output = source.exec_run(
                    cmd=f"ping -c 1 -W 2 {target_ip}", tty=True
                )

                if exit_code == 0:
                    return (
                        True,
                        f"容器 {source_container} 可以连接到 {target_container} ({target_ip})",
                    )

            return False, f"容器 {source_container} 无法连接到 {target_container}"

        except Exception as e:
            logger.error(f"检查网络连接失败: {e}")
            return False, f"检查网络连接失败: {str(e)}"
