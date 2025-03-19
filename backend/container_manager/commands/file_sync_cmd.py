#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器内文件同步命令行界面

提供管理容器和宿主机之间文件同步的命令行功能
"""

import os
import sys
import click
import json
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from backend.container_manager.file_sync_manager import get_file_sync_manager

# 配置日志
import logging

logger = logging.getLogger("smoothstack.container_manager.commands.file_sync_cmd")


@click.group(name="file-sync", help="容器内文件同步管理")
def file_sync_cmd_group():
    """容器内文件同步管理命令组"""
    pass


@file_sync_cmd_group.command(name="configure", help="配置文件同步")
@click.argument("container_name", required=True)
@click.option("--host-path", "-h", required=True, help="宿主机路径")
@click.option("--container-path", "-c", required=True, help="容器内路径")
@click.option(
    "--mode",
    type=click.Choice(["bidirectional", "host-to-container", "container-to-host"]),
    default="bidirectional",
    help="同步模式 (默认: bidirectional)",
)
@click.option("--exclude", "-e", multiple=True, help="排除的文件模式 (可多次指定)")
@click.option("--include", "-i", multiple=True, help="包含的文件模式 (可多次指定)")
@click.option("--interval", type=int, default=1, help="同步检查间隔（秒）(默认: 1)")
@click.option(
    "--preserve-permissions/--no-preserve-permissions",
    default=True,
    help="是否保留文件权限 (默认: 保留)",
)
def configure_sync(
    container_name,
    host_path,
    container_path,
    mode,
    exclude,
    include,
    interval,
    preserve_permissions,
):
    """配置容器和宿主机之间的文件同步"""
    sync_manager = get_file_sync_manager()

    success = sync_manager.configure_sync(
        container_name=container_name,
        host_path=host_path,
        container_path=container_path,
        sync_mode=mode,
        exclude_patterns=list(exclude) if exclude else None,
        include_patterns=list(include) if include else None,
        sync_interval=interval,
        preserve_permissions=preserve_permissions,
    )

    if success:
        click.secho(f"成功配置容器 '{container_name}' 的文件同步", fg="green")
        click.echo(f"宿主机路径: {host_path}")
        click.echo(f"容器路径: {container_path}")
        click.echo(f"同步模式: {mode}")
        if exclude:
            click.echo(f"排除模式: {', '.join(exclude)}")
        if include:
            click.echo(f"包含模式: {', '.join(include)}")
        click.echo(f"同步间隔: {interval}秒")
        click.echo(f"保留权限: {'是' if preserve_permissions else '否'}")
    else:
        click.secho(f"配置容器 '{container_name}' 的文件同步失败", fg="red")


@file_sync_cmd_group.command(name="start", help="启动文件同步")
@click.argument("container_name", required=True)
def start_sync(container_name):
    """启动文件同步"""
    sync_manager = get_file_sync_manager()

    success = sync_manager.start_sync(container_name)

    if success:
        click.secho(f"成功启动容器 '{container_name}' 的文件同步", fg="green")
    else:
        click.secho(f"启动容器 '{container_name}' 的文件同步失败", fg="red")


@file_sync_cmd_group.command(name="stop", help="停止文件同步")
@click.argument("container_name", required=True)
def stop_sync(container_name):
    """停止文件同步"""
    sync_manager = get_file_sync_manager()

    success = sync_manager.stop_sync(container_name)

    if success:
        click.secho(f"成功停止容器 '{container_name}' 的文件同步", fg="green")
    else:
        click.secho(f"停止容器 '{container_name}' 的文件同步失败", fg="red")


@file_sync_cmd_group.command(name="list", help="列出所有同步配置")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_configs(json_output):
    """列出所有同步配置"""
    sync_manager = get_file_sync_manager()
    configs = sync_manager.list_sync_configs()

    if json_output:
        click.echo(json.dumps(configs, indent=2, ensure_ascii=False))
        return

    if not configs:
        click.echo("未找到同步配置")
        return

    # 格式化表格输出
    table_data = []
    for config in configs:
        container_name = config["container_name"]
        sync_config = config["config"]
        status = config["status"]

        table_data.append(
            [
                container_name,
                sync_config["host_path"],
                sync_config["container_path"],
                sync_config["sync_mode"],
                sync_config["sync_interval"],
                status,
            ]
        )

    headers = ["容器名称", "宿主机路径", "容器路径", "同步模式", "间隔(秒)", "状态"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@file_sync_cmd_group.command(name="show", help="查看同步配置详情")
@click.argument("container_name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def show_config(container_name, json_output):
    """查看同步配置详情"""
    sync_manager = get_file_sync_manager()
    config = sync_manager.get_sync_config(container_name)

    if not config:
        click.secho(f"容器 '{container_name}' 没有同步配置", fg="red")
        return

    if json_output:
        click.echo(json.dumps(config, indent=2, ensure_ascii=False))
        return

    # 显示基本信息
    click.secho(f"容器: {container_name}", bold=True)
    click.echo(f"宿主机路径: {config['host_path']}")
    click.echo(f"容器路径: {config['container_path']}")
    click.echo(f"同步模式: {config['sync_mode']}")
    click.echo(f"同步间隔: {config['sync_interval']}秒")
    click.echo(f"保留权限: {'是' if config['preserve_permissions'] else '否'}")
    click.echo(f"状态: {config['status']}")

    # 显示排除和包含模式
    if config["exclude_patterns"]:
        click.echo(f"排除模式: {', '.join(config['exclude_patterns'])}")
    if config["include_patterns"]:
        click.echo(f"包含模式: {', '.join(config['include_patterns'])}")

    # 显示上次同步时间
    if "last_sync_time" in config:
        import datetime

        last_sync = datetime.datetime.fromtimestamp(config["last_sync_time"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        click.echo(f"上次同步: {last_sync}")


@file_sync_cmd_group.command(name="sync-once", help="执行一次性同步")
@click.argument("container_name", required=True)
def sync_once(container_name):
    """执行一次性同步"""
    sync_manager = get_file_sync_manager()

    success = sync_manager.sync_once(container_name)

    if success:
        click.secho(f"成功完成容器 '{container_name}' 的一次性同步", fg="green")
    else:
        click.secho(f"执行容器 '{container_name}' 的一次性同步失败", fg="red")


@file_sync_cmd_group.command(name="remove", help="移除同步配置")
@click.argument("container_name", required=True)
@click.confirmation_option(prompt="确定要移除此同步配置吗?")
def remove_config(container_name):
    """移除同步配置"""
    sync_manager = get_file_sync_manager()

    success = sync_manager.remove_sync_config(container_name)

    if success:
        click.secho(f"成功移除容器 '{container_name}' 的同步配置", fg="green")
    else:
        click.secho(f"移除容器 '{container_name}' 的同步配置失败", fg="red")


@file_sync_cmd_group.command(name="status", help="检查同步状态")
@click.argument("container_name", required=True)
def check_status(container_name):
    """检查同步状态"""
    sync_manager = get_file_sync_manager()

    config = sync_manager.get_sync_config(container_name)
    if not config:
        click.secho(f"容器 '{container_name}' 没有同步配置", fg="red")
        return

    is_syncing = sync_manager.is_syncing(container_name)

    if is_syncing:
        click.secho(f"容器 '{container_name}' 的文件同步正在运行", fg="green")
    else:
        click.secho(f"容器 '{container_name}' 的文件同步已停止", fg="yellow")

    # 显示上次同步时间
    if "last_sync_time" in config:
        import datetime

        last_sync = datetime.datetime.fromtimestamp(config["last_sync_time"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        click.echo(f"上次同步: {last_sync}")
