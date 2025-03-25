#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库迁移工具

用于自动生成和应用数据库迁移脚本
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional

# 添加项目根目录到PATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入数据库连接管理器
from backend.database.connection import get_connection


def run_command(command: List[str], check: bool = True) -> int:
    """
    运行外部命令

    Args:
        command: 要运行的命令和参数
        check: 是否检查返回值

    Returns:
        命令的退出代码
    """
    print(f"执行命令: {' '.join(command)}")
    result = subprocess.run(command, check=check)
    return result.returncode


def generate_migration(message: str) -> int:
    """
    生成迁移脚本

    Args:
        message: 迁移说明

    Returns:
        命令的退出代码
    """
    return run_command(["alembic", "revision", "--autogenerate", "-m", message])


def upgrade_database(revision: Optional[str] = "head") -> int:
    """
    升级数据库

    Args:
        revision: 要升级到的版本，默认为最新

    Returns:
        命令的退出代码
    """
    return run_command(["alembic", "upgrade", str(revision)])


def downgrade_database(revision: str) -> int:
    """
    降级数据库

    Args:
        revision: 要降级到的版本

    Returns:
        命令的退出代码
    """
    return run_command(["alembic", "downgrade", revision])


def show_history() -> int:
    """
    显示迁移历史

    Returns:
        命令的退出代码
    """
    return run_command(["alembic", "history", "--verbose"])


def show_current() -> int:
    """
    显示当前版本

    Returns:
        命令的退出代码
    """
    return run_command(["alembic", "current"])


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库迁移工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 生成迁移命令
    generate_parser = subparsers.add_parser("generate", help="生成迁移脚本")
    generate_parser.add_argument("-m", "--message", required=True, help="迁移说明")

    # 升级数据库命令
    upgrade_parser = subparsers.add_parser("upgrade", help="升级数据库")
    upgrade_parser.add_argument(
        "-r", "--revision", default="head", help="要升级到的版本，默认为最新"
    )

    # 降级数据库命令
    downgrade_parser = subparsers.add_parser("downgrade", help="降级数据库")
    downgrade_parser.add_argument(
        "-r", "--revision", required=True, help="要降级到的版本"
    )

    # 显示历史命令
    subparsers.add_parser("history", help="显示迁移历史")

    # 显示当前版本命令
    subparsers.add_parser("current", help="显示当前版本")

    # 初始化数据库命令
    subparsers.add_parser("init", help="初始化数据库")

    args = parser.parse_args()

    # 确保数据库连接初始化
    get_connection().init_engines()

    # 执行相应的命令
    if args.command == "generate":
        return generate_migration(args.message)
    elif args.command == "upgrade":
        return upgrade_database(args.revision)
    elif args.command == "downgrade":
        return downgrade_database(args.revision)
    elif args.command == "history":
        return show_history()
    elif args.command == "current":
        return show_current()
    elif args.command == "init":
        # 初始化数据库，相当于升级到最新版本
        return upgrade_database()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
