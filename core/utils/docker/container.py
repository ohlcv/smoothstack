#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker容器管理模块

提供容器的创建、启动、停止、删除等操作。
支持CLI命令和Python API两种实现方式。
"""

from typing import List, Dict, Optional, Any, Union
from .manager import DockerManager, RunMode, OutputFormat


class ContainerManager:
    """Docker容器管理类"""

    def __init__(self, docker_manager: DockerManager):
        self.docker = docker_manager

    def list_containers(
        self,
        all: bool = False,
        quiet: bool = False,
        size: bool = False,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """列出容器"""
        if self.docker.mode == RunMode.PYTHON_API:
            return self._list_containers_api(all, quiet, size, filters)
        return self._list_containers_cli(all, quiet, size, filters)

    def _list_containers_cli(
        self, all: bool, quiet: bool, size: bool, filters: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """使用CLI命令列出容器"""
        cmd = ["container", "ls"]
        if all:
            cmd.append("--all")
        if quiet:
            cmd.append("--quiet")
        if size:
            cmd.append("--size")
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])

        cmd.append("--format")
        cmd.append(
            '{"ID":"{{.ID}}", "Image":"{{.Image}}", "Command":"{{.Command}}", "CreatedAt":"{{.CreatedAt}}", "Status":"{{.Status}}", "Ports":"{{.Ports}}", "Names":"{{.Names}}"'
            + (',"Size":"{{.Size}}"' if size else "")
            + "}"
        )

        result = self.docker._run_docker_command(cmd)
        if result.returncode != 0:
            self.docker.print_message(f"[bold red]列出容器失败: {result.stderr}[/]")
            return []

        import json

        containers = []
        for line in result.stdout.splitlines():
            try:
                container = json.loads(line)
                containers.append(container)
            except json.JSONDecodeError:
                continue

        return containers

    def _list_containers_api(
        self, all: bool, quiet: bool, size: bool, filters: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """使用Python API列出容器"""
        try:
            containers = self.docker.docker_client.containers.list(
                all=all, filters=filters or {}
            )

            result = []
            for container in containers:
                if quiet:
                    result.append({"ID": container.short_id})
                    continue

                info = {
                    "ID": container.short_id,
                    "Image": (
                        container.image.tags[0]
                        if container.image.tags
                        else container.image.short_id
                    ),
                    "Command": (
                        container.attrs["Config"]["Cmd"][0]
                        if container.attrs["Config"]["Cmd"]
                        else ""
                    ),
                    "CreatedAt": container.attrs["Created"],
                    "Status": container.status,
                    "Names": container.name,
                }

                # 添加端口信息
                ports = []
                port_bindings = container.attrs["NetworkSettings"]["Ports"] or {}
                for container_port, host_bindings in port_bindings.items():
                    if host_bindings:
                        for binding in host_bindings:
                            ports.append(
                                f"{binding['HostIp']}:{binding['HostPort']}->{container_port}"
                            )
                info["Ports"] = ", ".join(ports)

                # 添加大小信息
                if size:
                    info["Size"] = self.docker.format_size(
                        container.attrs["SizeRw"] or 0
                    )

                result.append(info)

            return result

        except Exception as e:
            self.docker.print_message(f"[bold red]列出容器失败: {e}[/]")
            return []

    def start(self, container_ids: List[str]) -> bool:
        """启动容器"""
        if self.docker.mode == RunMode.PYTHON_API:
            return self._start_container_api(container_ids)
        return self._start_container_cli(container_ids)

    def _start_container_cli(self, container_ids: List[str]) -> bool:
        """使用CLI命令启动容器"""
        cmd = ["container", "start"] + container_ids
        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]启动容器失败: {result.stderr}[/]")
            return False

        self.docker.print_message("[bold green]容器启动成功[/]")
        return True

    def _start_container_api(self, container_ids: List[str]) -> bool:
        """使用Python API启动容器"""
        try:
            for container_id in container_ids:
                container = self.docker.docker_client.containers.get(container_id)
                container.start()

            self.docker.print_message("[bold green]容器启动成功[/]")
            return True

        except Exception as e:
            self.docker.print_message(f"[bold red]启动容器失败: {e}[/]")
            return False

    def stop(self, container_ids: List[str], timeout: int = 10) -> bool:
        """停止容器"""
        if self.docker.mode == RunMode.PYTHON_API:
            return self._stop_container_api(container_ids, timeout)
        return self._stop_container_cli(container_ids, timeout)

    def _stop_container_cli(self, container_ids: List[str], timeout: int) -> bool:
        """使用CLI命令停止容器"""
        cmd = ["container", "stop", "--time", str(timeout)] + container_ids
        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]停止容器失败: {result.stderr}[/]")
            return False

        self.docker.print_message("[bold green]容器停止成功[/]")
        return True

    def _stop_container_api(self, container_ids: List[str], timeout: int) -> bool:
        """使用Python API停止容器"""
        try:
            for container_id in container_ids:
                container = self.docker.docker_client.containers.get(container_id)
                container.stop(timeout=timeout)

            self.docker.print_message("[bold green]容器停止成功[/]")
            return True

        except Exception as e:
            self.docker.print_message(f"[bold red]停止容器失败: {e}[/]")
            return False
