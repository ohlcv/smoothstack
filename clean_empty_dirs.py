#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除当前目录及其子目录中的所有空文件夹
"""

import os
import sys
import argparse
import time
from typing import List, Tuple, Dict


# 定义ANSI颜色代码
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def is_dir_empty(path: str) -> bool:
    """
    检查目录是否为空（不包含任何文件或子目录）

    参数:
        path: 目录路径

    返回:
        bool: 如果目录为空则返回True，否则返回False
    """
    return len(os.listdir(path)) == 0


def find_empty_dirs(
    start_path: str = ".", ignore_dirs: List[str] = None
) -> Tuple[List[str], Dict]:
    """
    递归查找所有空目录

    参数:
        start_path: 开始搜索的路径，默认为当前目录
        ignore_dirs: 要忽略的目录名列表

    返回:
        Tuple[List[str], Dict]: 空目录路径列表和统计信息
    """
    if ignore_dirs is None:
        ignore_dirs = [".git", ".svn", ".hg", "__pycache__", "node_modules"]

    # 检查起始路径是否存在
    if not os.path.exists(start_path):
        print(f"{Colors.RED}错误：路径不存在 - {start_path}{Colors.RESET}")
        sys.exit(1)

    empty_dirs = []
    stats = {
        "total_dirs": 0,
        "scanned_dirs": 0,
        "ignored_dirs": 0,
        "start_time": time.time(),
    }

    for root, dirs, files in os.walk(start_path, topdown=False):
        stats["total_dirs"] += len(dirs) + 1  # +1 for current directory

        # 过滤掉要忽略的目录
        ignored = [d for d in dirs if d in ignore_dirs]
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        stats["ignored_dirs"] += len(ignored)

        # 检查当前目录是否为空
        # 由于我们使用 topdown=False，所以我们先处理子目录
        # 这意味着当我们到达这个目录时，子目录可能已经被删除
        stats["scanned_dirs"] += 1
        if root != start_path and not os.listdir(root):  # 避免删除起始目录
            empty_dirs.append(root)

    stats["end_time"] = time.time()
    stats["duration"] = stats["end_time"] - stats["start_time"]

    return empty_dirs, stats


def remove_empty_dirs(
    dirs: List[str], dry_run: bool = False
) -> Tuple[int, List[str], List[str]]:
    """
    删除指定的空目录

    参数:
        dirs: 要删除的目录路径列表
        dry_run: 如果为True，则只打印将要删除的目录而不实际删除

    返回:
        Tuple[int, List[str], List[str]]: 成功删除的目录数量、成功列表和失败的目录列表
    """
    count = 0
    failed = []
    succeeded = []

    for dir_path in dirs:
        try:
            if not dry_run:
                os.rmdir(dir_path)
                print(f"{Colors.GREEN}已删除{Colors.RESET}: {dir_path}")
                succeeded.append(dir_path)
            else:
                print(f"{Colors.YELLOW}将删除{Colors.RESET}: {dir_path}")
                succeeded.append(dir_path)
            count += 1
        except OSError as e:
            print(
                f"{Colors.RED}错误{Colors.RESET}: 无法删除 {dir_path}: {e}",
                file=sys.stderr,
            )
            failed.append(dir_path)

    return count, succeeded, failed


def get_user_confirmation(count: int) -> bool:
    """
    获取用户确认

    参数:
        count: 要删除的目录数量

    返回:
        bool: 用户是否确认删除
    """
    while True:
        response = input(
            f"\n{Colors.YELLOW}确认删除这 {count} 个空文件夹吗? (y/n): {Colors.RESET}"
        ).lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("请输入 'y' 或 'n'")


def print_summary(
    stats: Dict, count: int, succeeded: List[str], failed: List[str], dry_run: bool
):
    """
    打印操作摘要

    参数:
        stats: 统计信息
        count: 删除的目录数量
        succeeded: 成功删除的目录列表
        failed: 失败的目录列表
        dry_run: 是否是干运行模式
    """
    print(f"\n{Colors.BOLD}{'删除预览' if dry_run else '删除结果'} 摘要{Colors.RESET}")
    print(f"{'=' * 50}")
    print(f"扫描目录总数: {stats['scanned_dirs']}")
    print(f"忽略的目录: {stats['ignored_dirs']}")
    print(f"找到的空目录: {len(succeeded) + len(failed)}")
    print(f"{'将删除' if dry_run else '成功删除'}: {Colors.GREEN}{count}{Colors.RESET}")

    if failed:
        print(f"删除失败: {Colors.RED}{len(failed)}{Colors.RESET}")

    print(f"扫描用时: {stats['duration']:.2f} 秒")
    print(f"{'=' * 50}")


def main():
    parser = argparse.ArgumentParser(
        description="清除当前目录及其子目录中的所有空文件夹"
    )
    parser.add_argument(
        "-p", "--path", default=".", help="开始搜索的路径，默认为当前目录"
    )
    parser.add_argument("-i", "--ignore", nargs="+", help="要忽略的目录名列表")
    parser.add_argument(
        "-d", "--dry-run", action="store_true", help="仅显示将要删除的目录，不实际删除"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细输出")
    parser.add_argument("-y", "--yes", action="store_true", help="不提示确认，直接删除")
    parser.add_argument(
        "-l", "--list", action="store_true", help="删除后列出所有已删除的文件夹"
    )
    parser.add_argument("--no-color", action="store_true", help="禁用彩色输出")

    args = parser.parse_args()

    # 如果禁用彩色输出，重置颜色代码
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith("__"):
                setattr(Colors, attr, "")

    try:
        start_path = os.path.abspath(args.path)

        if not os.path.exists(start_path):
            print(f"{Colors.RED}错误：路径不存在 - {start_path}{Colors.RESET}")
            return 1

        ignore_dirs = args.ignore or [
            ".git",
            ".svn",
            ".hg",
            "__pycache__",
            "node_modules",
        ]

        print(f"{Colors.CYAN}空文件夹清理工具{Colors.RESET}")

        if args.verbose:
            print(f"{Colors.BOLD}开始搜索路径{Colors.RESET}: {start_path}")
            print(f"{Colors.BOLD}忽略的目录{Colors.RESET}: {', '.join(ignore_dirs)}")

        print(f"正在扫描空文件夹...", end="", flush=True)
        empty_dirs, stats = find_empty_dirs(start_path, ignore_dirs)
        print(f"\r{' ' * 30}\r", end="")  # 清除"正在扫描"消息

        if not empty_dirs:
            print(f"{Colors.GREEN}未找到空文件夹。{Colors.RESET}")
            return 0

        # 按深度排序，确保先删除最深的目录
        empty_dirs.sort(key=lambda x: x.count(os.sep), reverse=True)

        if args.verbose:
            print(f"\n{Colors.BOLD}找到 {len(empty_dirs)} 个空文件夹:{Colors.RESET}")
            for d in empty_dirs:
                print(f"  {d}")

        # 干运行模式或者获取用户确认
        proceed = True
        if not args.dry_run and not args.yes:
            if args.verbose:
                print("\n要删除的空文件夹:")
                for d in empty_dirs[:10]:  # 只显示前10个
                    print(f"  {d}")
                if len(empty_dirs) > 10:
                    print(f"  ...以及其他 {len(empty_dirs) - 10} 个目录")
            proceed = get_user_confirmation(len(empty_dirs))

        if proceed:
            count, succeeded, failed = remove_empty_dirs(empty_dirs, args.dry_run)

            # 打印摘要
            print_summary(stats, count, succeeded, failed, args.dry_run)

            # 如果请求了详细列表并且有成功删除的项目
            if args.list and succeeded:
                print(
                    f"\n{Colors.BOLD}{'将要删除' if args.dry_run else '已删除'}的文件夹列表:{Colors.RESET}"
                )
                for i, path in enumerate(succeeded, 1):
                    print(f"  {i}. {path}")

            # 如果有失败项
            if failed:
                print(f"\n{Colors.RED}{Colors.BOLD}删除失败的文件夹:{Colors.RESET}")
                for i, path in enumerate(failed, 1):
                    print(f"  {i}. {path}")
        else:
            print(f"\n{Colors.YELLOW}操作已取消。{Colors.RESET}")

        return 0
    except Exception as e:
        print(f"{Colors.RED}发生错误: {str(e)}{Colors.RESET}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
