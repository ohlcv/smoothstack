#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SmoothStack CLI工具

管理开发环境容器，多容器服务组，网络配置和容器健康状态
"""

import click
import logging
from typing import List, Dict, Any

from .dev_env_cmd import dev_env_cmd_group
from .service_cmd import service_cmd_group
from .network_cmd import network_cmd_group
from .health_cmd import health_cmd_group

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.commands.cli")


@click.group(help="SmoothStack 容器管理工具")
@click.version_option(version="0.3.0")
def cli():
    """SmoothStack容器管理CLI工具"""
    pass


# 添加子命令组
cli.add_command(dev_env_cmd_group)
cli.add_command(service_cmd_group)
cli.add_command(network_cmd_group)
cli.add_command(health_cmd_group)


if __name__ == "__main__":
    cli()
