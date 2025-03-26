"""
清理命令
"""

import os
from pathlib import Path
from typing import List
from .base import BaseCommand


class CleanCommand(BaseCommand):
    """清理命令类"""

    def empty_dirs(self):
        """清理空目录"""
        self.info("开始查找空文件夹...")

        # 获取当前目录
        current_path = self.project_root
        self.info(f"当前工作目录: {current_path}")

        # 检查当前目录是否存在
        if not os.path.exists(current_path):
            raise RuntimeError(f"当前工作目录不存在: {current_path}")

        # 记录找到的空目录
        empty_dirs: List[str] = []

        # 递归查找空目录
        for root, dirs, files in os.walk(current_path, topdown=False):
            # 跳过某些目录
            dirs[:] = [d for d in dirs if d not in [".git", ".svn", "__pycache__"]]

            # 检查当前目录是否为空(且不是根目录)
            if root != str(current_path) and not os.listdir(root):
                empty_dirs.append(root)

        # 输出结果
        if not empty_dirs:
            self.info("未找到空文件夹")
            return

        self.info(f"\n找到 {len(empty_dirs)} 个空文件夹:")
        for d in empty_dirs:
            self.info(f"  {d}")

        # 询问是否删除
        choice = input("\n是否删除这些空文件夹? (y/n): ").lower()
        if choice not in ("y", "yes"):
            self.info("操作已取消")
            return

        # 删除空目录
        deleted = 0
        for d in empty_dirs:
            try:
                os.rmdir(d)
                self.info(f"已删除: {d}")
                deleted += 1
            except OSError as e:
                self.error(f"错误: 无法删除 {d}: {e}")

        self.success(f"\n成功删除 {deleted} 个空文件夹")
