#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境模型

定义开发环境的数据模型和配置
"""

import os
import json
import enum
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field, asdict

import yaml

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.models.dev_environment")


class EnvironmentType(enum.Enum):
    """
    开发环境类型
    """

    PYTHON = "python"  # Python开发环境
    NODEJS = "nodejs"  # Node.js开发环境
    FULLSTACK = "fullstack"  # 全栈开发环境
    DATABASE = "database"  # 数据库环境
    CUSTOM = "custom"  # 自定义环境


@dataclass
class PortMapping:
    """
    端口映射配置
    """

    host_port: int  # 主机端口
    container_port: int  # 容器端口
    protocol: str = "tcp"  # 协议，默认为tcp
    description: Optional[str] = None  # 描述

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        返回:
            Dict[str, Any]: 字典格式的端口映射
        """
        result = asdict(self)
        # 移除None值
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortMapping":
        """
        从字典创建端口映射

        参数:
            data (Dict[str, Any]): 端口映射字典

        返回:
            PortMapping: 端口映射对象
        """
        return cls(
            host_port=data.get("host_port"),
            container_port=data.get("container_port"),
            protocol=data.get("protocol", "tcp"),
            description=data.get("description"),
        )

    def __str__(self) -> str:
        """端口映射的字符串表示"""
        return f"{self.host_port}:{self.container_port}/{self.protocol}"


@dataclass
class VolumeMount:
    """
    卷挂载配置
    """

    host_path: str  # 主机路径
    container_path: str  # 容器路径
    read_only: bool = False  # 是否只读
    description: Optional[str] = None  # 描述

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        返回:
            Dict[str, Any]: 字典格式的卷挂载
        """
        result = asdict(self)
        # 移除None值
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VolumeMount":
        """
        从字典创建卷挂载

        参数:
            data (Dict[str, Any]): 卷挂载字典

        返回:
            VolumeMount: 卷挂载对象
        """
        return cls(
            host_path=data.get("host_path"),
            container_path=data.get("container_path"),
            read_only=data.get("read_only", False),
            description=data.get("description"),
        )

    def __str__(self) -> str:
        """卷挂载的字符串表示"""
        ro_str = ":ro" if self.read_only else ""
        return f"{self.host_path}:{self.container_path}{ro_str}"


@dataclass
class DevEnvironment:
    """
    开发环境配置
    """

    name: str  # 环境名称
    env_type: EnvironmentType  # 环境类型
    image: str  # 容器镜像
    description: Optional[str] = None  # 环境描述
    command: Optional[str] = None  # 容器启动命令
    entrypoint: Optional[List[str]] = None  # 容器入口点
    working_dir: str = "/app"  # 工作目录
    ports: List[PortMapping] = field(default_factory=list)  # 端口映射列表
    volumes: List[VolumeMount] = field(default_factory=list)  # 卷挂载列表
    environment: Dict[str, str] = field(default_factory=dict)  # 环境变量
    cpu_limit: Optional[float] = None  # CPU限制
    memory_limit: Optional[str] = None  # 内存限制，如"512m"
    network_mode: str = "bridge"  # 网络模式
    restart_policy: str = "no"  # 重启策略
    vscode_extensions: List[str] = field(default_factory=list)  # VSCode扩展列表
    devcontainer_features: Dict[str, Any] = field(
        default_factory=dict
    )  # DevContainer功能

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        返回:
            Dict[str, Any]: 字典格式的开发环境配置
        """
        # 使用asdict创建基本字典
        result = {}
        result["name"] = self.name
        result["env_type"] = self.env_type.value
        result["image"] = self.image

        # 添加非None的字段
        if self.description:
            result["description"] = self.description
        if self.command:
            result["command"] = self.command
        if self.entrypoint:
            result["entrypoint"] = self.entrypoint

        result["working_dir"] = self.working_dir

        # 处理列表和字典字段
        if self.ports:
            result["ports"] = [port.to_dict() for port in self.ports]
        if self.volumes:
            result["volumes"] = [volume.to_dict() for volume in self.volumes]
        if self.environment:
            result["environment"] = self.environment

        # 处理资源限制
        if self.cpu_limit is not None:
            result["cpu_limit"] = self.cpu_limit
        if self.memory_limit:
            result["memory_limit"] = self.memory_limit

        # 网络和重启策略
        result["network_mode"] = self.network_mode
        result["restart_policy"] = self.restart_policy

        # VSCode相关配置
        if self.vscode_extensions:
            result["vscode_extensions"] = self.vscode_extensions
        if self.devcontainer_features:
            result["devcontainer_features"] = self.devcontainer_features

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DevEnvironment":
        """
        从字典创建开发环境配置

        参数:
            data (Dict[str, Any]): 开发环境配置字典

        返回:
            DevEnvironment: 开发环境配置对象
        """
        # 处理环境类型
        try:
            env_type = EnvironmentType(data.get("env_type", "custom"))
        except (ValueError, KeyError):
            env_type = EnvironmentType.CUSTOM

        # 处理端口映射
        ports = []
        for port_data in data.get("ports", []):
            if isinstance(port_data, dict):
                ports.append(PortMapping.from_dict(port_data))

        # 处理卷挂载
        volumes = []
        for volume_data in data.get("volumes", []):
            if isinstance(volume_data, dict):
                volumes.append(VolumeMount.from_dict(volume_data))

        # 创建开发环境对象
        return cls(
            name=data.get("name", ""),
            env_type=env_type,
            image=data.get("image", ""),
            description=data.get("description"),
            command=data.get("command"),
            entrypoint=data.get("entrypoint"),
            working_dir=data.get("working_dir", "/app"),
            ports=ports,
            volumes=volumes,
            environment=data.get("environment", {}),
            cpu_limit=data.get("cpu_limit"),
            memory_limit=data.get("memory_limit"),
            network_mode=data.get("network_mode", "bridge"),
            restart_policy=data.get("restart_policy", "no"),
            vscode_extensions=data.get("vscode_extensions", []),
            devcontainer_features=data.get("devcontainer_features", {}),
        )

    def save_to_file(self, file_path: str) -> bool:
        """
        保存到YAML文件

        参数:
            file_path (str): 文件路径

        返回:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            # 转换为字典并保存
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.to_dict(), f, default_flow_style=False, allow_unicode=True
                )

            logger.info(f"保存开发环境配置到文件：{file_path}")
            return True
        except Exception as e:
            logger.error(f"保存开发环境配置失败：{e}")
            return False

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["DevEnvironment"]:
        """
        从YAML文件加载

        参数:
            file_path (str): 文件路径

        返回:
            Optional[DevEnvironment]: 开发环境配置对象，如果加载失败则返回None
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 创建对象
            if isinstance(data, dict):
                logger.info(f"从文件加载开发环境配置：{file_path}")
                return cls.from_dict(data)
            else:
                logger.error(f"文件格式错误：{file_path}")
                return None
        except Exception as e:
            logger.error(f"加载开发环境配置失败：{e}")
            return None

    def create_devcontainer_config(self, project_dir: str) -> bool:
        """
        创建VSCode DevContainer配置

        参数:
            project_dir (str): 项目目录

        返回:
            bool: 是否创建成功
        """
        try:
            # 创建.devcontainer目录
            devcontainer_dir = os.path.join(project_dir, ".devcontainer")
            os.makedirs(devcontainer_dir, exist_ok=True)

            # 创建devcontainer.json配置
            config = {
                "name": f"{self.name} Development Environment",
                "image": self.image,
                "workspaceFolder": self.working_dir,
                "workspaceMount": f"source=${{localWorkspaceFolder}},target={self.working_dir},type=bind",
                "remoteUser": "root",  # 默认使用root用户，可根据需要修改
            }

            # 添加命令和入口点
            if self.command:
                config["overrideCommand"] = True
                config["command"] = self.command

            # 添加环境变量
            if self.environment:
                config["remoteEnv"] = self.environment

            # 添加端口映射
            if self.ports:
                config["forwardPorts"] = [p.container_port for p in self.ports]

                # 添加端口属性
                port_attributes = {}
                for port in self.ports:
                    port_attributes[str(port.container_port)] = {
                        "protocol": port.protocol,
                        "label": (
                            port.description
                            if port.description
                            else f"Port {port.container_port}"
                        ),
                    }

                if port_attributes:
                    config["portsAttributes"] = port_attributes

            # 添加卷挂载
            if self.volumes:
                mounts = []
                for volume in self.volumes:
                    # 跳过工作目录的挂载，因为已经在workspaceMount中指定
                    if volume.container_path == self.working_dir:
                        continue

                    # 转换路径格式
                    host_path = volume.host_path.replace(
                        "${workspaceFolder}", "${localWorkspaceFolder}"
                    )

                    mounts.append(
                        {
                            "source": host_path,
                            "target": volume.container_path,
                            "type": "bind",
                            "readonly": volume.read_only,
                        }
                    )

                if mounts:
                    config["mounts"] = mounts

            # 添加VSCode扩展
            if self.vscode_extensions:
                config["extensions"] = self.vscode_extensions

            # 添加自定义特性
            if self.devcontainer_features:
                config["features"] = self.devcontainer_features

            # 添加资源限制
            if self.cpu_limit is not None or self.memory_limit:
                config["runArgs"] = []

                if self.cpu_limit is not None:
                    config["runArgs"].extend(["--cpus", str(self.cpu_limit)])

                if self.memory_limit:
                    config["runArgs"].extend(["--memory", self.memory_limit])

            # 写入配置文件
            config_path = os.path.join(devcontainer_dir, "devcontainer.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            logger.info(f"创建DevContainer配置：{config_path}")
            return True
        except Exception as e:
            logger.error(f"创建DevContainer配置失败：{e}")
            return False
