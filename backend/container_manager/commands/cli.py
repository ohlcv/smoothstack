#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SmoothStack CLI工具

用于管理开发环境容器、多容器服务、网络配置、容器健康状态、持久化存储、
多容器策略管理、开发环境热重载和容器内文件同步
"""

import logging
import click

# 配置日志
logger = logging.getLogger(__name__)

# 导入命令组
try:
    from .consistency_cmd import consistency_cmd_group
except ImportError as e:
    logger.warning(f"无法导入一致性管理命令组: {e}")
    consistency_cmd_group = None


@click.group()
def cli():
    """SmoothStack容器管理工具"""
    pass


# 注册命令组
if consistency_cmd_group is not None:
    cli.add_command(consistency_cmd_group)

if __name__ == "__main__":
    cli()
