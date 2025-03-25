#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境命令

提供开发环境模板管理和创建开发容器的命令行接口
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.prompt import Prompt, Confirm

# 导入开发环境管理器
from ..dev_environment_manager import DevEnvironmentManager
from ..models.dev_environment import (
    DevEnvironment,
    EnvironmentType,
    PortMapping,
    VolumeMount,
)

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.commands.dev_env")

# 创建控制台对象
console = Console()

# 初始化开发环境管理器
dev_environment_manager = DevEnvironmentManager()


@click.group(name="dev", help="开发环境管理命令")
def dev_env_group():
    """开发环境管理命令组"""
    pass


@dev_env_group.command(name="list", help="列出开发环境模板")
def list_templates():
    """列出所有开发环境模板"""
    try:
        # 获取模板列表
        templates = dev_environment_manager.list_templates()

        if not templates:
            console.print("[yellow]没有找到开发环境模板[/yellow]")
            return

        # 创建表格
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title="开发环境模板",
        )

        # 添加列
        table.add_column("名称", style="cyan")
        table.add_column("类型", style="green")
        table.add_column("镜像", style="blue")
        table.add_column("描述", style="yellow")
        table.add_column("端口", style="magenta")

        # 添加行
        for template in templates:
            # 格式化端口
            ports_str = (
                ", ".join(str(p) for p in template.ports) if template.ports else "无"
            )

            # 添加行
            table.add_row(
                template.name,
                template.env_type.name,
                template.image,
                template.description or "无描述",
                ports_str,
            )

        # 显示表格
        console.print(table)

    except Exception as e:
        logger.error(f"列出开发环境模板时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        sys.exit(1)


@dev_env_group.command(name="info", help="查看开发环境模板详情")
@click.argument("template_name", required=True)
def template_info(template_name: str):
    """查看开发环境模板详情"""
    try:
        # 获取模板
        template = dev_environment_manager.get_template(template_name)

        if not template:
            console.print(f"[red]模板不存在: {template_name}[/red]")
            return 1

        # 创建表格
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("属性", style="cyan")
        table.add_column("值", style="yellow")

        # 添加基本信息
        table.add_row("名称", template.name)
        table.add_row("类型", template.env_type.name)
        table.add_row("镜像", template.image)
        table.add_row("描述", template.description or "无描述")

        # 添加容器配置
        if template.command:
            table.add_row("启动命令", template.command)
        if template.entrypoint:
            table.add_row("入口点", str(template.entrypoint))
        if template.working_dir:
            table.add_row("工作目录", template.working_dir)

        # 添加端口配置
        if template.ports:
            ports_str = "\n".join(
                f"{p.host_port}:{p.container_port}/{p.protocol}"
                + (f" ({p.description})" if p.description else "")
                for p in template.ports
            )
            table.add_row("端口映射", ports_str)

        # 添加卷配置
        if template.volumes:
            volumes_str = "\n".join(
                f"{v.host_path}:{v.container_path}"
                + (":ro" if v.read_only else "")
                + (f" ({v.description})" if v.description else "")
                for v in template.volumes
            )
            table.add_row("卷挂载", volumes_str)

        # 添加环境变量
        if template.environment:
            env_str = "\n".join(f"{k}={v}" for k, v in template.environment.items())
            table.add_row("环境变量", env_str)

        # 添加资源限制
        if template.cpu_limit:
            table.add_row("CPU限制", str(template.cpu_limit))
        if template.memory_limit:
            table.add_row("内存限制", template.memory_limit)

        # 添加网络设置
        table.add_row("网络模式", template.network_mode)
        table.add_row("重启策略", template.restart_policy)

        # 添加VSCode配置
        if template.vscode_extensions:
            extensions_str = "\n".join(template.vscode_extensions)
            table.add_row("VSCode扩展", extensions_str)

        # 显示面板
        console.print(
            Panel(table, title=f"模板详情: {template.name}", border_style="cyan")
        )

        return 0
    except Exception as e:
        logger.error(f"查看模板详情时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@dev_env_group.command(name="create", help="创建开发环境")
@click.argument("template_name", required=True)
@click.option("--name", "-n", help="容器名称", required=True)
@click.option(
    "--project-dir", "-d", help="项目目录", type=click.Path(exists=False), default="."
)
@click.option(
    "--create-devcontainer/--no-create-devcontainer",
    default=True,
    help="是否创建DevContainer配置",
)
@click.option(
    "--start-container/--no-start-container", default=True, help="是否启动容器"
)
@click.option("--pull-image/--no-pull-image", default=False, help="是否拉取最新镜像")
@click.option("--env", "-e", multiple=True, help="环境变量 (格式: KEY=VALUE)")
def create_environment(
    template_name: str,
    name: str,
    project_dir: str,
    create_devcontainer: bool,
    start_container: bool,
    pull_image: bool,
    env: List[str],
):
    """创建开发环境"""
    try:
        # 解析环境变量
        environment = {}
        for env_str in env:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                environment[key] = value

        # 准备选项
        options = {
            "create_devcontainer": create_devcontainer,
            "start_container": start_container,
            "pull_image": pull_image,
            "environment": environment,
        }

        # 创建环境
        console.print(
            f"[cyan]正在创建开发环境 {name} (基于模板 {template_name})...[/cyan]"
        )
        success, message = dev_environment_manager.create_environment(
            template_name=template_name,
            container_name=name,
            project_dir=project_dir,
            options=options,
        )

        if success:
            console.print(f"[green]开发环境创建成功: {message}[/green]")

            if create_devcontainer:
                console.print(
                    f"[green]已创建VSCode DevContainer配置于 {os.path.join(project_dir, '.devcontainer')}[/green]"
                )
                console.print(
                    "[cyan]提示: 使用VSCode打开项目目录，然后使用 Remote-Containers: Reopen in Container 命令[/cyan]"
                )

            return 0
        else:
            console.print(f"[red]开发环境创建失败: {message}[/red]")
            return 1
    except Exception as e:
        logger.error(f"创建开发环境时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@dev_env_group.command(name="create-template", help="创建自定义开发环境模板")
@click.option("--name", "-n", help="模板名称", required=True)
@click.option(
    "--type",
    "-t",
    "env_type",
    help="环境类型",
    type=click.Choice([e.name for e in EnvironmentType]),
    default="CUSTOM",
)
@click.option("--image", "-i", help="镜像名称", required=True)
@click.option("--description", "-d", help="描述", default=None)
@click.option("--working-dir", "-w", help="工作目录", default="/app")
@click.option("--port", "-p", multiple=True, help="端口映射 (格式: 主机端口:容器端口)")
@click.option(
    "--volume", "-v", multiple=True, help="卷挂载 (格式: 主机路径:容器路径[:ro])"
)
@click.option("--env", "-e", multiple=True, help="环境变量 (格式: KEY=VALUE)")
@click.option("--interactive", is_flag=True, help="交互式创建")
def create_template(
    name: str,
    env_type: str,
    image: str,
    description: str,
    working_dir: str,
    port: List[str],
    volume: List[str],
    env: List[str],
    interactive: bool,
):
    """创建自定义开发环境模板"""
    try:
        if interactive:
            return _create_template_interactive()

        # 解析环境类型
        try:
            environment_type = EnvironmentType[env_type]
        except KeyError:
            environment_type = EnvironmentType.CUSTOM

        # 解析端口映射
        ports = []
        for port_str in port:
            try:
                if ":" in port_str:
                    host_port, container_port = port_str.split(":", 1)
                    ports.append(
                        PortMapping(
                            host_port=int(host_port), container_port=int(container_port)
                        )
                    )
            except Exception as e:
                console.print(
                    f"[yellow]警告: 无法解析端口映射 {port_str}: {e}[/yellow]"
                )

        # 解析卷挂载
        volumes = []
        for volume_str in volume:
            try:
                if ":" in volume_str:
                    parts = volume_str.split(":")
                    if len(parts) == 2:
                        host_path, container_path = parts
                        read_only = False
                    elif len(parts) == 3 and parts[2].lower() == "ro":
                        host_path, container_path = parts[0:2]
                        read_only = True
                    else:
                        console.print(
                            f"[yellow]警告: 无法解析卷挂载 {volume_str}[/yellow]"
                        )
                        continue

                    volumes.append(
                        VolumeMount(
                            host_path=host_path,
                            container_path=container_path,
                            read_only=read_only,
                        )
                    )
            except Exception as e:
                console.print(
                    f"[yellow]警告: 无法解析卷挂载 {volume_str}: {e}[/yellow]"
                )

        # 解析环境变量
        environment = {}
        for env_str in env:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                environment[key] = value

        # 创建模板
        template = DevEnvironment(
            name=name,
            env_type=environment_type,
            image=image,
            description=description,
            working_dir=working_dir,
            ports=ports,
            volumes=volumes,
            environment=environment,
        )

        # 保存模板
        success = dev_environment_manager.create_template(template)

        if success:
            console.print(f"[green]模板创建成功: {name}[/green]")
            return 0
        else:
            console.print(f"[red]模板创建失败[/red]")
            return 1
    except Exception as e:
        logger.error(f"创建模板时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


def _create_template_interactive():
    """交互式创建模板"""
    try:
        console.print(
            Panel("[bold cyan]交互式创建开发环境模板[/bold cyan]", box=box.ROUNDED)
        )

        # 基本信息
        name = Prompt.ask("[cyan]模板名称[/cyan]")

        # 显示环境类型选项
        console.print("[cyan]环境类型:[/cyan]")
        for i, env_type in enumerate(EnvironmentType):
            console.print(f"  {i+1}. {env_type.name}")

        type_index = (
            int(Prompt.ask("[cyan]选择环境类型 (输入编号)[/cyan]", default="5")) - 1
        )
        env_type = (
            list(EnvironmentType)[type_index]
            if 0 <= type_index < len(EnvironmentType)
            else EnvironmentType.CUSTOM
        )

        image = Prompt.ask("[cyan]镜像名称[/cyan]")
        description = Prompt.ask("[cyan]描述[/cyan]", default="")
        working_dir = Prompt.ask("[cyan]工作目录[/cyan]", default="/app")

        # 端口映射
        ports = []
        while Confirm.ask("[cyan]添加端口映射?[/cyan]", default=True):
            host_port = int(Prompt.ask("[cyan]主机端口[/cyan]"))
            container_port = int(Prompt.ask("[cyan]容器端口[/cyan]"))
            protocol = Prompt.ask("[cyan]协议[/cyan]", default="tcp")
            description = Prompt.ask("[cyan]描述[/cyan]", default="")

            ports.append(
                PortMapping(
                    host_port=host_port,
                    container_port=container_port,
                    protocol=protocol,
                    description=description or None,
                )
            )

        # 卷挂载
        volumes = []
        while Confirm.ask("[cyan]添加卷挂载?[/cyan]", default=True):
            host_path = Prompt.ask("[cyan]主机路径[/cyan]")
            container_path = Prompt.ask("[cyan]容器路径[/cyan]")
            read_only = Confirm.ask("[cyan]只读?[/cyan]", default=False)
            description = Prompt.ask("[cyan]描述[/cyan]", default="")

            volumes.append(
                VolumeMount(
                    host_path=host_path,
                    container_path=container_path,
                    read_only=read_only,
                    description=description or None,
                )
            )

        # 环境变量
        environment = {}
        while Confirm.ask("[cyan]添加环境变量?[/cyan]", default=True):
            key = Prompt.ask("[cyan]变量名[/cyan]")
            value = Prompt.ask("[cyan]变量值[/cyan]")
            environment[key] = value

        # 资源限制
        cpu_limit = None
        memory_limit = None
        if Confirm.ask("[cyan]设置资源限制?[/cyan]", default=False):
            cpu_limit_str = Prompt.ask("[cyan]CPU限制 (核心数)[/cyan]", default="")
            memory_limit = Prompt.ask(
                "[cyan]内存限制 (如: 512m, 1g)[/cyan]", default=""
            )

            try:
                cpu_limit = float(cpu_limit_str) if cpu_limit_str else None
            except ValueError:
                cpu_limit = None

        # VSCode扩展
        vscode_extensions = []
        if Confirm.ask("[cyan]添加VSCode扩展?[/cyan]", default=True):
            while True:
                extension = Prompt.ask("[cyan]扩展ID (留空结束)[/cyan]", default="")
                if not extension:
                    break
                vscode_extensions.append(extension)

        # 创建模板
        template = DevEnvironment(
            name=name,
            env_type=env_type,
            image=image,
            description=description or None,
            working_dir=working_dir,
            ports=ports,
            volumes=volumes,
            environment=environment,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            vscode_extensions=vscode_extensions,
        )

        # 显示模板摘要
        console.print("\n[bold cyan]模板摘要:[/bold cyan]")
        console.print(f"  名称: {template.name}")
        console.print(f"  类型: {template.env_type.name}")
        console.print(f"  镜像: {template.image}")
        if template.description:
            console.print(f"  描述: {template.description}")

        # 确认创建
        if Confirm.ask("[cyan]确认创建该模板?[/cyan]", default=True):
            # 保存模板
            success = dev_environment_manager.create_template(template)

            if success:
                console.print(f"[green]模板创建成功: {name}[/green]")
                return 0
            else:
                console.print(f"[red]模板创建失败[/red]")
                return 1
        else:
            console.print("[yellow]取消创建模板[/yellow]")
            return 0
    except Exception as e:
        logger.error(f"交互式创建模板时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@dev_env_group.command(name="delete", help="删除开发环境模板")
@click.argument("template_name", required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
def delete_template(template_name: str, force: bool):
    """删除开发环境模板"""
    try:
        # 获取模板
        template = dev_environment_manager.get_template(template_name)

        if not template:
            console.print(f"[red]模板不存在: {template_name}[/red]")
            return 1

        # 确认删除
        if not force and not Confirm.ask(
            f"[yellow]确认删除模板 {template_name}?[/yellow]", default=False
        ):
            console.print("[yellow]取消删除模板[/yellow]")
            return 0

        # 删除模板
        success = dev_environment_manager.delete_template(template_name)

        if success:
            console.print(f"[green]模板删除成功: {template_name}[/green]")
            return 0
        else:
            console.print(f"[red]模板删除失败[/red]")
            return 1
    except Exception as e:
        logger.error(f"删除模板时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@dev_env_group.command(name="export", help="导出开发环境模板")
@click.argument("template_name", required=True)
@click.option("--output", "-o", help="输出文件路径", default=None)
def export_template(template_name: str, output: Optional[str]):
    """导出开发环境模板"""
    try:
        # 获取模板
        template = dev_environment_manager.get_template(template_name)

        if not template:
            console.print(f"[red]模板不存在: {template_name}[/red]")
            return 1

        # 确定输出路径
        if not output:
            output = f"{template_name}.yaml"

        # 保存模板
        success = template.save_to_file(output)

        if success:
            console.print(f"[green]模板导出成功: {output}[/green]")
            return 0
        else:
            console.print(f"[red]模板导出失败[/red]")
            return 1
    except Exception as e:
        logger.error(f"导出模板时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@dev_env_group.command(name="import", help="导入开发环境模板")
@click.argument("file_path", type=click.Path(exists=True), required=True)
def import_template(file_path: str):
    """导入开发环境模板"""
    try:
        # 加载模板
        template = DevEnvironment.load_from_file(file_path)

        if not template:
            console.print(f"[red]无法加载模板文件: {file_path}[/red]")
            return 1

        # 保存模板
        success = dev_environment_manager.create_template(template)

        if success:
            console.print(f"[green]模板导入成功: {template.name}[/green]")
            return 0
        else:
            console.print(f"[red]模板导入失败[/red]")
            return 1
    except Exception as e:
        logger.error(f"导入模板时出错: {e}")
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    dev_env_group()
