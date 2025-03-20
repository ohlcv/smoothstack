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
    """
    Smoothstack基础异常类
    """

    # 错误代码
    error_code = "E000"
    # 错误消息
    message = "发生了未知错误"
    # 错误严重程度
    severity = "error"
    # 退出码
    exit_code = 1
    # 是否显示堆栈跟踪
    show_traceback = False
    # 是否记录到日志
    log_error = True

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None,
        exit_code: Optional[int] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息，覆盖默认消息
            details: 错误的详细信息
            cause: 导致此错误的原始异常
            exit_code: 程序退出码
        """
        self.details = details
        self.cause = cause
        if exit_code is not None:
            self.exit_code = exit_code

        super().__init__(message or self.message)

    def __str__(self) -> str:
        """返回错误消息"""
        return self.args[0] if self.args else self.message

    def get_traceback(self) -> Optional[Traceback]:
        """获取格式化的堆栈跟踪"""
        if not self.show_traceback:
            return None

        if self.cause:
            # 返回原始异常的堆栈跟踪
            return Traceback.from_exception(
                type(self.cause),
                self.cause,
                traceback=None,  # 让Rich自动提取堆栈跟踪
            )

        # 返回当前异常的堆栈跟踪
        return Traceback.from_exception(
            type(self),
            self,
            traceback=None,  # 让Rich自动提取堆栈跟踪
        )

    def log(self) -> None:
        """将错误记录到日志"""
        if not self.log_error:
            return

        error_msg = str(self)
        if self.details:
            error_msg += f" - {self.details}"

        log_fn = getattr(logger, self.severity, logger.error)
        log_fn(f"错误 {self.error_code}: {error_msg}")

        if self.cause:
            logger.debug(f"原始异常: {self.cause!r}")
            if hasattr(self.cause, "__traceback__") and self.cause.__traceback__:
                tb_str = "".join(traceback.format_tb(self.cause.__traceback__))
                logger.debug(f"原始异常堆栈跟踪:\n{tb_str}")


class ConfigError(SmoothstackError):
    """配置错误"""

    error_code = "E100"
    message = "配置错误"


class CommandError(SmoothstackError):
    """命令执行错误"""

    error_code = "E200"
    message = "命令执行错误"


class DependencyError(SmoothstackError):
    """依赖管理错误"""

    error_code = "E300"
    message = "依赖管理错误"


class ContainerError(SmoothstackError):
    """容器管理错误"""

    error_code = "E400"
    message = "容器管理错误"


class FileSystemError(SmoothstackError):
    """文件系统错误"""

    error_code = "E500"
    message = "文件系统错误"


class NetworkError(SmoothstackError):
    """网络错误"""

    error_code = "E600"
    message = "网络错误"


class UserError(SmoothstackError):
    """用户错误，通常是用户输入问题"""

    error_code = "E700"
    message = "输入错误"
    severity = "warning"
    show_traceback = False


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
