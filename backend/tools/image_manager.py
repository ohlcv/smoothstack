#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker镜像管理工具

提供Docker镜像和容器的细粒度管理，包括：
- 镜像的拉取、列表、删除和标记
- 镜像依赖的管理
- 镜像构建和清理
"""

import os
import sys
import json
import subprocess
import click
from typing import List, Dict, Optional, Any


@click.group()
def cli():
    """Smoothstack Docker镜像管理工具"""
    pass


def _run_docker_command(
    cmd: List[str], capture_output: bool = True
) -> subprocess.CompletedProcess:
    """运行Docker命令并返回结果"""
    try:
        result = subprocess.run(
            ["docker"] + cmd, capture_output=capture_output, text=True, check=False
        )
        return result
    except Exception as e:
        click.echo(f"执行Docker命令失败: {e}")
        sys.exit(1)


def _check_docker_installed() -> bool:
    """检查Docker是否已安装"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


# ===== 镜像命令 =====
@cli.group("image")
def image():
    """Docker镜像管理"""
    if not _check_docker_installed():
        click.echo("错误: Docker未安装或无法访问")
        sys.exit(1)


@image.command("list")
@click.option("--all", "-a", is_flag=True, help="显示所有镜像，包括中间层镜像")
@click.option("--filter", "-f", multiple=True, help="根据条件过滤输出")
@click.option("--format", help="使用Go模板格式化输出")
@click.option("--quiet", "-q", is_flag=True, help="只显示镜像ID")
def list_images(all, filter, format, quiet):
    """列出本地Docker镜像"""
    cmd = ["images"]

    if all:
        cmd.append("--all")

    for f in filter:
        cmd.extend(["--filter", f])

    if format:
        cmd.extend(["--format", format])

    if quiet:
        cmd.append("--quiet")

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"列出镜像失败: {result.stderr}")
        sys.exit(1)


@image.command("pull")
@click.argument("image_name")
@click.option("--all-tags", "-a", is_flag=True, help="下载所有标记的镜像")
@click.option("--quiet", "-q", is_flag=True, help="抑制详细输出")
def pull_image(image_name, all_tags, quiet):
    """从Docker Hub拉取镜像"""
    cmd = ["pull"]

    if all_tags:
        cmd.append("--all-tags")

    if quiet:
        cmd.append("--quiet")

    cmd.append(image_name)

    click.echo(f"正在拉取镜像: {image_name}")

    result = _run_docker_command(cmd, capture_output=False)

    if result.returncode != 0:
        click.echo(f"拉取镜像失败: {result.stderr}")
        sys.exit(1)


@image.command("rm")
@click.argument("image_names", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除镜像")
def remove_image(image_names, force):
    """删除本地Docker镜像"""
    cmd = ["rmi"]

    if force:
        cmd.append("--force")

    cmd.extend(image_names)

    click.echo(f"正在删除镜像: {', '.join(image_names)}")

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"删除镜像失败: {result.stderr}")
        sys.exit(1)


@image.command("tag")
@click.argument("source_image")
@click.argument("target_image")
def tag_image(source_image, target_image):
    """为镜像添加标签"""
    cmd = ["tag", source_image, target_image]

    click.echo(f"正在为镜像 {source_image} 添加标签 {target_image}")

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(f"标签添加成功")
    else:
        click.echo(f"添加标签失败: {result.stderr}")
        sys.exit(1)


@image.command("build")
@click.option("--file", "-f", help="指定Dockerfile路径")
@click.option("--tag", "-t", multiple=True, help="为镜像添加名称和标签")
@click.option("--build-arg", multiple=True, help="设置构建参数")
@click.option("--no-cache", is_flag=True, help="不使用构建缓存")
@click.argument("path")
def build_image(file, tag, build_arg, no_cache, path):
    """构建Docker镜像"""
    cmd = ["build"]

    if file:
        cmd.extend(["--file", file])

    for t in tag:
        cmd.extend(["--tag", t])

    for arg in build_arg:
        cmd.extend(["--build-arg", arg])

    if no_cache:
        cmd.append("--no-cache")

    cmd.append(path)

    click.echo(f"正在构建镜像...")

    result = _run_docker_command(cmd, capture_output=False)

    if result.returncode != 0:
        click.echo(f"构建镜像失败")
        sys.exit(1)


@image.command("inspect")
@click.argument("image_names", nargs=-1, required=True)
@click.option("--format", help="使用Go模板格式化输出")
def inspect_image(image_names, format):
    """查看镜像详细信息"""
    cmd = ["inspect"]

    if format:
        cmd.extend(["--format", format])

    cmd.extend(image_names)

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        try:
            # 尝试解析为JSON并美化输出
            if not format:
                data = json.loads(result.stdout)
                click.echo(json.dumps(data, indent=2))
            else:
                click.echo(result.stdout)
        except json.JSONDecodeError:
            click.echo(result.stdout)
    else:
        click.echo(f"查看镜像详情失败: {result.stderr}")
        sys.exit(1)


@image.command("prune")
@click.option(
    "--all", "-a", is_flag=True, help="删除所有未使用的镜像，不仅仅是悬空镜像"
)
@click.option("--force", "-f", is_flag=True, help="不提示确认")
def prune_images(all, force):
    """删除未使用的镜像"""
    cmd = ["image", "prune"]

    if all:
        cmd.append("--all")

    if force:
        cmd.append("--force")

    click.echo("正在清理未使用的镜像...")

    result = _run_docker_command(cmd, capture_output=not force)

    if result.returncode == 0:
        if not force:
            click.echo(result.stdout)
    else:
        click.echo(f"清理镜像失败: {result.stderr}")
        sys.exit(1)


# ===== 容器命令 =====
@cli.group("container")
def container():
    """Docker容器管理"""
    if not _check_docker_installed():
        click.echo("错误: Docker未安装或无法访问")
        sys.exit(1)


@container.command("list")
@click.option("--all", "-a", is_flag=True, help="显示所有容器，包括已停止的")
@click.option("--quiet", "-q", is_flag=True, help="只显示容器ID")
@click.option("--size", "-s", is_flag=True, help="显示容器文件大小")
@click.option("--filter", "-f", multiple=True, help="根据条件过滤输出")
def list_containers(all, quiet, size, filter):
    """列出容器"""
    cmd = ["ps"]

    if all:
        cmd.append("--all")

    if quiet:
        cmd.append("--quiet")

    if size:
        cmd.append("--size")

    for f in filter:
        cmd.extend(["--filter", f])

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"列出容器失败: {result.stderr}")
        sys.exit(1)


@container.command("start")
@click.argument("container_ids", nargs=-1, required=True)
def start_container(container_ids):
    """启动容器"""
    cmd = ["start"]
    cmd.extend(container_ids)

    click.echo(f"正在启动容器: {', '.join(container_ids)}")

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"启动容器失败: {result.stderr}")
        sys.exit(1)


@container.command("stop")
@click.argument("container_ids", nargs=-1, required=True)
@click.option("--time", "-t", type=int, default=10, help="等待容器停止的秒数")
def stop_container(container_ids, time):
    """停止容器"""
    cmd = ["stop", f"--time={time}"]
    cmd.extend(container_ids)

    click.echo(f"正在停止容器: {', '.join(container_ids)}")

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"停止容器失败: {result.stderr}")
        sys.exit(1)


@container.command("rm")
@click.argument("container_ids", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除正在运行的容器")
@click.option("--volumes", "-v", is_flag=True, help="删除与容器关联的匿名卷")
def remove_container(container_ids, force, volumes):
    """删除容器"""
    cmd = ["rm"]

    if force:
        cmd.append("--force")

    if volumes:
        cmd.append("--volumes")

    cmd.extend(container_ids)

    click.echo(f"正在删除容器: {', '.join(container_ids)}")

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"删除容器失败: {result.stderr}")
        sys.exit(1)


@container.command("logs")
@click.argument("container_id")
@click.option("--follow", "-f", is_flag=True, help="跟踪日志输出")
@click.option("--tail", type=int, help="显示最新的N行日志")
@click.option("--timestamps", "-t", is_flag=True, help="显示时间戳")
def container_logs(container_id, follow, tail, timestamps):
    """查看容器日志"""
    cmd = ["logs"]

    if follow:
        cmd.append("--follow")

    if tail is not None:
        cmd.extend(["--tail", str(tail)])

    if timestamps:
        cmd.append("--timestamps")

    cmd.append(container_id)

    result = _run_docker_command(cmd, capture_output=not follow)

    if not follow:
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.echo(f"获取容器日志失败: {result.stderr}")
            sys.exit(1)


if __name__ == "__main__":
    cli()
