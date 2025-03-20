"""
版本更新检查命令模块，提供CLI工具版本更新检查命令
"""

import click
from rich.console import Console

from .utils.version import check_for_updates, display_update_info
from .utils.logger import get_logger
from .utils.errors import cli_error_handler, NetworkError

# 创建日志记录器
logger = get_logger("version_cmd")

# 创建控制台实例
console = Console()


@click.group()
def version():
    """版本管理命令"""
    pass


@version.command()
@click.option("--force", "-f", is_flag=True, help="强制检查更新（忽略缓存）")
@click.option("--silent", "-s", is_flag=True, help="静默模式，只在有更新时显示信息")
@cli_error_handler
def check(force: bool, silent: bool):
    """检查是否有新版本可用"""
    logger.debug(f"执行版本检查，参数：force={force}, silent={silent}")

    try:
        # 检查更新
        has_update, version_info = check_for_updates(
            show_current=not silent, force=force
        )

        # 显示版本信息
        if has_update or not silent:
            display_update_info(version_info, has_update)

        # 设置退出代码
        return 0 if not has_update else 1

    except NetworkError as e:
        if not silent:
            console.print(f"[red]检查更新失败: {str(e)}[/red]")
        logger.error(f"检查更新失败: {e}")
        return 2
