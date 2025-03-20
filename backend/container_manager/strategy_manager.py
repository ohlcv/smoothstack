#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多容器策略管理器

提供多容器部署、扩展、资源分配和依赖管理的策略功能
"""

import os
import time
import json
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from pathlib import Path
import docker
from docker.errors import DockerException, NotFound, APIError

from backend.container_manager.manager import ContainerManager
from backend.container_manager.models.strategy import (
    DeploymentStrategy,
    ResourceAllocationPolicy,
)
from backend.container_manager.service_orchestrator import ServiceOrchestrator

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.strategy_manager")


class StrategyManager:
    """多容器策略管理器"""

    def __init__(self):
        """初始化策略管理器"""
        try:
            self.container_manager = ContainerManager()
            self.service_orchestrator = ServiceOrchestrator()
            self.client = self.container_manager.client
            self._strategies = {}  # 存储策略对象
            self._strategy_lock = threading.RLock()  # 保护策略数据的锁

            # 创建策略存储目录
            self._config_dir = Path.home() / ".smoothstack" / "strategies"
            self._config_dir.mkdir(parents=True, exist_ok=True)

            # 加载已保存的策略
            self._load_strategies()

            logger.info("策略管理器初始化成功")
        except Exception as e:
            logger.error(f"策略管理器初始化失败: {e}")
            raise

    def _load_strategies(self) -> None:
        """加载已保存的策略"""
        try:
            strategy_files = list(self._config_dir.glob("*.json"))
            for file_path in strategy_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        strategy_data = json.load(f)
                        strategy = DeploymentStrategy.from_dict(strategy_data)
                        self._strategies[strategy.name] = strategy
                        logger.debug(f"已加载策略 '{strategy.name}'")
                except Exception as e:
                    logger.error(f"加载策略文件 {file_path} 失败: {e}")

            logger.info(f"已加载 {len(self._strategies)} 个策略")
        except Exception as e:
            logger.error(f"加载策略失败: {e}")

    def _save_strategy(self, strategy: DeploymentStrategy) -> bool:
        """保存策略到文件"""
        try:
            file_path = self._config_dir / f"{strategy.name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(strategy.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug(f"策略 '{strategy.name}' 已保存到 {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存策略 '{strategy.name}' 失败: {e}")
            return False

    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        列出所有可用策略

        Returns:
            策略信息列表
        """
        with self._strategy_lock:
            return [strategy.to_dict() for strategy in self._strategies.values()]

    def get_strategy(self, strategy_name: str) -> Optional[DeploymentStrategy]:
        """
        获取指定名称的策略

        Args:
            strategy_name: 策略名称

        Returns:
            策略对象，如不存在则返回None
        """
        with self._strategy_lock:
            return self._strategies.get(strategy_name)

    def create_strategy(
        self,
        name: str,
        description: str = "",
        container_configs: List[Dict[str, Any]] = None,
        resource_policy: Dict[str, Any] = None,
        dependency_graph: Dict[str, List[str]] = None,
        labels: Dict[str, str] = None,
        restart_policy: str = "unless-stopped",
    ) -> DeploymentStrategy:
        """
        创建新的部署策略

        Args:
            name: 策略名称
            description: 策略描述
            container_configs: 容器配置列表
            resource_policy: 资源分配策略
            dependency_graph: 容器依赖关系图
            labels: 策略标签
            restart_policy: 重启策略

        Returns:
            创建的策略对象
        """
        with self._strategy_lock:
            if name in self._strategies:
                raise ValueError(f"策略 '{name}' 已存在")

            # 创建资源分配策略
            if resource_policy:
                allocation_policy = ResourceAllocationPolicy.from_dict(resource_policy)
            else:
                allocation_policy = ResourceAllocationPolicy()

            # 创建策略对象
            strategy = DeploymentStrategy(
                name=name,
                description=description,
                container_configs=container_configs or [],
                resource_policy=allocation_policy,
                dependency_graph=dependency_graph or {},
                labels=labels or {},
                restart_policy=restart_policy,
            )

            # 保存策略
            self._strategies[name] = strategy
            self._save_strategy(strategy)

            logger.info(f"已创建策略 '{name}'")
            return strategy

    def update_strategy(
        self,
        name: str,
        description: Optional[str] = None,
        container_configs: Optional[List[Dict[str, Any]]] = None,
        resource_policy: Optional[Dict[str, Any]] = None,
        dependency_graph: Optional[Dict[str, List[str]]] = None,
        labels: Optional[Dict[str, str]] = None,
        restart_policy: Optional[str] = None,
    ) -> Optional[DeploymentStrategy]:
        """
        更新现有策略

        Args:
            name: 策略名称
            description: 策略描述
            container_configs: 容器配置列表
            resource_policy: 资源分配策略
            dependency_graph: 容器依赖关系图
            labels: 策略标签
            restart_policy: 重启策略

        Returns:
            更新后的策略对象，如不存在则返回None
        """
        with self._strategy_lock:
            strategy = self._strategies.get(name)
            if not strategy:
                logger.warning(f"要更新的策略 '{name}' 不存在")
                return None

            # 更新策略属性
            if description is not None:
                strategy.description = description

            if container_configs is not None:
                strategy.container_configs = container_configs

            if resource_policy is not None:
                strategy.resource_policy = ResourceAllocationPolicy.from_dict(
                    resource_policy
                )

            if dependency_graph is not None:
                strategy.dependency_graph = dependency_graph

            if labels is not None:
                strategy.labels = labels

            if restart_policy is not None:
                strategy.restart_policy = restart_policy

            # 保存更新后的策略
            self._save_strategy(strategy)

            logger.info(f"已更新策略 '{name}'")
            return strategy

    def delete_strategy(self, name: str) -> bool:
        """
        删除策略

        Args:
            name: 策略名称

        Returns:
            是否成功删除
        """
        with self._strategy_lock:
            if name not in self._strategies:
                logger.warning(f"要删除的策略 '{name}' 不存在")
                return False

            # 删除策略文件
            file_path = self._config_dir / f"{name}.json"
            if file_path.exists():
                file_path.unlink()

            # 从内存中移除
            del self._strategies[name]

            logger.info(f"已删除策略 '{name}'")
            return True

    def deploy_strategy(
        self,
        strategy_name: str,
        deployment_name: str = None,
        environment_variables: Dict[str, Dict[str, str]] = None,
        network_name: str = None,
    ) -> Dict[str, Any]:
        """
        部署策略

        Args:
            strategy_name: 策略名称
            deployment_name: 部署名称，默认使用策略名称
            environment_variables: 容器环境变量，格式为 {container_name: {var_name: var_value}}
            network_name: 网络名称，如果指定则将所有容器连接到此网络

        Returns:
            部署结果，包含成功创建的容器和错误信息
        """
        # 获取策略
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return {"error": f"策略 '{strategy_name}' 不存在"}

        deployment_name = deployment_name or strategy_name
        environment_variables = environment_variables or {}

        logger.info(f"开始部署策略 '{strategy_name}' 为 '{deployment_name}'")

        # 部署结果
        result = {
            "strategy_name": strategy_name,
            "deployment_name": deployment_name,
            "containers": {},
            "errors": {},
        }

        # 根据依赖图确定部署顺序
        deployment_order = self._resolve_deployment_order(strategy.dependency_graph)

        # 创建网络(如果需要)
        if network_name:
            try:
                self.container_manager.create_network(network_name)
                logger.info(f"已创建网络 '{network_name}'")
            except Exception as e:
                logger.warning(f"创建网络 '{network_name}' 失败: {e}")

        # 按顺序部署容器
        for container_name in deployment_order:
            # 查找容器配置
            container_config = next(
                (
                    c
                    for c in strategy.container_configs
                    if c.get("name") == container_name
                ),
                None,
            )

            if not container_config:
                logger.warning(f"找不到容器 '{container_name}' 的配置")
                result["errors"][container_name] = "配置缺失"
                continue

            # 准备容器创建参数
            create_params = self._prepare_container_params(
                container_config,
                strategy,
                deployment_name,
                environment_variables.get(container_name, {}),
                network_name,
            )

            # 创建容器
            try:
                container = self.client.containers.create(**create_params)
                logger.info(f"已创建容器 {container.name} ({container.id})")
                result["containers"][container_name] = {
                    "id": container.id,
                    "name": container.name,
                    "status": "created",
                }

                # 启动容器
                container.start()
                logger.info(f"已启动容器 {container.name}")
                result["containers"][container_name]["status"] = "running"

            except Exception as e:
                logger.error(f"创建容器 '{container_name}' 失败: {e}")
                result["errors"][container_name] = str(e)
                # 如果是关键容器，可能需要清理已创建的容器
                if container_config.get("is_critical", False):
                    self._cleanup_deployment(result["containers"])
                    result["status"] = "failed"
                    result["message"] = (
                        f"关键容器 '{container_name}' 创建失败，已回滚部署"
                    )
                    return result

        # 如果有错误但不是关键错误
        if result["errors"]:
            result["status"] = "partial"
            result["message"] = "部分容器创建成功，部分失败"
        else:
            result["status"] = "success"
            result["message"] = "所有容器创建成功"

        return result

    def _resolve_deployment_order(
        self, dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """
        根据依赖关系解析部署顺序

        Args:
            dependency_graph: 依赖关系图，格式为 {container_name: [dependency1, dependency2]}

        Returns:
            容器部署顺序列表
        """
        # 所有容器名称
        all_containers = set(dependency_graph.keys())
        for deps in dependency_graph.values():
            all_containers.update(deps)

        # 计算入度（依赖数量）
        in_degree = {container: 0 for container in all_containers}
        for container, deps in dependency_graph.items():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0)
            in_degree[container] = in_degree.get(container, 0) + len(deps)

        # 拓扑排序
        queue = [container for container, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # 更新依赖于current的容器
            for container, deps in dependency_graph.items():
                if current in deps:
                    in_degree[container] -= 1
                    if in_degree[container] == 0:
                        queue.append(container)

        # 检查是否有循环依赖
        if len(result) != len(all_containers):
            logger.warning("依赖图中可能存在循环依赖")
            # 添加剩余的容器
            remaining = all_containers - set(result)
            result.extend(remaining)

        return result

    def _prepare_container_params(
        self,
        container_config: Dict[str, Any],
        strategy: DeploymentStrategy,
        deployment_name: str,
        env_vars: Dict[str, str],
        network_name: str = None,
    ) -> Dict[str, Any]:
        """
        准备容器创建参数

        Args:
            container_config: 容器配置
            strategy: 策略对象
            deployment_name: 部署名称
            env_vars: 环境变量
            network_name: 网络名称

        Returns:
            容器创建参数
        """
        # 基本参数
        name = f"{deployment_name}-{container_config['name']}"
        image = container_config["image"]

        # 构建容器参数字典
        params = {
            "name": name,
            "image": image,
            "detach": True,
            "restart_policy": {"Name": strategy.restart_policy},
        }

        # 命令
        if "command" in container_config:
            params["command"] = container_config["command"]

        # 端口映射
        if "ports" in container_config:
            ports = {}
            for port_mapping in container_config["ports"]:
                if isinstance(port_mapping, dict):
                    container_port = port_mapping["container_port"]
                    host_port = port_mapping.get("host_port")
                    if host_port:
                        ports[f"{container_port}/tcp"] = host_port
                    else:
                        ports[f"{container_port}/tcp"] = None
                elif isinstance(port_mapping, str):
                    parts = port_mapping.split(":")
                    if len(parts) == 2:
                        host_port, container_port = parts
                        ports[f"{container_port}/tcp"] = int(host_port)
                    else:
                        ports[f"{parts[0]}/tcp"] = None
            params["ports"] = ports

        # 环境变量
        environment = container_config.get("environment", {}).copy()
        environment.update(env_vars)
        if environment:
            params["environment"] = environment

        # 卷挂载
        if "volumes" in container_config:
            volumes = {}
            for volume_mapping in container_config["volumes"]:
                if isinstance(volume_mapping, dict):
                    source = volume_mapping["source"]
                    target = volume_mapping["target"]
                    mode = volume_mapping.get("mode", "rw")
                    volumes[source] = {"bind": target, "mode": mode}
                elif isinstance(volume_mapping, str):
                    parts = volume_mapping.split(":")
                    if len(parts) >= 2:
                        source = parts[0]
                        target = parts[1]
                        mode = parts[2] if len(parts) > 2 else "rw"
                        volumes[source] = {"bind": target, "mode": mode}
            params["volumes"] = volumes

        # 资源限制
        resource_limits = strategy.resource_policy.get_container_resources(
            container_config["name"]
        )
        if resource_limits:
            for key, value in resource_limits.items():
                if key == "memory":
                    if "mem_limit" not in params:
                        params["mem_limit"] = value
                elif key == "cpu":
                    if "cpu_quota" not in params:
                        # 转换CPU核心份额为微秒配额
                        # 100000 微秒是Docker默认的CPU周期
                        cpu_value = float(value)
                        params["cpu_quota"] = int(cpu_value * 100000)
                        params["cpu_period"] = 100000

        # 网络设置
        if network_name:
            params["network"] = network_name

        # 标签
        labels = {f"smoothstack.strategy": strategy.name}
        labels.update(strategy.labels)
        labels.update(container_config.get("labels", {}))
        params["labels"] = labels

        return params

    def _cleanup_deployment(self, containers: Dict[str, Dict[str, Any]]) -> None:
        """
        清理部署的容器

        Args:
            containers: 已创建的容器信息
        """
        logger.info("开始清理部署的容器")
        for container_name, info in containers.items():
            try:
                container = self.client.containers.get(info["id"])
                if container.status == "running":
                    logger.info(f"停止容器 {container.name}")
                    container.stop(timeout=10)
                logger.info(f"移除容器 {container.name}")
                container.remove()
            except Exception as e:
                logger.error(f"清理容器 {container_name} 失败: {e}")

    def stop_strategy(self, deployment_name: str) -> Dict[str, Any]:
        """
        停止策略部署

        Args:
            deployment_name: 部署名称

        Returns:
            停止结果
        """
        result = {
            "deployment_name": deployment_name,
            "stopped_containers": [],
            "errors": {},
        }

        # 查找与此部署相关的容器
        try:
            containers = self.client.containers.list(
                all=True, filters={"name": deployment_name}
            )

            for container in containers:
                try:
                    if container.status == "running":
                        logger.info(f"停止容器 {container.name}")
                        container.stop(timeout=10)
                    result["stopped_containers"].append(container.name)
                except Exception as e:
                    logger.error(f"停止容器 {container.name} 失败: {e}")
                    result["errors"][container.name] = str(e)

            if not result["errors"]:
                result["status"] = "success"
                result["message"] = f"成功停止部署 '{deployment_name}' 的所有容器"
            else:
                result["status"] = "partial"
                result["message"] = f"部分容器停止失败"

        except Exception as e:
            logger.error(f"停止部署 {deployment_name} 失败: {e}")
            result["status"] = "failed"
            result["message"] = str(e)

        return result

    def remove_strategy_deployment(
        self, deployment_name: str, force: bool = False
    ) -> Dict[str, Any]:
        """
        移除策略部署

        Args:
            deployment_name: 部署名称
            force: 是否强制移除

        Returns:
            移除结果
        """
        result = {
            "deployment_name": deployment_name,
            "removed_containers": [],
            "errors": {},
        }

        # 查找与此部署相关的容器
        try:
            containers = self.client.containers.list(
                all=True, filters={"name": deployment_name}
            )

            for container in containers:
                try:
                    if container.status == "running" and not force:
                        logger.info(f"停止容器 {container.name}")
                        container.stop(timeout=10)

                    logger.info(f"移除容器 {container.name}")
                    container.remove(force=force)
                    result["removed_containers"].append(container.name)
                except Exception as e:
                    logger.error(f"移除容器 {container.name} 失败: {e}")
                    result["errors"][container.name] = str(e)

            if not result["errors"]:
                result["status"] = "success"
                result["message"] = f"成功移除部署 '{deployment_name}' 的所有容器"
            else:
                result["status"] = "partial"
                result["message"] = f"部分容器移除失败"

        except Exception as e:
            logger.error(f"移除部署 {deployment_name} 失败: {e}")
            result["status"] = "failed"
            result["message"] = str(e)

        return result

    def list_strategy_deployments(self) -> List[Dict[str, Any]]:
        """
        列出当前的策略部署

        Returns:
            部署信息列表
        """
        try:
            # 查找所有带有策略标签的容器
            containers = self.client.containers.list(
                all=True, filters={"label": "smoothstack.strategy"}
            )

            # 按部署名称分组
            deployments = {}

            for container in containers:
                strategy_name = container.labels.get("smoothstack.strategy")
                if not strategy_name:
                    continue

                # 从容器名称中提取部署名称
                container_name = container.name
                parts = container_name.split("-")
                if len(parts) < 2:
                    continue

                # 假设部署名称是容器名称减去最后一部分
                deployment_name = "-".join(parts[:-1])

                if deployment_name not in deployments:
                    deployments[deployment_name] = {
                        "deployment_name": deployment_name,
                        "strategy_name": strategy_name,
                        "containers": [],
                        "status": "unknown",
                        "created_at": None,
                    }

                # 记录容器信息
                container_info = {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": (
                        container.image.tags[0]
                        if container.image.tags
                        else container.image.id
                    ),
                }

                deployments[deployment_name]["containers"].append(container_info)

                # 更新部署创建时间
                if (
                    not deployments[deployment_name]["created_at"]
                    or container.attrs["Created"]
                    < deployments[deployment_name]["created_at"]
                ):
                    deployments[deployment_name]["created_at"] = container.attrs[
                        "Created"
                    ]

            # 确定每个部署的整体状态
            for deployment in deployments.values():
                statuses = [c["status"] for c in deployment["containers"]]
                if all(s == "running" for s in statuses):
                    deployment["status"] = "running"
                elif all(s == "exited" for s in statuses):
                    deployment["status"] = "stopped"
                elif any(s == "running" for s in statuses):
                    deployment["status"] = "partial"
                else:
                    deployment["status"] = "stopped"

                # 计算容器数量
                deployment["container_count"] = len(deployment["containers"])

            return list(deployments.values())

        except Exception as e:
            logger.error(f"列出策略部署失败: {e}")
            return []

    def inspect_deployment(self, deployment_name: str) -> Dict[str, Any]:
        """
        查看部署详情

        Args:
            deployment_name: 部署名称

        Returns:
            部署详情
        """
        try:
            # 查找与此部署相关的容器
            containers = self.client.containers.list(
                all=True, filters={"name": deployment_name}
            )

            if not containers:
                return {"error": f"找不到部署 '{deployment_name}'"}

            # 提取策略名称
            strategy_name = None
            for container in containers:
                if "smoothstack.strategy" in container.labels:
                    strategy_name = container.labels["smoothstack.strategy"]
                    break

            # 获取策略对象
            strategy = self.get_strategy(strategy_name) if strategy_name else None

            # 收集容器信息
            container_info = []
            for container in containers:
                ports = []
                for port, bindings in (
                    container.attrs.get("NetworkSettings", {}).get("Ports", {}).items()
                ):
                    if bindings:
                        for binding in bindings:
                            ports.append(
                                f"{binding['HostIp']}:{binding['HostPort']}->{port}"
                            )
                    else:
                        ports.append(f"{port}")

                networks = list(
                    container.attrs.get("NetworkSettings", {})
                    .get("Networks", {})
                    .keys()
                )

                container_info.append(
                    {
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": (
                            container.image.tags[0]
                            if container.image.tags
                            else container.image.id
                        ),
                        "created": container.attrs["Created"],
                        "ports": ports,
                        "networks": networks,
                        "labels": container.labels,
                        "environment": container.attrs.get("Config", {}).get("Env", []),
                    }
                )

            # 整理部署信息
            result = {
                "deployment_name": deployment_name,
                "strategy_name": strategy_name,
                "strategy": strategy.to_dict() if strategy else None,
                "containers": container_info,
                "container_count": len(container_info),
            }

            # 计算状态
            statuses = [c["status"] for c in container_info]
            if all(s == "running" for s in statuses):
                result["status"] = "running"
            elif all(s == "exited" for s in statuses):
                result["status"] = "stopped"
            elif any(s == "running" for s in statuses):
                result["status"] = "partial"
            else:
                result["status"] = "stopped"

            return result

        except Exception as e:
            logger.error(f"获取部署 {deployment_name} 详情失败: {e}")
            return {"error": str(e)}


# 单例模式获取策略管理器实例
_strategy_manager_instance = None


def get_strategy_manager() -> StrategyManager:
    """
    获取策略管理器单例实例

    Returns:
        策略管理器实例
    """
    global _strategy_manager_instance
    if _strategy_manager_instance is None:
        _strategy_manager_instance = StrategyManager()
    return _strategy_manager_instance
