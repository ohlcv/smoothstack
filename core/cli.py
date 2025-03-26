#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI入口模块

集成所有命令模块,提供统一的命令行接口
"""

import os
import sys
import click
from typing import Optional, Dict, Any, List, Tuple
from .commands.project import project
from .commands.dependency import dependency
from .commands.build import build
from .commands.test import test
from .utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Smoothstack CLI工具

    提供项目管理、依赖管理、构建部署、测试等功能。
    """
    pass


# 注册命令组
cli.add_command(project)
cli.add_command(dependency)
cli.add_command(build)
cli.add_command(test)


if __name__ == "__main__":
    cli()
