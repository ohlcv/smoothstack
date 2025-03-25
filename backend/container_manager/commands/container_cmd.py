#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理命令

提供容器生命周期管理的命令行接口，包括启动、停止、重启和查看容器状态。
"""

import os
import sys
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

# 导入容器管理器
from backend.container_manager import get_container_manager, ContainerStatus

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.commands")

# 创建控制台对象
console = Console()


@click.group(name="container", help="容器管理命令")
def container_group():
    """容器管理命令组"""
    global container_manager
    container_manager = get_container_manager()
    if not container_manager:
        click.secho("无法初始化容器管理器", fg="red")
        sys.exit(1)


@container_group.command(name="ls", help="列出容器")
@click.option("--all", "-a", is_flag=True, help="显示所有容器，包括已停止的")
@click.option("--filter", "-f", multiple=True, help="过滤条件 (格式: key=value)")
def list_containers(all: bool, filter: List[str]):
    """列出容器"""
    try:
        # 处理过滤器
        filters = {}
        if filter:
            for f in filter:
                if "=" in f:
                    key, value = f.split("=", 1)
                    filters[key] = value

        # 获取容器列表
        containers = container_manager.list_containers(
            all_containers=all, filters=filters
        )

        if not containers:
            console.print("[yellow]没有找到容器[/yellow]")
            return

        # 创建表格
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title="容器列表",
        )

        # 添加列
        table.add_column("ID", style="dim", no_wrap=True)
        table.add_column("名称", style="green")
        table.add_column("镜像", style="blue")
        table.add_column("状态", style="yellow")
        table.add_column("创建时间", style="magenta")
        table.add_column("端口", style="cyan")

        # 添加行
        for container in containers:
            # 格式化容器ID（只显示前12个字符）
            container_id = container.id[:12] if container.id else "N/A"

            # 格式化容器状态
            status_color = {
                ContainerStatus.RUNNING: "[green]运行中[/green]",
                ContainerStatus.STOPPED: "[red]已停止[/red]",
                ContainerStatus.PAUSED: "[yellow]已暂停[/yellow]",
                ContainerStatus.RESTARTING: "[cyan]重启中[/cyan]",
                ContainerStatus.REMOVING: "[magenta]移除中[/magenta]",
                ContainerStatus.EXITED: "[red]已退出[/red]",
                ContainerStatus.DEAD: "[red]已死亡[/red]",
                ContainerStatus.CREATED: "[blue]已创建[/blue]",
            }.get(container.status, f"[grey]{container.status}[/grey]")

            # 格式化端口
            ports_str = (
                ", ".join(
                    f"{host_port}->{container_port}"
                    for host_port, container_port in container.ports.items()
                )
                if container.ports
                else "无"
            )

            # 格式化创建时间
            created_at = (
                container.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if container.created_at
                else "Unknown"
            )

            # 添加行
            table.add_row(
                container_id,
                container.name or "无名称",
                container.image or "无镜像",
                status_color,
                created_at,
                ports_str,
            )

        # 显示表格
        console.print(table)

    except Exception as e:
        logger.error(f"列出容器时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        sys.exit(1)


# 添加list命令的别名
container_group.add_command(list_containers, name="list")


@container_group.command(name="start", help="启动容器")
@click.argument("container_id_or_name", required=True)
@click.option("--timeout", "-t", type=int, default=None, help="启动超时时间（秒）")
def start_container(container_id_or_name: str, timeout: Optional[int]):
    """启动容器"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]启动容器中...[/cyan]"),
            transient=True,
        ) as progress:
            progress.add_task("启动", total=None)
            # 启动容器
            success, message = container_manager.start_container(
                container_id_or_name, timeout=timeout
            )

        if success:
            console.print(f"[green]容器启动成功: {container_id_or_name}[/green]")

            # 获取并显示容器详情
            container = container_manager.get_container(container_id_or_name)
            if container:
                _display_container_details(container)

            return 0
        else:
            console.print(f"[red]容器启动失败: {message}[/red]")
            return 1
    except Exception as e:
        logger.error(f"启动容器时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@container_group.command(name="stop", help="停止容器")
@click.argument("container_id_or_name", required=True)
@click.option("--timeout", "-t", type=int, default=None, help="停止超时时间（秒）")
def stop_container(container_id_or_name: str, timeout: Optional[int]):
    """停止容器"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]停止容器中...[/cyan]"),
            transient=True,
        ) as progress:
            progress.add_task("停止", total=None)
            # 停止容器
            success, message = container_manager.stop_container(
                container_id_or_name, timeout=timeout
            )

        if success:
            console.print(f"[green]容器停止成功: {container_id_or_name}[/green]")
            return 0
        else:
            console.print(f"[red]容器停止失败: {message}[/red]")
            return 1
    except Exception as e:
        logger.error(f"停止容器时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@container_group.command(name="restart", help="重启容器")
@click.argument("container_id_or_name", required=True)
@click.option("--timeout", "-t", type=int, default=None, help="重启超时时间（秒）")
def restart_container(container_id_or_name: str, timeout: Optional[int]):
    """重启容器"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]重启容器中...[/cyan]"),
            transient=True,
        ) as progress:
            progress.add_task("重启", total=None)
            # 重启容器
            success, message = container_manager.restart_container(
                container_id_or_name, timeout=timeout
            )

        if success:
            console.print(f"[green]容器重启成功: {container_id_or_name}[/green]")

            # 获取并显示容器详情
            container = container_manager.get_container(container_id_or_name)
            if container:
                _display_container_details(container)

            return 0
        else:
            console.print(f"[red]容器重启失败: {message}[/red]")
            return 1
    except Exception as e:
        logger.error(f"重启容器时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@container_group.command(name="logs", help="查看容器日志")
@click.argument("container_id_or_name", required=True)
@click.option("--tail", "-n", type=int, default=100, help="显示最后n行日志")
@click.option("--follow", "-f", is_flag=True, help="持续查看日志")
@click.option("--since", "-s", type=int, default=None, help="显示多少秒前的日志")
def container_logs(
    container_id_or_name: str, tail: int, follow: bool, since: Optional[int]
):
    """查看容器日志"""
    try:
        # 如果是持续查看模式
        if follow:
            console.print(
                f"[cyan]正在查看容器 {container_id_or_name} 的日志 (按Ctrl+C退出)[/cyan]"
            )

            # 获取初始日志
            success, logs = container_manager.get_container_logs(
                container_id_or_name, tail=tail, since=since
            )

            if not success:
                if isinstance(logs, str):
                    console.print(f"[red]{logs}[/red]")
                return 1

            # 打印初始日志
            for log in logs:
                console.print(log)

            # 持续查看日志
            last_time = time.time()
            try:
                while True:
                    time.sleep(1)
                    success, new_logs = container_manager.get_container_logs(
                        container_id_or_name,
                        tail=100,
                        since=int(time.time() - last_time),
                    )

                    if success and new_logs:
                        for log in new_logs:
                            console.print(log)

                    last_time = time.time()
            except KeyboardInterrupt:
                console.print("[yellow]已停止查看日志[/yellow]")
                return 0
        else:
            # 获取日志
            success, logs = container_manager.get_container_logs(
                container_id_or_name, tail=tail, since=since
            )

            if success:
                if not logs:
                    console.print("[yellow]没有日志[/yellow]")
                else:
                    # 输出日志
                    for log in logs:
                        console.print(log)
                return 0
            else:
                if isinstance(logs, str):
                    console.print(f"[red]{logs}[/red]")
                return 1
    except Exception as e:
        logger.error(f"查看容器日志时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@container_group.command(name="stats", help="查看容器统计信息")
@click.argument("container_id_or_name", required=True)
@click.option("--watch", "-w", is_flag=True, help="持续监控统计信息")
def container_stats(container_id_or_name: str, watch: bool):
    """查看容器统计信息"""
    try:
        if watch:
            console.print(
                f"[cyan]正在监控容器 {container_id_or_name} 的统计信息 (按Ctrl+C退出)[/cyan]"
            )

            try:
                while True:
                    # 清屏
                    os.system("cls" if os.name == "nt" else "clear")

                    # 获取统计信息
                    success, stats = container_manager.get_container_stats(
                        container_id_or_name
                    )

                    if success:
                        _display_container_stats(stats)
                    else:
                        console.print(
                            f"[red]获取统计信息失败: {stats.get('error', '未知错误')}[/red]"
                        )
                        return 1

                    time.sleep(2)
            except KeyboardInterrupt:
                console.print("[yellow]已停止监控[/yellow]")
                return 0
        else:
            # 获取统计信息
            success, stats = container_manager.get_container_stats(container_id_or_name)

            if success:
                _display_container_stats(stats)
                return 0
            else:
                console.print(
                    f"[red]获取统计信息失败: {stats.get('error', '未知错误')}[/red]"
                )
                return 1
    except Exception as e:
        logger.error(f"查看容器统计信息时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@container_group.command(name="info", help="查看容器详情")
@click.argument("container_id_or_name", required=True)
def container_info(container_id_or_name: str):
    """查看容器详情"""
    try:
        # 获取容器信息
        container = container_manager.get_container(container_id_or_name)

        if not container:
            console.print(f"[red]容器不存在: {container_id_or_name}[/red]")
            return 1

        # 显示容器详情
        _display_container_details(container)
        return 0
    except Exception as e:
        logger.error(f"查看容器详情时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@container_group.command(name="check", help="检查Docker服务状态")
def check_docker():
    """检查Docker服务状态"""
    try:
        # 检查Docker服务状态
        success, message = container_manager.check_docker_service()

        if success:
            console.print(Panel(message, title="Docker服务状态", border_style="green"))
            return 0
        else:
            console.print(Panel(message, title="Docker服务状态", border_style="red"))
            return 1
    except Exception as e:
        logger.error(f"检查Docker服务状态时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


def _display_container_details(container):
    """显示容器详情"""
    # 容器状态颜色
    status_color = {
        ContainerStatus.RUNNING: "green",
        ContainerStatus.STOPPED: "red",
        ContainerStatus.PAUSED: "yellow",
        ContainerStatus.RESTARTING: "cyan",
        ContainerStatus.REMOVING: "magenta",
        ContainerStatus.EXITED: "red",
        ContainerStatus.DEAD: "red",
        ContainerStatus.CREATED: "blue",
    }.get(container.status, "grey")

    # 创建表格
    table = Table(show_header=False, box=box.ROUNDED)
    table.add_column("字段", style="cyan")
    table.add_column("值", style="yellow")

    # 添加基本信息
    table.add_row("ID", container.id)
    table.add_row("名称", container.name)
    table.add_row("镜像", container.image)
    table.add_row("状态", f"[{status_color}]{container.status.name}[/{status_color}]")

    if container.created_at:
        table.add_row("创建时间", container.created_at.strftime("%Y-%m-%d %H:%M:%S"))

    # 添加网络信息
    if container.ip_address:
        table.add_row("IP地址", container.ip_address)

    if container.network_mode:
        table.add_row("网络模式", container.network_mode)

    # 添加端口信息
    if container.ports:
        ports_str = ", ".join(
            f"{host_port}->{container_port}"
            for host_port, container_port in container.ports.items()
        )
        table.add_row("端口映射", ports_str)

    # 添加卷信息
    if container.volumes:
        volumes_str = "\n".join(
            f"{host_path} -> {container_path}"
            for host_path, container_path in container.volumes.items()
        )
        table.add_row("卷挂载", volumes_str)

    # 添加资源限制信息
    if container.cpu_limit:
        table.add_row("CPU限制", str(container.cpu_limit))

    if container.memory_limit:
        # 将字节转换为更易读的格式
        memory_mb = container.memory_limit / (1024 * 1024)
        table.add_row("内存限制", f"{memory_mb:.2f} MB")

    # 添加健康状态信息
    if container.health_status:
        table.add_row("健康状态", container.health_status)

    # 添加重启次数
    if container.restart_count is not None:
        table.add_row("重启次数", str(container.restart_count))

    # 显示面板
    console.print(
        Panel(table, title=f"容器详情: {container.name}", border_style="cyan")
    )


def _display_container_stats(stats):
    """显示容器统计信息"""
    # 获取CPU和内存使用率
    cpu_percent = stats["cpu"]["usage_percent"]
    memory_percent = stats["memory"]["usage_percent"]

    # 设置使用率颜色
    cpu_color = "green"
    if cpu_percent > 70:
        cpu_color = "yellow"
    if cpu_percent > 90:
        cpu_color = "red"

    memory_color = "green"
    if memory_percent > 70:
        memory_color = "yellow"
    if memory_percent > 90:
        memory_color = "red"

    # 创建表格
    table = Table(show_header=False, box=box.ROUNDED)
    table.add_column("指标", style="cyan")
    table.add_column("值", style="yellow")

    # 添加基本信息
    table.add_row("容器ID", stats["id"][:12])
    table.add_row("容器名称", stats["name"])
    table.add_row("读取时间", stats["read_time"])

    # 添加CPU信息
    table.add_row("CPU使用率", f"[{cpu_color}]{cpu_percent:.2f}%[/{cpu_color}]")
    table.add_row("CPU核心数", str(stats["cpu"]["online_cpus"]))

    # 添加内存信息
    memory_usage_mb = stats["memory"]["usage"] / (1024 * 1024)
    memory_limit_mb = stats["memory"]["limit"] / (1024 * 1024)

    table.add_row(
        "内存使用率", f"[{memory_color}]{memory_percent:.2f}%[/{memory_color}]"
    )
    table.add_row("内存使用", f"{memory_usage_mb:.2f} MB / {memory_limit_mb:.2f} MB")

    # 添加网络信息
    network_rx_mb = stats["network"]["rx_bytes"] / (1024 * 1024)
    network_tx_mb = stats["network"]["tx_bytes"] / (1024 * 1024)

    table.add_row("网络接收", f"{network_rx_mb:.2f} MB")
    table.add_row("网络发送", f"{network_tx_mb:.2f} MB")

    # 添加进程信息
    table.add_row("进程数", str(stats["pid"]))

    # 显示面板
    console.print(
        Panel(table, title=f"容器统计信息: {stats['name']}", border_style="cyan")
    )


if __name__ == "__main__":
    container_group()
