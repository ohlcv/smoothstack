#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker Compose管理模块

提供Docker Compose服务的管理功能，包括：
- 服务的启动、停止和重启
- 配置文件的验证和解析
- 服务状态监控
"""

import os
import yaml
from typing import List, Dict, Optional, Any, Union
from .manager import DockerManager, RunMode, OutputFormat


class ComposeManager:
    """Docker Compose管理类"""

    def __init__(self, docker_manager: DockerManager):
        self.docker = docker_manager

    def up(
        self,
        services: Optional[List[str]] = None,
        detach: bool = True,
        build: bool = False,
        remove_orphans: bool = False,
        file: Optional[str] = None,
    ) -> bool:
        """启动服务"""
        cmd = ["compose"]
        if file:
            cmd.extend(["-f", file])

        cmd.append("up")

        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        if remove_orphans:
            cmd.append("--remove-orphans")

        if services:
            cmd.extend(services)

        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]启动服务失败: {result.stderr}[/]")
            return False

        self.docker.print_message("[bold green]服务启动成功[/]")
        return True

    def down(
        self,
        volumes: bool = False,
        remove_orphans: bool = False,
        file: Optional[str] = None,
    ) -> bool:
        """停止服务"""
        cmd = ["compose"]
        if file:
            cmd.extend(["-f", file])

        cmd.append("down")

        if volumes:
            cmd.append("-v")
        if remove_orphans:
            cmd.append("--remove-orphans")

        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]停止服务失败: {result.stderr}[/]")
            return False

        self.docker.print_message("[bold green]服务停止成功[/]")
        return True

    def ps(
        self,
        services: Optional[List[str]] = None,
        all: bool = False,
        file: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """查看服务状态"""
        cmd = ["compose"]
        if file:
            cmd.extend(["-f", file])

        cmd.append("ps")

        if all:
            cmd.append("--all")
        if services:
            cmd.extend(services)

        cmd.append("--format")
        cmd.append(
            '{"Name":"{{.Name}}", "Service":"{{.Service}}", "Status":"{{.Status}}", "Ports":"{{.Ports}}"}'
        )

        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]查看服务状态失败: {result.stderr}[/]")
            return []

        import json

        services = []
        for line in result.stdout.splitlines():
            try:
                service = json.loads(line)
                services.append(service)
            except json.JSONDecodeError:
                continue

        return services

    def logs(
        self,
        services: Optional[List[str]] = None,
        follow: bool = False,
        tail: Optional[int] = None,
        file: Optional[str] = None,
    ) -> bool:
        """查看服务日志"""
        cmd = ["compose"]
        if file:
            cmd.extend(["-f", file])

        cmd.append("logs")

        if follow:
            cmd.append("-f")
        if tail is not None:
            cmd.extend(["--tail", str(tail)])
        if services:
            cmd.extend(services)

        result = self.docker._run_docker_command(cmd, capture_output=not follow)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]查看服务日志失败: {result.stderr}[/]")
            return False

        if not follow:
            self.docker.print_message(result.stdout)
        return True

    def validate_config(self, file: str) -> bool:
        """验证配置文件"""
        try:
            with open(file, "r") as f:
                yaml.safe_load(f)

            cmd = ["compose", "-f", file, "config"]
            result = self.docker._run_docker_command(cmd)

            if result.returncode != 0:
                self.docker.print_message(
                    f"[bold red]配置文件验证失败: {result.stderr}[/]"
                )
                return False

            self.docker.print_message("[bold green]配置文件验证成功[/]")
            return True

        except Exception as e:
            self.docker.print_message(f"[bold red]配置文件验证失败: {e}[/]")
            return False
