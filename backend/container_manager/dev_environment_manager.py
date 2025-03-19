#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境管理器

管理开发环境模板和创建开发容器
"""

import os
import sys
import glob
import time
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union

import yaml
import docker
from docker.errors import DockerException, ImageNotFound, APIError

from .models.dev_environment import (
    DevEnvironment,
    EnvironmentType,
    PortMapping,
    VolumeMount,
)

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.dev_environment_manager")


class DevEnvironmentManager:
    """
    开发环境管理器

    管理开发环境模板和创建开发容器
    支持集成VSCode DevContainer
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化开发环境管理器

        参数:
            templates_dir: 模板目录路径，默认为用户目录下的.smoothstack/templates
        """
        # 设置模板目录
        if templates_dir:
            self.templates_dir = os.path.abspath(templates_dir)
        else:
            self.templates_dir = os.path.expanduser("~/.smoothstack/templates")

        # 确保模板目录存在
        os.makedirs(self.templates_dir, exist_ok=True)

        # 初始化Docker客户端
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except DockerException as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            self.docker_client = None

        # 加载模板
        self.templates: Dict[str, DevEnvironment] = {}
        self.load_templates()

        # 如果没有模板，创建默认模板
        if not self.templates:
            logger.info("未找到模板，创建默认模板")
            self.create_default_templates()

    def load_templates(self) -> None:
        """加载所有模板"""
        logger.info(f"从{self.templates_dir}加载模板")
        self.templates = {}

        # 查找所有YAML文件
        yaml_files = glob.glob(os.path.join(self.templates_dir, "*.yaml")) + glob.glob(
            os.path.join(self.templates_dir, "*.yml")
        )

        # 加载模板
        for yaml_file in yaml_files:
            try:
                template = DevEnvironment.load_from_file(yaml_file)
                if template:
                    logger.debug(f"加载模板: {template.name}")
                    self.templates[template.name] = template
            except Exception as e:
                logger.error(f"加载模板{yaml_file}失败: {e}")

    def create_default_templates(self) -> None:
        """创建默认模板"""
        # Python开发环境
        python_env = DevEnvironment(
            name="python",
            env_type=EnvironmentType.PYTHON,
            image="python:3.9-slim",
            description="Python开发环境",
            working_dir="/app",
            ports=[
                PortMapping(host_port=8000, container_port=8000, description="Web服务")
            ],
            volumes=[
                VolumeMount(host_path="${workspaceFolder}", container_path="/app")
            ],
            environment={"PYTHONPATH": "/app", "PYTHONUNBUFFERED": "1"},
            vscode_extensions=[
                "ms-python.python",
                "ms-python.vscode-pylance",
                "njpwerner.autodocstring",
            ],
        )

        # Node.js开发环境
        nodejs_env = DevEnvironment(
            name="nodejs",
            env_type=EnvironmentType.NODEJS,
            image="node:16",
            description="Node.js开发环境",
            working_dir="/app",
            ports=[
                PortMapping(host_port=3000, container_port=3000, description="Web服务"),
                PortMapping(host_port=9229, container_port=9229, description="调试"),
            ],
            volumes=[
                VolumeMount(host_path="${workspaceFolder}", container_path="/app")
            ],
            vscode_extensions=["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"],
        )

        # 全栈开发环境
        fullstack_env = DevEnvironment(
            name="fullstack",
            env_type=EnvironmentType.FULLSTACK,
            image="mcr.microsoft.com/vscode/devcontainers/universal:latest",
            description="全栈开发环境 (Python + Node.js)",
            working_dir="/workspace",
            ports=[
                PortMapping(host_port=3000, container_port=3000, description="前端"),
                PortMapping(host_port=8000, container_port=8000, description="后端"),
            ],
            volumes=[
                VolumeMount(host_path="${workspaceFolder}", container_path="/workspace")
            ],
            vscode_extensions=[
                "ms-python.python",
                "dbaeumer.vscode-eslint",
                "esbenp.prettier-vscode",
            ],
        )

        # PostgreSQL数据库环境
        postgres_env = DevEnvironment(
            name="postgres",
            env_type=EnvironmentType.DATABASE,
            image="postgres:13",
            description="PostgreSQL数据库环境",
            ports=[
                PortMapping(
                    host_port=5432, container_port=5432, description="PostgreSQL"
                )
            ],
            environment={
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "postgres",
                "POSTGRES_DB": "devdb",
            },
            volumes=[
                VolumeMount(
                    host_path="${workspaceFolder}/data",
                    container_path="/var/lib/postgresql/data",
                )
            ],
        )

        # 保存默认模板
        self.templates["python"] = python_env
        self.save_template(python_env)

        self.templates["nodejs"] = nodejs_env
        self.save_template(nodejs_env)

        self.templates["fullstack"] = fullstack_env
        self.save_template(fullstack_env)

        self.templates["postgres"] = postgres_env
        self.save_template(postgres_env)

        logger.info("创建了默认模板")

    def save_template(self, template: DevEnvironment) -> bool:
        """
        保存模板

        参数:
            template: 要保存的模板

        返回:
            是否保存成功
        """
        # 保存到模板目录
        file_path = os.path.join(self.templates_dir, f"{template.name}.yaml")
        result = template.save_to_file(file_path)

        if result:
            # 更新内部缓存
            self.templates[template.name] = template
            logger.info(f"模板 {template.name} 保存成功")
        else:
            logger.error(f"模板 {template.name} 保存失败")

        return result

    def get_template(self, name: str) -> Optional[DevEnvironment]:
        """
        获取模板

        参数:
            name: 模板名称

        返回:
            模板对象，如果不存在则返回None
        """
        return self.templates.get(name)

    def list_templates(self) -> List[DevEnvironment]:
        """
        获取所有模板

        返回:
            模板列表
        """
        return list(self.templates.values())

    def create_template(self, template: DevEnvironment) -> bool:
        """
        创建新模板

        参数:
            template: 模板对象

        返回:
            是否创建成功
        """
        # 检查名称冲突
        if template.name in self.templates:
            logger.warning(f"模板 {template.name} 已存在，将被覆盖")

        # 保存模板
        return self.save_template(template)

    def update_template(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        更新现有模板

        参数:
            name: 模板名称
            updates: 要更新的字段

        返回:
            是否更新成功
        """
        # 检查模板是否存在
        template = self.get_template(name)
        if not template:
            logger.error(f"模板 {name} 不存在")
            return False

        # 更新字段
        template_dict = template.to_dict()
        template_dict.update(updates)

        # 创建新模板
        updated_template = DevEnvironment.from_dict(template_dict)

        # 保存模板
        return self.save_template(updated_template)

    def delete_template(self, name: str) -> bool:
        """
        删除模板

        参数:
            name: 模板名称

        返回:
            是否删除成功
        """
        # 检查模板是否存在
        if name not in self.templates:
            logger.error(f"模板 {name} 不存在")
            return False

        # 删除模板文件
        file_path = os.path.join(self.templates_dir, f"{name}.yaml")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)

            # 从内部缓存中移除
            del self.templates[name]
            logger.info(f"模板 {name} 删除成功")
            return True
        except Exception as e:
            logger.error(f"删除模板 {name} 失败: {e}")
            return False

    def create_environment(
        self,
        template_name: str,
        container_name: str,
        project_dir: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        从模板创建开发环境

        参数:
            template_name: 模板名称
            container_name: 容器名称
            project_dir: 项目目录
            options: 创建选项
                - create_devcontainer: 是否创建DevContainer配置
                - start_container: 是否启动容器
                - pull_image: 是否拉取最新镜像
                - environment: 额外的环境变量

        返回:
            (是否成功, 消息)
        """
        if options is None:
            options = {}

        # 默认选项
        create_devcontainer = options.get("create_devcontainer", True)
        start_container = options.get("start_container", True)
        pull_image = options.get("pull_image", False)
        extra_env = options.get("environment", {})

        # 获取模板
        template = self.get_template(template_name)
        if not template:
            return False, f"模板 {template_name} 不存在"

        # 检查Docker客户端
        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 确保项目目录存在
            project_dir = os.path.abspath(project_dir)
            os.makedirs(project_dir, exist_ok=True)

            # 创建DevContainer配置
            if create_devcontainer:
                logger.info(f"为 {container_name} 创建DevContainer配置")
                template.create_devcontainer_config(project_dir)

            # 如果不需要启动容器，直接返回
            if not start_container:
                return True, f"DevContainer配置已创建于 {project_dir}/.devcontainer"

            # 拉取镜像
            if pull_image:
                logger.info(f"拉取镜像: {template.image}")
                self.docker_client.images.pull(template.image)

            # 准备环境变量
            environment = dict(template.environment)
            environment.update(extra_env)

            # 准备卷挂载
            volumes = {}
            for volume in template.volumes:
                # 处理${workspaceFolder}变量
                host_path = volume.host_path.replace("${workspaceFolder}", project_dir)
                # 确保主机路径存在
                if not os.path.exists(host_path):
                    os.makedirs(host_path, exist_ok=True)
                # 添加到卷映射
                volumes[host_path] = {
                    "bind": volume.container_path,
                    "mode": "ro" if volume.read_only else "rw",
                }

            # 准备端口映射
            ports = {}
            for port in template.ports:
                ports[f"{port.container_port}/{port.protocol}"] = port.host_port

            # 创建容器配置
            container_config = {
                "name": container_name,
                "image": template.image,
                "detach": True,
                "environment": environment,
                "volumes": volumes,
                "ports": ports,
                "network_mode": template.network_mode,
                "restart_policy": {"Name": template.restart_policy},
            }

            # 添加工作目录
            if template.working_dir:
                container_config["working_dir"] = template.working_dir

            # 添加启动命令
            if template.command:
                container_config["command"] = template.command

            # 添加入口点
            if template.entrypoint:
                container_config["entrypoint"] = template.entrypoint

            # 添加资源限制
            if template.cpu_limit is not None or template.memory_limit:
                container_config["nano_cpus"] = (
                    int(template.cpu_limit * 1e9)
                    if template.cpu_limit is not None
                    else None
                )
                container_config["mem_limit"] = template.memory_limit

            # 创建并启动容器
            logger.info(f"创建容器: {container_name}")
            container = self.docker_client.containers.run(**container_config)

            return True, f"容器 {container_name} 已创建并启动"
        except ImageNotFound:
            return False, f"镜像不存在: {template.image}"
        except APIError as e:
            return False, f"Docker API错误: {str(e)}"
        except Exception as e:
            logger.error(f"创建环境失败: {e}")
            return False, f"创建环境失败: {str(e)}"

    def build_custom_image(
        self,
        dockerfile_path: str,
        image_name: str,
        build_args: Optional[Dict[str, str]] = None,
        pull: bool = False,
    ) -> Tuple[bool, str]:
        """
        构建自定义Docker镜像

        参数:
            dockerfile_path: Dockerfile路径
            image_name: 镜像名称
            build_args: 构建参数
            pull: 是否拉取基础镜像

        返回:
            (是否成功, 消息)
        """
        if not os.path.exists(dockerfile_path):
            return False, f"Dockerfile不存在: {dockerfile_path}"

        if not self.docker_client:
            return False, "Docker客户端未初始化"

        try:
            # 构建上下文目录
            context_path = os.path.dirname(os.path.abspath(dockerfile_path))
            dockerfile_name = os.path.basename(dockerfile_path)

            logger.info(
                f"构建镜像: {image_name}, 上下文: {context_path}, Dockerfile: {dockerfile_name}"
            )

            # 构建镜像
            image, logs = self.docker_client.images.build(
                path=context_path,
                dockerfile=dockerfile_name,
                tag=image_name,
                buildargs=build_args,
                pull=pull,
            )

            # 记录构建日志
            for log in logs:
                if "stream" in log:
                    logger.debug(log["stream"].strip())

            return True, f"镜像 {image_name} 构建成功，ID: {image.id}"
        except Exception as e:
            logger.error(f"构建镜像失败: {e}")
            return False, f"构建镜像失败: {str(e)}"


# 创建全局单例实例
dev_environment_manager = DevEnvironmentManager()
