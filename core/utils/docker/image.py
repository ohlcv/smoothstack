#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker镜像管理模块

提供镜像的拉取、构建、标记和删除等操作。
支持CLI命令和Python API两种实现方式。
"""

from typing import List, Dict, Optional, Any, Union
from .manager import DockerManager, RunMode, OutputFormat


class ImageManager:
    """Docker镜像管理类"""

    def __init__(self, docker_manager: DockerManager):
        self.docker = docker_manager

    def list_images(
        self,
        all: bool = False,
        quiet: bool = False,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """列出镜像"""
        if self.docker.mode == RunMode.PYTHON_API:
            return self._list_images_api(all, quiet, filters)
        return self._list_images_cli(all, quiet, filters)

    def _list_images_cli(
        self, all: bool, quiet: bool, filters: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """使用CLI命令列出镜像"""
        cmd = ["image", "ls"]
        if all:
            cmd.append("--all")
        if quiet:
            cmd.append("--quiet")
        if filters:
            for k, v in filters.items():
                cmd.extend(["--filter", f"{k}={v}"])

        cmd.append("--format")
        cmd.append(
            '{"ID":"{{.ID}}", "Repository":"{{.Repository}}", "Tag":"{{.Tag}}", "CreatedAt":"{{.CreatedAt}}", "Size":"{{.Size}}"}'
        )

        result = self.docker._run_docker_command(cmd)
        if result.returncode != 0:
            self.docker.print_message(f"[bold red]列出镜像失败: {result.stderr}[/]")
            return []

        import json

        images = []
        for line in result.stdout.splitlines():
            try:
                image = json.loads(line)
                images.append(image)
            except json.JSONDecodeError:
                continue

        return images

    def _list_images_api(
        self, all: bool, quiet: bool, filters: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """使用Python API列出镜像"""
        try:
            images = self.docker.docker_client.images.list(
                all=all, filters=filters or {}
            )

            result = []
            for image in images:
                if quiet:
                    result.append({"ID": image.short_id})
                    continue

                # 处理仓库和标签
                repo_tags = (
                    image.tags[0].split(":") if image.tags else ["<none>", "<none>"]
                )

                info = {
                    "ID": image.short_id,
                    "Repository": repo_tags[0],
                    "Tag": repo_tags[1] if len(repo_tags) > 1 else "latest",
                    "CreatedAt": self.docker.format_time_ago(image.attrs["Created"]),
                    "Size": self.docker.format_size(image.attrs["Size"]),
                }
                result.append(info)

            return result

        except Exception as e:
            self.docker.print_message(f"[bold red]列出镜像失败: {e}[/]")
            return []

    def pull(self, image: str, tag: str = "latest") -> bool:
        """拉取镜像"""
        if self.docker.mode == RunMode.PYTHON_API:
            return self._pull_image_api(image, tag)
        return self._pull_image_cli(image, tag)

    def _pull_image_cli(self, image: str, tag: str) -> bool:
        """使用CLI命令拉取镜像"""
        cmd = ["image", "pull", f"{image}:{tag}"]
        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]拉取镜像失败: {result.stderr}[/]")
            return False

        self.docker.print_message("[bold green]镜像拉取成功[/]")
        return True

    def _pull_image_api(self, image: str, tag: str) -> bool:
        """使用Python API拉取镜像"""
        try:
            self.docker.docker_client.images.pull(image, tag=tag)
            self.docker.print_message("[bold green]镜像拉取成功[/]")
            return True

        except Exception as e:
            self.docker.print_message(f"[bold red]拉取镜像失败: {e}[/]")
            return False

    def build(
        self,
        path: str,
        tag: Optional[str] = None,
        dockerfile: Optional[str] = None,
        buildargs: Optional[Dict[str, str]] = None,
    ) -> bool:
        """构建镜像"""
        if self.docker.mode == RunMode.PYTHON_API:
            return self._build_image_api(path, tag, dockerfile, buildargs)
        return self._build_image_cli(path, tag, dockerfile, buildargs)

    def _build_image_cli(
        self,
        path: str,
        tag: Optional[str],
        dockerfile: Optional[str],
        buildargs: Optional[Dict[str, str]],
    ) -> bool:
        """使用CLI命令构建镜像"""
        cmd = ["image", "build", path]
        if tag:
            cmd.extend(["-t", tag])
        if dockerfile:
            cmd.extend(["-f", dockerfile])
        if buildargs:
            for k, v in buildargs.items():
                cmd.extend(["--build-arg", f"{k}={v}"])

        result = self.docker._run_docker_command(cmd)

        if result.returncode != 0:
            self.docker.print_message(f"[bold red]构建镜像失败: {result.stderr}[/]")
            return False

        self.docker.print_message("[bold green]镜像构建成功[/]")
        return True

    def _build_image_api(
        self,
        path: str,
        tag: Optional[str],
        dockerfile: Optional[str],
        buildargs: Optional[Dict[str, str]],
    ) -> bool:
        """使用Python API构建镜像"""
        try:
            self.docker.docker_client.images.build(
                path=path, tag=tag, dockerfile=dockerfile, buildargs=buildargs
            )

            self.docker.print_message("[bold green]镜像构建成功[/]")
            return True

        except Exception as e:
            self.docker.print_message(f"[bold red]构建镜像失败: {e}[/]")
            return False
