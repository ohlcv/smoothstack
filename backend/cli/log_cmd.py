"""
日志管理命令模块
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .utils.logger import get_logger, init_logging, set_log_level
from .utils.platform import get_data_dir, is_windows
from .utils.errors import FileSystemError, UserError

# 创建日志记录器
logger = get_logger("log_cmd")

# 控制台实例
console = Console()


@click.group()
def log():
    """日志管理命令"""
    pass


@log.command()
@click.option(
    "--level", "-l", help="设置日志级别 (debug, info, warning, error, critical)"
)
@click.option("--module", "-m", help="指定要设置级别的模块名称")
def level(level: Optional[str], module: Optional[str]):
    """设置日志级别"""
    if not level:
        # 显示当前日志级别
        console.print("[bold]当前日志级别[/bold]")
        table = Table()
        table.add_column("模块", style="cyan")
        table.add_column("级别", style="green")

        # 添加根日志器级别
        table.add_row("根日志器", "INFO")  # 默认级别

        console.print(table)
        return

    # 验证日志级别
    valid_levels = ["debug", "info", "warning", "error", "critical"]
    if level.lower() not in valid_levels:
        raise UserError(
            f"无效的日志级别: {level}", f"有效的级别为: {', '.join(valid_levels)}"
        )

    # 设置日志级别
    set_log_level(level.lower(), module)

    if module:
        logger.info(f"将模块 {module} 的日志级别设置为 {level.upper()}")
        console.print(
            f"[green]已将模块 {module} 的日志级别设置为 {level.upper()}[/green]"
        )
    else:
        logger.info(f"将全局日志级别设置为 {level.upper()}")
        console.print(f"[green]已将全局日志级别设置为 {level.upper()}[/green]")


@log.command()
@click.option("--lines", "-n", type=int, default=50, help="显示的行数")
@click.option("--tail", "-t", is_flag=True, help="持续监视日志文件")
@click.option("--all", "-a", is_flag=True, help="显示所有日志记录")
@click.option("--file", "-f", help="指定要查看的日志文件")
def view(lines: int, tail: bool, all: bool, file: Optional[str]):
    """查看日志内容"""
    # 确定日志文件路径
    log_dir = get_data_dir() / "logs"

    if file:
        log_file = Path(file)
        if not log_file.is_absolute():
            log_file = log_dir / file
    else:
        # 查找最新的日志文件
        try:
            log_files = list(log_dir.glob("smoothstack_*.log"))
            if not log_files:
                raise FileSystemError("未找到日志文件", f"日志目录: {log_dir}")

            # 按修改时间排序，取最新的
            log_file = sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)[
                0
            ]
        except Exception as e:
            raise FileSystemError("获取日志文件失败", str(e))

    # 检查文件存在
    if not log_file.exists():
        raise FileSystemError(f"日志文件不存在: {log_file}")

    # 读取日志内容
    try:
        if tail:
            # 使用系统命令持续监视日志
            cmd = ""
            if is_windows():
                # Windows - PowerShell
                cmd = f"powershell -command \"Get-Content -Path '{log_file}' -Tail {lines} -Wait\""
            else:
                # Unix - tail
                cmd = f"tail -n {lines} -f '{log_file}'"

            console.print(f"[cyan]正在监视日志文件: {log_file}[/cyan]")
            console.print("[yellow]按 Ctrl+C 退出[/yellow]")
            os.system(cmd)
        else:
            # 直接读取指定行数
            with log_file.open("r", encoding="utf-8") as f:
                if all:
                    content = f.read()
                else:
                    # 读取最后几行
                    lines_list: List[str] = []

                    # 简单实现，可能不是最高效的方法
                    for line in f:
                        lines_list.append(line)
                        if len(lines_list) > lines:
                            lines_list.pop(0)

                    content = "".join(lines_list)

            # 显示日志内容
            syntax = Syntax(
                content, "text", theme="monokai", line_numbers=True, word_wrap=True
            )

            panel = Panel(
                syntax,
                title=f"日志文件: {log_file.name}",
                subtitle=f"最后 {len(content.splitlines())} 行" if not all else None,
            )

            console.print(panel)

    except KeyboardInterrupt:
        # 优雅地处理Ctrl+C
        console.print("\n[yellow]监视已停止[/yellow]")
    except Exception as e:
        raise FileSystemError(f"读取日志文件失败: {str(e)}")


@log.command()
@click.option("--all", "-a", is_flag=True, help="清除所有日志文件")
@click.option("--days", "-d", type=int, default=7, help="保留最近几天的日志")
def clean(all: bool, days: int):
    """清理日志文件"""
    # 确定日志目录
    log_dir = get_data_dir() / "logs"

    try:
        # 获取所有日志文件
        log_files = list(log_dir.glob("smoothstack_*.log"))
        if not log_files:
            console.print("[yellow]未找到日志文件[/yellow]")
            return

        if all:
            # 清除所有日志文件
            for log_file in log_files:
                log_file.unlink()

            logger.info(f"清除了所有 {len(log_files)} 个日志文件")
            console.print(f"[green]已清除所有 {len(log_files)} 个日志文件[/green]")
        else:
            # 清除旧的日志文件
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_time = cutoff_date.timestamp()

            # 筛选旧文件
            old_files = [f for f in log_files if f.stat().st_mtime < cutoff_time]

            # 删除旧文件
            for log_file in old_files:
                log_file.unlink()

            if old_files:
                logger.info(f"清除了 {len(old_files)} 个超过 {days} 天的日志文件")
                console.print(
                    f"[green]已清除 {len(old_files)} 个超过 {days} 天的日志文件[/green]"
                )
            else:
                console.print(f"[yellow]没有超过 {days} 天的日志文件需要清除[/yellow]")

    except Exception as e:
        raise FileSystemError(f"清理日志文件失败: {str(e)}")


@log.command()
def list():
    """列出日志文件"""
    # 确定日志目录
    log_dir = get_data_dir() / "logs"

    try:
        # 获取所有日志文件
        log_files = list(log_dir.glob("smoothstack_*.log"))
        if not log_files:
            console.print("[yellow]未找到日志文件[/yellow]")
            return

        # 创建日志文件表格
        table = Table(title="日志文件列表")
        table.add_column("文件名", style="cyan")
        table.add_column("大小", style="green", justify="right")
        table.add_column("修改时间", style="yellow")

        # 将文件按修改时间排序，最新的在前面
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # 获取格式化的文件大小函数
        def format_size(size_bytes):
            # 简单的文件大小格式化
            for unit in ["B", "KB", "MB", "GB"]:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.2f} TB"

        # 添加文件信息
        for log_file in log_files:
            file_stat = log_file.stat()
            size = format_size(file_stat.st_size)
            mtime = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(file_stat.st_mtime)
            )

            table.add_row(log_file.name, size, mtime)

        console.print(table)

    except Exception as e:
        raise FileSystemError(f"列出日志文件失败: {str(e)}")
