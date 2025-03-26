#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
构建命令模块

提供构建和部署相关的命令,包括:
- 项目构建
- 容器镜像管理
- 部署配置管理
- 部署状态监控
"""

import os
import sys
import yaml
import click
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BuildCommand(BaseCommand):
    """构建命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.deploy_dir = self.project_root / "deploy"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.deploy_dir.mkdir(parents=True, exist_ok=True)

    def build(self, project_name: str, tag: Optional[str] = None):
        """构建项目"""
        try:
            self.info(f"构建项目: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查Dockerfile
            dockerfile = project_dir / "Dockerfile"
            if not dockerfile.exists():
                raise RuntimeError(f"Dockerfile不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 构建镜像
            image_name = f"{project_name}:{tag if tag else 'latest'}"
            if os.system(f"docker build -t {image_name} .") != 0:
                raise RuntimeError("构建镜像失败")

            self.success(f"项目构建成功: {image_name}")

        except Exception as e:
            self.error(f"构建项目失败: {e}")
            raise

    def push(self, project_name: str, registry: str, tag: Optional[str] = None):
        """推送镜像"""
        try:
            self.info(f"推送镜像: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 标记镜像
            image_name = f"{project_name}:{tag if tag else 'latest'}"
            remote_name = f"{registry}/{image_name}"
            if os.system(f"docker tag {image_name} {remote_name}") != 0:
                raise RuntimeError("标记镜像失败")

            # 推送镜像
            if os.system(f"docker push {remote_name}") != 0:
                raise RuntimeError("推送镜像失败")

            self.success(f"镜像推送成功: {remote_name}")

        except Exception as e:
            self.error(f"推送镜像失败: {e}")
            raise

    def deploy(self, project_name: str, env: str):
        """部署项目"""
        try:
            self.info(f"部署项目: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查部署配置
            deploy_dir = self.deploy_dir / project_name / env
            if not deploy_dir.exists():
                raise RuntimeError(f"部署配置不存在: {project_name}/{env}")

            # 检查docker-compose.yml
            compose_file = deploy_dir / "docker-compose.yml"
            if not compose_file.exists():
                raise RuntimeError(f"docker-compose.yml不存在: {project_name}/{env}")

            # 切换到部署目录
            os.chdir(str(deploy_dir))

            # 部署服务
            if os.system("docker-compose up -d") != 0:
                raise RuntimeError("部署服务失败")

            self.success(f"项目部署成功: {project_name}/{env}")

        except Exception as e:
            self.error(f"部署项目失败: {e}")
            raise

    def rollback(self, project_name: str, env: str):
        """回滚部署"""
        try:
            self.info(f"回滚部署: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查部署配置
            deploy_dir = self.deploy_dir / project_name / env
            if not deploy_dir.exists():
                raise RuntimeError(f"部署配置不存在: {project_name}/{env}")

            # 检查docker-compose.yml
            compose_file = deploy_dir / "docker-compose.yml"
            if not compose_file.exists():
                raise RuntimeError(f"docker-compose.yml不存在: {project_name}/{env}")

            # 切换到部署目录
            os.chdir(str(deploy_dir))

            # 回滚服务
            if os.system("docker-compose down") != 0:
                raise RuntimeError("停止服务失败")

            if os.system("docker-compose up -d") != 0:
                raise RuntimeError("启动服务失败")

            self.success(f"部署回滚成功: {project_name}/{env}")

        except Exception as e:
            self.error(f"回滚部署失败: {e}")
            raise

    def status(self, project_name: str, env: str):
        """查看部署状态"""
        try:
            self.info(f"查看部署状态: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查部署配置
            deploy_dir = self.deploy_dir / project_name / env
            if not deploy_dir.exists():
                raise RuntimeError(f"部署配置不存在: {project_name}/{env}")

            # 检查docker-compose.yml
            compose_file = deploy_dir / "docker-compose.yml"
            if not compose_file.exists():
                raise RuntimeError(f"docker-compose.yml不存在: {project_name}/{env}")

            # 切换到部署目录
            os.chdir(str(deploy_dir))

            # 查看服务状态
            if os.system("docker-compose ps") != 0:
                raise RuntimeError("查看服务状态失败")

        except Exception as e:
            self.error(f"查看部署状态失败: {e}")
            raise

    def logs(self, project_name: str, env: str, service: Optional[str] = None):
        """查看部署日志"""
        try:
            self.info(f"查看部署日志: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查部署配置
            deploy_dir = self.deploy_dir / project_name / env
            if not deploy_dir.exists():
                raise RuntimeError(f"部署配置不存在: {project_name}/{env}")

            # 检查docker-compose.yml
            compose_file = deploy_dir / "docker-compose.yml"
            if not compose_file.exists():
                raise RuntimeError(f"docker-compose.yml不存在: {project_name}/{env}")

            # 切换到部署目录
            os.chdir(str(deploy_dir))

            # 查看服务日志
            if service:
                if os.system(f"docker-compose logs {service}") != 0:
                    raise RuntimeError(f"查看服务日志失败: {service}")
            else:
                if os.system("docker-compose logs") != 0:
                    raise RuntimeError("查看服务日志失败")

        except Exception as e:
            self.error(f"查看部署日志失败: {e}")
            raise


# CLI命令
@click.group()
def build():
    """构建和部署命令"""
    pass


@build.command()
@click.argument("project_name")
@click.option("--tag", "-t", help="镜像标签")
def build_image(project_name: str, tag: Optional[str]):
    """构建项目"""
    cmd = BuildCommand()
    cmd.build(project_name, tag)


@build.command()
@click.argument("project_name")
@click.argument("registry")
@click.option("--tag", "-t", help="镜像标签")
def push_image(project_name: str, registry: str, tag: Optional[str]):
    """推送镜像"""
    cmd = BuildCommand()
    cmd.push(project_name, registry, tag)


@build.command()
@click.argument("project_name")
@click.argument("env")
def deploy(project_name: str, env: str):
    """部署项目"""
    cmd = BuildCommand()
    cmd.deploy(project_name, env)


@build.command()
@click.argument("project_name")
@click.argument("env")
def rollback(project_name: str, env: str):
    """回滚部署"""
    cmd = BuildCommand()
    cmd.rollback(project_name, env)


@build.command()
@click.argument("project_name")
@click.argument("env")
def status(project_name: str, env: str):
    """查看部署状态"""
    cmd = BuildCommand()
    cmd.status(project_name, env)


@build.command()
@click.argument("project_name")
@click.argument("env")
@click.option("--service", "-s", help="服务名称")
def logs(project_name: str, env: str, service: Optional[str]):
    """查看部署日志"""
    cmd = BuildCommand()
    cmd.logs(project_name, env, service)
