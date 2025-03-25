"""
配置命令模块，提供配置导入导出和管理命令
"""

import os
import click
import json
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

from .utils.config import get_config_manager, ConfigFormat
from .utils.logger import get_logger
from .utils.errors import cli_error_handler, ConfigError, FileError
from .utils.interactive import InteractivePrompt

# 创建日志记录器
logger = get_logger("config_cmd")

# 创建控制台实例
console = Console()


@click.group()
def config():
    """配置管理命令"""
    pass


@config.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--unset", "-u", is_flag=True, help="删除配置项")
@cli_error_handler
def set(key: Optional[str], value: Optional[str], unset: bool):
    """设置或查看配置项"""
    logger.debug(f"执行配置设置命令，参数：key={key}, value={value}, unset={unset}")

    # 获取配置管理器
    config_mgr = get_config_manager()

    # 删除配置项
    if unset:
        if not key:
            console.print("[red]请指定要删除的配置项[/red]")
            return 1

        success = config_mgr.delete(key)
        if success:
            config_mgr.save()
            console.print(f"[green]已删除配置项: {key}[/green]")
        else:
            console.print(f"[yellow]配置项 {key} 不存在[/yellow]")
        return 0

    # 设置配置项
    if key and value:
        # 尝试解析JSON格式值
        try:
            # 如果值是一个有效的JSON，解析它
            if (
                (value.startswith("{") and value.endswith("}"))
                or (value.startswith("[") and value.endswith("]"))
                or value.lower() in ("true", "false", "null")
                or (value.replace(".", "").replace("-", "").isdigit())
            ):
                parsed_value = json.loads(value)
                config_mgr.set(key, parsed_value)
            else:
                config_mgr.set(key, value)
        except json.JSONDecodeError:
            # 如果不是有效的JSON，按原样存储
            config_mgr.set(key, value)

        config_mgr.save()
        console.print(f"[green]已设置配置项: {key} = {config_mgr.get(key)}[/green]")
        return 0

    # 查看配置项
    if key:
        value = config_mgr.get(key)
        if value is None:
            console.print(f"[yellow]配置项 {key} 不存在[/yellow]")
        else:
            console.print(
                f"{key} = [green]{json.dumps(value, ensure_ascii=False)}[/green]"
            )
    else:
        # 显示所有配置
        _display_config(config_mgr.list())

    return 0


@config.command(name="list")
@click.argument("prefix", required=False)
@cli_error_handler
def list_config(prefix: Optional[str] = None):
    """列出配置项"""
    logger.debug(f"执行配置列表命令，参数：prefix={prefix}")

    # 获取配置管理器
    config_mgr = get_config_manager()

    # 获取配置项
    config_items = config_mgr.list(prefix or "")

    # 显示配置
    _display_config(config_items)

    return 0


@config.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "toml", "env"]),
    help="配置文件格式",
)
@click.option("--replace", "-r", is_flag=True, help="替换现有配置（默认合并）")
@cli_error_handler
def import_config(file: str, format: Optional[str], replace: bool):
    """从文件导入配置"""
    logger.debug(
        f"执行配置导入命令，参数：file={file}, format={format}, replace={replace}"
    )

    # 获取配置管理器
    config_mgr = get_config_manager()

    # 确定格式
    config_format = None
    if format:
        try:
            config_format = ConfigFormat.from_extension(format)
        except ConfigError as e:
            console.print(f"[red]{str(e)}[/red]")
            return 1

    # 导入配置
    try:
        config_mgr.import_config(file, config_format, not replace)
        console.print(f"[green]成功从 {file} 导入配置[/green]")

        # 显示导入后的配置
        if InteractivePrompt.confirm("是否显示当前配置?", default=False):
            _display_config(config_mgr.list())

    except (FileError, ConfigError) as e:
        console.print(f"[red]导入配置失败: {str(e)}[/red]")
        if e.get_details():
            console.print(f"[red]详情: {e.get_details()}[/red]")
        return 1

    return 0


@config.command()
@click.argument("file", type=click.Path())
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "toml", "env"]),
    help="配置文件格式",
)
@cli_error_handler
def export(file: str, format: Optional[str]):
    """导出配置到文件"""
    logger.debug(f"执行配置导出命令，参数：file={file}, format={format}")

    # 获取配置管理器
    config_mgr = get_config_manager()

    # 确定格式
    config_format = None
    if format:
        try:
            config_format = ConfigFormat.from_extension(format)
        except ConfigError as e:
            console.print(f"[red]{str(e)}[/red]")
            return 1

    # 导出配置
    try:
        # 检查文件是否存在
        if os.path.exists(file):
            # 确认覆盖
            if not InteractivePrompt.confirm(
                f"文件 {file} 已存在，是否覆盖?", default=False
            ):
                console.print("[yellow]操作已取消[/yellow]")
                return 0

        config_mgr.export_config(file, config_format)
        console.print(f"[green]成功导出配置到 {file}[/green]")

    except ConfigError as e:
        console.print(f"[red]导出配置失败: {str(e)}[/red]")
        if e.get_details():
            console.print(f"[red]详情: {e.get_details()}[/red]")
        return 1

    return 0


@config.command()
@click.option("--force", "-f", is_flag=True, help="不提示确认")
@cli_error_handler
def reset(force: bool):
    """重置所有配置为默认值"""
    logger.debug(f"执行配置重置命令，参数：force={force}")

    # 获取配置管理器
    config_mgr = get_config_manager()

    # 确认重置
    if not force:
        if not InteractivePrompt.confirm(
            "确定要重置所有配置为默认值吗?", default=False
        ):
            console.print("[yellow]操作已取消[/yellow]")
            return 0

    # 重置配置
    config_mgr.config = {}
    config_mgr.save()
    console.print("[green]已重置所有配置为默认值[/green]")

    return 0


def _display_config(config_items: Dict[str, Any]) -> None:
    """
    显示配置项

    Args:
        config_items: 配置项字典
    """
    if not config_items:
        console.print("[yellow]无配置项[/yellow]")
        return

    # 创建表格
    table = Table(title="配置项")
    table.add_column("键", style="cyan")
    table.add_column("值", style="green")

    # 添加配置项
    for key, value in sorted(config_items.items()):
        table.add_row(key, json.dumps(value, ensure_ascii=False))

    # 显示表格
    console.print(table)
