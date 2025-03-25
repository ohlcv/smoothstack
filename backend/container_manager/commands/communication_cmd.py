#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨容器通信命令行界面

提供管理容器间通信的命令行功能
"""

import os
import sys
import click
import json
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from backend.container_manager.communication_manager import get_communication_manager

# 配置日志
import logging

logger = logging.getLogger("smoothstack.container_manager.commands.communication_cmd")


@click.group(name="comm", help="跨容器通信管理")
def communication_cmd_group():
    """跨容器通信管理命令组"""
    pass


@communication_cmd_group.command(name="configure-redis", help="配置基于Redis的容器通信")
@click.argument("channel_name", required=True)
@click.option("--host", "-h", default="localhost", help="Redis主机 (默认: localhost)")
@click.option("--port", "-p", type=int, default=6379, help="Redis端口 (默认: 6379)")
@click.option("--db", "-d", type=int, default=0, help="Redis数据库索引 (默认: 0)")
@click.option("--password", help="Redis密码")
@click.option(
    "--container", "-c", multiple=True, help="参与通信的容器名称 (可多次指定)"
)
def configure_redis(channel_name, host, port, db, password, container):
    """配置基于Redis的容器通信"""
    comm_manager = get_communication_manager()

    success = comm_manager.configure_redis_communication(
        channel_name=channel_name,
        host=host,
        port=port,
        db=db,
        password=password,
        container_names=list(container) if container else None,
    )

    if success:
        click.secho(f"成功配置基于Redis的通信频道 '{channel_name}'", fg="green")
        click.echo(f"Redis服务器: {host}:{port}")
        click.echo(f"Redis数据库: {db}")
        if container:
            click.echo(f"参与容器: {', '.join(container)}")
    else:
        click.secho(f"配置通信频道 '{channel_name}' 失败", fg="red")


@communication_cmd_group.command(
    name="configure-direct", help="配置基于直接Socket的容器通信"
)
@click.argument("channel_name", required=True)
@click.option(
    "--protocol",
    type=click.Choice(["tcp", "udp"]),
    default="tcp",
    help="通信协议 (默认: tcp)",
)
@click.option("--host", "-h", default="0.0.0.0", help="监听主机 (默认: 0.0.0.0)")
@click.option("--port", "-p", type=int, default=5555, help="监听端口 (默认: 5555)")
@click.option(
    "--container", "-c", multiple=True, help="参与通信的容器名称 (可多次指定)"
)
def configure_direct(channel_name, protocol, host, port, container):
    """配置基于直接Socket的容器通信"""
    comm_manager = get_communication_manager()

    success = comm_manager.configure_direct_communication(
        channel_name=channel_name,
        protocol=protocol,
        host=host,
        port=port,
        container_names=list(container) if container else None,
    )

    if success:
        click.secho(f"成功配置基于直接Socket的通信频道 '{channel_name}'", fg="green")
        click.echo(f"协议: {protocol}")
        click.echo(f"主机: {host}")
        click.echo(f"端口: {port}")
        if container:
            click.echo(f"参与容器: {', '.join(container)}")
    else:
        click.secho(f"配置通信频道 '{channel_name}' 失败", fg="red")


@communication_cmd_group.command(
    name="configure-network", help="配置基于Docker网络的容器通信"
)
@click.argument("channel_name", required=True)
@click.option("--network", "-n", required=True, help="Docker网络名称")
@click.option(
    "--container",
    "-c",
    required=True,
    multiple=True,
    help="参与通信的容器名称 (可多次指定)",
)
def configure_network(channel_name, network, container):
    """配置基于Docker网络的容器通信"""
    comm_manager = get_communication_manager()

    success = comm_manager.configure_docker_network_communication(
        channel_name=channel_name,
        network_name=network,
        container_names=list(container),
    )

    if success:
        click.secho(f"成功配置基于Docker网络的通信频道 '{channel_name}'", fg="green")
        click.echo(f"网络: {network}")
        click.echo(f"参与容器: {', '.join(container)}")
    else:
        click.secho(f"配置通信频道 '{channel_name}' 失败", fg="red")


@communication_cmd_group.command(
    name="configure-volume", help="配置基于共享卷的容器通信"
)
@click.argument("channel_name", required=True)
@click.option("--volume", "-v", required=True, help="Docker卷名称")
@click.option("--path", "-p", default="/shared", help="容器内挂载路径 (默认: /shared)")
@click.option(
    "--container",
    "-c",
    required=True,
    multiple=True,
    help="参与通信的容器名称 (可多次指定)",
)
def configure_volume(channel_name, volume, path, container):
    """配置基于共享卷的容器通信"""
    comm_manager = get_communication_manager()

    success = comm_manager.configure_volume_communication(
        channel_name=channel_name,
        volume_name=volume,
        mount_path=path,
        container_names=list(container),
    )

    if success:
        click.secho(f"成功配置基于共享卷的通信频道 '{channel_name}'", fg="green")
        click.echo(f"卷: {volume}")
        click.echo(f"挂载路径: {path}")
        click.echo(f"参与容器: {', '.join(container)}")
    else:
        click.secho(f"配置通信频道 '{channel_name}' 失败", fg="red")


@communication_cmd_group.command(name="publish", help="发布消息到通信频道")
@click.argument("channel_name", required=True)
@click.option("--message", "-m", required=True, help="消息内容")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["command", "event", "data", "heartbeat"]),
    default="data",
    help="消息类型 (默认: data)",
)
@click.option("--source", "-s", help="源容器名称")
@click.option("--target", "-c", multiple=True, help="目标容器名称 (可多次指定)")
def publish_message(channel_name, message, type, source, target):
    """发布消息到通信频道"""
    comm_manager = get_communication_manager()

    # 获取消息类型常量
    message_type = None
    if type == "command":
        message_type = comm_manager.MSG_TYPE_COMMAND
    elif type == "event":
        message_type = comm_manager.MSG_TYPE_EVENT
    elif type == "data":
        message_type = comm_manager.MSG_TYPE_DATA
    elif type == "heartbeat":
        message_type = comm_manager.MSG_TYPE_HEARTBEAT

    success = comm_manager.publish_message(
        channel_name=channel_name,
        message=message,
        message_type=message_type,
        source_container=source,
        target_containers=list(target) if target else None,
    )

    if success:
        click.secho(f"成功发布消息到通信频道 '{channel_name}'", fg="green")
        click.echo(f"消息类型: {type}")
        if source:
            click.echo(f"源容器: {source}")
        if target:
            click.echo(f"目标容器: {', '.join(target)}")
    else:
        click.secho(f"发布消息到通信频道 '{channel_name}' 失败", fg="red")


@communication_cmd_group.command(name="list", help="列出所有通信频道")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_channels(json_output):
    """列出所有通信频道"""
    comm_manager = get_communication_manager()
    channels = comm_manager.list_channels()

    if json_output:
        click.echo(json.dumps(channels, indent=2, ensure_ascii=False))
        return

    if not channels:
        click.echo("未找到通信频道")
        return

    # 格式化表格输出
    table_data = []
    for channel in channels:
        channel_name = channel["name"]
        config = channel["config"]
        channel_type = config["type"]
        active = "活跃" if channel["active"] else "停止"
        subscribers = channel["subscribers"]

        # 根据通信类型获取特定信息
        details = ""
        if channel_type == "redis":
            details = f"{config['redis_host']}:{config['redis_port']}"
        elif channel_type == "direct":
            details = f"{config['protocol']}://{config['host']}:{config['port']}"
        elif channel_type == "docker_network":
            details = f"network:{config['network_name']}"
        elif channel_type == "volume":
            details = f"volume:{config['volume_name']}"

        table_data.append(
            [
                channel_name,
                channel_type,
                details,
                len(config.get("container_names", [])),
                subscribers,
                active,
            ]
        )

    headers = ["频道名称", "类型", "连接详情", "容器数", "订阅者", "状态"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@communication_cmd_group.command(name="show", help="查看通信频道详情")
@click.argument("channel_name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def show_channel(channel_name, json_output):
    """查看通信频道详情"""
    comm_manager = get_communication_manager()
    channel = comm_manager.get_channel_info(channel_name)

    if not channel:
        click.secho(f"通信频道 '{channel_name}' 不存在", fg="red")
        return

    if json_output:
        click.echo(json.dumps(channel, indent=2, ensure_ascii=False))
        return

    config = channel["config"]
    channel_type = config["type"]

    # 显示基本信息
    click.secho(f"频道: {channel_name}", bold=True)
    click.echo(f"类型: {channel_type}")
    click.echo(f"状态: {'活跃' if channel['active'] else '停止'}")
    click.echo(f"订阅者数量: {channel['subscribers']}")
    click.echo(f"创建时间: {format_timestamp(config.get('created_at', 0))}")

    # 显示容器
    if "container_names" in config and config["container_names"]:
        click.echo(f"参与容器: {', '.join(config['container_names'])}")

    # 显示类型特定配置
    if channel_type == "redis":
        click.echo(f"Redis服务器: {config['redis_host']}:{config['redis_port']}")
        click.echo(f"Redis数据库: {config['redis_db']}")
    elif channel_type == "direct":
        click.echo(f"协议: {config['protocol']}")
        click.echo(f"主机: {config['host']}")
        click.echo(f"端口: {config['port']}")
    elif channel_type == "docker_network":
        click.echo(f"Docker网络: {config['network_name']}")
    elif channel_type == "volume":
        click.echo(f"Docker卷: {config['volume_name']}")
        click.echo(f"挂载路径: {config['mount_path']}")


@communication_cmd_group.command(name="remove", help="移除通信频道")
@click.argument("channel_name", required=True)
@click.confirmation_option(prompt="确定要移除此通信频道吗?")
def remove_channel(channel_name):
    """移除通信频道"""
    comm_manager = get_communication_manager()

    success = comm_manager.remove_channel(channel_name)

    if success:
        click.secho(f"成功移除通信频道 '{channel_name}'", fg="green")
    else:
        click.secho(f"移除通信频道 '{channel_name}' 失败", fg="red")


def format_timestamp(timestamp):
    """格式化时间戳为可读字符串"""
    if not timestamp:
        return "未知"

    import datetime

    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
