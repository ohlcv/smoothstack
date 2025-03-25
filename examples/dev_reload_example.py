#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境热重载示例

演示如何使用热重载管理器配置和管理前端和后端的热重载功能
"""

import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path

from backend.container_manager.dev_reload_manager import get_dev_reload_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dev_reload_example")


def print_separator(title=None):
    """打印分隔符"""
    width = 80
    if title:
        print("\n" + "=" * 10 + f" {title} " + "=" * (width - len(title) - 12) + "\n")
    else:
        print("\n" + "=" * width + "\n")


def example_configure_frontend():
    """示例1: 配置前端热重载"""
    print_separator("配置前端热重载")

    reload_manager = get_dev_reload_manager()

    # 配置前端容器的热重载
    container_name = "frontend-dev"
    watch_paths = [
        "/app/src",
        "/app/public",
    ]

    # 自定义Vite配置
    vite_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 3000,
            "hmr": {
                "host": "0.0.0.0",
                "port": 3000,
                "protocol": "ws",
                "clientPort": 3000,
            },
            "watch": {
                "usePolling": True,
                "interval": 100,
            },
        },
    }

    logger.info(f"为容器 '{container_name}' 配置前端热重载")
    success = reload_manager.configure_frontend_reload(
        container_name=container_name,
        watch_paths=watch_paths,
        vite_config=vite_config,
    )

    if success:
        logger.info("前端热重载配置成功")
        logger.info(f"监视路径: {', '.join(watch_paths)}")
        logger.info(
            f"HMR服务: {vite_config['server']['host']}:{vite_config['server']['port']}"
        )
    else:
        logger.error("前端热重载配置失败")

    return container_name


def example_configure_backend():
    """示例2: 配置后端热重载"""
    print_separator("配置后端热重载")

    reload_manager = get_dev_reload_manager()

    # 配置后端容器的热重载
    container_name = "backend-dev"
    watch_paths = [
        "/app/src",
        "/app/api",
    ]

    # 自定义排除模式
    exclude_patterns = [
        "*.pyc",
        "__pycache__",
        "*.swp",
        "*.swx",
        ".git",
        "*.log",
    ]

    logger.info(f"为容器 '{container_name}' 配置后端热重载")
    success = reload_manager.configure_backend_reload(
        container_name=container_name,
        watch_paths=watch_paths,
        reload_command="kill -HUP 1",  # 发送HUP信号重启应用
        exclude_patterns=exclude_patterns,
        debounce_ms=1000,  # 1秒防抖时间
    )

    if success:
        logger.info("后端热重载配置成功")
        logger.info(f"监视路径: {', '.join(watch_paths)}")
        logger.info(f"排除模式: {', '.join(exclude_patterns)}")
        logger.info("重载命令: kill -HUP 1")
        logger.info("防抖时间: 1000ms")
    else:
        logger.error("后端热重载配置失败")

    return container_name


def example_list_configs():
    """示例3: 列出热重载配置"""
    print_separator("列出热重载配置")

    reload_manager = get_dev_reload_manager()

    configs = reload_manager.list_reload_configs()
    if not configs:
        logger.info("未找到热重载配置")
        return

    logger.info(f"找到 {len(configs)} 个热重载配置:")
    for config in configs:
        print(f"\n容器名称: {config['container_name']}")
        print(f"类型: {config['config']['type']}")
        print(f"监视路径: {', '.join(config['config']['watch_paths'])}")
        print(f"是否活跃: {'是' if config['active'] else '否'}")


def example_start_reload(container_name):
    """示例4: 启动热重载"""
    print_separator("启动热重载")

    reload_manager = get_dev_reload_manager()

    logger.info(f"启动容器 '{container_name}' 的热重载")
    success = reload_manager.start_reload(container_name)

    if success:
        logger.info("热重载启动成功")
    else:
        logger.error("热重载启动失败")


def example_stop_reload(container_name):
    """示例5: 停止热重载"""
    print_separator("停止热重载")

    reload_manager = get_dev_reload_manager()

    logger.info(f"停止容器 '{container_name}' 的热重载")
    success = reload_manager.stop_reload(container_name)

    if success:
        logger.info("热重载停止成功")
    else:
        logger.error("热重载停止失败")


def example_remove_config(container_name):
    """示例6: 移除热重载配置"""
    print_separator("移除热重载配置")

    reload_manager = get_dev_reload_manager()

    logger.info(f"移除容器 '{container_name}' 的热重载配置")
    success = reload_manager.remove_reload_config(container_name)

    if success:
        logger.info("热重载配置移除成功")
    else:
        logger.error("热重载配置移除失败")


def run_all_examples():
    """运行所有示例"""
    # 示例1: 配置前端热重载
    frontend_container = example_configure_frontend()

    # 示例2: 配置后端热重载
    backend_container = example_configure_backend()

    # 示例3: 列出热重载配置
    example_list_configs()

    # 示例4: 启动热重载
    example_start_reload(frontend_container)
    example_start_reload(backend_container)

    # 等待一段时间
    logger.info("等待10秒...")
    time.sleep(10)

    # 示例5: 停止热重载
    example_stop_reload(frontend_container)
    example_stop_reload(backend_container)

    # 示例6: 移除热重载配置
    example_remove_config(frontend_container)
    example_remove_config(backend_container)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="开发环境热重载示例")
    parser.add_argument("--example", type=int, help="运行特定示例 (1-6)")

    args = parser.parse_args()

    if args.example:
        if args.example == 1:
            example_configure_frontend()
        elif args.example == 2:
            example_configure_backend()
        elif args.example == 3:
            example_list_configs()
        elif args.example == 4:
            container_name = input("请输入容器名称: ")
            example_start_reload(container_name)
        elif args.example == 5:
            container_name = input("请输入容器名称: ")
            example_stop_reload(container_name)
        elif args.example == 6:
            container_name = input("请输入容器名称: ")
            example_remove_config(container_name)
        else:
            logger.error(f"无效的示例编号: {args.example}")
    else:
        run_all_examples()
