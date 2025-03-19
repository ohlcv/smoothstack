#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理命令行入口

将容器管理命令集成到Smoothstack的命令行工具中
"""

import logging
import click

# 导入容器管理命令
from .container_cmd import container_group

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
    logger.info("Container management commands registered")


if __name__ == "__main__":
    # 仅用于开发测试
    @click.group()
    def cli():
        """Smoothstack命令行工具"""
        pass

    # 注册命令
    register_commands(cli)

    # 运行CLI
    cli()
