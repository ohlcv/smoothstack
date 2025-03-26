#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一Docker管理工具

整合了命令行调用和Python API两种方式管理Docker容器和镜像：
- 自动选择最佳实现方式：CLI命令或Python API
- 支持容器的创建、启动、停止、删除和监控
- 支持镜像的拉取、构建、标记和删除
- 美观的界面和详细的错误处理
"""

import os
import sys
import json
import time
import logging
import subprocess
import shutil
from typing import List, Dict, Optional, Any, Union, Tuple
import click

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 命令行配置
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


# 运行模式配置
class RunMode:
    CLI = "cli"  # 使用Docker CLI命令
    PYTHON_API = "api"  # 使用Python Docker API
    AUTO = "auto"  # 自动选择最佳实现


# 全局变量
docker_client = None
rich_available = False
current_mode = RunMode.AUTO
USE_RICH_OUTPUT = False  # 是否使用Rich进行美化输出

# 检查Rich库是否可用
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn
    from rich.panel import Panel
    from rich import box

    # 创建Rich控制台
    console = Console()
    rich_available = True
    USE_RICH_OUTPUT = True
except ImportError:
    # 如果Rich不可用，使用基本输出
    rich_available = False
    USE_RICH_OUTPUT = False
    logger.debug("Rich库不可用，将使用标准输出")


def print_fancy(message, style=""):
    """增强的消息输出函数，支持Rich格式化或标准输出"""
    if USE_RICH_OUTPUT and rich_available:
        console.print(message)
    else:
        # 去除Rich标记的简单实现
        message = message.replace("[bold ", "").replace("[/]", "")
        message = message.replace("[green]", "").replace("[red]", "")
        message = message.replace("[yellow]", "").replace("[blue]", "")
        print(message)


def _check_docker_installed() -> bool:
    """检查Docker是否已安装"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def get_docker_client():
    """获取或创建Docker客户端实例，如果不可用则返回None"""
    global docker_client
    if docker_client is None:
        try:
            import docker

            docker_client = docker.from_env()
            # 测试连接
            docker_client.ping()
        except (ImportError, Exception) as e:
            if USE_RICH_OUTPUT:
                print_fancy(f"[bold yellow]警告: 无法连接到Docker API: {e}[/]")
                print_fancy("[yellow]将使用Docker命令行接口[/]")
            else:
                logger.warning(f"无法连接到Docker API: {e}")
                logger.info("将使用Docker命令行接口")
            docker_client = None
    return docker_client


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
        print_fancy(f"[bold red]执行Docker命令失败: {e}[/]")
        sys.exit(1)


def determine_run_mode(requested_mode=RunMode.AUTO) -> str:
    """确定实际运行模式"""
    if requested_mode == RunMode.CLI:
        if not _check_docker_installed():
            print_fancy("[bold red]错误: Docker未安装或无法访问[/]")
            sys.exit(1)
        return RunMode.CLI

    if requested_mode == RunMode.PYTHON_API:
        client = get_docker_client()
        if client is None:
            print_fancy("[bold yellow]警告: Python Docker API不可用，将使用CLI模式[/]")
            if not _check_docker_installed():
                print_fancy("[bold red]错误: Docker CLI也不可用[/]")
                sys.exit(1)
            return RunMode.CLI
        return RunMode.PYTHON_API

    # 自动模式：优先使用Python API，如果不可用则使用CLI
    client = get_docker_client()
    if client is not None:
        return RunMode.PYTHON_API

    if not _check_docker_installed():
        print_fancy("[bold red]错误: Docker未安装或无法访问[/]")
        sys.exit(1)

    return RunMode.CLI


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--mode",
    type=click.Choice([RunMode.CLI, RunMode.PYTHON_API, RunMode.AUTO]),
    default=RunMode.AUTO,
    help="指定运行模式：命令行(cli)、Python API(api)或自动选择(auto)",
)
@click.option("--plain", is_flag=True, help="使用纯文本输出，不使用富文本格式")
def cli(mode, plain):
    """Docker管理工具

    统一的命令行接口，用于管理Docker容器和镜像。
    根据环境自动选择使用Docker CLI命令或Python Docker API。
    """
    global current_mode, USE_RICH_OUTPUT

    # 设置输出模式
    if plain:
        USE_RICH_OUTPUT = False

    # 确定运行模式
    current_mode = determine_run_mode(mode)

    # 显示当前模式
    mode_str = "Docker CLI" if current_mode == RunMode.CLI else "Python Docker API"
    print_fancy(f"[bold blue]使用 {mode_str} 模式运行[/]")


# ===== 容器管理命令 =====
@cli.group("container")
def container():
    """容器管理命令"""
    pass


@container.command("list")
@click.option("--all", "-a", is_flag=True, help="显示所有容器，包括已停止的")
@click.option("--quiet", "-q", is_flag=True, help="只显示容器ID")
@click.option("--size", "-s", is_flag=True, help="显示容器文件大小")
@click.option("--filter", "-f", multiple=True, help="根据条件过滤输出")
def list_containers(all, quiet, size, filter):
    """列出容器"""
    if current_mode == RunMode.PYTHON_API:
        _list_containers_api(all, quiet, size, filter)
    else:
        _list_containers_cli(all, quiet, size, filter)


def _list_containers_cli(all, quiet, size, filter):
    """使用CLI命令列出容器"""
    cmd = ["container", "ls"]

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
        print_fancy(result.stdout)
    else:
        print_fancy(f"[bold red]列出容器失败: {result.stderr}[/]")
        sys.exit(1)


def _list_containers_api(all, quiet, size, filter):
    """使用Python API列出容器"""
    client = get_docker_client()

    if USE_RICH_OUTPUT and rich_available:
        with console.status("[bold green]正在获取容器列表...[/]"):
            try:
                filters = {}
                for f in filter:
                    if "=" in f:
                        key, value = f.split("=", 1)
                        filters[key] = value

                containers = client.containers.list(all=all, filters=filters)

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
                if size:
                    table.add_column("大小", style="bright_black")

                for container in containers:
                    # 获取容器详细信息
                    container_info = client.api.inspect_container(container.id)

                    # 解析端口信息
                    ports = []
                    port_info = container_info.get("NetworkSettings", {}).get(
                        "Ports", {}
                    )
                    for container_port, host_ports in port_info.items():
                        if host_ports:
                            for binding in host_ports:
                                ports.append(
                                    f"{binding['HostPort']}->{container_port.split('/')[0]}"
                                )
                        else:
                            ports.append(container_port)

                    # 格式化时间
                    created_at = (
                        container_info["Created"].split(".")[0].replace("T", " ")
                    )

                    # 获取名称（移除前导斜杠）
                    name = container_info["Name"].strip("/")

                    # 获取镜像名称
                    image_name = (
                        container.image.tags[0]
                        if container.image.tags
                        else container.image.id[:12]
                    )

                    # 行数据
                    row_data = [
                        container.id[:12],
                        name,
                        image_name,
                        container.status,
                        created_at,
                        ", ".join(ports) if ports else "",
                    ]

                    # 添加大小信息（如果需要）
                    if size:
                        size_info = container_info.get("SizeRw", 0)
                        size_root_fs = container_info.get("SizeRootFs", 0)
                        if size_info and size_root_fs:
                            row_data.append(
                                f"{_format_size(size_info)} (virtual {_format_size(size_root_fs)})"
                            )
                        else:
                            row_data.append("N/A")

                    # 添加行
                    table.add_row(*row_data)

                console.print(table)

            except Exception as e:
                console.print(f"[bold red]列出容器时出错: {e}[/]")
                sys.exit(1)
    else:
        # 普通输出模式
        try:
            filters = {}
            for f in filter:
                if "=" in f:
                    key, value = f.split("=", 1)
                    filters[key] = value

            containers = client.containers.list(all=all, filters=filters)

            if not containers:
                print("未找到容器")
                return

            if quiet:
                for container in containers:
                    print(container.id)
                return

            # 打印表头
            header = ["CONTAINER ID", "NAME", "IMAGE", "STATUS", "CREATED", "PORTS"]
            if size:
                header.append("SIZE")
            print("\t".join(header))

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

                # 获取名称（移除前导斜杠）
                name = container_info["Name"].strip("/")

                # 获取镜像名称
                image_name = (
                    container.image.tags[0]
                    if container.image.tags
                    else container.image.id[:12]
                )

                # 行数据
                row_data = [
                    container.id[:12],
                    name,
                    image_name,
                    container.status,
                    created_at,
                    ", ".join(ports) if ports else "",
                ]

                # 添加大小信息（如果需要）
                if size:
                    size_info = container_info.get("SizeRw", 0)
                    size_root_fs = container_info.get("SizeRootFs", 0)
                    if size_info and size_root_fs:
                        row_data.append(
                            f"{_format_size(size_info)} (virtual {_format_size(size_root_fs)})"
                        )
                    else:
                        row_data.append("N/A")

                print("\t".join(row_data))

        except Exception as e:
            print(f"列出容器时出错: {e}")
            sys.exit(1)


@container.command("start")
@click.argument("container_ids", nargs=-1, required=True)
def start_container(container_ids):
    """启动容器"""
    if current_mode == RunMode.PYTHON_API:
        _start_container_api(container_ids)
    else:
        _start_container_cli(container_ids)


def _start_container_cli(container_ids):
    """使用CLI命令启动容器"""
    for container_id in container_ids:
        cmd = ["container", "start", container_id]
        print_fancy(f"[green]正在启动容器: {container_id}[/]")

        result = _run_docker_command(cmd)

        if result.returncode == 0:
            print_fancy(f"[bold green]容器 {container_id} 已启动[/]")
        else:
            print_fancy(f"[bold red]启动容器 {container_id} 失败: {result.stderr}[/]")


def _start_container_api(container_ids):
    """使用Python API启动容器"""
    client = get_docker_client()

    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            print_fancy(f"[green]正在启动容器: {container_id}[/]")
            container.start()
            print_fancy(f"[bold green]容器 {container_id} 已启动[/]")
        except Exception as e:
            print_fancy(f"[bold red]启动容器 {container_id} 时出错: {e}[/]")


@container.command("stop")
@click.argument("container_ids", nargs=-1, required=True)
@click.option("--time", "-t", type=int, default=10, help="等待容器停止的秒数")
def stop_container(container_ids, time):
    """停止容器"""
    if current_mode == RunMode.PYTHON_API:
        _stop_container_api(container_ids, time)
    else:
        _stop_container_cli(container_ids, time)


def _stop_container_cli(container_ids, time):
    """使用CLI命令停止容器"""
    for container_id in container_ids:
        cmd = ["container", "stop"]

        if time != 10:  # 只有在非默认值时添加
            cmd.extend(["-t", str(time)])

        cmd.append(container_id)
        print_fancy(f"[yellow]正在停止容器: {container_id}[/]")

        result = _run_docker_command(cmd)

        if result.returncode == 0:
            print_fancy(f"[bold green]容器 {container_id} 已停止[/]")
        else:
            print_fancy(f"[bold red]停止容器 {container_id} 失败: {result.stderr}[/]")


def _stop_container_api(container_ids, time):
    """使用Python API停止容器"""
    client = get_docker_client()

    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            print_fancy(f"[yellow]正在停止容器: {container_id}[/]")
            container.stop(timeout=time)
            print_fancy(f"[bold green]容器 {container_id} 已停止[/]")
        except Exception as e:
            print_fancy(f"[bold red]停止容器 {container_id} 时出错: {e}[/]")


# ===== 镜像管理命令 =====
@cli.group("image")
def image():
    """镜像管理命令"""
    pass


@image.command("list")
@click.option("--all", "-a", is_flag=True, help="显示所有镜像，包括中间层镜像")
@click.option("--quiet", "-q", is_flag=True, help="只显示镜像ID")
@click.option("--filter", "-f", multiple=True, help="根据条件过滤输出")
def list_images(all, quiet, filter):
    """列出本地Docker镜像"""
    if current_mode == RunMode.PYTHON_API:
        _list_images_api(all, quiet, filter)
    else:
        _list_images_cli(all, quiet, filter)


def _list_images_cli(all, quiet, filter):
    """使用CLI命令列出镜像"""
    cmd = ["image", "ls"]

    if all:
        cmd.append("--all")

    if quiet:
        cmd.append("--quiet")

    for f in filter:
        cmd.extend(["--filter", f])

    result = _run_docker_command(cmd)

    if result.returncode == 0:
        print_fancy(result.stdout)
    else:
        print_fancy(f"[bold red]列出镜像失败: {result.stderr}[/]")
        sys.exit(1)


def _list_images_api(all, quiet, filter):
    """使用Python API列出镜像"""
    client = get_docker_client()

    if USE_RICH_OUTPUT and rich_available:
        with console.status("[bold green]正在获取镜像列表...[/]"):
            try:
                # 转换过滤器参数
                filters = {}
                for f in filter:
                    if "=" in f:
                        key, value = f.split("=", 1)
                        filters[key] = value

                # 获取镜像列表
                images = client.images.list(all=all, filters=filters)

                if not images:
                    console.print("[yellow]未找到镜像[/]")
                    return

                if quiet:
                    for image in images:
                        console.print(image.id)
                    return

                # 创建表格
                table = Table(title="镜像列表", box=box.ROUNDED)
                table.add_column("REPOSITORY", style="green")
                table.add_column("TAG", style="blue")
                table.add_column("IMAGE ID", style="cyan")
                table.add_column("CREATED", style="magenta")
                table.add_column("SIZE", style="yellow")

                for image in images:
                    # 处理没有tag的镜像
                    if not image.tags:
                        # 处理为<none>:<none>
                        repo = "<none>"
                        tag = "<none>"
                        table.add_row(
                            repo,
                            tag,
                            image.short_id.replace("sha256:", ""),
                            _format_time_ago(image.attrs.get("Created", "")),
                            _format_size(image.attrs.get("Size", 0)),
                        )
                    else:
                        # 处理每个tag
                        for tag_name in image.tags:
                            if ":" in tag_name:
                                repo, tag = tag_name.split(":", 1)
                            else:
                                repo, tag = tag_name, "latest"

                            table.add_row(
                                repo,
                                tag,
                                image.short_id.replace("sha256:", ""),
                                _format_time_ago(image.attrs.get("Created", "")),
                                _format_size(image.attrs.get("Size", 0)),
                            )

                console.print(table)

            except Exception as e:
                console.print(f"[bold red]列出镜像时出错: {e}[/]")
                sys.exit(1)
    else:
        # 普通输出模式
        try:
            # 转换过滤器参数
            filters = {}
            for f in filter:
                if "=" in f:
                    key, value = f.split("=", 1)
                    filters[key] = value

            # 获取镜像列表
            images = client.images.list(all=all, filters=filters)

            if not images:
                print("未找到镜像")
                return

            if quiet:
                for image in images:
                    print(image.id)
                return

            # 打印表头
            print("REPOSITORY\tTAG\tIMAGE ID\tCREATED\tSIZE")

            for image in images:
                # 处理没有tag的镜像
                if not image.tags:
                    # 处理为<none>:<none>
                    repo = "<none>"
                    tag = "<none>"
                    print(
                        f"{repo}\t{tag}\t{image.short_id.replace('sha256:', '')}\t{_format_time_ago(image.attrs.get('Created', ''))}\t{_format_size(image.attrs.get('Size', 0))}"
                    )
                else:
                    # 处理每个tag
                    for tag_name in image.tags:
                        if ":" in tag_name:
                            repo, tag = tag_name.split(":", 1)
                        else:
                            repo, tag = tag_name, "latest"

                        print(
                            f"{repo}\t{tag}\t{image.short_id.replace('sha256:', '')}\t{_format_time_ago(image.attrs.get('Created', ''))}\t{_format_size(image.attrs.get('Size', 0))}"
                        )

        except Exception as e:
            print(f"列出镜像时出错: {e}")
            sys.exit(1)


# ===== 辅助函数 =====
def _format_size(size_bytes):
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def _format_time_ago(timestamp_str):
    """格式化时间为多久以前"""
    if not timestamp_str:
        return "N/A"

    try:
        # 处理Docker API返回的时间格式
        if "T" in timestamp_str:
            # ISO格式的时间戳
            timestamp_str = timestamp_str.replace("Z", "+00:00")
            from datetime import datetime
            import dateutil.parser

            created_time = dateutil.parser.parse(timestamp_str)
            now = datetime.now(created_time.tzinfo)
            diff = now - created_time

            # 计算时间差
            seconds = diff.total_seconds()
            if seconds < 60:
                return f"{int(seconds)} seconds ago"
            elif seconds < 3600:
                return f"{int(seconds / 60)} minutes ago"
            elif seconds < 86400:
                return f"{int(seconds / 3600)} hours ago"
            elif seconds < 604800:
                return f"{int(seconds / 86400)} days ago"
            elif seconds < 2592000:
                return f"{int(seconds / 604800)} weeks ago"
            elif seconds < 31536000:
                return f"{int(seconds / 2592000)} months ago"
            else:
                return f"{int(seconds / 31536000)} years ago"
        else:
            # 可能是UNIX时间戳
            try:
                from datetime import datetime

                created_time = datetime.fromtimestamp(float(timestamp_str))
                now = datetime.now()
                diff = now - created_time
                seconds = diff.total_seconds()

                if seconds < 60:
                    return f"{int(seconds)} seconds ago"
                elif seconds < 3600:
                    return f"{int(seconds / 60)} minutes ago"
                elif seconds < 86400:
                    return f"{int(seconds / 3600)} hours ago"
                elif seconds < 604800:
                    return f"{int(seconds / 86400)} days ago"
                elif seconds < 2592000:
                    return f"{int(seconds / 604800)} weeks ago"
                elif seconds < 31536000:
                    return f"{int(seconds / 2592000)} months ago"
                else:
                    return f"{int(seconds / 31536000)} years ago"
            except:
                return timestamp_str
    except:
        return timestamp_str


# 添加更多必要的命令（根据项目需求）
# 例如：image.command("pull"), image.command("rm")等

if __name__ == "__main__":
    cli()
