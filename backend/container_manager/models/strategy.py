#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多容器策略模型

定义部署策略和资源分配策略的数据模型
"""

from typing import Dict, List, Any, Optional, Union, Set
import copy
import json


class ResourceAllocationPolicy:
    """资源分配策略类"""

    def __init__(
        self,
        global_limits: Dict[str, str] = None,
        container_specific_limits: Dict[str, Dict[str, str]] = None,
        scale_factors: Dict[str, float] = None,
    ):
        """
        初始化资源分配策略

        Args:
            global_limits: 全局资源限制，如 {"memory": "2g", "cpu": "1.5"}
            container_specific_limits: 特定容器的资源限制
            scale_factors: 容器资源扩展因子
        """
        self.global_limits = global_limits or {}
        self.container_specific_limits = container_specific_limits or {}
        self.scale_factors = scale_factors or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            策略字典表示
        """
        return {
            "global_limits": self.global_limits,
            "container_specific_limits": self.container_specific_limits,
            "scale_factors": self.scale_factors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceAllocationPolicy":
        """
        从字典创建对象

        Args:
            data: 策略字典数据

        Returns:
            资源分配策略对象
        """
        return cls(
            global_limits=data.get("global_limits", {}),
            container_specific_limits=data.get("container_specific_limits", {}),
            scale_factors=data.get("scale_factors", {}),
        )

    def get_container_resources(self, container_name: str) -> Dict[str, str]:
        """
        获取容器的资源限制

        Args:
            container_name: 容器名称

        Returns:
            资源限制字典
        """
        # 先使用全局限制
        resources = copy.deepcopy(self.global_limits)

        # 应用容器特定限制
        if container_name in self.container_specific_limits:
            for key, value in self.container_specific_limits[container_name].items():
                resources[key] = value

        # 应用扩展因子
        if container_name in self.scale_factors:
            scale = self.scale_factors[container_name]
            for key, value in resources.items():
                if key == "memory" and isinstance(value, str):
                    # 处理内存限制，如 "2g", "512m"
                    unit = value[-1].lower()
                    if unit in "kmgt":
                        try:
                            amount = float(value[:-1])
                            scaled_amount = amount * scale
                            resources[key] = f"{scaled_amount}{unit}"
                        except ValueError:
                            pass
                elif key == "cpu" and (
                    isinstance(value, str) or isinstance(value, (int, float))
                ):
                    # 处理CPU限制，如 "1.5", "2"
                    try:
                        amount = float(value)
                        scaled_amount = amount * scale
                        resources[key] = str(scaled_amount)
                    except ValueError:
                        pass

        return resources


class DeploymentStrategy:
    """部署策略类"""

    def __init__(
        self,
        name: str,
        description: str = "",
        container_configs: List[Dict[str, Any]] = None,
        resource_policy: ResourceAllocationPolicy = None,
        dependency_graph: Dict[str, List[str]] = None,
        labels: Dict[str, str] = None,
        restart_policy: str = "unless-stopped",
    ):
        """
        初始化部署策略

        Args:
            name: 策略名称
            description: 策略描述
            container_configs: 容器配置列表
            resource_policy: 资源分配策略
            dependency_graph: 容器依赖关系图，如 {"web": ["db", "redis"]}表示web依赖db和redis
            labels: 标签
            restart_policy: 重启策略
        """
        self.name = name
        self.description = description
        self.container_configs = container_configs or []
        self.resource_policy = resource_policy or ResourceAllocationPolicy()
        self.dependency_graph = dependency_graph or {}
        self.labels = labels or {}
        self.restart_policy = restart_policy

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            策略字典表示
        """
        return {
            "name": self.name,
            "description": self.description,
            "container_configs": self.container_configs,
            "resource_policy": self.resource_policy.to_dict(),
            "dependency_graph": self.dependency_graph,
            "labels": self.labels,
            "restart_policy": self.restart_policy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeploymentStrategy":
        """
        从字典创建对象

        Args:
            data: 策略字典数据

        Returns:
            部署策略对象
        """
        resource_policy_data = data.get("resource_policy", {})
        resource_policy = ResourceAllocationPolicy.from_dict(resource_policy_data)

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            container_configs=data.get("container_configs", []),
            resource_policy=resource_policy,
            dependency_graph=data.get("dependency_graph", {}),
            labels=data.get("labels", {}),
            restart_policy=data.get("restart_policy", "unless-stopped"),
        )

    def add_container_config(self, config: Dict[str, Any]) -> None:
        """
        添加容器配置

        Args:
            config: 容器配置字典
        """
        container_name = config.get("name")
        if not container_name:
            raise ValueError("容器配置必须包含名称")

        # 检查是否已存在同名容器
        for i, existing_config in enumerate(self.container_configs):
            if existing_config.get("name") == container_name:
                # 更新现有配置
                self.container_configs[i] = config
                return

        # 添加新配置
        self.container_configs.append(config)

    def remove_container_config(self, container_name: str) -> bool:
        """
        移除容器配置

        Args:
            container_name: 容器名称

        Returns:
            是否成功移除
        """
        for i, config in enumerate(self.container_configs):
            if config.get("name") == container_name:
                del self.container_configs[i]

                # 同时移除依赖关系
                if container_name in self.dependency_graph:
                    del self.dependency_graph[container_name]

                # 移除其他容器对此容器的依赖
                for dependencies in self.dependency_graph.values():
                    if container_name in dependencies:
                        dependencies.remove(container_name)

                return True

        return False

    def add_dependency(
        self, container_name: str, depends_on: Union[str, List[str]]
    ) -> None:
        """
        添加容器依赖关系

        Args:
            container_name: 容器名称
            depends_on: 依赖的容器名称或列表
        """
        # 确保容器存在
        container_exists = False
        for config in self.container_configs:
            if config.get("name") == container_name:
                container_exists = True
                break

        if not container_exists:
            raise ValueError(f"容器 '{container_name}' 不存在")

        # 初始化依赖列表
        if container_name not in self.dependency_graph:
            self.dependency_graph[container_name] = []

        # 添加依赖
        if isinstance(depends_on, str):
            depends_on = [depends_on]

        for dep in depends_on:
            # 检查依赖的容器是否存在
            dep_exists = False
            for config in self.container_configs:
                if config.get("name") == dep:
                    dep_exists = True
                    break

            if not dep_exists:
                raise ValueError(f"依赖的容器 '{dep}' 不存在")

            # 检查是否会导致循环依赖
            if self._would_create_cycle(container_name, dep):
                raise ValueError(
                    f"添加依赖 '{container_name}' -> '{dep}' 会导致循环依赖"
                )

            # 添加依赖
            if dep not in self.dependency_graph[container_name]:
                self.dependency_graph[container_name].append(dep)

    def remove_dependency(self, container_name: str, dependency: str) -> bool:
        """
        移除容器依赖关系

        Args:
            container_name: 容器名称
            dependency: 要移除的依赖

        Returns:
            是否成功移除
        """
        if (
            container_name in self.dependency_graph
            and dependency in self.dependency_graph[container_name]
        ):
            self.dependency_graph[container_name].remove(dependency)
            return True
        return False

    def _would_create_cycle(self, container: str, new_dependency: str) -> bool:
        """
        检查添加新依赖是否会导致循环依赖

        Args:
            container: 容器名称
            new_dependency: 新依赖

        Returns:
            是否会导致循环
        """
        # 检查反向依赖路径
        visited = set()
        stack = [new_dependency]

        while stack:
            current = stack.pop()
            if current == container:
                return True

            if current in visited:
                continue

            visited.add(current)

            # 添加当前节点的所有依赖项
            for dep_container, dependencies in self.dependency_graph.items():
                if current in dependencies and dep_container not in visited:
                    stack.append(dep_container)

        return False
