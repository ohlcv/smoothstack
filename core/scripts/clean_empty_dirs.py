#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 - 清除当前目录及其子目录中的所有空文件夹
"""

import os
import sys


def main():
    """主函数，清理当前目录下的空文件夹"""
    print("开始查找空文件夹...")

    # 获取当前目录
    current_path = os.getcwd()
    print(f"当前工作目录: {current_path}")

    # 检查当前目录是否存在
    if not os.path.exists(current_path):
        print(f"错误: 当前工作目录不存在: {current_path}")
        return 1

    # 记录找到的空目录
    empty_dirs = []

    # 递归查找空目录
    for root, dirs, files in os.walk(current_path, topdown=False):
        # 跳过某些目录
        dirs[:] = [d for d in dirs if d not in [".git", ".svn", "__pycache__"]]

        # 检查当前目录是否为空(且不是根目录)
        if root != current_path and not os.listdir(root):
            empty_dirs.append(root)

    # 输出结果
    if not empty_dirs:
        print("未找到空文件夹")
        return 0

    print(f"\n找到 {len(empty_dirs)} 个空文件夹:")
    for d in empty_dirs:
        print(f"  {d}")

    # 询问是否删除
    choice = input("\n是否删除这些空文件夹? (y/n): ").lower()
    if choice not in ("y", "yes"):
        print("操作已取消")
        return 0

    # 删除空目录
    deleted = 0
    for d in empty_dirs:
        try:
            os.rmdir(d)
            print(f"已删除: {d}")
            deleted += 1
        except OSError as e:
            print(f"错误: 无法删除 {d}: {e}")

    print(f"\n成功删除 {deleted} 个空文件夹")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
