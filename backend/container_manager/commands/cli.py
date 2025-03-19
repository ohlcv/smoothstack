#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理命令行入口

将容器管理命令集成到Smoothstack的命令行工具中
"""

import logging
import click
from rich.logging import RichHandler

# 导入容器管理命令
from .container_cmd import container_group
from .dev_env_cmd import dev_env_group

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.cli")


def register_commands(cli_group):
    """
    将容器管理命令注册到Smoothstack的命令行工具中

    Args:
        cli_group: Smoothstack的命令行工具组
    """
    # 添加容器管理命令组
    cli_group.add_command(container_group)
    cli_group.add_command(dev_env_group)
    logger.info("Container management commands registered")


if __name__ == "__main__":
    # 仅用于开发测试
    @click.group(help="Smoothstack 容器管理系统")
    def cli():
        """Smoothstack 容器管理系统命令行接口"""
        pass

    # 注册命令
    register_commands(cli)

    # 运行CLI
    cli()
