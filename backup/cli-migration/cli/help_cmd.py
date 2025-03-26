"""
帮助命令实现
"""

import sys
from pathlib import Path
from typing import List, Optional

from .help import HelpManager


def help_command(args: Optional[List[str]] = None) -> int:
    """
    帮助命令入口

    Args:
        args: 命令行参数列表

    Returns:
        退出码
    """
    if args is None:
        args = sys.argv[1:]

    # 创建帮助管理器
    help_manager = HelpManager()

    # 解析参数
    if not args:
        # 显示总体帮助
        help_manager.show_help()
    else:
        # 显示特定主题的帮助
        help_manager.show_help(args[0])

    return 0


if __name__ == "__main__":
    sys.exit(help_command())
