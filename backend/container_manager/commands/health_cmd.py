#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器健康检查命令行界面

提供容器健康监控相关的命令行功能
"""

import os
import sys
import time
import click
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from docker.errors import NotFound

from backend.container_manager.health_checker import (
    get_health_checker,
    HealthStatus,
    ResourceThresholds,
    NotificationConfig,
)

logger = logging.getLogger("smoothstack.container_manager.commands.health_cmd")


@click.group(name="health", help="容器健康检查和监控管理")
def health_cmd_group():
    """容器健康监控命令组"""
    pass


@health_cmd_group.command(name="status", help="显示健康检查服务状态")
def health_status():
    """显示健康检查服务状态"""
    health_checker = get_health_checker()

    if health_checker.is_monitoring():
        click.secho("健康检查服务状态: ", nl=False)
        click.secho("运行中", fg="green")

        # 显示监控容器数量
        containers = health_checker.list_monitored_containers()
        click.echo(f"监控容器数量: {len(containers)}")
        click.echo(f"检查间隔: {health_checker.check_interval}秒")

        # 显示健康状态统计
        report = health_checker.get_health_report()
        summary = report.get("summary", {})

        click.echo("\n健康状态统计:")
        click.echo(f"  总计: {summary.get('total', 0)}")
        click.echo(f"  健康: {summary.get('healthy', 0)}")
        click.secho(
            f"  警告: {summary.get('warning', 0)}",
            fg="yellow" if summary.get("warning", 0) > 0 else None,
        )
        click.secho(
            f"  不健康: {summary.get('unhealthy', 0)}",
            fg="red" if summary.get("unhealthy", 0) > 0 else None,
        )
        click.secho(
            f"  未知: {summary.get('unknown', 0)}",
            fg="blue" if summary.get("unknown", 0) > 0 else None,
        )
    else:
        click.secho("健康检查服务状态: ", nl=False)
        click.secho("未运行", fg="red")
        click.echo("使用 'smoothstack health start' 启动服务")


@health_cmd_group.command(name="start", help="启动健康检查监控服务")
@click.option("--interval", "-i", type=int, default=None, help="健康检查间隔(秒)")
@click.option(
    "--container", "-c", multiple=True, help="要监控的容器ID或名称(可多次指定)"
)
@click.option("--all", "-a", is_flag=True, default=False, help="监控所有运行中的容器")
@click.option(
    "--reset", "-r", is_flag=True, default=False, help="重置现有的监控容器列表"
)
def start_health_monitor(interval, container, all, reset):
    """启动健康检查监控服务"""
    health_checker = get_health_checker()

    if health_checker.is_monitoring():
        click.secho("健康检查服务已在运行中", fg="yellow")

        if interval or container or all or reset:
            click.echo("要更改配置，请先停止服务: smoothstack health stop")

        return

    # 设置检查间隔
    if interval is not None:
        health_checker.check_interval = interval

    # 启动监控
    success = health_checker.start_monitoring(
        containers=container, monitor_all=all, use_existing=not reset
    )

    if success:
        click.secho("健康检查监控服务已启动", fg="green")
        health_status()
    else:
        click.secho("启动健康检查监控服务失败", fg="red")


@health_cmd_group.command(name="stop", help="停止健康检查监控服务")
def stop_health_monitor():
    """停止健康检查监控服务"""
    health_checker = get_health_checker()

    if not health_checker.is_monitoring():
        click.secho("健康检查服务未在运行", fg="yellow")
        return

    success = health_checker.stop_monitoring()

    if success:
        click.secho("健康检查监控服务已停止", fg="green")
    else:
        click.secho("停止健康检查监控服务失败", fg="red")


@health_cmd_group.command(name="add", help="添加容器到监控列表")
@click.argument("container", nargs=-1, required=True)
def add_container(container):
    """添加容器到监控列表"""
    health_checker = get_health_checker()

    success_count = 0
    fail_count = 0

    for container_id_or_name in container:
        success = health_checker.add_container(container_id_or_name)
        if success:
            click.secho(f"已添加容器 {container_id_or_name} 到监控列表", fg="green")
            success_count += 1
        else:
            click.secho(f"添加容器 {container_id_or_name} 失败", fg="red")
            fail_count += 1

    click.echo(f"总计: 成功 {success_count}, 失败 {fail_count}")


@health_cmd_group.command(name="remove", help="从监控列表移除容器")
@click.argument("container", nargs=-1, required=True)
def remove_container(container):
    """从监控列表移除容器"""
    health_checker = get_health_checker()

    success_count = 0
    fail_count = 0

    for container_id_or_name in container:
        success = health_checker.remove_container(container_id_or_name)
        if success:
            click.secho(f"已从监控列表移除容器 {container_id_or_name}", fg="green")
            success_count += 1
        else:
            click.secho(f"移除容器 {container_id_or_name} 失败", fg="red")
            fail_count += 1

    click.echo(f"总计: 成功 {success_count}, 失败 {fail_count}")


@health_cmd_group.command(name="list", help="列出所有被监控的容器")
@click.option(
    "--json", "-j", "json_output", is_flag=True, default=False, help="以JSON格式输出"
)
def list_containers(json_output):
    """列出所有被监控的容器"""
    health_checker = get_health_checker()
    containers = health_checker.list_monitored_containers()

    if json_output:
        click.echo(json.dumps(containers, indent=2, ensure_ascii=False))
        return

    if not containers:
        click.echo("当前没有监控的容器")
        return

    click.secho("监控中的容器:", bold=True)
    click.echo("ID\t\t名称\t\t状态\t\t健康状态\t\t最后检查时间")
    click.echo("-" * 120)

    status_colors = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.WARNING: "yellow",
        HealthStatus.UNHEALTHY: "red",
        HealthStatus.UNKNOWN: "blue",
        HealthStatus.STARTING: "cyan",
    }

    for container in containers:
        container_id = container["id"][:12]
        name = container["name"]
        status = container["status"]
        health = container["health"]
        last_check = container["last_check"] or "未检查"

        health_color = status_colors.get(health, None)

        click.echo(f"{container_id}\t{name}\t\t{status}\t\t", nl=False)
        click.secho(f"{health}", fg=health_color, nl=False)
        click.echo(f"\t\t{last_check}")


@health_cmd_group.command(name="check", help="检查指定容器的健康状态")
@click.argument("container", required=True)
@click.option("--verbose", "-v", is_flag=True, default=False, help="显示详细信息")
@click.option(
    "--json", "-j", "json_output", is_flag=True, default=False, help="以JSON格式输出"
)
def check_container(container, verbose, json_output):
    """检查指定容器的健康状态"""
    health_checker = get_health_checker()
    result = health_checker.check_container_health(container)

    if json_output:
        click.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return

    status_colors = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.WARNING: "yellow",
        HealthStatus.UNHEALTHY: "red",
        HealthStatus.UNKNOWN: "blue",
        HealthStatus.STARTING: "cyan",
    }

    status_display = {
        HealthStatus.HEALTHY: "健康",
        HealthStatus.WARNING: "警告",
        HealthStatus.UNHEALTHY: "不健康",
        HealthStatus.UNKNOWN: "未知",
        HealthStatus.STARTING: "启动中",
    }

    click.secho(
        f"容器: {result.container_name} ({result.container_id[:12]})", bold=True
    )
    click.echo(f"检查时间: {result.check_time}")
    click.echo(f"状态: ", nl=False)
    click.secho(
        status_display.get(result.status, result.status),
        fg=status_colors.get(result.status, None),
    )
    click.echo(f"消息: {result.message}")

    if verbose and result.details:
        click.secho("\n详细信息:", bold=True)

        # 显示Docker健康检查状态
        docker_health = result.details.get("docker_health_status")
        if docker_health:
            click.echo(f"Docker健康检查状态: {docker_health}")

        # 显示资源使用情况
        stats = result.details.get("stats", {})
        if stats:
            click.secho("\n资源使用情况:", bold=True)

            # CPU
            cpu = stats.get("cpu", {})
            if cpu:
                cpu_usage = cpu.get("usage_percent", 0)
                click.echo(f"CPU使用率: ", nl=False)
                color = "green"
                if cpu_usage >= 95:
                    color = "red"
                elif cpu_usage >= 80:
                    color = "yellow"
                click.secho(f"{cpu_usage:.2f}%", fg=color)

            # 内存
            memory = stats.get("memory", {})
            if memory:
                memory_usage = memory.get("usage", 0)
                memory_limit = memory.get("limit", 0)
                memory_percent = memory.get("usage_percent", 0)

                # 格式化内存大小
                def format_bytes(size):
                    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                        if size < 1024.0 or unit == "PB":
                            return f"{size:.2f} {unit}"
                        size /= 1024.0

                formatted_usage = format_bytes(memory_usage)
                formatted_limit = format_bytes(memory_limit)

                click.echo(
                    f"内存使用: {formatted_usage} / {formatted_limit} (", nl=False
                )

                color = "green"
                if memory_percent >= 95:
                    color = "red"
                elif memory_percent >= 80:
                    color = "yellow"

                click.secho(f"{memory_percent:.2f}%", fg=color, nl=False)
                click.echo(")")

            # 网络
            network = stats.get("network", {})
            if network:
                rx_bytes = network.get("rx_bytes", 0)
                tx_bytes = network.get("tx_bytes", 0)

                click.echo(f"网络接收: {format_bytes(rx_bytes)}")
                click.echo(f"网络发送: {format_bytes(tx_bytes)}")

            # 进程数
            pid = stats.get("pid", 0)
            if pid:
                click.echo(f"进程数: {pid}")


@health_cmd_group.command(name="report", help="生成健康状态报告")
@click.option("--container", "-c", help="指定容器(默认为所有监控容器)")
@click.option(
    "--json", "-j", "json_output", is_flag=True, default=False, help="以JSON格式输出"
)
def health_report(container, json_output):
    """生成健康状态报告"""
    health_checker = get_health_checker()
    report = health_checker.get_health_report(container)

    if json_output:
        click.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if "error" in report:
        click.secho(f"错误: {report['error']}", fg="red")
        return

    # 单容器报告
    if container:
        check_container(container, verbose=True, json_output=False)
        return

    # 所有容器汇总报告
    summary = report.get("summary", {})
    reports = report.get("reports", {})

    click.secho("容器健康状态报告", bold=True)
    click.echo(f"生成时间: {datetime.now().isoformat()}")

    click.secho("\n健康状态统计:", bold=True)
    click.echo(f"  总计: {summary.get('total', 0)}")
    click.echo(f"  健康: {summary.get('healthy', 0)}")
    click.secho(
        f"  警告: {summary.get('warning', 0)}",
        fg="yellow" if summary.get("warning", 0) > 0 else None,
    )
    click.secho(
        f"  不健康: {summary.get('unhealthy', 0)}",
        fg="red" if summary.get("unhealthy", 0) > 0 else None,
    )
    click.secho(
        f"  未知: {summary.get('unknown', 0)}",
        fg="blue" if summary.get("unknown", 0) > 0 else None,
    )

    if reports:
        click.secho("\n容器状态详情:", bold=True)

        # 按健康状态分组
        by_status = {
            HealthStatus.UNHEALTHY: [],
            HealthStatus.WARNING: [],
            HealthStatus.HEALTHY: [],
            HealthStatus.UNKNOWN: [],
            HealthStatus.STARTING: [],
        }

        for container_id, container_report in reports.items():
            status = container_report.get("status", HealthStatus.UNKNOWN)
            by_status[status].append(container_report)

        # 首先显示不健康的容器
        if by_status[HealthStatus.UNHEALTHY]:
            click.secho("\n[不健康]", fg="red", bold=True)
            for report in by_status[HealthStatus.UNHEALTHY]:
                click.echo(
                    f"  {report['container_name']} ({report['container_id'][:12]}): {report['message']}"
                )

        # 然后显示警告状态的容器
        if by_status[HealthStatus.WARNING]:
            click.secho("\n[警告]", fg="yellow", bold=True)
            for report in by_status[HealthStatus.WARNING]:
                click.echo(
                    f"  {report['container_name']} ({report['container_id'][:12]}): {report['message']}"
                )

        # 显示启动中的容器
        if by_status[HealthStatus.STARTING]:
            click.secho("\n[启动中]", fg="cyan", bold=True)
            for report in by_status[HealthStatus.STARTING]:
                click.echo(
                    f"  {report['container_name']} ({report['container_id'][:12]}): {report['message']}"
                )

        # 显示未知状态的容器
        if by_status[HealthStatus.UNKNOWN]:
            click.secho("\n[未知]", fg="blue", bold=True)
            for report in by_status[HealthStatus.UNKNOWN]:
                click.echo(
                    f"  {report['container_name']} ({report['container_id'][:12]}): {report['message']}"
                )

        # 最后显示健康的容器
        if by_status[HealthStatus.HEALTHY]:
            click.secho("\n[健康]", fg="green", bold=True)
            for report in by_status[HealthStatus.HEALTHY]:
                click.echo(
                    f"  {report['container_name']} ({report['container_id'][:12]})"
                )


@health_cmd_group.command(name="monitor", help="实时监控容器健康状态")
@click.option("--container", "-c", help="指定要监控的容器(默认监控所有)")
@click.option("--interval", "-i", type=int, default=5, help="刷新间隔(秒)")
def monitor_health(container, interval):
    """实时监控容器健康状态"""
    health_checker = get_health_checker()

    try:
        click.secho("实时健康监控 (按 Ctrl+C 退出)", bold=True)

        while True:
            # 清屏
            click.clear()

            click.secho("容器健康状态实时监控", bold=True)
            click.echo(f"刷新时间: {datetime.now().isoformat()}")

            if container:
                # 监控单个容器
                result = health_checker.check_container_health(container)
                check_container(container, verbose=True, json_output=False)
            else:
                # 监控所有容器
                health_report(None, json_output=False)

            click.echo(f"\n每 {interval} 秒刷新一次. 按 Ctrl+C 退出.")
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\n已退出监控模式")


@health_cmd_group.group(name="config", help="管理健康检查配置")
def config_cmd_group():
    """健康检查配置管理命令组"""
    pass


@config_cmd_group.command(name="show", help="显示当前配置")
@click.option(
    "--json", "-j", "json_output", is_flag=True, default=False, help="以JSON格式输出"
)
def show_config(json_output):
    """显示当前配置"""
    health_checker = get_health_checker()

    config = {
        "check_interval": health_checker.check_interval,
        "thresholds": health_checker.thresholds.to_dict(),
        "notification": health_checker.notification_config.to_dict(),
    }

    if json_output:
        click.echo(json.dumps(config, indent=2, ensure_ascii=False))
        return

    click.secho("健康检查配置:", bold=True)
    click.echo(f"检查间隔: {config['check_interval']}秒")

    click.secho("\n资源阈值:", bold=True)
    thresholds = config["thresholds"]
    click.echo(f"  CPU警告阈值: {thresholds['cpu_warning']}%")
    click.echo(f"  CPU严重阈值: {thresholds['cpu_critical']}%")
    click.echo(f"  内存警告阈值: {thresholds['memory_warning']}%")
    click.echo(f"  内存严重阈值: {thresholds['memory_critical']}%")
    click.echo(f"  磁盘警告阈值: {thresholds['disk_warning']}%")
    click.echo(f"  磁盘严重阈值: {thresholds['disk_critical']}%")
    click.echo(f"  重启次数阈值: {thresholds['restart_threshold']}")

    click.secho("\n通知配置:", bold=True)
    notification = config["notification"]
    click.echo(f"  启用通知: {notification['enabled']}")
    click.echo(f"  状态变化时通知: {notification['notify_on_status_change']}")
    click.echo(f"  警告状态时通知: {notification['notify_on_warning']}")
    click.echo(f"  严重状态时通知: {notification['notify_on_critical']}")
    click.echo(f"  通知间隔: {notification['notification_interval']}秒")
    click.echo(f"  通知处理器: {', '.join(notification['notification_handlers'])}")


@config_cmd_group.command(name="update", help="更新健康检查配置")
@click.option("--interval", "-i", type=int, help="检查间隔(秒)")
@click.option("--cpu-warning", type=float, help="CPU警告阈值(%)")
@click.option("--cpu-critical", type=float, help="CPU严重阈值(%)")
@click.option("--memory-warning", type=float, help="内存警告阈值(%)")
@click.option("--memory-critical", type=float, help="内存严重阈值(%)")
@click.option("--disk-warning", type=float, help="磁盘警告阈值(%)")
@click.option("--disk-critical", type=float, help="磁盘严重阈值(%)")
@click.option("--restart-threshold", type=int, help="重启次数阈值")
@click.option("--enable-notification/--disable-notification", help="启用/禁用通知")
@click.option("--notification-interval", type=int, help="通知间隔(秒)")
def update_config(
    interval,
    cpu_warning,
    cpu_critical,
    memory_warning,
    memory_critical,
    disk_warning,
    disk_critical,
    restart_threshold,
    enable_notification,
    notification_interval,
):
    """更新健康检查配置"""
    health_checker = get_health_checker()

    # 构建阈值配置
    thresholds = {}
    if cpu_warning is not None:
        thresholds["cpu_warning"] = cpu_warning
    if cpu_critical is not None:
        thresholds["cpu_critical"] = cpu_critical
    if memory_warning is not None:
        thresholds["memory_warning"] = memory_warning
    if memory_critical is not None:
        thresholds["memory_critical"] = memory_critical
    if disk_warning is not None:
        thresholds["disk_warning"] = disk_warning
    if disk_critical is not None:
        thresholds["disk_critical"] = disk_critical
    if restart_threshold is not None:
        thresholds["restart_threshold"] = restart_threshold

    # 构建通知配置
    notification = {}
    if enable_notification is not None:
        notification["enabled"] = enable_notification
    if notification_interval is not None:
        notification["notification_interval"] = notification_interval

    # 更新配置
    success = health_checker.update_config(
        thresholds=thresholds if thresholds else None,
        notification=notification if notification else None,
        check_interval=interval,
    )

    if success:
        click.secho("配置已更新", fg="green")
        # 显示更新后的配置
        show_config(json_output=False)
    else:
        click.secho("更新配置失败", fg="red")


@config_cmd_group.command(name="reset", help="重置为默认配置")
@click.confirmation_option(prompt="确定要重置为默认配置吗?")
def reset_config():
    """重置为默认配置"""
    health_checker = get_health_checker()

    success = health_checker.update_config(
        thresholds=ResourceThresholds().to_dict(),
        notification=NotificationConfig().to_dict(),
        check_interval=60,
    )

    if success:
        click.secho("配置已重置为默认值", fg="green")
        # 显示更新后的配置
        show_config(json_output=False)
    else:
        click.secho("重置配置失败", fg="red")
