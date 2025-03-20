#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务编排命令行接口

提供服务组管理的命令行工具
"""

import os
import sys
import click
import yaml
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
from tabulate import tabulate

from backend.config import config
from ..service_orchestrator import ServiceOrchestrator
from ..models.service_group import ServiceGroup, ServiceStatus

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.commands.service_cmd")


@click.group(name="service", help="多容器服务管理")
def service_cmd_group():
    """服务编排命令组"""
    pass


@service_cmd_group.command(name="list", help="列出所有服务组")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def list_services(verbose: bool):
    """列出所有服务组"""
    orchestrator = ServiceOrchestrator()
    service_groups = orchestrator.list_service_groups()

    if not service_groups:
        click.echo("未发现服务组配置")
        return

    # 获取服务组状态
    rows = []
    for sg in service_groups:
        status, service_statuses = orchestrator.get_service_group_status(sg.name)
        service_count = len(sg.services)
        network_count = len(sg.networks)

        if verbose:
            # 详细输出模式
            row = [
                sg.name,
                sg.description or "",
                status.name if status else "UNKNOWN",
                service_count,
                network_count,
                sg.version or "",
                ", ".join(service_statuses.keys()),
            ]
            rows.append(row)
        else:
            # 简略输出模式
            row = [
                sg.name,
                sg.description or "",
                status.name if status else "UNKNOWN",
                service_count,
                network_count,
            ]
            rows.append(row)

    if verbose:
        headers = ["名称", "描述", "状态", "服务数", "网络数", "版本", "服务"]
    else:
        headers = ["名称", "描述", "状态", "服务数", "网络数"]

    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


@service_cmd_group.command(name="create", help="创建新服务组")
@click.argument("name", required=True)
@click.option("--description", "-d", help="服务组描述")
@click.option("--version", "-v", default="1.0", help="服务组版本")
@click.option("--from-compose", "-f", help="从Docker Compose文件导入")
def create_service_group(
    name: str, description: Optional[str], version: str, from_compose: Optional[str]
):
    """创建新服务组"""
    orchestrator = ServiceOrchestrator()

    # 检查是否已存在
    if orchestrator.get_service_group(name):
        click.echo(f"服务组已存在: {name}")
        return

    if from_compose:
        # 从Docker Compose文件导入
        if not os.path.exists(from_compose):
            click.echo(f"Compose文件不存在: {from_compose}")
            return

        click.echo(f"从Compose文件导入服务组: {from_compose}")
        success, message = orchestrator.import_from_compose_file(from_compose, name)
        click.echo(message)
    else:
        # 创建空服务组
        service_group = ServiceGroup(
            name=name,
            description=description or f"服务组 {name}",
            version=version,
        )

        if orchestrator.save_service_group(service_group):
            click.echo(f"已创建服务组: {name}")
        else:
            click.echo(f"创建服务组失败: {name}")


@service_cmd_group.command(name="delete", help="删除服务组")
@click.argument("name", required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除，同时移除所有相关容器")
def delete_service_group(name: str, force: bool):
    """删除服务组"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    if force:
        # 先移除所有容器
        click.echo(f"移除服务组相关资源: {name}")
        success, messages = orchestrator.remove_service_group(name)
        for message in messages:
            click.echo(f"  - {message}")

    # 删除配置
    if orchestrator.delete_service_group(name):
        click.echo(f"已删除服务组: {name}")
    else:
        click.echo(f"删除服务组失败: {name}")


@service_cmd_group.command(name="deploy", help="部署服务组")
@click.argument("name", required=True)
def deploy_service_group(name: str):
    """部署服务组"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    click.echo(f"部署服务组: {name}")
    success, messages = orchestrator.deploy_service_group(service_group)
    for message in messages:
        click.echo(f"  - {message}")

    if success:
        click.echo(f"服务组部署成功: {name}")
    else:
        click.echo(f"服务组部署部分失败: {name}")


@service_cmd_group.command(name="start", help="启动服务组")
@click.argument("name", required=True)
def start_service_group(name: str):
    """启动服务组"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    click.echo(f"启动服务组: {name}")
    success, messages = orchestrator.start_service_group(name)
    for message in messages:
        click.echo(f"  - {message}")

    if success:
        click.echo(f"服务组启动成功: {name}")
    else:
        click.echo(f"服务组启动部分失败: {name}")


@service_cmd_group.command(name="stop", help="停止服务组")
@click.argument("name", required=True)
@click.option("--timeout", "-t", type=int, help="停止超时时间（秒）")
def stop_service_group(name: str, timeout: Optional[int]):
    """停止服务组"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    click.echo(f"停止服务组: {name}")
    success, messages = orchestrator.stop_service_group(name, timeout)
    for message in messages:
        click.echo(f"  - {message}")

    if success:
        click.echo(f"服务组停止成功: {name}")
    else:
        click.echo(f"服务组停止部分失败: {name}")


@service_cmd_group.command(name="remove", help="移除服务组相关容器")
@click.argument("name", required=True)
@click.option("--volumes", "-v", is_flag=True, help="同时移除卷")
def remove_service_group(name: str, volumes: bool):
    """移除服务组相关容器"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    click.echo(f"移除服务组相关容器: {name}")
    success, messages = orchestrator.remove_service_group(name, volumes)
    for message in messages:
        click.echo(f"  - {message}")

    if success:
        click.echo(f"服务组容器移除成功: {name}")
    else:
        click.echo(f"服务组容器移除部分失败: {name}")


@service_cmd_group.command(name="status", help="查看服务组状态")
@click.argument("name", required=True)
def service_group_status(name: str):
    """查看服务组状态"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    status, service_statuses = orchestrator.get_service_group_status(name)

    click.echo(f"服务组: {name}")
    click.echo(f"描述: {service_group.description}")
    click.echo(f"版本: {service_group.version}")
    click.echo(f"状态: {status.name}")

    # 显示服务状态
    if service_statuses:
        click.echo("\n服务状态:")
        service_rows = []
        for service_name, status in service_statuses.items():
            service = service_group.services.get(service_name)
            if service:
                service_rows.append(
                    [
                        service_name,
                        status.upper(),
                        service.image,
                        service.container_name or f"<自动生成>",
                    ]
                )

        click.echo(
            tabulate(
                service_rows,
                headers=["服务", "状态", "镜像", "容器名"],
                tablefmt="grid",
            )
        )

    # 显示网络状态
    if service_group.networks:
        click.echo("\n网络:")
        network_rows = []
        for network_name, network in service_group.networks.items():
            # 获取网络状态
            network_stats = orchestrator.get_network_stats(network.name)
            if network_stats:
                network_rows.append(
                    [
                        network.name,
                        network.driver,
                        network_stats.get("subnet") or "<未设置>",
                        network_stats.get("containers", 0),
                    ]
                )
            else:
                network_rows.append(
                    [
                        network.name,
                        network.driver,
                        network.subnet or "<未设置>",
                        "未创建",
                    ]
                )

        click.echo(
            tabulate(
                network_rows,
                headers=["网络", "驱动", "子网", "容器数"],
                tablefmt="grid",
            )
        )


@service_cmd_group.command(name="edit", help="编辑服务组配置")
@click.argument("name", required=True)
def edit_service_group(name: str):
    """编辑服务组配置"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    # 获取服务组配置文件路径
    service_groups_dir = config.get("service_orchestrator.service_groups_dir")
    if not service_groups_dir:
        click.echo("未配置服务组目录")
        return

    file_path = os.path.join(service_groups_dir, f"{name}.yaml")
    if not os.path.exists(file_path):
        click.echo(f"配置文件不存在: {file_path}")
        return

    # 使用环境变量中的编辑器打开文件
    editor = os.environ.get("EDITOR", "vim")
    click.echo(f"使用 {editor} 编辑配置文件: {file_path}")

    os.system(f"{editor} {file_path}")

    # 重新加载服务组
    orchestrator.load_service_groups()
    click.echo(f"服务组配置已重新加载")


@service_cmd_group.command(name="inspect", help="查看服务组配置详情")
@click.argument("name", required=True)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="输出格式",
)
def inspect_service_group(name: str, format: str):
    """查看服务组配置详情"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    # 转换为字典
    data = service_group.to_dict()

    if format == "json":
        import json

        output = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        output = yaml.dump(data, default_flow_style=False, allow_unicode=True)

    click.echo(output)


@service_cmd_group.command(name="export", help="导出服务组配置")
@click.argument("name", required=True)
@click.option("--output", "-o", required=True, help="输出文件路径")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="输出格式",
)
def export_service_group(name: str, output: str, format: str):
    """导出服务组配置"""
    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    # 转换为字典
    data = service_group.to_dict()

    try:
        with open(output, "w", encoding="utf-8") as f:
            if format == "json":
                import json

                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        click.echo(f"已导出服务组配置到: {output}")
    except Exception as e:
        click.echo(f"导出失败: {e}")


@service_cmd_group.command(name="import", help="导入服务组配置")
@click.argument("file_path", required=True, type=click.Path(exists=True))
@click.option("--name", "-n", help="自定义服务组名称")
def import_service_group(file_path: str, name: Optional[str]):
    """导入服务组配置"""
    orchestrator = ServiceOrchestrator()

    # 检查文件格式
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in [".yml", ".yaml"]:
        # 判断是否为Docker Compose文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if "services" in data:
                # 看起来是Docker Compose文件
                click.echo(f"检测到Docker Compose文件格式，将使用Compose导入功能")
                success, message = orchestrator.import_from_compose_file(
                    file_path, name
                )
                click.echo(message)
                return
        except Exception as e:
            click.echo(f"读取文件失败: {e}")
            return

    # 尝试直接导入服务组配置
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if file_ext == ".json":
                import json

                data = json.load(f)
            else:
                data = yaml.safe_load(f)

        if not data:
            click.echo("配置文件为空或格式错误")
            return

        # 使用文件中的名称或自定义名称
        group_name = name or data.get("name")
        if not group_name:
            click.echo("未指定服务组名称，且配置文件中未包含名称")
            return

        # 检查是否已存在
        if orchestrator.get_service_group(group_name) and not click.confirm(
            f"服务组 {group_name} 已存在，是否覆盖?"
        ):
            return

        # 创建服务组
        service_group = ServiceGroup.from_dict(data)
        if name:
            service_group.name = name

        if orchestrator.save_service_group(service_group):
            click.echo(f"已导入服务组: {service_group.name}")
        else:
            click.echo("导入服务组失败")

    except Exception as e:
        click.echo(f"导入失败: {e}")


@service_cmd_group.command(name="logs", help="查看服务组日志")
@click.argument("name", required=True)
@click.argument("service", required=False)
@click.option("--tail", "-n", type=int, default=100, help="显示最后N行日志")
@click.option("--follow", "-f", is_flag=True, help="持续显示日志")
def service_logs(name: str, service: Optional[str], tail: int, follow: bool):
    """查看服务组日志"""
    import docker

    orchestrator = ServiceOrchestrator()

    # 检查是否存在
    service_group = orchestrator.get_service_group(name)
    if not service_group:
        click.echo(f"服务组不存在: {name}")
        return

    # 初始化Docker客户端
    try:
        docker_client = docker.from_env()
    except Exception as e:
        click.echo(f"Docker客户端初始化失败: {e}")
        return

    container_prefix = config.get("service_orchestrator.container_prefix", "sms_")

    # 获取容器名称
    if service:
        # 查看单个服务的日志
        if service not in service_group.services:
            click.echo(f"服务不存在: {service}")
            return

        container_name = service_group.services[service].container_name
        if not container_name:
            container_name = f"{container_prefix}{name}_{service}"

        try:
            container = docker_client.containers.get(container_name)
            logs = container.logs(tail=tail, stream=follow).decode("utf-8")
            if follow:
                # 持续显示日志
                for line in logs:
                    click.echo(line, nl=False)
            else:
                # 一次性显示日志
                click.echo(logs)
        except Exception as e:
            click.echo(f"获取容器日志失败: {e}")

    else:
        # 查看所有服务的日志
        click.echo(f"显示服务组 {name} 的所有服务日志")

        for service_name, service_obj in service_group.services.items():
            container_name = service_obj.container_name
            if not container_name:
                container_name = f"{container_prefix}{name}_{service_name}"

            try:
                container = docker_client.containers.get(container_name)
                logs = container.logs(tail=tail).decode("utf-8")

                click.echo(f"\n=== 服务: {service_name} ===")
                click.echo(logs)
            except docker.errors.NotFound:
                click.echo(f"\n=== 服务: {service_name} ===")
                click.echo("容器不存在或未启动")
            except Exception as e:
                click.echo(f"\n=== 服务: {service_name} ===")
                click.echo(f"获取容器日志失败: {e}")
