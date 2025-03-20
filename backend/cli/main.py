"""
Smoothstack CLI 工具主入口
"""

import sys
from typing import List, Optional
import click
from rich.console import Console

from .help import HelpManager
from .help_cmd import help_command
from .completion_cmd import completion

# 创建Rich控制台实例
console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Smoothstack CLI 工具 - 简化全栈开发流程"""
    pass


@cli.command()
@click.argument("topic", required=False)
def help(topic: Optional[str] = None):
    """显示帮助信息"""
    help_command([topic] if topic else [])


@cli.command()
@click.argument("name", required=False)
@click.option("--template", "-t", default="basic", help="项目模板")
@click.option("--python-version", default="3.8", help="Python版本")
@click.option("--node-version", default="16", help="Node.js版本")
@click.option("--docker/--no-docker", default=False, help="是否添加Docker支持")
@click.option("--git/--no-git", default=True, help="是否初始化Git仓库")
@click.option("--force", "-f", is_flag=True, help="强制覆盖已存在的目录")
def init(
    name: Optional[str],
    template: str,
    python_version: str,
    node_version: str,
    docker: bool,
    git: bool,
    force: bool,
):
    """初始化新项目"""
    # TODO: 实现项目初始化功能
    console.print("[red]项目初始化功能尚未实现[/red]")


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "-l", is_flag=True, help="列出所有配置")
@click.option("--unset", "-u", is_flag=True, help="删除配置项")
def config(key: Optional[str], value: Optional[str], list: bool, unset: bool):
    """管理配置"""
    # TODO: 实现配置管理功能
    console.print("[red]配置管理功能尚未实现[/red]")


@cli.command()
@click.argument("command", required=True)
@click.option("--name", "-n", help="服务名称")
@click.option("--detach", "-d", is_flag=True, help="后台运行")
def service(command: str, name: Optional[str], detach: bool):
    """管理服务"""
    # TODO: 实现服务管理功能
    console.print("[red]服务管理功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--watch", "-w", is_flag=True, help="监视模式")
@click.option("--coverage", "-c", is_flag=True, help="生成覆盖率报告")
def test(type: str, watch: bool, coverage: bool):
    """运行测试"""
    # TODO: 实现测试功能
    console.print("[red]测试功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--fix", "-f", is_flag=True, help="自动修复问题")
def lint(type: str, fix: bool):
    """代码检查"""
    # TODO: 实现代码检查功能
    console.print("[red]代码检查功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--mode", default="development", help="构建模式")
@click.option("--output", "-o", help="输出目录")
def build(type: str, mode: str, output: Optional[str]):
    """构建项目"""
    # TODO: 实现项目构建功能
    console.print("[red]项目构建功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--port", "-p", help="端口号")
@click.option("--host", "-h", help="主机地址")
def dev(type: str, port: Optional[str], host: Optional[str]):
    """启动开发服务器"""
    # TODO: 实现开发服务器功能
    console.print("[red]开发服务器功能尚未实现[/red]")


cli.add_command(completion)


def main():
    """CLI工具入口函数"""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
