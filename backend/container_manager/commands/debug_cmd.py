#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器内调试命令行界面

提供容器内应用程序调试配置和管理的命令行功能
"""

import os
import sys
import click
import json
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from backend.container_manager.debug_manager import get_debug_manager

# 配置日志
import logging

logger = logging.getLogger("smoothstack.container_manager.commands.debug_cmd")


@click.group(name="debug", help="容器内调试管理")
def debug_cmd_group():
    """容器内调试管理命令组"""
    pass


@debug_cmd_group.command(name="configure-python", help="配置Python应用调试环境")
@click.argument("container_name", required=True)
@click.option("--port", "-p", type=int, default=5678, help="调试器端口")
@click.option("--source-root", "-s", default="/app", help="容器内源代码根目录")
@click.option("--host-root", "-h", help="主机源代码根目录，默认为当前目录")
@click.option(
    "--auto-reload/--no-auto-reload", default=True, help="是否在代码修改后自动重载"
)
def configure_python(container_name, port, source_root, host_root, auto_reload):
    """配置Python应用的调试环境"""
    debug_manager = get_debug_manager()

    success = debug_manager.configure_python_debug(
        container_name=container_name,
        debug_port=port,
        source_root=source_root,
        host_source_root=host_root,
        auto_reload=auto_reload,
    )

    if success:
        click.secho(f"成功配置容器 '{container_name}' 的Python调试环境", fg="green")
        click.echo(f"调试端口: {port}")
        click.echo(f"容器源码路径: {source_root}")
        click.echo(f"主机源码路径: {host_root or os.getcwd()}")
        click.echo(f"自动重载: {'启用' if auto_reload else '禁用'}")
    else:
        click.secho(f"配置容器 '{container_name}' 的Python调试环境失败", fg="red")


@debug_cmd_group.command(name="configure-node", help="配置Node.js应用调试环境")
@click.argument("container_name", required=True)
@click.option("--port", "-p", type=int, default=9229, help="调试器端口")
@click.option("--source-root", "-s", default="/app", help="容器内源代码根目录")
@click.option("--host-root", "-h", help="主机源代码根目录，默认为当前目录")
@click.option("--inspector/--legacy", default=True, help="使用Node.js Inspector协议")
def configure_node(container_name, port, source_root, host_root, inspector):
    """配置Node.js应用的调试环境"""
    debug_manager = get_debug_manager()

    success = debug_manager.configure_node_debug(
        container_name=container_name,
        debug_port=port,
        source_root=source_root,
        host_source_root=host_root,
        inspector=inspector,
    )

    if success:
        click.secho(f"成功配置容器 '{container_name}' 的Node.js调试环境", fg="green")
        click.echo(f"调试端口: {port}")
        click.echo(f"容器源码路径: {source_root}")
        click.echo(f"主机源码路径: {host_root or os.getcwd()}")
        click.echo(f"调试协议: {'Inspector' if inspector else 'Legacy'}")
    else:
        click.secho(f"配置容器 '{container_name}' 的Node.js调试环境失败", fg="red")


@debug_cmd_group.command(name="list", help="列出所有调试配置")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_configs(json_output):
    """列出所有调试配置"""
    debug_manager = get_debug_manager()
    configs = debug_manager.list_debug_configs()

    if json_output:
        click.echo(json.dumps(configs, indent=2, ensure_ascii=False))
        return

    if not configs:
        click.echo("未找到调试配置")
        return

    # 格式化表格输出
    table_data = []
    for config in configs:
        container_name = config["container_name"]
        debug_config = config["config"]
        debug_type = debug_config["type"]

        table_data.append(
            [
                container_name,
                debug_type.upper(),
                debug_config["debug_port"],
                debug_config["source_root"],
                debug_config["host_source_root"],
            ]
        )

    headers = ["容器名称", "类型", "调试端口", "容器源码路径", "主机源码路径"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@debug_cmd_group.command(name="show", help="查看调试配置详情")
@click.argument("container_name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def show_config(container_name, json_output):
    """查看调试配置详情"""
    debug_manager = get_debug_manager()
    config = debug_manager.get_debug_config(container_name)

    if not config:
        click.secho(f"容器 '{container_name}' 没有调试配置", fg="red")
        return

    if json_output:
        click.echo(json.dumps(config, indent=2, ensure_ascii=False))
        return

    # 显示基本信息
    click.secho(f"容器: {container_name}", bold=True)
    click.echo(f"类型: {config['type'].upper()}")
    click.echo(f"调试端口: {config['debug_port']}")
    click.echo(f"容器源码路径: {config['source_root']}")
    click.echo(f"主机源码路径: {config['host_source_root']}")

    # 显示类型特定配置
    if config["type"] == "python":
        click.echo(f"自动重载: {'启用' if config.get('auto_reload', True) else '禁用'}")
    elif config["type"] == "node":
        click.echo(
            f"调试协议: {'Inspector' if config.get('inspector', True) else 'Legacy'}"
        )


@debug_cmd_group.command(name="generate-vscode", help="生成VS Code调试配置")
@click.argument("container_name", required=True)
@click.option(
    "--output", "-o", help="输出文件路径，默认为当前目录下的.vscode/launch.json"
)
def generate_vscode(container_name, output):
    """生成VS Code调试配置"""
    debug_manager = get_debug_manager()

    output_path = debug_manager.generate_vscode_launch(
        container_name=container_name,
        output_path=output,
    )

    if output_path:
        click.secho(f"成功生成VS Code调试配置: {output_path}", fg="green")
        click.echo("请在VS Code中使用此配置连接到容器进行调试")
    else:
        click.secho(f"生成VS Code调试配置失败", fg="red")


@debug_cmd_group.command(name="generate-pycharm", help="生成PyCharm调试配置")
@click.argument("container_name", required=True)
@click.option("--output", "-o", help="输出目录路径，默认为当前目录下的.idea")
def generate_pycharm(container_name, output):
    """生成PyCharm调试配置"""
    debug_manager = get_debug_manager()

    output_path = debug_manager.generate_pycharm_config(
        container_name=container_name,
        output_path=output,
    )

    if output_path:
        click.secho(f"成功生成PyCharm调试配置提示", fg="green")
    else:
        click.secho(f"生成PyCharm调试配置失败", fg="red")


@debug_cmd_group.command(name="start", help="启动调试会话")
@click.argument("container_name", required=True)
@click.option("--module", "-m", help="应用模块名或入口文件")
def start_debug(container_name, module):
    """启动调试会话"""
    debug_manager = get_debug_manager()

    success = debug_manager.start_debug_session(
        container_name=container_name,
        app_module=module or "",
    )

    if success:
        click.secho(f"成功启动容器 '{container_name}' 的调试会话", fg="green")
        click.echo("请使用您的开发工具连接到调试会话")
    else:
        click.secho(f"启动容器 '{container_name}' 的调试会话失败", fg="red")


@debug_cmd_group.command(name="remove", help="移除调试配置")
@click.argument("container_name", required=True)
@click.confirmation_option(prompt="确定要移除此调试配置吗?")
def remove_config(container_name):
    """移除调试配置"""
    debug_manager = get_debug_manager()

    success = debug_manager.remove_debug_config(container_name)

    if success:
        click.secho(f"成功移除容器 '{container_name}' 的调试配置", fg="green")
    else:
        click.secho(f"移除容器 '{container_name}' 的调试配置失败", fg="red")
