#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python Docker管理工具

使用Python Docker API实现Docker容器和镜像的管理功能，包括：
- 容器的创建、启动、停止、删除和监控
- 镜像的拉取、构建、标记和删除
- 使用Python API而非命令行实现Docker交互
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Optional, Any, Union
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
from rich.panel import Panel
from rich import box

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker客户端
docker_client = None

# Rich控制台
console = Console()


def get_docker_client():
    """获取或创建Docker客户端实例"""
    global docker_client
    if docker_client is None:
        try:
            import docker

            docker_client = docker.from_env()
            # 测试连接
            docker_client.ping()
        except (ImportError, Exception) as e:
            console.print(f"[bold red]错误: 无法连接到Docker: {e}[/]")
            console.print(
                "[yellow]请确保Docker已安装并正在运行，且已安装docker包: pip install docker[/]"
            )
            sys.exit(1)
    return docker_client


@click.group()
def cli():
    """Python Docker管理工具

    使用Python Docker API实现的容器和镜像管理工具
    """
    try:
        # 预检查Docker是否可用
        get_docker_client()
    except Exception as e:
        console.print(f"[bold red]初始化Docker客户端失败: {e}[/]")
        sys.exit(1)


@cli.group("container")
def container():
    """容器管理命令"""
    pass


@container.command("list")
@click.option("--all", "-a", is_flag=True, help="显示所有容器，包括已停止的")
@click.option("--quiet", "-q", is_flag=True, help="只显示容器ID")
def list_containers(all, quiet):
    """列出容器"""
    client = get_docker_client()

    with console.status("[bold green]正在获取容器列表...[/]"):
        try:
            containers = client.containers.list(all=all)

            if not containers:
                console.print("[yellow]未找到容器[/]")
                return

            if quiet:
                for container in containers:
                    console.print(container.id)
                return

            # 创建表格
            table = Table(title="容器列表", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("名称", style="green")
            table.add_column("镜像", style="blue")
            table.add_column("状态", style="yellow")
            table.add_column("创建时间", style="magenta")
            table.add_column("端口", style="red")

            for container in containers:
                # 获取容器详细信息
                container_info = client.api.inspect_container(container.id)

                # 解析端口信息
                ports = []
                port_info = container_info.get("NetworkSettings", {}).get("Ports", {})
                for container_port, host_ports in port_info.items():
                    if host_ports:
                        for binding in host_ports:
                            ports.append(
                                f"{binding['HostPort']}->{container_port.split('/')[0]}"
                            )
                    else:
                        ports.append(container_port)

                # 格式化时间
                created_at = container_info["Created"].split(".")[0].replace("T", " ")

                # 获取第一个名称（移除前导斜杠）
                name = container_info["Name"].strip("/")

                # 添加行
                table.add_row(
                    container.id[:12],
                    name,
                    (
                        container.image.tags[0]
                        if container.image.tags
                        else container.image.id[:12]
                    ),
                    container.status,
                    created_at,
                    ", ".join(ports) if ports else "",
                )

            console.print(table)

        except Exception as e:
            console.print(f"[bold red]列出容器时出错: {e}[/]")
            sys.exit(1)


@container.command("start")
@click.argument("container_ids", nargs=-1, required=True)
def start_container(container_ids):
    """启动容器"""
    client = get_docker_client()

    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            console.print(f"[green]正在启动容器: {container_id}[/]")
            container.start()
            console.print(f"[bold green]容器 {container_id} 已启动[/]")
        except Exception as e:
            console.print(f"[bold red]启动容器 {container_id} 时出错: {e}[/]")


@container.command("stop")
@click.argument("container_ids", nargs=-1, required=True)
@click.option("--time", "-t", type=int, default=10, help="等待容器停止的秒数")
def stop_container(container_ids, time):
    """停止容器"""
    client = get_docker_client()

    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            console.print(f"[yellow]正在停止容器: {container_id}[/]")
            container.stop(timeout=time)
            console.print(f"[bold green]容器 {container_id} 已停止[/]")
        except Exception as e:
            console.print(f"[bold red]停止容器 {container_id} 时出错: {e}[/]")


@container.command("restart")
@click.argument("container_ids", nargs=-1, required=True)
@click.option("--time", "-t", type=int, default=10, help="等待容器停止的秒数")
def restart_container(container_ids, time):
    """重启容器"""
    client = get_docker_client()

    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            console.print(f"[yellow]正在重启容器: {container_id}[/]")
            container.restart(timeout=time)
            console.print(f"[bold green]容器 {container_id} 已重启[/]")
        except Exception as e:
            console.print(f"[bold red]重启容器 {container_id} 时出错: {e}[/]")


@container.command("logs")
@click.argument("container_id")
@click.option("--follow", "-f", is_flag=True, help="跟踪日志输出")
@click.option("--tail", type=int, default=100, help="显示最新的N行日志")
@click.option("--timestamps", "-t", is_flag=True, help="显示时间戳")
def container_logs(container_id, follow, tail, timestamps):
    """查看容器日志"""
    client = get_docker_client()

    try:
        container = client.containers.get(container_id)

        # 如果不是跟踪模式，直接获取日志并显示
        if not follow:
            logs = container.logs(
                tail=tail, timestamps=timestamps, stream=False
            ).decode("utf-8")
            console.print(logs)
            return

        # 跟踪模式
        console.print(f"[green]正在跟踪容器 {container_id} 的日志，按 Ctrl+C 停止[/]")
        try:
            for line in container.logs(
                tail=tail, timestamps=timestamps, stream=True, follow=True
            ):
                console.print(line.decode("utf-8").strip())
        except KeyboardInterrupt:
            console.print("[yellow]已停止日志跟踪[/]")

    except Exception as e:
        console.print(f"[bold red]获取容器 {container_id} 的日志时出错: {e}[/]")


@container.command("rm")
@click.argument("container_ids", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除正在运行的容器")
@click.option("--volumes", "-v", is_flag=True, help="删除与容器关联的匿名卷")
def remove_container(container_ids, force, volumes):
    """删除容器"""
    client = get_docker_client()

    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            console.print(f"[yellow]正在删除容器: {container_id}[/]")
            container.remove(force=force, v=volumes)
            console.print(f"[bold green]容器 {container_id} 已删除[/]")
        except Exception as e:
            console.print(f"[bold red]删除容器 {container_id} 时出错: {e}[/]")


@container.command("exec")
@click.argument("container_id")
@click.argument("command")
@click.option("--interactive", "-i", is_flag=True, help="保持STDIN打开")
@click.option("--tty", "-t", is_flag=True, help="分配伪TTY")
def exec_container(container_id, command, interactive, tty):
    """在容器中执行命令"""
    client = get_docker_client()

    try:
        container = client.containers.get(container_id)

        # 解析命令
        cmd_parts = command.split()

        if interactive or tty:
            console.print("[yellow]警告: 交互模式在此CLI中不完全支持[/]")
            console.print(
                f"[yellow]建议使用原生Docker命令: docker exec {'-it' if interactive and tty else '-i' if interactive else '-t' if tty else ''} {container_id} {command}[/]"
            )

        # 执行命令
        result = container.exec_run(cmd_parts, stdout=True, stderr=True, stream=False)

        exit_code = result.exit_code
        output = result.output.decode("utf-8")

        console.print(f"[green]命令执行完成，退出码: {exit_code}[/]")
        if output:
            console.print(output)

    except Exception as e:
        console.print(f"[bold red]在容器 {container_id} 中执行命令时出错: {e}[/]")


@cli.group("image")
def image():
    """镜像管理命令"""
    pass


@image.command("list")
@click.option("--all", "-a", is_flag=True, help="显示所有镜像，包括中间层镜像")
@click.option("--quiet", "-q", is_flag=True, help="只显示镜像ID")
@click.option("--filter", "-f", multiple=True, help="根据提供的条件过滤输出")
def list_images(all, quiet, filter):
    """列出镜像"""
    client = get_docker_client()

    with console.status("[bold green]正在获取镜像列表...[/]"):
        try:
            # 处理过滤器
            filters = {}
            for f in filter:
                if "=" in f:
                    key, value = f.split("=", 1)
                    filters[key] = value

            # 获取镜像
            images = client.images.list(all=all, filters=filters)

            if not images:
                console.print("[yellow]未找到镜像[/]")
                return

            if quiet:
                for image in images:
                    console.print(image.id.replace("sha256:", "")[:12])
                return

            # 创建表格
            table = Table(title="镜像列表", box=box.ROUNDED)
            table.add_column("仓库", style="cyan")
            table.add_column("标签", style="green")
            table.add_column("镜像ID", style="blue")
            table.add_column("创建时间", style="magenta")
            table.add_column("大小", style="yellow")

            for image in images:
                repo_tags = image.tags

                # 处理无标签镜像
                if not repo_tags:
                    # 安全处理创建时间
                    try:
                        created_time = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(image.attrs["Created"])
                        )
                    except (TypeError, ValueError):
                        # 如果是字符串格式的ISO时间
                        if isinstance(image.attrs["Created"], str):
                            created_time = (
                                image.attrs["Created"].split(".")[0].replace("T", " ")
                            )
                        else:
                            created_time = "未知"

                    table.add_row(
                        "<none>",
                        "<none>",
                        image.id.replace("sha256:", "")[:12],
                        created_time,
                        f"{round(image.attrs['Size'] / 1024 / 1024, 2)} MB",
                    )
                    continue

                # 处理有标签的镜像
                for tag in repo_tags:
                    if ":" in tag:
                        repo, tag_name = tag.rsplit(":", 1)
                    else:
                        repo, tag_name = tag, "latest"

                    # 安全处理创建时间
                    try:
                        created_time = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(image.attrs["Created"])
                        )
                    except (TypeError, ValueError):
                        # 如果是字符串格式的ISO时间
                        if isinstance(image.attrs["Created"], str):
                            created_time = (
                                image.attrs["Created"].split(".")[0].replace("T", " ")
                            )
                        else:
                            created_time = "未知"

                    table.add_row(
                        repo,
                        tag_name,
                        image.id.replace("sha256:", "")[:12],
                        created_time,
                        f"{round(image.attrs['Size'] / 1024 / 1024, 2)} MB",
                    )

            console.print(table)

        except Exception as e:
            console.print(f"[bold red]列出镜像时出错: {e}[/]")
            sys.exit(1)


@image.command("pull")
@click.argument("image_name")
@click.option("--all-tags", "-a", is_flag=True, help="下载所有标记的镜像")
def pull_image(image_name, all_tags):
    """拉取镜像"""
    client = get_docker_client()

    try:
        if ":" not in image_name and not all_tags:
            console.print(f"[yellow]未指定标签，默认使用latest[/]")
            image_name = f"{image_name}:latest"

        with console.status(
            f"[bold green]正在拉取镜像: {image_name}...[/]", spinner="dots"
        ):
            if all_tags:
                repository = image_name.split(":")[0]
                console.print(f"[green]正在拉取仓库 {repository} 的所有标签[/]")
                for line in client.api.pull(
                    repository, stream=True, decode=True, all_tags=True
                ):
                    if "progress" in line:
                        continue
                    console.print(f"[dim]{json.dumps(line)}[/]")
            else:
                for line in client.api.pull(image_name, stream=True, decode=True):
                    if "progress" in line:
                        continue
                    console.print(f"[dim]{json.dumps(line)}[/]")

        console.print(f"[bold green]镜像 {image_name} 拉取完成[/]")

    except Exception as e:
        console.print(f"[bold red]拉取镜像 {image_name} 时出错: {e}[/]")
        sys.exit(1)


@image.command("rm")
@click.argument("image_names", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除镜像")
def remove_image(image_names, force):
    """删除镜像"""
    client = get_docker_client()

    for image_name in image_names:
        try:
            console.print(f"[yellow]正在删除镜像: {image_name}[/]")
            client.images.remove(image_name, force=force)
            console.print(f"[bold green]镜像 {image_name} 已删除[/]")
        except Exception as e:
            console.print(f"[bold red]删除镜像 {image_name} 时出错: {e}[/]")


@image.command("tag")
@click.argument("source_image")
@click.argument("target_image")
def tag_image(source_image, target_image):
    """为镜像添加标签"""
    client = get_docker_client()

    try:
        console.print(f"[green]正在为镜像 {source_image} 添加标签 {target_image}[/]")

        # 获取源镜像
        image = client.images.get(source_image)

        # 添加标签
        image.tag(
            *target_image.split(":", 1) if ":" in target_image else (target_image, None)
        )

        console.print(f"[bold green]标签添加成功[/]")

    except Exception as e:
        console.print(f"[bold red]为镜像添加标签时出错: {e}[/]")
        sys.exit(1)


@image.command("build")
@click.option("--file", "-f", help="指定Dockerfile路径")
@click.option("--tag", "-t", multiple=True, help="为镜像添加名称和标签")
@click.option("--build-arg", multiple=True, help="设置构建参数")
@click.option("--no-cache", is_flag=True, help="不使用构建缓存")
@click.argument("path")
def build_image(file, tag, build_arg, no_cache, path):
    """构建镜像"""
    client = get_docker_client()

    try:
        # 处理构建参数
        buildargs = {}
        for arg in build_arg:
            if "=" in arg:
                key, value = arg.split("=", 1)
                buildargs[key] = value

        # 显示构建信息
        console.print(f"[green]正在构建镜像[/]")
        console.print(f"[green]路径: {path}[/]")
        if file:
            console.print(f"[green]Dockerfile: {file}[/]")
        if tag:
            console.print(f"[green]标签: {', '.join(tag)}[/]")
        if no_cache:
            console.print(f"[green]不使用缓存[/]")

        # 开始构建
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            build_task = progress.add_task("[green]构建中...", total=None)

            response = client.api.build(
                path=path,
                dockerfile=file,
                tag=tag[0] if tag else None,
                nocache=no_cache,
                rm=True,
                buildargs=buildargs,
                decode=True,
            )

            for chunk in response:
                if "stream" in chunk:
                    # 更新进度
                    progress.update(
                        build_task, description=f"[green]{chunk['stream'].strip()}[/]"
                    )
                elif "error" in chunk:
                    progress.update(
                        build_task, description=f"[red]{chunk['error'].strip()}[/]"
                    )
                    raise Exception(chunk["error"])

        console.print(f"[bold green]镜像构建完成[/]")

        # 如果有多个标签，为镜像添加其他标签
        if len(tag) > 1:
            image = client.images.get(tag[0])
            for t in tag[1:]:
                console.print(f"[green]添加标签: {t}[/]")
                image.tag(*t.split(":", 1) if ":" in t else (t, None))

    except Exception as e:
        console.print(f"[bold red]构建镜像时出错: {e}[/]")
        sys.exit(1)


@image.command("inspect")
@click.argument("image_names", nargs=-1, required=True)
def inspect_image(image_names):
    """查看镜像详情"""
    client = get_docker_client()

    for image_name in image_names:
        try:
            # 获取镜像详情
            image = client.images.get(image_name)

            # 显示镜像信息
            info = {
                "ID": image.id,
                "Tags": image.tags,
                "Created": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(image.attrs["Created"])
                ),
                "Size": f"{round(image.attrs['Size'] / 1024 / 1024, 2)} MB",
                "Architecture": image.attrs.get("Architecture", ""),
                "OS": image.attrs.get("Os", ""),
                "Author": image.attrs.get("Author", ""),
                "Digest": image.attrs.get("RepoDigests", [""])[0],
                "Entrypoint": image.attrs.get("Config", {}).get("Entrypoint", []),
                "Cmd": image.attrs.get("Config", {}).get("Cmd", []),
                "Env": image.attrs.get("Config", {}).get("Env", []),
                "ExposedPorts": list(
                    image.attrs.get("Config", {}).get("ExposedPorts", {}).keys()
                ),
                "Labels": image.attrs.get("Config", {}).get("Labels", {}),
            }

            # 创建面板
            panel = Panel.fit(
                "\n".join(
                    [f"[cyan]{k}[/]: [yellow]{v}[/]" for k, v in info.items() if v]
                ),
                title=f"镜像信息: {image_name}",
                border_style="green",
                padding=(1, 2),
            )

            console.print(panel)

        except Exception as e:
            console.print(f"[bold red]查看镜像 {image_name} 详情时出错: {e}[/]")


@image.command("prune")
@click.option(
    "--all", "-a", is_flag=True, help="删除所有未使用的镜像，不仅仅是悬空镜像"
)
@click.option("--force", "-f", is_flag=True, help="不提示确认")
def prune_images(all, force):
    """清理未使用的镜像"""
    client = get_docker_client()

    try:
        if not force:
            confirm = click.confirm(
                f"确定要{'删除所有未使用的镜像' if all else '删除未使用的悬空镜像'}吗?"
            )
            if not confirm:
                console.print("[yellow]操作已取消[/]")
                return

        with console.status("[bold green]正在清理镜像...[/]"):
            result = client.images.prune(filters={"dangling": not all})

            if result.get("ImagesDeleted"):
                console.print(
                    f"[bold green]已删除 {len(result['ImagesDeleted'])} 个镜像[/]"
                )
                for item in result["ImagesDeleted"]:
                    if "Untagged" in item:
                        console.print(f"[green]取消标记: {item['Untagged']}[/]")
                    if "Deleted" in item:
                        console.print(f"[green]已删除: {item['Deleted']}[/]")
            else:
                console.print("[yellow]没有镜像被删除[/]")

            if "SpaceReclaimed" in result:
                console.print(
                    f"[bold green]释放空间: {round(result['SpaceReclaimed'] / 1024 / 1024, 2)} MB[/]"
                )

    except Exception as e:
        console.print(f"[bold red]清理镜像时出错: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
