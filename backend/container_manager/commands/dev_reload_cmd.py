#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境热重载命令行界面

提供前端和后端热重载配置和管理的命令行功能
"""

import os
import sys
import click
import json
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from backend.container_manager.dev_reload_manager import get_dev_reload_manager

# 配置日志
import logging

logger = logging.getLogger("smoothstack.container_manager.commands.dev_reload_cmd")


@click.group(name="reload", help="开发环境热重载管理")
def dev_reload_cmd_group():
    """开发环境热重载管理命令组"""
    pass


@dev_reload_cmd_group.command(name="list", help="列出所有热重载配置")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_configs(json_output):
    """列出所有热重载配置"""
    reload_manager = get_dev_reload_manager()
    configs = reload_manager.list_reload_configs()

    if json_output:
        click.echo(json.dumps(configs, indent=2, ensure_ascii=False))
        return

    if not configs:
        click.echo("未找到热重载配置")
        return

    # 格式化表格输出
    table_data = []
    for config in configs:
        container_name = config["container_name"]
        reload_config = config["config"]
        active = config["active"]

        table_data.append(
            [
                container_name,
                reload_config["type"],
                ", ".join(reload_config["watch_paths"]),
                "是" if active else "否",
            ]
        )

    headers = ["容器名称", "类型", "监视路径", "是否活跃"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@dev_reload_cmd_group.command(name="show", help="查看热重载配置详情")
@click.argument("container_name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def show_config(container_name, json_output):
    """查看热重载配置详情"""
    reload_manager = get_dev_reload_manager()
    config = reload_manager.get_reload_config(container_name)

    if not config:
        click.secho(f"容器 '{container_name}' 没有热重载配置", fg="red")
        return

    if json_output:
        click.echo(json.dumps(config, indent=2, ensure_ascii=False))
        return

    # 显示基本信息
    click.secho(f"容器: {config['container_name']}", bold=True)
    click.echo(f"类型: {config['config']['type']}")
    click.echo(f"状态: {'活跃' if config['active'] else '未活跃'}")

    # 显示监视路径
    click.secho("\n监视路径:", bold=True)
    for path in config["config"]["watch_paths"]:
        click.echo(f"  - {path}")

    # 显示类型特定配置
    if config["config"]["type"] == "frontend":
        click.secho("\nVite配置:", bold=True)
        vite_config = config["config"]["vite_config"]
        click.echo(f"  主机: {vite_config['server']['host']}")
        click.echo(f"  端口: {vite_config['server']['port']}")
        click.echo(f"  HMR协议: {vite_config['server']['hmr']['protocol']}")

    elif config["config"]["type"] == "backend":
        click.secho("\n后端配置:", bold=True)
        click.echo(f"  重载命令: {config['config']['reload_command']}")
        click.echo(f"  防抖时间: {config['config']['debounce_ms']}ms")

        click.secho("\n排除模式:", bold=True)
        for pattern in config["config"]["exclude_patterns"]:
            click.echo(f"  - {pattern}")


@dev_reload_cmd_group.command(name="configure-frontend", help="配置前端热重载")
@click.argument("container_name", required=True)
@click.argument("watch_paths", nargs=-1, required=True)
@click.option("--port", "-p", type=int, default=3000, help="HMR服务端口")
@click.option("--host", "-h", default="0.0.0.0", help="HMR服务主机地址")
@click.option("--config", "-c", type=click.Path(exists=True), help="Vite配置文件路径")
def configure_frontend(container_name, watch_paths, port, host, config):
    """配置前端热重载"""
    reload_manager = get_dev_reload_manager()

    # 加载Vite配置
    vite_config = None
    if config:
        try:
            with open(config, "r", encoding="utf-8") as f:
                vite_config = json.load(f)
        except Exception as e:
            click.secho(f"加载Vite配置文件失败: {e}", fg="red")
            return

    # 配置热重载
    success = reload_manager.configure_frontend_reload(
        container_name=container_name,
        watch_paths=list(watch_paths),
        vite_config=vite_config,
        hmr_port=port,
        hmr_host=host,
    )

    if success:
        click.secho(f"成功配置容器 '{container_name}' 的前端热重载", fg="green")
        click.echo(f"监视路径: {', '.join(watch_paths)}")
        click.echo(f"HMR服务: {host}:{port}")
    else:
        click.secho(f"配置容器 '{container_name}' 的前端热重载失败", fg="red")


@dev_reload_cmd_group.command(name="configure-backend", help="配置后端热重载")
@click.argument("container_name", required=True)
@click.argument("watch_paths", nargs=-1, required=True)
@click.option("--command", "-c", help="重载命令")
@click.option("--exclude", "-e", multiple=True, help="排除的文件模式")
@click.option("--debounce", "-d", type=int, default=1000, help="重载延迟时间（毫秒）")
def configure_backend(container_name, watch_paths, command, exclude, debounce):
    """配置后端热重载"""
    reload_manager = get_dev_reload_manager()

    # 配置热重载
    success = reload_manager.configure_backend_reload(
        container_name=container_name,
        watch_paths=list(watch_paths),
        reload_command=command,
        exclude_patterns=list(exclude) if exclude else None,
        debounce_ms=debounce,
    )

    if success:
        click.secho(f"成功配置容器 '{container_name}' 的后端热重载", fg="green")
        click.echo(f"监视路径: {', '.join(watch_paths)}")
        if command:
            click.echo(f"重载命令: {command}")
        if exclude:
            click.echo(f"排除模式: {', '.join(exclude)}")
        click.echo(f"防抖时间: {debounce}ms")
    else:
        click.secho(f"配置容器 '{container_name}' 的后端热重载失败", fg="red")


@dev_reload_cmd_group.command(name="start", help="启动热重载")
@click.argument("container_name", required=True)
def start_reload(container_name):
    """启动热重载"""
    reload_manager = get_dev_reload_manager()

    success = reload_manager.start_reload(container_name)

    if success:
        click.secho(f"成功启动容器 '{container_name}' 的热重载", fg="green")
    else:
        click.secho(f"启动容器 '{container_name}' 的热重载失败", fg="red")


@dev_reload_cmd_group.command(name="stop", help="停止热重载")
@click.argument("container_name", required=True)
def stop_reload(container_name):
    """停止热重载"""
    reload_manager = get_dev_reload_manager()

    success = reload_manager.stop_reload(container_name)

    if success:
        click.secho(f"成功停止容器 '{container_name}' 的热重载", fg="green")
    else:
        click.secho(f"停止容器 '{container_name}' 的热重载失败", fg="red")


@dev_reload_cmd_group.command(name="remove", help="移除热重载配置")
@click.argument("container_name", required=True)
@click.confirmation_option(prompt="确定要移除此热重载配置吗?")
def remove_config(container_name):
    """移除热重载配置"""
    reload_manager = get_dev_reload_manager()

    success = reload_manager.remove_reload_config(container_name)

    if success:
        click.secho(f"成功移除容器 '{container_name}' 的热重载配置", fg="green")
    else:
        click.secho(f"移除容器 '{container_name}' 的热重载配置失败", fg="red")
