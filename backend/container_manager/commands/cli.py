#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SmoothStack CLI工具

管理开发环境容器，多容器服务组，网络配置，容器健康状态，持久化存储，多容器策略管理，开发环境热重载和容器内文件同步
"""

import click
import logging
from typing import List, Dict, Any

# 导入已实现的命令组
try:
    from .dev_env_cmd import dev_env_cmd_group
except ImportError:
    dev_env_cmd_group = None

try:
    from .service_cmd import service_cmd_group
except ImportError:
    service_cmd_group = None

try:
    from .network_cmd import network_cmd_group
except ImportError:
    network_cmd_group = None

try:
    from .health_cmd import health_cmd_group
except ImportError:
    health_cmd_group = None

try:
    from .storage_cmd import storage_cmd_group
except ImportError:
    storage_cmd_group = None

try:
    from .strategy_cmd import strategy_cmd_group
except ImportError:
    strategy_cmd_group = None

try:
    from .dev_reload_cmd import dev_reload_cmd_group
except ImportError:
    dev_reload_cmd_group = None

try:
    from .debug_cmd import debug_cmd_group
except ImportError:
    debug_cmd_group = None

try:
    from .file_sync_cmd import file_sync_cmd_group
except ImportError:
    file_sync_cmd_group = None

try:
    from .container_cmd import container_cmd_group
except ImportError:
    container_cmd_group = None

try:
    from .project_cmd import project_cmd_group
except ImportError:
    project_cmd_group = None

try:
    from .communication_cmd import communication_cmd_group
except ImportError:
    communication_cmd_group = None

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.commands.cli")


@click.group(help="SmoothStack 容器管理工具")
@click.version_option(version="0.3.0")
def cli():
    """SmoothStack容器管理CLI工具"""
    pass


# 添加子命令组
if dev_env_cmd_group is not None:
    cli.add_command(dev_env_cmd_group)
if service_cmd_group is not None:
    cli.add_command(service_cmd_group)
if network_cmd_group is not None:
    cli.add_command(network_cmd_group)
if health_cmd_group is not None:
    cli.add_command(health_cmd_group)
if storage_cmd_group is not None:
    cli.add_command(storage_cmd_group)
if strategy_cmd_group is not None:
    cli.add_command(strategy_cmd_group)
if dev_reload_cmd_group is not None:
    cli.add_command(dev_reload_cmd_group)
if debug_cmd_group is not None:
    cli.add_command(debug_cmd_group)
if file_sync_cmd_group is not None:
    cli.add_command(file_sync_cmd_group)
if container_cmd_group is not None:
    cli.add_command(container_cmd_group)
if project_cmd_group is not None:
    cli.add_command(project_cmd_group)
if communication_cmd_group is not None:
    cli.add_command(communication_cmd_group)


if __name__ == "__main__":
    cli()
