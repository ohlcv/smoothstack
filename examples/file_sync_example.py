#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器内文件同步示例程序

演示如何配置和使用容器和宿主机之间的文件同步功能
"""

import os
import sys
import time
import logging
import argparse
import random
import string
from pathlib import Path
import threading
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("file_sync_example")

# 临时文件目录
TEMP_DIR_HOST = os.path.join(os.path.dirname(__file__), "sync_demo_host")
TEMP_DIR_CONTAINER = "/app/sync_demo_container"

# 模拟文件更改间隔（秒）
FILE_CHANGE_INTERVAL = 5


def create_sample_file(path, filename, content=None):
    """创建示例文件"""
    file_path = os.path.join(path, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 生成随机内容（如果未提供）
    if content is None:
        content = "".join(random.choices(string.ascii_letters + string.digits, k=100))
        content += f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"创建文件: {file_path}")
    return file_path


def create_initial_files():
    """创建初始示例文件"""
    # 创建主机端目录
    if os.path.exists(TEMP_DIR_HOST):
        logger.info(f"清理已存在的目录: {TEMP_DIR_HOST}")
        import shutil

        shutil.rmtree(TEMP_DIR_HOST)

    os.makedirs(TEMP_DIR_HOST, exist_ok=True)
    logger.info(f"创建主机端目录: {TEMP_DIR_HOST}")

    # 创建一些初始文件
    create_sample_file(
        TEMP_DIR_HOST, "file1.txt", "这是主机上的文件1\n可以验证它是否会同步到容器"
    )
    create_sample_file(
        TEMP_DIR_HOST, "file2.txt", "这是主机上的文件2\n可以验证它是否会同步到容器"
    )
    create_sample_file(
        TEMP_DIR_HOST,
        "subdir/file3.txt",
        "这是子目录中的文件\n测试目录结构是否正确同步",
    )

    # 创建排除和包含模式测试文件
    create_sample_file(TEMP_DIR_HOST, "exclude_me.tmp", "这个文件会被排除模式过滤")
    create_sample_file(TEMP_DIR_HOST, "include_me.py", "这个文件会被包含模式匹配")

    logger.info("初始文件创建完成")


def simulate_host_file_changes():
    """模拟主机端文件变化"""
    while True:
        try:
            # 随机决定操作类型
            operation = random.choice(["create", "update", "delete"])

            if operation == "create":
                # 创建新文件
                filename = f"host_new_{int(time.time())}.txt"
                create_sample_file(TEMP_DIR_HOST, filename)
                logger.info(f"[主机] 创建了新文件: {filename}")

            elif operation == "update":
                # 更新现有文件
                existing_files = []
                for root, _, files in os.walk(TEMP_DIR_HOST):
                    for file in files:
                        if not file.startswith(".") and not file.endswith(".tmp"):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, TEMP_DIR_HOST)
                            existing_files.append(rel_path)

                if existing_files:
                    file_to_update = random.choice(existing_files)
                    content = f"文件已在主机上更新\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n随机内容: {''.join(random.choices(string.ascii_letters, k=50))}"
                    create_sample_file(TEMP_DIR_HOST, file_to_update, content)
                    logger.info(f"[主机] 更新了文件: {file_to_update}")

            elif operation == "delete":
                # 删除文件
                existing_files = []
                for root, _, files in os.walk(TEMP_DIR_HOST):
                    for file in files:
                        if file.startswith("host_new_"):  # 只删除我们创建的临时文件
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, TEMP_DIR_HOST)
                            existing_files.append((rel_path, file_path))

                if existing_files:
                    rel_path, file_path = random.choice(existing_files)
                    os.remove(file_path)
                    logger.info(f"[主机] 删除了文件: {rel_path}")

            # 随机等待一段时间
            wait_time = random.uniform(
                FILE_CHANGE_INTERVAL * 0.8, FILE_CHANGE_INTERVAL * 1.2
            )
            time.sleep(wait_time)

        except Exception as e:
            logger.error(f"模拟主机文件变化时发生错误: {e}")
            time.sleep(2)  # 出错后短暂休息


def simulate_container_file_changes():
    """模拟容器端文件变化"""
    # 注意: 这个函数在真实环境中应该在容器内运行
    # 在这个演示中，我们假设主机上的另一个目录代表容器内部
    container_dir = os.path.join(os.path.dirname(__file__), "sync_demo_container")
    os.makedirs(container_dir, exist_ok=True)

    while True:
        try:
            # 随机决定操作类型
            operation = random.choice(["create", "update"])  # 排除删除操作以简化演示

            if operation == "create":
                # 创建新文件
                filename = f"container_new_{int(time.time())}.txt"
                file_path = os.path.join(container_dir, filename)
                content = f"这是容器内创建的文件\n创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n随机内容: {''.join(random.choices(string.ascii_letters, k=50))}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"[容器] 创建了新文件: {filename}")

            elif operation == "update":
                # 更新现有文件
                existing_files = []
                if os.path.exists(container_dir):
                    for root, _, files in os.walk(container_dir):
                        for file in files:
                            if not file.startswith("."):
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, container_dir)
                                existing_files.append((rel_path, file_path))

                if existing_files:
                    rel_path, file_path = random.choice(existing_files)
                    content = f"文件已在容器内更新\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n随机内容: {''.join(random.choices(string.ascii_letters, k=50))}"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"[容器] 更新了文件: {rel_path}")

            # 随机等待一段时间
            wait_time = random.uniform(
                FILE_CHANGE_INTERVAL * 0.8, FILE_CHANGE_INTERVAL * 1.2
            )
            time.sleep(wait_time)

        except Exception as e:
            logger.error(f"模拟容器文件变化时发生错误: {e}")
            time.sleep(2)  # 出错后短暂休息


def print_separator(title=None):
    """打印分隔符"""
    width = 80
    if title:
        print("\n" + "=" * 10 + f" {title} " + "=" * (width - len(title) - 12) + "\n")
    else:
        print("\n" + "=" * width + "\n")


def run_demo():
    """运行演示程序"""
    print_separator("容器内文件同步演示程序")
    print("这个程序演示如何使用容器内文件同步功能")
    print("它会在本地创建示例文件，并模拟主机和容器之间的文件变化")
    print("要在实际容器环境中测试，请按照以下步骤操作：")
    print("1. 在容器中运行 SmoothStack 命令配置文件同步")
    print("   smoothstack file-sync configure <容器名> \\ ")
    print("     --host-path ./sync_demo_host \\ ")
    print("     --container-path /app/sync_demo_container \\ ")
    print("     --mode bidirectional \\ ")
    print("     --exclude '.*\\.tmp$' \\ ")
    print("     --include '.*\\.py$'")
    print("2. 启动文件同步")
    print("   smoothstack file-sync start <容器名>")
    print("3. 检查同步状态")
    print("   smoothstack file-sync status <容器名>")
    print_separator()

    # 创建初始文件
    print("创建初始示例文件...")
    create_initial_files()
    print(f"初始文件已创建在: {TEMP_DIR_HOST}")
    print("您可以在另一个终端观察文件变化情况")
    print_separator()

    # 启动模拟线程
    print("启动文件变化模拟...")
    host_thread = threading.Thread(target=simulate_host_file_changes, daemon=True)
    host_thread.start()
    print("主机端文件变化模拟已启动")

    # 注意：在真实环境中，容器端的模拟应该在容器内运行
    # 此处仅作为演示
    container_thread = threading.Thread(
        target=simulate_container_file_changes, daemon=True
    )
    container_thread.start()
    print("容器端文件变化模拟已启动（演示模式）")

    print_separator("文件变化日志")
    print("按 Ctrl+C 停止演示")

    try:
        # 主线程继续运行，直到用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n演示已停止")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="容器内文件同步示例程序")
    parser.add_argument(
        "--interval",
        type=int,
        default=FILE_CHANGE_INTERVAL,
        help=f"文件变化间隔（秒）(默认: {FILE_CHANGE_INTERVAL})",
    )

    args = parser.parse_args()
    FILE_CHANGE_INTERVAL = args.interval

    run_demo()
