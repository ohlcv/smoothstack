"""
交互式界面工具模块，提供交互式命令行界面组件
"""

import sys
import os
from typing import (
    List,
    Dict,
    Any,
    Optional,
    Union,
    Callable,
    TypeVar,
    Generic,
    Tuple,
    cast,
)
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.columns import Columns
from rich.syntax import Syntax

from .logger import get_logger
from .errors import UserError

# 创建日志记录器
logger = get_logger("interactive")

# 创建控制台实例
console = Console()

# 定义类型变量
T = TypeVar("T")


class InteractivePrompt:
    """
    交互式提示工具类
    """

    @staticmethod
    def text(
        message: str,
        default: Optional[str] = None,
        choices: Optional[List[str]] = None,
        password: bool = False,
        show_default: bool = True,
        show_choices: bool = True,
    ) -> str:
        """
        提示用户输入文本

        Args:
            message: 提示信息
            default: 默认值
            choices: 可选值列表
            password: 是否为密码输入
            show_default: 是否显示默认值
            show_choices: 是否显示可选值

        Returns:
            用户输入的文本
        """
        try:
            result = Prompt.ask(
                message,
                default=default,
                choices=choices,
                password=password,
                show_default=show_default,
                show_choices=show_choices,
            )
            # 确保返回字符串，而不是None
            return result if result is not None else ""
        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            sys.exit(1)

    @staticmethod
    def confirm(message: str, default: bool = False, show_default: bool = True) -> bool:
        """
        提示用户确认

        Args:
            message: 提示信息
            default: 默认值
            show_default: 是否显示默认值

        Returns:
            用户确认结果
        """
        try:
            return Confirm.ask(message, default=default, show_default=show_default)
        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            sys.exit(1)

    @staticmethod
    def integer(
        message: str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        show_default: bool = True,
    ) -> int:
        """
        提示用户输入整数

        Args:
            message: 提示信息
            default: 默认值
            min_value: 最小值
            max_value: 最大值
            show_default: 是否显示默认值

        Returns:
            用户输入的整数
        """
        try:
            # Rich的IntPrompt.ask接受int类型参数，返回int
            result: int = IntPrompt.ask(
                message,
                default=default,
                show_default=show_default,
            )

            # 手动处理最小值和最大值约束
            if min_value is not None and result < min_value:
                console.print(f"[red]输入值必须大于或等于 {min_value}[/red]")
                # 递归调用自身，类型安全
                return InteractivePrompt.integer(
                    message, default, min_value, max_value, show_default
                )

            if max_value is not None and result > max_value:
                console.print(f"[red]输入值必须小于或等于 {max_value}[/red]")
                # 递归调用自身，类型安全
                return InteractivePrompt.integer(
                    message, default, min_value, max_value, show_default
                )

            return result
        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            sys.exit(1)
        except ValueError:
            console.print("[red]请输入有效的整数[/red]")
            # 递归调用自身，类型安全
            return InteractivePrompt.integer(
                message, default, min_value, max_value, show_default
            )

    @staticmethod
    def select(
        message: str,
        choices: List[str],
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """
        提示用户从列表中选择一项

        Args:
            message: 提示信息
            choices: 可选项列表
            default: 默认选项
            show_default: 是否显示默认值

        Returns:
            用户选择的项
        """
        if not choices:
            raise UserError("选项列表不能为空")

        # 构建选择提示
        if show_default and default:
            default_index = choices.index(default) + 1 if default in choices else None
        else:
            default_index = None

        # 显示选择菜单
        console.print(f"{message}:")
        for i, choice in enumerate(choices, 1):
            if default and choice == default:
                console.print(f"  {i}. [green]{choice}[/green] (默认)")
            else:
                console.print(f"  {i}. {choice}")

        # 获取用户选择
        while True:
            try:
                if default_index:
                    choice_prompt = f"请选择 (1-{len(choices)}) [默认: {default_index}]"
                else:
                    choice_prompt = f"请选择 (1-{len(choices)})"

                choice_input = Prompt.ask(
                    choice_prompt, default=str(default_index or "")
                )

                if not choice_input and default:
                    return default

                choice_index = int(choice_input)
                if 1 <= choice_index <= len(choices):
                    return choices[choice_index - 1]
                else:
                    console.print(f"[red]无效的选择: {choice_index}，请重新选择[/red]")
            except ValueError:
                console.print("[red]请输入有效的数字[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow]操作已取消[/yellow]")
                sys.exit(1)

    @staticmethod
    def multi_select(
        message: str,
        choices: List[str],
        defaults: Optional[List[str]] = None,
        min_selections: int = 0,
        max_selections: Optional[int] = None,
    ) -> List[str]:
        """
        提示用户从列表中选择多项

        Args:
            message: 提示信息
            choices: 可选项列表
            defaults: 默认选中的项
            min_selections: 最少选择数量
            max_selections: 最多选择数量

        Returns:
            用户选择的项列表
        """
        if not choices:
            raise UserError("选项列表不能为空")

        defaults = defaults or []

        # 显示选择菜单
        selection_limit = ""
        if min_selections > 0 and max_selections:
            selection_limit = f" (请选择 {min_selections}-{max_selections} 项)"
        elif min_selections > 0:
            selection_limit = f" (请至少选择 {min_selections} 项)"
        elif max_selections:
            selection_limit = f" (请最多选择 {max_selections} 项)"

        console.print(f"{message}{selection_limit}:")
        for i, choice in enumerate(choices, 1):
            mark = "[x]" if choice in defaults else "[ ]"
            if choice in defaults:
                console.print(f"  {i}. [green]{mark} {choice}[/green]")
            else:
                console.print(f"  {i}. {mark} {choice}")

        # 获取用户选择
        try:
            selection_input = Prompt.ask(
                "请输入选项编号，用逗号分隔多个选项 (例如: 1,3,5)"
            )

            if not selection_input and defaults:
                return defaults

            # 解析选择
            selected_indices = []
            for part in selection_input.split(","):
                part = part.strip()
                if "-" in part:  # 处理范围，如 1-3
                    start, end = part.split("-")
                    selected_indices.extend(range(int(start), int(end) + 1))
                else:
                    selected_indices.append(int(part))

            # 验证选择
            selected_items = []
            for idx in selected_indices:
                if 1 <= idx <= len(choices):
                    selected_items.append(choices[idx - 1])
                else:
                    console.print(f"[yellow]忽略无效的选择: {idx}[/yellow]")

            # 检查选择数量
            if min_selections > 0 and len(selected_items) < min_selections:
                console.print(f"[red]请至少选择 {min_selections} 项[/red]")
                return InteractivePrompt.multi_select(
                    message, choices, defaults, min_selections, max_selections
                )

            if max_selections and len(selected_items) > max_selections:
                console.print(f"[red]请最多选择 {max_selections} 项[/red]")
                return InteractivePrompt.multi_select(
                    message, choices, defaults, min_selections, max_selections
                )

            return selected_items

        except ValueError:
            console.print("[red]请输入有效的数字[/red]")
            return InteractivePrompt.multi_select(
                message, choices, defaults, min_selections, max_selections
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            sys.exit(1)

    @staticmethod
    def path(
        message: str,
        default: Optional[str] = None,
        file_okay: bool = True,
        dir_okay: bool = True,
        exists: bool = False,
        create_missing: bool = False,
    ) -> str:
        """
        提示用户输入文件路径

        Args:
            message: 提示信息
            default: 默认路径
            file_okay: 是否接受文件路径
            dir_okay: 是否接受目录路径
            exists: 路径是否必须存在
            create_missing: 是否创建不存在的目录

        Returns:
            用户输入的路径
        """
        try:
            while True:
                path_input = Prompt.ask(message, default=default or "")
                path_str = str(path_input)  # 确保是字符串
                path = Path(path_str)

                # 检查路径是否存在
                if exists and not path.exists():
                    console.print(f"[red]路径不存在: {path_str}[/red]")
                    continue

                # 检查路径类型
                if path.exists():
                    if path.is_file() and not file_okay:
                        console.print(f"[red]不接受文件路径: {path_str}[/red]")
                        continue
                    if path.is_dir() and not dir_okay:
                        console.print(f"[red]不接受目录路径: {path_str}[/red]")
                        continue
                elif create_missing and dir_okay:
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        console.print(f"[green]已创建目录: {path_str}[/green]")
                    except OSError as e:
                        console.print(f"[red]创建目录失败: {e}[/red]")
                        continue

                return path_str

        except KeyboardInterrupt:
            console.print("\n[yellow]操作已取消[/yellow]")
            sys.exit(1)


class InteractiveProgress:
    """
    交互式进度显示工具类
    """

    def __init__(self, description: str = "处理中"):
        """
        初始化进度显示

        Args:
            description: 进度描述
        """
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold]{task.percentage:>3.0f}%"),
            TextColumn("[cyan]{task.fields[status]}"),
        )
        self.description = description
        self.task_id: Optional[TaskID] = None

    def __enter__(self) -> "InteractiveProgress":
        """
        进入上下文
        """
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=100, status="")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文
        """
        self.progress.stop()

    def update(
        self, advance: Optional[float] = None, status: Optional[str] = None
    ) -> None:
        """
        更新进度

        Args:
            advance: 进度增量
            status: 状态文本
        """
        if self.task_id is not None:
            kwargs = {}
            if advance is not None:
                kwargs["advance"] = advance
            if status is not None:
                kwargs["status"] = status
            self.progress.update(self.task_id, **kwargs)

    def complete(self, status: str = "完成") -> None:
        """
        标记任务为完成

        Args:
            status: 完成状态文本
        """
        if self.task_id is not None:
            self.progress.update(self.task_id, completed=100, status=status)


class InteractiveTable:
    """
    交互式表格工具类
    """

    @staticmethod
    def display(
        data: List[Dict[str, Any]],
        columns: List[Tuple[str, str]],
        title: Optional[str] = None,
    ) -> None:
        """
        显示数据表格

        Args:
            data: 数据列表，每一项是一个字典
            columns: 列定义列表，每一项是(key, title)元组
            title: 表格标题
        """
        table = Table(title=title)

        # 添加表头
        for key, header in columns:
            table.add_column(header)

        # 添加数据行
        for item in data:
            row = []
            for key, _ in columns:
                value = item.get(key, "")
                row.append(str(value))
            table.add_row(*row)

        # 显示表格
        console.print(table)

    @staticmethod
    def select(
        data: List[Dict[str, Any]],
        columns: List[Tuple[str, str]],
        title: Optional[str] = None,
        id_key: str = "id",
        multi: bool = False,
        min_selections: int = 0,
        max_selections: Optional[int] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        显示数据表格并让用户选择

        Args:
            data: 数据列表，每一项是一个字典
            columns: 列定义列表，每一项是(key, title)元组
            title: 表格标题
            id_key: 标识列的键名
            multi: 是否允许多选
            min_selections: 最少选择数量
            max_selections: 最多选择数量

        Returns:
            用户选择的数据项或数据项列表
        """
        if not data:
            raise UserError("表格数据不能为空")

        # 显示表格
        table = Table(title=title)
        table.add_column("#", style="cyan")

        # 添加表头
        for key, header in columns:
            table.add_column(header)

        # 添加数据行
        for i, item in enumerate(data, 1):
            row = [str(i)]
            for key, _ in columns:
                value = item.get(key, "")
                row.append(str(value))
            table.add_row(*row)

        console.print(table)

        # 获取用户选择
        if multi:
            # 多选模式
            selection_limit = ""
            if min_selections > 0 and max_selections:
                selection_limit = f" (请选择 {min_selections}-{max_selections} 项)"
            elif min_selections > 0:
                selection_limit = f" (请至少选择 {min_selections} 项)"
            elif max_selections:
                selection_limit = f" (请最多选择 {max_selections} 项)"

            try:
                selection_input = Prompt.ask(
                    f"请输入选项编号，用逗号分隔多个选项 (例如: 1,3,5){selection_limit}"
                )

                # 解析选择
                selected_indices = []
                for part in selection_input.split(","):
                    part = part.strip()
                    if "-" in part:  # 处理范围，如 1-3
                        start, end = part.split("-")
                        selected_indices.extend(range(int(start), int(end) + 1))
                    else:
                        selected_indices.append(int(part))

                # 验证选择
                selected_items = []
                for idx in selected_indices:
                    if 1 <= idx <= len(data):
                        selected_items.append(data[idx - 1])
                    else:
                        console.print(f"[yellow]忽略无效的选择: {idx}[/yellow]")

                # 检查选择数量
                if min_selections > 0 and len(selected_items) < min_selections:
                    console.print(f"[red]请至少选择 {min_selections} 项[/red]")
                    return InteractiveTable.select(
                        data,
                        columns,
                        title,
                        id_key,
                        multi,
                        min_selections,
                        max_selections,
                    )

                if max_selections and len(selected_items) > max_selections:
                    console.print(f"[red]请最多选择 {max_selections} 项[/red]")
                    return InteractiveTable.select(
                        data,
                        columns,
                        title,
                        id_key,
                        multi,
                        min_selections,
                        max_selections,
                    )

                return selected_items

            except ValueError:
                console.print("[red]请输入有效的数字[/red]")
                return InteractiveTable.select(
                    data, columns, title, id_key, multi, min_selections, max_selections
                )
            except KeyboardInterrupt:
                console.print("\n[yellow]操作已取消[/yellow]")
                sys.exit(1)
        else:
            # 单选模式
            while True:
                try:
                    choice_input = Prompt.ask(f"请选择 (1-{len(data)})")
                    choice_index = int(choice_input)

                    if 1 <= choice_index <= len(data):
                        return data[choice_index - 1]
                    else:
                        console.print(
                            f"[red]无效的选择: {choice_index}，请重新选择[/red]"
                        )
                except ValueError:
                    console.print("[red]请输入有效的数字[/red]")
                except KeyboardInterrupt:
                    console.print("\n[yellow]操作已取消[/yellow]")
                    sys.exit(1)


class InteractiveForm:
    """
    交互式表单工具类
    """

    @staticmethod
    def input(
        fields: List[Dict[str, Any]], title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        显示表单并获取用户输入

        Args:
            fields: 表单字段列表
            title: 表单标题

        Returns:
            用户输入的数据
        """
        if title:
            console.print(f"[bold]{title}[/bold]")

        result = {}
        for field in fields:
            field_type = field.get("type", "text")
            name = field["name"]
            label = field.get("label", name)
            required = field.get("required", False)
            default = field.get("default")
            choices = field.get("choices")
            validator = field.get("validator")
            min_value = field.get("min")
            max_value = field.get("max")
            help_text = field.get("help")

            # 显示帮助文本
            if help_text:
                console.print(f"[dim]{help_text}[/dim]")

            # 处理必填标记
            required_mark = " [red]*[/red]" if required else ""
            prompt_text = f"{label}{required_mark}"

            # 根据字段类型处理输入
            value = None
            while value is None:
                try:
                    if field_type == "text":
                        value = InteractivePrompt.text(
                            prompt_text, default=default, choices=choices
                        )
                    elif field_type == "password":
                        value = InteractivePrompt.text(
                            prompt_text, default=default, password=True
                        )
                    elif field_type == "number":
                        value = InteractivePrompt.integer(
                            prompt_text,
                            default=default,
                            min_value=min_value,
                            max_value=max_value,
                        )
                    elif field_type == "boolean":
                        value = InteractivePrompt.confirm(
                            prompt_text, default=default or False
                        )
                    elif field_type == "select":
                        if not choices:
                            raise UserError(f"字段 {name} 的选项列表为空")
                        value = InteractivePrompt.select(
                            prompt_text, choices, default=default
                        )
                    elif field_type == "multiselect":
                        if not choices:
                            raise UserError(f"字段 {name} 的选项列表为空")
                        value = InteractivePrompt.multi_select(
                            prompt_text,
                            choices,
                            defaults=default,
                            min_selections=min_value or 0,
                            max_selections=max_value,
                        )
                    elif field_type == "path":
                        value = InteractivePrompt.path(
                            prompt_text,
                            default=default,
                            exists=field.get("exists", False),
                            file_okay=field.get("file_okay", True),
                            dir_okay=field.get("dir_okay", True),
                            create_missing=field.get("create_missing", False),
                        )
                    else:
                        raise UserError(f"不支持的字段类型: {field_type}")

                    # 验证输入
                    if validator and callable(validator):
                        try:
                            value = validator(value)
                        except Exception as e:
                            console.print(f"[red]验证失败: {str(e)}[/red]")
                            value = None
                            continue

                    # 验证必填
                    if required and (value is None or value == "" or value == []):
                        console.print("[red]此字段为必填项[/red]")
                        value = None
                        continue

                except KeyboardInterrupt:
                    console.print("\n[yellow]操作已取消[/yellow]")
                    sys.exit(1)

            # 保存结果
            result[name] = value

        return result


class InteractiveWizard(Generic[T]):
    """
    交互式向导工具类
    """

    def __init__(self, title: str):
        """
        初始化向导

        Args:
            title: 向导标题
        """
        self.title = title
        self.steps: List[Dict[str, Any]] = []
        self.data: Dict[str, Any] = {}

    def add_step(
        self,
        title: str,
        handler: Callable[[Dict[str, Any]], Any],
        optional: bool = False,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> "InteractiveWizard[T]":
        """
        添加向导步骤

        Args:
            title: 步骤标题
            handler: 步骤处理函数
            optional: 是否为可选步骤
            condition: 步骤条件函数，返回True时才执行此步骤

        Returns:
            向导实例
        """
        self.steps.append(
            {
                "title": title,
                "handler": handler,
                "optional": optional,
                "condition": condition,
            }
        )
        return self

    def run(self) -> T:
        """
        运行向导

        Returns:
            向导执行结果
        """
        console.print(f"[bold blue]===== {self.title} =====[/bold blue]")

        # 显示步骤概览
        console.print("\n[bold]向导步骤：[/bold]")
        for i, step in enumerate(self.steps, 1):
            optional_text = " [dim](可选)[/dim]" if step["optional"] else ""
            console.print(f"{i}. {step['title']}{optional_text}")

        console.print("\n[dim]按 Ctrl+C 随时取消向导[/dim]\n")

        # 执行每个步骤
        try:
            for i, step in enumerate(self.steps, 1):
                # 检查条件
                condition = step["condition"]
                if condition and not condition(self.data):
                    logger.debug(f"跳过步骤 {i}: {step['title']} (条件不满足)")
                    continue

                # 显示步骤标题
                console.print(f"[bold cyan]步骤 {i}: {step['title']}[/bold cyan]")

                # 如果是可选步骤，询问是否执行
                if step["optional"]:
                    execute = InteractivePrompt.confirm("是否执行此步骤?", default=True)
                    if not execute:
                        logger.debug(f"跳过步骤 {i}: {step['title']} (用户选择跳过)")
                        continue

                # 执行步骤处理函数
                handler = step["handler"]
                result = handler(self.data)

                # 如果有返回值，更新数据
                if isinstance(result, dict):
                    self.data.update(result)

                console.print()  # 添加空行分隔

            # 向导完成
            console.print(f"[bold green]===== {self.title} 完成 =====[/bold green]")

            # 返回结果
            if hasattr(self, "result_handler") and callable(
                getattr(self, "result_handler")
            ):
                return getattr(self, "result_handler")(self.data)
            return self.data  # type: ignore

        except KeyboardInterrupt:
            console.print("\n[yellow]向导已取消[/yellow]")
            sys.exit(1)

    def set_result_handler(
        self, handler: Callable[[Dict[str, Any]], T]
    ) -> "InteractiveWizard[T]":
        """
        设置结果处理函数

        Args:
            handler: 结果处理函数

        Returns:
            向导实例
        """
        self.result_handler = handler
        return self
