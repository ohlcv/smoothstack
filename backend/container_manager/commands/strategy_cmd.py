#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多容器策略管理命令行界面

提供策略创建、部署、管理相关的命令行功能
"""

import os
import sys
import click
import json
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from backend.container_manager.strategy_manager import get_strategy_manager

# 配置日志
import logging

logger = logging.getLogger("smoothstack.container_manager.commands.strategy_cmd")


@click.group(name="strategy", help="多容器策略管理")
def strategy_cmd_group():
    """多容器策略管理命令组"""
    pass


@strategy_cmd_group.command(name="list", help="列出所有部署策略")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_strategies(json_output):
    """列出所有部署策略"""
    strategy_manager = get_strategy_manager()
    strategies = strategy_manager.list_strategies()

    if json_output:
        click.echo(json.dumps(strategies, indent=2, ensure_ascii=False))
        return

    if not strategies:
        click.echo("未找到部署策略")
        return

    # 格式化表格输出
    table_data = []
    for strategy in strategies:
        container_count = len(strategy.get("container_configs", []))
        dependency_count = sum(
            len(deps) for deps in strategy.get("dependency_graph", {}).values()
        )

        table_data.append(
            [
                strategy.get("name"),
                strategy.get("description") or "无描述",
                container_count,
                dependency_count,
                strategy.get("restart_policy", "unless-stopped"),
            ]
        )

    headers = ["名称", "描述", "容器数量", "依赖关系数", "重启策略"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@strategy_cmd_group.command(name="create", help="创建新部署策略")
@click.argument("name", required=True)
@click.option("--description", "-d", help="策略描述")
@click.option(
    "--restart-policy",
    "-r",
    default="unless-stopped",
    type=click.Choice(["no", "always", "on-failure", "unless-stopped"]),
    help="容器重启策略",
)
@click.option("--template", "-t", help="从JSON文件导入策略模板")
def create_strategy(name, description, restart_policy, template):
    """创建新部署策略"""
    strategy_manager = get_strategy_manager()

    # 检查策略是否已存在
    existing = strategy_manager.get_strategy(name)
    if existing:
        click.secho(f"策略 '{name}' 已存在", fg="red")
        return

    # 从模板文件加载配置
    container_configs = []
    resource_policy = {}
    dependency_graph = {}
    labels = {}

    if template:
        try:
            with open(template, "r", encoding="utf-8") as f:
                template_data = json.load(f)

                # 提取模板数据
                container_configs = template_data.get("container_configs", [])
                resource_policy = template_data.get("resource_policy", {})
                dependency_graph = template_data.get("dependency_graph", {})
                labels = template_data.get("labels", {})

                # 可以从模板覆盖描述和重启策略
                if not description and "description" in template_data:
                    description = template_data["description"]

                if "restart_policy" in template_data:
                    restart_policy = template_data["restart_policy"]

            click.secho(f"从模板 {template} 加载配置成功", fg="green")
        except Exception as e:
            click.secho(f"从模板加载配置失败: {e}", fg="red")
            return

    try:
        strategy = strategy_manager.create_strategy(
            name=name,
            description=description or "",
            container_configs=container_configs,
            resource_policy=resource_policy,
            dependency_graph=dependency_graph,
            labels=labels,
            restart_policy=restart_policy,
        )

        click.secho(f"成功创建策略 '{name}'", fg="green")

        # 如果没有容器配置，提示用户添加
        if not container_configs:
            click.echo("策略创建成功，但没有容器配置。")
            click.echo(
                f"使用 'strategy add-container {name} <container_name> <image>' 添加容器配置"
            )

    except Exception as e:
        click.secho(f"创建策略失败: {e}", fg="red")


@strategy_cmd_group.command(name="show", help="查看策略详情")
@click.argument("name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def show_strategy(name, json_output):
    """查看策略详情"""
    strategy_manager = get_strategy_manager()
    strategy = strategy_manager.get_strategy(name)

    if not strategy:
        click.secho(f"策略 '{name}' 不存在", fg="red")
        return

    strategy_dict = strategy.to_dict()

    if json_output:
        click.echo(json.dumps(strategy_dict, indent=2, ensure_ascii=False))
        return

    # 基本信息
    click.secho(f"策略: {strategy_dict['name']}", bold=True)
    click.echo(f"描述: {strategy_dict['description'] or '无'}")
    click.echo(f"重启策略: {strategy_dict['restart_policy']}")

    # 容器配置
    click.secho("\n容器配置:", bold=True)
    if not strategy_dict["container_configs"]:
        click.echo("  无容器配置")
    else:
        container_table = []
        for config in strategy_dict["container_configs"]:
            ports = config.get("ports", [])
            if isinstance(ports, list):
                ports_str = ", ".join(str(p) for p in ports)
            else:
                ports_str = str(ports)

            volumes = config.get("volumes", [])
            if isinstance(volumes, list):
                volumes_str = ", ".join(str(v) for v in volumes)
            else:
                volumes_str = str(volumes)

            container_table.append(
                [
                    config.get("name", ""),
                    config.get("image", ""),
                    ports_str,
                    volumes_str,
                    "是" if config.get("is_critical", False) else "否",
                ]
            )

        headers = ["名称", "镜像", "端口", "卷", "关键容器"]
        click.echo(tabulate(container_table, headers=headers, tablefmt="grid"))

    # 依赖关系
    click.secho("\n依赖关系:", bold=True)
    if not strategy_dict["dependency_graph"]:
        click.echo("  无依赖关系")
    else:
        for container, dependencies in strategy_dict["dependency_graph"].items():
            if dependencies:
                click.echo(f"  {container} 依赖: {', '.join(dependencies)}")
            else:
                click.echo(f"  {container} 无依赖")

    # 资源策略
    click.secho("\n资源策略:", bold=True)
    resource_policy = strategy_dict["resource_policy"]

    # 全局限制
    click.echo("  全局资源限制:")
    global_limits = resource_policy.get("global_limits", {})
    if global_limits:
        for resource, limit in global_limits.items():
            click.echo(f"    {resource}: {limit}")
    else:
        click.echo("    无全局限制")

    # 容器特定限制
    click.echo("  容器特定资源限制:")
    container_limits = resource_policy.get("container_specific_limits", {})
    if container_limits:
        for container, limits in container_limits.items():
            click.echo(f"    {container}:")
            for resource, limit in limits.items():
                click.echo(f"      {resource}: {limit}")
    else:
        click.echo("    无容器特定限制")

    # 标签
    if strategy_dict.get("labels"):
        click.secho("\n标签:", bold=True)
        for key, value in strategy_dict["labels"].items():
            click.echo(f"  {key}: {value}")


@strategy_cmd_group.command(name="delete", help="删除部署策略")
@click.argument("name", required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除，即使有活跃部署")
@click.confirmation_option(prompt="确定要删除此策略吗?")
def delete_strategy(name, force):
    """删除部署策略"""
    strategy_manager = get_strategy_manager()

    # 检查策略是否存在
    if not strategy_manager.get_strategy(name):
        click.secho(f"策略 '{name}' 不存在", fg="red")
        return

    # 检查是否有活跃部署
    if not force:
        deployments = strategy_manager.list_strategy_deployments()
        active_deployments = [d for d in deployments if d.get("strategy_name") == name]

        if active_deployments:
            deployment_names = [d.get("deployment_name") for d in active_deployments]
            click.secho(
                f"策略 '{name}' 有活跃部署: {', '.join(deployment_names)}", fg="yellow"
            )
            click.echo("使用 --force 选项强制删除，或先删除相关部署")
            return

    # 删除策略
    success = strategy_manager.delete_strategy(name)
    if success:
        click.secho(f"成功删除策略 '{name}'", fg="green")
    else:
        click.secho(f"删除策略 '{name}' 失败", fg="red")


@strategy_cmd_group.command(name="add-container", help="向策略添加容器配置")
@click.argument("strategy_name", required=True)
@click.argument("container_name", required=True)
@click.argument("image", required=True)
@click.option("--command", "-c", help="容器启动命令")
@click.option(
    "--port", "-p", multiple=True, help="端口映射，格式为host:container或container"
)
@click.option(
    "--volume", "-v", multiple=True, help="卷映射，格式为source:target[:mode]"
)
@click.option("--env", "-e", multiple=True, help="环境变量，格式为KEY=VALUE")
@click.option("--critical", is_flag=True, help="标记为关键容器，失败时回滚整个部署")
def add_container(
    strategy_name, container_name, image, command, port, volume, env, critical
):
    """向策略添加容器配置"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    # 解析环境变量
    environment = {}
    for env_pair in env:
        if "=" in env_pair:
            key, value = env_pair.split("=", 1)
            environment[key] = value

    # 创建容器配置
    container_config = {
        "name": container_name,
        "image": image,
        "is_critical": critical,
    }

    if command:
        container_config["command"] = command

    if port:
        container_config["ports"] = list(port)

    if volume:
        container_config["volumes"] = list(volume)

    if environment:
        container_config["environment"] = environment

    try:
        # 添加容器配置到策略
        strategy.add_container_config(container_config)

        # 保存更新后的策略
        strategy_manager.update_strategy(
            name=strategy_name,
            container_configs=strategy.container_configs,
        )

        click.secho(
            f"成功向策略 '{strategy_name}' 添加容器 '{container_name}'", fg="green"
        )

    except Exception as e:
        click.secho(f"添加容器配置失败: {e}", fg="red")


@strategy_cmd_group.command(name="remove-container", help="从策略移除容器配置")
@click.argument("strategy_name", required=True)
@click.argument("container_name", required=True)
def remove_container(strategy_name, container_name):
    """从策略移除容器配置"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    # 移除容器配置
    success = strategy.remove_container_config(container_name)
    if not success:
        click.secho(f"策略 '{strategy_name}' 中不存在容器 '{container_name}'", fg="red")
        return

    # 保存更新后的策略
    try:
        strategy_manager.update_strategy(
            name=strategy_name,
            container_configs=strategy.container_configs,
            dependency_graph=strategy.dependency_graph,  # 依赖关系也会更新
        )

        click.secho(
            f"成功从策略 '{strategy_name}' 移除容器 '{container_name}'", fg="green"
        )

    except Exception as e:
        click.secho(f"移除容器配置失败: {e}", fg="red")


@strategy_cmd_group.command(name="add-dependency", help="添加容器依赖关系")
@click.argument("strategy_name", required=True)
@click.argument("container_name", required=True)
@click.argument("depends_on", required=True)
def add_dependency(strategy_name, container_name, depends_on):
    """添加容器依赖关系"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    # 添加依赖关系
    try:
        # 支持多个依赖，用逗号分隔
        dependencies = [dep.strip() for dep in depends_on.split(",")]

        strategy.add_dependency(container_name, dependencies)

        # 保存更新后的策略
        strategy_manager.update_strategy(
            name=strategy_name,
            dependency_graph=strategy.dependency_graph,
        )

        click.secho(f"成功添加依赖关系: {container_name} -> {depends_on}", fg="green")

    except Exception as e:
        click.secho(f"添加依赖关系失败: {e}", fg="red")


@strategy_cmd_group.command(name="remove-dependency", help="移除容器依赖关系")
@click.argument("strategy_name", required=True)
@click.argument("container_name", required=True)
@click.argument("dependency", required=True)
def remove_dependency(strategy_name, container_name, dependency):
    """移除容器依赖关系"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    # 移除依赖关系
    success = strategy.remove_dependency(container_name, dependency)
    if not success:
        click.secho(f"依赖关系不存在: {container_name} -> {dependency}", fg="red")
        return

    # 保存更新后的策略
    try:
        strategy_manager.update_strategy(
            name=strategy_name,
            dependency_graph=strategy.dependency_graph,
        )

        click.secho(f"成功移除依赖关系: {container_name} -> {dependency}", fg="green")

    except Exception as e:
        click.secho(f"移除依赖关系失败: {e}", fg="red")


@strategy_cmd_group.command(name="set-resources", help="设置容器资源限制")
@click.argument("strategy_name", required=True)
@click.option("--container", "-c", help="容器名称，不指定则设置全局资源限制")
@click.option("--memory", "-m", help="内存限制，如512m, 2g")
@click.option("--cpu", help="CPU限制，如0.5, 2")
@click.option("--scale-factor", "-s", type=float, help="资源扩展因子")
def set_resources(strategy_name, container, memory, cpu, scale_factor):
    """设置容器资源限制"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    try:
        resource_policy = strategy.resource_policy

        # 设置资源限制
        if container:
            # 容器特定资源限制
            if container not in resource_policy.container_specific_limits:
                resource_policy.container_specific_limits[container] = {}

            if memory:
                resource_policy.container_specific_limits[container]["memory"] = memory

            if cpu:
                resource_policy.container_specific_limits[container]["cpu"] = cpu

            # 设置扩展因子
            if scale_factor is not None:
                resource_policy.scale_factors[container] = scale_factor

            click.secho(f"已设置容器 '{container}' 的资源限制", fg="green")
        else:
            # 全局资源限制
            if memory:
                resource_policy.global_limits["memory"] = memory

            if cpu:
                resource_policy.global_limits["cpu"] = cpu

            click.secho(f"已设置全局资源限制", fg="green")

        # 保存更新后的策略
        strategy_manager.update_strategy(
            name=strategy_name,
            resource_policy=resource_policy.to_dict(),
        )

    except Exception as e:
        click.secho(f"设置资源限制失败: {e}", fg="red")


@strategy_cmd_group.command(name="export", help="导出策略配置")
@click.argument("strategy_name", required=True)
@click.option("--output", "-o", help="输出文件路径，默认为<strategy_name>.json")
def export_strategy(strategy_name, output):
    """导出策略配置"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    # 导出策略
    try:
        output_file = output or f"{strategy_name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(strategy.to_dict(), f, indent=2, ensure_ascii=False)

        click.secho(f"策略 '{strategy_name}' 已导出到 {output_file}", fg="green")

    except Exception as e:
        click.secho(f"导出策略失败: {e}", fg="red")


#
# 部署命令
#


@strategy_cmd_group.command(name="deploy", help="部署策略")
@click.argument("strategy_name", required=True)
@click.option("--name", "-n", help="部署名称，默认使用策略名称")
@click.option("--env", "-e", multiple=True, help="环境变量，格式为container:KEY=VALUE")
@click.option("--network", help="网络名称，将所有容器连接到此网络")
def deploy_strategy(strategy_name, name, env, network):
    """部署策略"""
    strategy_manager = get_strategy_manager()

    # 获取策略
    strategy = strategy_manager.get_strategy(strategy_name)
    if not strategy:
        click.secho(f"策略 '{strategy_name}' 不存在", fg="red")
        return

    # 解析环境变量
    env_vars = {}
    for env_pair in env:
        if ":" in env_pair and "=" in env_pair:
            container, var_pair = env_pair.split(":", 1)
            key, value = var_pair.split("=", 1)

            if container not in env_vars:
                env_vars[container] = {}

            env_vars[container][key] = value

    # 部署策略
    try:
        deployment_name = name or strategy_name
        click.echo(f"正在部署策略 '{strategy_name}' 为 '{deployment_name}'...")

        result = strategy_manager.deploy_strategy(
            strategy_name=strategy_name,
            deployment_name=deployment_name,
            environment_variables=env_vars,
            network_name=network,
        )

        # 检查部署结果
        if "error" in result:
            click.secho(f"部署失败: {result['error']}", fg="red")
            return

        if result.get("status") == "success":
            click.secho(f"部署成功: {result.get('message', '')}", fg="green")
        elif result.get("status") == "partial":
            click.secho(f"部分部署成功: {result.get('message', '')}", fg="yellow")

            # 显示错误信息
            if result.get("errors"):
                click.echo("错误详情:")
                for container, error in result["errors"].items():
                    click.echo(f"  {container}: {error}")
        else:
            click.secho(f"部署失败: {result.get('message', '')}", fg="red")

        # 显示创建的容器
        if result.get("containers"):
            click.echo("\n创建的容器:")
            for container, info in result["containers"].items():
                click.echo(
                    f"  {container}: {info['name']} ({info['id'][:12]}) - {info['status']}"
                )

    except Exception as e:
        click.secho(f"部署策略失败: {e}", fg="red")


@strategy_cmd_group.command(name="stop", help="停止策略部署")
@click.argument("deployment_name", required=True)
def stop_strategy(deployment_name):
    """停止策略部署"""
    strategy_manager = get_strategy_manager()

    try:
        click.echo(f"正在停止部署 '{deployment_name}'...")

        result = strategy_manager.stop_strategy(deployment_name)

        if result.get("status") == "success":
            click.secho(result.get("message", "停止成功"), fg="green")
        elif result.get("status") == "partial":
            click.secho(result.get("message", "部分容器停止失败"), fg="yellow")

            # 显示错误信息
            if result.get("errors"):
                click.echo("错误详情:")
                for container, error in result["errors"].items():
                    click.echo(f"  {container}: {error}")
        else:
            click.secho(result.get("message", "停止失败"), fg="red")

    except Exception as e:
        click.secho(f"停止部署失败: {e}", fg="red")


@strategy_cmd_group.command(name="remove", help="移除策略部署")
@click.argument("deployment_name", required=True)
@click.option("--force", "-f", is_flag=True, help="强制移除运行中的容器")
def remove_strategy(deployment_name, force):
    """移除策略部署"""
    strategy_manager = get_strategy_manager()

    try:
        click.echo(f"正在移除部署 '{deployment_name}'...")

        result = strategy_manager.remove_strategy_deployment(
            deployment_name, force=force
        )

        if result.get("status") == "success":
            click.secho(result.get("message", "移除成功"), fg="green")
        elif result.get("status") == "partial":
            click.secho(result.get("message", "部分容器移除失败"), fg="yellow")

            # 显示错误信息
            if result.get("errors"):
                click.echo("错误详情:")
                for container, error in result["errors"].items():
                    click.echo(f"  {container}: {error}")
        else:
            click.secho(result.get("message", "移除失败"), fg="red")

    except Exception as e:
        click.secho(f"移除部署失败: {e}", fg="red")


@strategy_cmd_group.command(name="list-deployments", help="列出所有策略部署")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_deployments(json_output):
    """列出所有策略部署"""
    strategy_manager = get_strategy_manager()

    try:
        deployments = strategy_manager.list_strategy_deployments()

        if json_output:
            click.echo(json.dumps(deployments, indent=2, ensure_ascii=False))
            return

        if not deployments:
            click.echo("未找到策略部署")
            return

        # 格式化表格输出
        table_data = []
        for deployment in deployments:
            table_data.append(
                [
                    deployment.get("deployment_name"),
                    deployment.get("strategy_name"),
                    deployment.get("status", "unknown"),
                    deployment.get("container_count", 0),
                    deployment.get("created_at", "未知"),
                ]
            )

        headers = ["部署名称", "策略名称", "状态", "容器数量", "创建时间"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

    except Exception as e:
        click.secho(f"列出部署失败: {e}", fg="red")


@strategy_cmd_group.command(name="inspect-deployment", help="查看部署详情")
@click.argument("deployment_name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def inspect_deployment(deployment_name, json_output):
    """查看部署详情"""
    strategy_manager = get_strategy_manager()

    try:
        deployment = strategy_manager.inspect_deployment(deployment_name)

        if "error" in deployment:
            click.secho(f"查看部署详情失败: {deployment['error']}", fg="red")
            return

        if json_output:
            click.echo(json.dumps(deployment, indent=2, ensure_ascii=False))
            return

        # 显示基本信息
        click.secho(f"部署: {deployment['deployment_name']}", bold=True)
        click.echo(f"策略: {deployment['strategy_name']}")
        click.echo(f"状态: {deployment['status']}")
        click.echo(f"容器数量: {deployment['container_count']}")

        # 显示容器信息
        click.secho("\n容器:", bold=True)
        container_table = []
        for container in deployment["containers"]:
            networks = ", ".join(container.get("networks", []))
            ports = ", ".join(container.get("ports", []))

            container_table.append(
                [
                    container.get("name"),
                    container.get("status"),
                    container.get("image"),
                    networks,
                    ports,
                ]
            )

        headers = ["名称", "状态", "镜像", "网络", "端口"]
        click.echo(tabulate(container_table, headers=headers, tablefmt="grid"))

    except Exception as e:
        click.secho(f"查看部署详情失败: {e}", fg="red")
