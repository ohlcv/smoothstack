"""
交互式命令模块，提供命令行交互模式支持
"""

import sys
import os
import shlex
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt

from .utils.logger import get_logger
from .utils.interactive import InteractivePrompt, InteractiveForm, InteractiveTable
from .utils.errors import UserError, cli_error_handler, CommandError

# 创建日志记录器
logger = get_logger("interactive_cmd")

# 创建控制台实例
console = Console()


class CommandHistory:
    """
    命令历史记录管理类
    """

    def __init__(self, max_size: int = 100):
        """
        初始化命令历史记录

        Args:
            max_size: 最大历史记录数量
        """
        self.history: List[str] = []
        self.max_size = max_size
        self.position = 0
        self._load_history()

    def _get_history_file(self) -> Path:
        """获取历史记录文件路径"""
        # 获取用户家目录
        home_dir = Path.home()
        # 创建.smoothstack目录（如果不存在）
        ss_dir = home_dir / ".smoothstack"
        ss_dir.mkdir(exist_ok=True)
        # 历史记录文件
        return ss_dir / "interactive_history"

    def _load_history(self) -> None:
        """加载历史记录"""
        history_file = self._get_history_file()
        if history_file.exists():
            try:
                with history_file.open("r", encoding="utf-8") as f:
                    self.history = [line.strip() for line in f.readlines()]
                    # 只保留最近的max_size条记录
                    self.history = self.history[-self.max_size :]
                    self.position = len(self.history)
            except Exception as e:
                logger.warning(f"加载历史记录失败: {e}")
                self.history = []
                self.position = 0

    def _save_history(self) -> None:
        """保存历史记录"""
        history_file = self._get_history_file()
        try:
            with history_file.open("w", encoding="utf-8") as f:
                for cmd in self.history:
                    f.write(f"{cmd}\n")
        except Exception as e:
            logger.warning(f"保存历史记录失败: {e}")

    def add(self, command: str) -> None:
        """
        添加命令到历史记录

        Args:
            command: 要添加的命令
        """
        # 忽略空命令和重复命令
        if not command.strip() or (self.history and self.history[-1] == command):
            return

        self.history.append(command)
        if len(self.history) > self.max_size:
            self.history.pop(0)
        self.position = len(self.history)
        self._save_history()

    def get_previous(self) -> Optional[str]:
        """
        获取上一条历史记录

        Returns:
            上一条历史记录，如果没有则返回None
        """
        if not self.history or self.position <= 0:
            return None

        self.position -= 1
        return self.history[self.position]

    def get_next(self) -> Optional[str]:
        """
        获取下一条历史记录

        Returns:
            下一条历史记录，如果没有则返回None
        """
        if not self.history or self.position >= len(self.history):
            return None

        self.position += 1
        if self.position == len(self.history):
            return ""
        return self.history[self.position]

    def list(self, n: int = 10) -> List[str]:
        """
        获取最近的n条历史记录

        Args:
            n: 要获取的记录数量

        Returns:
            最近的n条历史记录
        """
        return self.history[-n:]


class CommandSuggester:
    """
    命令建议生成器
    """

    def __init__(self, cli_obj: click.Group):
        """
        初始化命令建议生成器

        Args:
            cli_obj: CLI对象
        """
        self.cli = cli_obj
        self.commands = self._get_all_commands()

    def _get_all_commands(self) -> List[str]:
        """获取所有可用命令"""
        result = []
        if self.cli:
            for cmd_name in self.cli.list_commands(ctx=None):  # type: ignore
                result.append(cmd_name)
        return result

    def suggest(self, partial_cmd: str) -> List[str]:
        """
        根据部分输入生成命令建议

        Args:
            partial_cmd: 部分输入的命令

        Returns:
            命令建议列表
        """
        suggestions = []
        words = shlex.split(partial_cmd) if partial_cmd else []

        if not words:
            # 空输入，建议所有命令
            suggestions = self.commands
        elif len(words) == 1 and not partial_cmd.endswith(" "):
            # 只有一个单词且未结束，建议匹配的命令
            cmd_prefix = words[0].lower()
            for cmd in self.commands:
                if cmd.lower().startswith(cmd_prefix):
                    suggestions.append(cmd)
        else:
            # 复杂命令，TODO: 增加子命令和选项的建议
            pass

        return suggestions[:10]  # 限制返回数量


class InteractiveCommandRunner:
    """
    交互式命令运行器
    """

    def __init__(self, cli_obj: click.Group):
        """
        初始化交互式命令运行器

        Args:
            cli_obj: CLI对象
        """
        self.cli = cli_obj
        self.history = CommandHistory()
        self.suggester = CommandSuggester(cli_obj)
        self.running = True

    def _parse_command(self, command_line: str) -> Tuple[List[str], Dict[str, str]]:
        """
        解析命令行

        Args:
            command_line: 命令行字符串

        Returns:
            (参数列表, 选项字典)
        """
        if not command_line:
            return [], {}

        args = []
        kwargs = {}

        try:
            # 使用shlex分割命令，保留引号内容
            tokens = shlex.split(command_line)

            current_key = None

            for token in tokens:
                if token.startswith("--"):
                    # 长选项
                    if "=" in token:
                        key, value = token[2:].split("=", 1)
                        kwargs[key] = value
                    else:
                        current_key = token[2:]
                        kwargs[current_key] = "true"  # 默认为true，如果后面有值会被覆盖
                elif token.startswith("-") and len(token) == 2:
                    # 短选项
                    current_key = token[1:]
                    kwargs[current_key] = "true"  # 默认为true，如果后面有值会被覆盖
                else:
                    # 值或位置参数
                    if current_key:
                        kwargs[current_key] = token
                        current_key = None
                    else:
                        args.append(token)

        except Exception as e:
            logger.warning(f"解析命令失败: {e}")
            # 出错时，将整个命令作为参数返回
            return [command_line], {}

        return args, kwargs

    def _process_special_command(self, command: str) -> bool:
        """
        处理特殊命令

        Args:
            command: 命令字符串

        Returns:
            是否为已处理的特殊命令
        """
        cmd = command.strip().lower()

        if cmd in ("exit", "quit", "q"):
            # 退出交互模式
            console.print("[yellow]退出交互模式[/yellow]")
            self.running = False
            return True

        if cmd in ("help", "?"):
            # 显示帮助
            self._show_help()
            return True

        if cmd == "clear" or cmd == "cls":
            # 清屏
            os.system("cls" if os.name == "nt" else "clear")
            return True

        if cmd.startswith("history"):
            # 显示历史记录
            parts = cmd.split()
            n = 10  # 默认显示10条
            if len(parts) > 1:
                try:
                    n = int(parts[1])
                except ValueError:
                    pass
            self._show_history(n)
            return True

        return False

    def _show_help(self) -> None:
        """显示帮助信息"""
        panel = Panel(
            """[bold]可用命令：[/bold]
            - [cyan]exit[/cyan], [cyan]quit[/cyan], [cyan]q[/cyan]: 退出交互模式
            - [cyan]help[/cyan], [cyan]?[/cyan]: 显示此帮助
            - [cyan]clear[/cyan], [cyan]cls[/cyan]: 清屏
            - [cyan]history [n][/cyan]: 显示最近n条历史记录
            - 输入任何CLI命令直接执行
            - 按[cyan]Tab[/cyan]键自动补全命令
            - 使用[cyan]↑[/cyan][cyan]↓[/cyan]键浏览历史记录""",
            title="交互模式帮助",
            border_style="blue",
        )
        console.print(panel)

    def _show_history(self, n: int = 10) -> None:
        """
        显示历史记录

        Args:
            n: 显示的记录数量
        """
        history = self.history.list(n)
        if not history:
            console.print("[yellow]没有历史记录[/yellow]")
            return

        table = Table(title=f"最近 {len(history)} 条命令")
        table.add_column("#", style="cyan")
        table.add_column("命令", style="green")

        for i, cmd in enumerate(history, 1):
            table.add_row(str(i), cmd)

        console.print(table)

    def _execute_command(self, command_line: str) -> None:
        """
        执行命令

        Args:
            command_line: 命令行字符串
        """
        if not command_line.strip():
            return

        # 添加到历史记录
        self.history.add(command_line)

        # 检查特殊命令
        if self._process_special_command(command_line):
            return

        # 解析命令行
        args, kwargs = self._parse_command(command_line)
        if not args:
            return

        # 执行命令
        try:
            logger.debug(f"执行命令: {command_line}")
            console.print(f"[dim]$ {command_line}[/dim]")

            # 构建命令行参数
            cmd_args = []
            for arg in args:
                cmd_args.append(arg)
            for key, value in kwargs.items():
                if value == "true":
                    cmd_args.append(f"--{key}")
                else:
                    cmd_args.append(f"--{key}={value}")

            # 调用CLI命令
            ctx = click.Context(self.cli, info_name=self.cli.name, obj={})
            try:
                result = self.cli.main(args=cmd_args, prog_name=None, obj=ctx.obj)  # type: ignore
                logger.debug(f"命令执行完成: {command_line}")
            except SystemExit:
                # 命令执行完成，忽略SystemExit
                pass

        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            console.print(f"[red]命令执行失败: {str(e)}[/red]")

    def run(self) -> None:
        """运行交互式命令行"""
        # 显示欢迎信息
        console.print(
            Panel(
                "[bold]欢迎使用 Smoothstack CLI 交互模式[/bold]\n"
                "输入 [cyan]help[/cyan] 或 [cyan]?[/cyan] 查看帮助，[cyan]exit[/cyan] 退出",
                border_style="green",
            )
        )

        # 主循环
        self.running = True
        while self.running:
            try:
                # 获取用户输入
                command = Prompt.ask("\n[bold green]smoothstack[/bold green] > ")

                # 执行命令
                self._execute_command(command)

            except KeyboardInterrupt:
                console.print("\n[yellow]操作已取消[/yellow]")
            except EOFError:
                console.print("\n[yellow]退出交互模式[/yellow]")
                break
            except Exception as e:
                logger.error(f"交互模式异常: {e}")
                console.print(f"[red]发生错误: {str(e)}[/red]")


@click.command()
@click.option("--history", "-h", is_flag=True, help="显示命令历史记录")
@click.option("--execute", "-e", help="执行单个命令后退出")
@cli_error_handler
def interactive(history: bool, execute: Optional[str]) -> None:
    """启动交互式命令模式"""
    from .main import cli  # 避免循环导入

    logger.debug("启动交互式命令模式")

    runner = InteractiveCommandRunner(cli)

    if history:
        # 只显示历史记录
        runner._show_history()
        return

    if execute:
        # 执行单个命令后退出
        runner._execute_command(execute)
        return

    # 启动交互式会话
    runner.run()
