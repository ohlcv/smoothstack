"""
命令补全管理命令
"""

import click
from rich.console import Console
from rich.table import Table

from .completion import (
    install_completion,
    uninstall_completion,
    list_completion_scripts,
    get_shell_type,
)

console = Console()


@click.group()
def completion():
    """管理命令补全"""
    pass


@completion.command()
def install():
    """安装命令补全"""
    if install_completion():
        console.print("[green]命令补全安装成功[/green]")
    else:
        console.print("[red]命令补全安装失败[/red]")
        return 1


@completion.command()
def uninstall():
    """卸载命令补全"""
    if uninstall_completion():
        console.print("[green]命令补全卸载成功[/green]")
    else:
        console.print("[red]命令补全卸载失败[/red]")
        return 1


@completion.command()
def list():
    """列出可用的补全脚本"""
    scripts = list_completion_scripts()
    if not scripts:
        console.print("[yellow]未找到补全脚本[/yellow]")
        return

    table = Table(title="可用的补全脚本")
    table.add_column("文件名", style="cyan")
    table.add_column("Shell类型", style="green")
    table.add_column("状态", style="yellow")

    current_shell = get_shell_type()
    for script in scripts:
        shell_type = ""
        if script.endswith(".bash"):
            shell_type = "Bash"
        elif script.endswith(".zsh"):
            shell_type = "Zsh"
        elif script.endswith(".ps1"):
            shell_type = "PowerShell"

        status = (
            "当前Shell"
            if (
                (current_shell == "bash" and script.endswith(".bash"))
                or (current_shell == "zsh" and script.endswith(".zsh"))
                or (current_shell == "powershell" and script.endswith(".ps1"))
            )
            else "可用"
        )

        table.add_row(script, shell_type, status)

    console.print(table)
