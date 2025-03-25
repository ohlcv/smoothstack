#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器持久化存储命令行界面

提供容器数据卷管理相关的命令行功能
"""

import os
import sys
import click
import json
from typing import Dict, List, Any
from datetime import datetime

from backend.container_manager.storage_manager import get_storage_manager

# 配置日志
import logging

logger = logging.getLogger("smoothstack.container_manager.commands.storage_cmd")


@click.group(name="storage", help="容器持久化存储管理")
def storage_cmd_group():
    """容器持久化存储管理命令组"""
    pass


@storage_cmd_group.command(name="list", help="列出所有数据卷")
@click.option("--dangling", is_flag=True, help="仅列出未使用的卷")
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_volumes(dangling, json_output):
    """列出所有数据卷"""
    storage_manager = get_storage_manager()

    filters = {}
    if dangling:
        filters = {"dangling": True}

    volumes = storage_manager.list_volumes(filters=filters)

    if json_output:
        click.echo(json.dumps(volumes, indent=2, ensure_ascii=False))
        return

    if not volumes:
        click.echo("未找到数据卷")
        return

    click.secho("数据卷:", bold=True)
    click.echo(f"{'名称':<30} {'驱动':<15} {'创建时间':<25} {'大小':<12} {'状态'}")
    click.echo("-" * 90)

    for volume in volumes:
        name = volume.get("name", "N/A")
        driver = volume.get("driver", "N/A")
        created = volume.get("created", "N/A")
        size = volume.get("size", "Unknown")

        used_by = len(storage_manager._find_containers_using_volume(name))
        status = "使用中" if used_by > 0 else "未使用"

        click.echo(f"{name:<30} {driver:<15} {created:<25} {size:<12} {status}")


@storage_cmd_group.command(name="create", help="创建新的数据卷")
@click.argument("name", required=True)
@click.option("--driver", "-d", default="local", help="存储驱动")
@click.option("--label", "-l", multiple=True, help="卷标签，格式为key=value")
def create_volume(name, driver, label):
    """创建新的数据卷"""
    storage_manager = get_storage_manager()

    # 解析标签
    labels = {}
    for item in label:
        parts = item.split("=", 1)
        if len(parts) == 2:
            labels[parts[0]] = parts[1]

    try:
        result = storage_manager.create_volume(name=name, driver=driver, labels=labels)
        click.secho(f"成功创建数据卷: {name}", fg="green")
        click.echo(f"驱动: {result['driver']}")
        click.echo(f"挂载点: {result['mountpoint']}")
        click.echo(f"创建时间: {result['created']}")

        if labels:
            click.echo("标签:")
            for k, v in result["labels"].items():
                click.echo(f"  {k}: {v}")
    except Exception as e:
        click.secho(f"创建数据卷失败: {e}", fg="red")


@storage_cmd_group.command(name="remove", help="删除数据卷")
@click.argument("names", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除（即使卷在使用中）")
def remove_volume(names, force):
    """删除数据卷"""
    storage_manager = get_storage_manager()

    success_count = 0
    failed_count = 0

    for name in names:
        try:
            if storage_manager.remove_volume(name, force=force):
                click.secho(f"成功删除数据卷: {name}", fg="green")
                success_count += 1
            else:
                click.secho(f"删除数据卷失败: {name}", fg="red")
                if not force:
                    click.echo("提示: 使用 --force 选项强制删除")
                failed_count += 1
        except Exception as e:
            click.secho(f"删除数据卷 {name} 失败: {e}", fg="red")
            failed_count += 1

    if len(names) > 1:
        click.echo(f"总计: {len(names)}, 成功: {success_count}, 失败: {failed_count}")


@storage_cmd_group.command(name="inspect", help="查看卷详情")
@click.argument("name", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def inspect_volume(name, json_output):
    """查看卷详情"""
    storage_manager = get_storage_manager()

    volume_info = storage_manager.inspect_volume(name)

    if json_output:
        click.echo(json.dumps(volume_info, indent=2, ensure_ascii=False))
        return

    if "error" in volume_info:
        click.secho(f"错误: {volume_info['error']}", fg="red")
        return

    click.secho(f"数据卷: {volume_info['name']}", bold=True)
    click.echo(f"驱动: {volume_info['driver']}")
    click.echo(f"挂载点: {volume_info['mountpoint']}")
    click.echo(f"创建时间: {volume_info['created']}")
    click.echo(f"范围: {volume_info['scope']}")

    if "size" in volume_info:
        click.echo(f"大小: {volume_info['size']}")

    # 显示标签
    if volume_info.get("labels"):
        click.secho("标签:", bold=True)
        for k, v in volume_info["labels"].items():
            click.echo(f"  {k}: {v}")

    # 显示使用此卷的容器
    used_by = volume_info.get("used_by", [])
    if used_by:
        click.secho("使用此卷的容器:", bold=True)
        for container in used_by:
            click.echo(f"  {container}")
    else:
        click.echo("使用此卷的容器: 无")


@storage_cmd_group.command(name="prune", help="清理未使用的卷")
@click.confirmation_option(prompt="确定要删除所有未使用的卷吗?")
def prune_volumes():
    """清理未使用的卷"""
    storage_manager = get_storage_manager()

    result = storage_manager.prune_volumes()

    if "error" in result:
        click.secho(f"清理卷时出错: {result['error']}", fg="red")
        return

    volumes_deleted = result.get("volumes_deleted", [])
    space_reclaimed = result.get("space_reclaimed", 0)

    if volumes_deleted:
        click.secho(f"已删除 {len(volumes_deleted)} 个未使用的卷:", fg="green")
        for volume in volumes_deleted:
            click.echo(f"  {volume}")

        # 格式化空间大小
        space_mb = space_reclaimed / (1024 * 1024)
        if space_mb > 1024:
            click.echo(f"释放空间: {space_mb/1024:.2f} GB")
        else:
            click.echo(f"释放空间: {space_mb:.2f} MB")
    else:
        click.echo("没有未使用的卷需要清理")


@storage_cmd_group.command(name="backup", help="备份卷数据到文件")
@click.argument("volume_name", required=True)
@click.argument("backup_path", required=True)
def backup_volume(volume_name, backup_path):
    """备份卷数据到文件"""
    storage_manager = get_storage_manager()

    click.echo(f"正在备份卷 {volume_name} 到 {backup_path}...")

    if storage_manager.backup_volume(volume_name, backup_path):
        click.secho(f"卷 {volume_name} 已成功备份到 {backup_path}", fg="green")
    else:
        click.secho(f"备份卷 {volume_name} 失败", fg="red")


@storage_cmd_group.command(name="restore", help="从备份文件恢复卷数据")
@click.argument("backup_path", required=True)
@click.argument("volume_name", required=True)
@click.option("--create", "-c", is_flag=True, default=True, help="如果卷不存在则创建")
def restore_volume(backup_path, volume_name, create):
    """从备份文件恢复卷数据"""
    storage_manager = get_storage_manager()

    click.echo(f"正在从 {backup_path} 恢复卷 {volume_name}...")

    if storage_manager.restore_volume(
        backup_path, volume_name, create_if_missing=create
    ):
        click.secho(f"已成功从 {backup_path} 恢复卷 {volume_name}", fg="green")
    else:
        click.secho(f"从 {backup_path} 恢复卷 {volume_name} 失败", fg="red")


@storage_cmd_group.command(name="container-volumes", help="列出容器使用的所有卷")
@click.argument("container", required=True)
@click.option("--json", "-j", "json_output", is_flag=True, help="以JSON格式输出")
def list_container_volumes(container, json_output):
    """列出容器使用的所有卷"""
    storage_manager = get_storage_manager()

    mounts = storage_manager.list_container_volumes(container)

    if json_output:
        click.echo(json.dumps(mounts, indent=2, ensure_ascii=False))
        return

    if not mounts:
        click.echo(f"容器 {container} 没有挂载卷或容器不存在")
        return

    click.secho(f"容器 {container} 的挂载点:", bold=True)
    click.echo(f"{'类型':<10} {'源':<40} {'目标':<30} {'模式':<10}")
    click.echo("-" * 90)

    for mount in mounts:
        mount_type = mount.get("type", "N/A")
        source = mount.get("source", "N/A")
        destination = mount.get("destination", "N/A")
        mode = mount.get("mode", "rw")

        click.echo(f"{mount_type:<10} {source:<40} {destination:<30} {mode:<10}")


@storage_cmd_group.command(name="mount-info", help="显示挂载点使用说明")
def mount_info():
    """显示挂载点使用说明"""
    click.secho("Docker卷挂载说明", bold=True)
    click.echo("Docker不支持向现有容器动态添加或删除卷，必须在创建容器时指定挂载。")

    click.secho("\n卷挂载示例:", bold=True)
    click.echo("  docker run -v my_volume:/data ...")
    click.echo("  这将把名为'my_volume'的卷挂载到容器的'/data'目录")

    click.secho("\n绑定挂载示例:", bold=True)
    click.echo("  docker run -v /host/path:/container/path ...")
    click.echo("  这将把主机的'/host/path'目录挂载到容器的'/container/path'目录")

    click.secho("\n只读挂载:", bold=True)
    click.echo("  docker run -v my_volume:/data:ro ...")
    click.echo("  使用':ro'后缀指定只读模式挂载")

    click.secho("\n使用Docker Compose:", bold=True)
    click.echo("  volumes:")
    click.echo("    - my_volume:/data")
    click.echo("    - /host/path:/container/path:ro")

    click.secho("\n注意事项:", bold=True)
    click.echo("  1. 容器停止后，卷中的数据仍然保留")
    click.echo("  2. 多个容器可以挂载同一个卷")
    click.echo("  3. 删除容器不会删除关联的卷")
    click.echo("  4. 使用'docker volume rm'或'docker volume prune'删除未使用的卷")
