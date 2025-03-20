"""
错误处理模块，提供自定义异常类和错误处理函数
"""

import sys
import traceback
from typing import Optional, Any, Type, Dict, List, Callable, cast

from rich.console import Console
from rich.panel import Panel
from rich.traceback import Traceback

from .logger import get_logger


# 创建日志记录器
logger = get_logger("errors")

# 控制台实例
console = Console(stderr=True)


class SmoothstackError(Exception):
    """Smoothstack错误基类"""

    error_code = "E000"
    message = "未知错误"

    def __init__(self, message: Optional[str] = None, details: Optional[str] = None):
        """
        初始化Smoothstack错误

        Args:
            message: 错误消息，如果为None则使用类定义的消息
            details: 错误详情
        """
        self.custom_message = message
        self.details = details
        super().__init__(self.get_message())

    def get_message(self) -> str:
        """获取错误消息"""
        if self.custom_message:
            return self.custom_message
        return self.message

    def get_details(self) -> Optional[str]:
        """获取错误详情"""
        return self.details

    def get_error_code(self) -> str:
        """获取错误代码"""
        return self.error_code

    def __str__(self) -> str:
        """返回错误字符串表示"""
        msg = f"{self.get_message()} [错误代码: {self.get_error_code()}]"
        if self.details:
            msg += f"\n详情: {self.details}"
        return msg


class UserError(SmoothstackError):
    """用户错误，表示用户操作引起的错误"""

    error_code = "E001"
    message = "用户操作错误"


class ConfigError(UserError):
    """配置错误，表示配置相关的用户错误"""

    pass


class CommandError(UserError):
    """命令错误，表示命令执行过程中的用户错误"""

    pass


class NetworkError(UserError):
    """网络错误，表示网络连接或请求相关的错误"""

    pass


class FileError(UserError):
    """文件错误，表示文件操作相关的用户错误"""

    pass


class InputError(SmoothstackError):
    """输入错误"""

    error_code = "E300"
    message = "输入错误"


class ValidationError(SmoothstackError):
    """验证错误"""

    error_code = "E400"
    message = "验证错误"


class FileSystemError(SmoothstackError):
    """文件系统错误"""

    error_code = "E500"
    message = "文件系统错误"


class DependencyError(SmoothstackError):
    """依赖管理错误"""

    error_code = "E300"
    message = "依赖管理错误"


class ContainerError(SmoothstackError):
    """容器管理错误"""

    error_code = "E400"
    message = "容器管理错误"


class InternalError(SmoothstackError):
    """内部错误，通常是编程问题"""

    error_code = "E800"
    message = "内部错误"
    severity = "critical"
    show_traceback = True


# 错误处理函数类型
ErrorHandler = Callable[[Exception], Optional[bool]]

# 错误处理器注册表
_error_handlers: Dict[Type[Exception], List[ErrorHandler]] = {}


def register_error_handler(
    exception_type: Type[Exception], handler: ErrorHandler
) -> None:
    """
    注册错误处理器

    Args:
        exception_type: 要处理的异常类型
        handler: 错误处理函数
    """
    if exception_type not in _error_handlers:
        _error_handlers[exception_type] = []
    _error_handlers[exception_type].append(handler)


def handle_exception(exc: Exception) -> bool:
    """
    处理异常

    Args:
        exc: 要处理的异常

    Returns:
        bool: 是否成功处理异常
    """
    # 遍历异常类层次结构，从最具体的开始
    exc_type = type(exc)
    mro = exc_type.mro()

    for cls in mro:
        if cls in _error_handlers:
            handlers = _error_handlers[cls]
            for handler in handlers:
                try:
                    result = handler(exc)
                    # 如果处理器返回True，表示已经处理了异常
                    if result:
                        return True
                except Exception as handler_exc:
                    logger.error(f"错误处理器出错: {handler_exc}")

    # 没有找到处理器或所有处理器都返回False
    return False


def default_error_handler(exc: Exception) -> bool:
    """
    默认错误处理函数

    Args:
        exc: 要处理的异常

    Returns:
        bool: 始终返回True，表示已处理异常
    """
    exit_code = 1

    if isinstance(exc, SmoothstackError):
        # 自定义错误
        exit_code = exc.exit_code
        error_msg = str(exc)
        details = exc.details
        severity = exc.severity.upper()
        error_code = exc.error_code

        # 记录日志
        exc.log()

        # 获取堆栈跟踪
        traceback_obj = exc.get_traceback()
    else:
        # 标准异常
        error_msg = str(exc)
        details = None
        severity = "ERROR"
        error_code = "E999"

        # 记录日志
        logger.error(f"未处理的异常: {error_msg}")
        logger.debug(f"异常类型: {type(exc).__name__}")
        if hasattr(exc, "__traceback__") and exc.__traceback__:
            tb_str = "".join(traceback.format_tb(exc.__traceback__))
            logger.debug(f"堆栈跟踪:\n{tb_str}")

        # 获取堆栈跟踪
        traceback_obj = Traceback.from_exception(
            type(exc),
            exc,
            traceback=None,  # 让Rich自动提取堆栈跟踪
        )

    # 构建错误面板
    title = f"[bold red]{severity}[/bold red] - 错误代码: {error_code}"

    content = f"[bold]{error_msg}[/bold]"
    if details:
        content += f"\n\n{details}"

    panel = Panel(content, title=title, border_style="red")
    console.print(panel)

    # 显示堆栈跟踪
    if traceback_obj:
        console.print(traceback_obj)

    return True


# 注册默认错误处理器
register_error_handler(Exception, default_error_handler)


def cli_error_handler(func: Callable) -> Callable:
    """
    CLI命令错误处理装饰器

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            handled = handle_exception(exc)
            if not handled:
                # 如果没有处理器处理，使用默认处理
                default_error_handler(exc)

            # 获取退出码
            exit_code = getattr(exc, "exit_code", 1)
            sys.exit(exit_code)

    # 保留原函数的元数据
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = func.__annotations__

    return wrapper
