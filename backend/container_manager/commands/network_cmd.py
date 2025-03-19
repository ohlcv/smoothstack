#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络管理命令行接口

提供容器网络配置和管理的命令行工具
"""

import os
import json
import click
import logging
from typing import Optional, List, Dict, Any
from tabulate import tabulate

from ..network_manager import NetworkManager
from ..models.service_group import ServiceNetwork, NetworkMode

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.commands.network_cmd")


@click.group(name="network", help="容器网络管理")
def network_cmd_group():
    """网络管理命令组"""
    pass


@network_cmd_group.command(name="list", help="列出网络")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--label", "-l", multiple=True, help="过滤标签，格式: KEY=VALUE")
def list_networks(verbose: bool, label: List[str]):
    """列出网络"""
    network_manager = NetworkManager()

    # 解析标签过滤
    filter_labels = {}
    for label_str in label:
        if "=" in label_str:
            key, value = label_str.split("=", 1)
            filter_labels[key] = value

    networks = network_manager.list_networks(filter_labels)

    if not networks:
        click.echo("未发现网络")
        return

    # 显示网络信息
    rows = []
    for network in networks:
        if verbose:
            # 详细模式
            subnet = ""
            gateway = ""
            ipam = network.get("ipam", {})
            if ipam and "Config" in ipam and ipam["Config"]:
                subnet = ipam["Config"][0].get("Subnet", "")
                gateway = ipam["Config"][0].get("Gateway", "")

            row = [
                network["name"],
                network["id"][:12],
                network["driver"],
                "是" if network["internal"] else "否",
                network["containers"],
                subnet,
                gateway,
            ]
            rows.append(row)
        else:
            # 简略模式
            row = [
                network["name"],
                network["id"][:12],
                network["driver"],
                "是" if network["internal"] else "否",
                network["containers"],
            ]
            rows.append(row)

    if verbose:
        headers = ["名称", "ID", "驱动", "内部网络", "容器数", "子网", "网关"]
    else:
        headers = ["名称", "ID", "驱动", "内部网络", "容器数"]

    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


@network_cmd_group.command(name="create", help="创建网络")
@click.argument("name", required=True)
@click.option("--driver", "-d", default="bridge", help="网络驱动")
@click.option("--subnet", "-s", help="子网")
@click.option("--gateway", "-g", help="网关")
@click.option("--internal", "-i", is_flag=True, help="内部网络，不连接外部")
@click.option("--ipv6", is_flag=True, help="启用IPv6")
@click.option("--template", "-t", help="使用模板创建")
@click.option("--option", "-o", multiple=True, help="驱动选项，格式: KEY=VALUE")
@click.option("--label", "-l", multiple=True, help="网络标签，格式: KEY=VALUE")
def create_network(
    name: str,
    driver: str,
    subnet: Optional[str],
    gateway: Optional[str],
    internal: bool,
    ipv6: bool,
    template: Optional[str],
    option: List[str],
    label: List[str],
):
    """创建网络"""
    network_manager = NetworkManager()

    # 解析选项和标签
    options = {}
    for opt_str in option:
        if "=" in opt_str:
            key, value = opt_str.split("=", 1)
            options[key] = value

    labels = {}
    for label_str in label:
        if "=" in label_str:
            key, value = label_str.split("=", 1)
            labels[key] = value

    if template:
        # 从模板创建
        click.echo(f"从模板 '{template}' 创建网络: {name}")
        success, message, network_id = network_manager.create_network_from_template(
            template_name=template,
            network_name=name,
            subnet=subnet,
            gateway=gateway,
            custom_options=options,
        )
        click.echo(message)
    else:
        # 直接创建
        network = ServiceNetwork(
            name=name,
            driver=driver,
            subnet=subnet,
            gateway=gateway,
            internal=internal,
            enable_ipv6=ipv6,
            labels=labels,
        )

        click.echo(f"创建网络: {name}")
        success, message, network_id = network_manager.create_network(network)
        click.echo(message)


@network_cmd_group.command(name="delete", help="删除网络")
@click.argument("name", required=True)
def delete_network(name: str):
    """删除网络"""
    network_manager = NetworkManager()

    click.echo(f"删除网络: {name}")
    success, message = network_manager.delete_network(name)
    click.echo(message)


@network_cmd_group.command(name="inspect", help="查看网络详情")
@click.argument("name", required=True)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="输出格式",
)
def inspect_network(name: str, format: str):
    """查看网络详情"""
    network_manager = NetworkManager()

    details = network_manager.get_network_details(name)
    if not details:
        click.echo(f"网络不存在: {name}")
        return

    if format == "json":
        click.echo(json.dumps(details, indent=2, ensure_ascii=False))
    else:
        click.echo(f"网络: {details['name']}")
        click.echo(f"ID: {details['id']}")
        click.echo(f"驱动: {details['driver']}")
        click.echo(f"范围: {details['scope']}")
        click.echo(f"内部网络: {'是' if details['internal'] else '否'}")

        if "subnet" in details:
            click.echo(f"子网: {details['subnet']}")
        if "gateway" in details:
            click.echo(f"网关: {details['gateway']}")

        # 显示容器连接信息
        if details.get("connected_containers"):
            click.echo("\n连接的容器:")
            container_rows = []
            for name, container in details["connected_containers"].items():
                container_rows.append(
                    [
                        name,
                        container["id"][:12],
                        container["ipv4_address"],
                        container["mac_address"],
                    ]
                )

            click.echo(
                tabulate(
                    container_rows,
                    headers=["容器名", "容器ID", "IPv4地址", "MAC地址"],
                    tablefmt="grid",
                )
            )
        else:
            click.echo("\n无容器连接到此网络")


@network_cmd_group.command(name="connect", help="将容器连接到网络")
@click.argument("network", required=True)
@click.argument("container", required=True)
@click.option("--ip", help="指定容器在此网络中的IP地址")
@click.option("--alias", "-a", multiple=True, help="容器在此网络中的别名")
def connect_container(
    network: str, container: str, ip: Optional[str], alias: List[str]
):
    """将容器连接到网络"""
    network_manager = NetworkManager()

    click.echo(f"将容器 {container} 连接到网络 {network}")
    success, message = network_manager.connect_container(
        network_name=network,
        container_name=container,
        ipv4_address=ip,
        aliases=alias if alias else None,
    )
    click.echo(message)


@network_cmd_group.command(name="disconnect", help="从网络断开容器")
@click.argument("network", required=True)
@click.argument("container", required=True)
def disconnect_container(network: str, container: str):
    """从网络断开容器"""
    network_manager = NetworkManager()

    click.echo(f"从网络 {network} 断开容器 {container}")
    success, message = network_manager.disconnect_container(
        network_name=network, container_name=container
    )
    click.echo(message)


@network_cmd_group.command(name="check", help="检查容器间的网络连接")
@click.argument("source", required=True)
@click.argument("target", required=True)
def check_connectivity(source: str, target: str):
    """检查容器间的网络连接"""
    network_manager = NetworkManager()

    click.echo(f"检查容器 {source} 到 {target} 的连接")
    success, message = network_manager.check_network_connectivity(
        source_container=source, target_container=target
    )

    if success:
        click.secho(message, fg="green")
    else:
        click.secho(message, fg="red")


@network_cmd_group.group(name="template", help="网络模板管理")
def template_group():
    """网络模板管理命令组"""
    pass


@template_group.command(name="list", help="列出网络模板")
def list_templates():
    """列出网络模板"""
    network_manager = NetworkManager()

    templates = network_manager.list_templates()

    if not templates:
        click.echo("未发现网络模板")
        return

    # 显示模板信息
    rows = []
    for template in templates:
        row = [
            template.get("name", ""),
            template.get("description", ""),
            template.get("driver", "bridge"),
            template.get("subnet", ""),
            "是" if template.get("internal", False) else "否",
        ]
        rows.append(row)

    headers = ["名称", "描述", "驱动", "子网", "内部网络"]
    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


@template_group.command(name="show", help="查看网络模板详情")
@click.argument("name", required=True)
def show_template(name: str):
    """查看网络模板详情"""
    network_manager = NetworkManager()

    template = network_manager.get_template(name)
    if not template:
        click.echo(f"网络模板不存在: {name}")
        return

    click.echo(json.dumps(template, indent=2, ensure_ascii=False))


@template_group.command(name="create", help="创建网络模板")
@click.argument("name", required=True)
@click.option("--description", "-d", help="模板描述")
@click.option("--driver", default="bridge", help="网络驱动")
@click.option("--subnet", "-s", help="子网")
@click.option("--gateway", "-g", help="网关")
@click.option("--internal", "-i", is_flag=True, help="内部网络，不连接外部")
@click.option("--ipv6", is_flag=True, help="启用IPv6")
@click.option("--option", "-o", multiple=True, help="驱动选项，格式: KEY=VALUE")
@click.option("--label", "-l", multiple=True, help="网络标签，格式: KEY=VALUE")
def create_template(
    name: str,
    description: Optional[str],
    driver: str,
    subnet: Optional[str],
    gateway: Optional[str],
    internal: bool,
    ipv6: bool,
    option: List[str],
    label: List[str],
):
    """创建网络模板"""
    network_manager = NetworkManager()

    # 解析选项和标签
    options = {}
    for opt_str in option:
        if "=" in opt_str:
            key, value = opt_str.split("=", 1)
            options[key] = value

    labels = {}
    for label_str in label:
        if "=" in label_str:
            key, value = label_str.split("=", 1)
            labels[key] = value

    # 添加标准标签
    labels["smoothstack.network_type"] = name
    if description:
        labels["smoothstack.description"] = description

    # 创建模板数据
    template_data = {
        "name": name,
        "description": description or f"网络模板 {name}",
        "driver": driver,
        "internal": internal,
        "enable_ipv6": ipv6,
        "options": options,
        "labels": labels,
    }

    if subnet:
        template_data["subnet"] = subnet
    if gateway:
        template_data["gateway"] = gateway

    # 保存模板
    if network_manager.save_template(template_data):
        click.echo(f"已创建网络模板: {name}")
    else:
        click.echo(f"创建网络模板失败: {name}")


@template_group.command(name="delete", help="删除网络模板")
@click.argument("name", required=True)
def delete_template(name: str):
    """删除网络模板"""
    network_manager = NetworkManager()

    if network_manager.delete_template(name):
        click.echo(f"已删除网络模板: {name}")
    else:
        click.echo(f"删除网络模板失败: {name}")


@template_group.command(name="import", help="从文件导入网络模板")
@click.argument("file_path", required=True, type=click.Path(exists=True))
def import_template(file_path: str):
    """从文件导入网络模板"""
    network_manager = NetworkManager()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)

        if not isinstance(template_data, dict) or "name" not in template_data:
            click.echo("文件格式错误，需要包含name字段的JSON对象")
            return

        if network_manager.save_template(template_data):
            click.echo(f"已导入网络模板: {template_data['name']}")
        else:
            click.echo(f"导入网络模板失败")
    except Exception as e:
        click.echo(f"导入失败: {e}")


@template_group.command(name="export", help="导出网络模板到文件")
@click.argument("name", required=True)
@click.argument("file_path", required=True)
def export_template(name: str, file_path: str):
    """导出网络模板到文件"""
    network_manager = NetworkManager()

    template = network_manager.get_template(name)
    if not template:
        click.echo(f"网络模板不存在: {name}")
        return

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        click.echo(f"已导出网络模板到: {file_path}")
    except Exception as e:
        click.echo(f"导出失败: {e}")
