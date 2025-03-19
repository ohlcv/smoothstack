#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安装器模块

提供不同类型的包安装器，用于管理依赖包的安装、卸载和更新
"""

from .base import BaseInstaller
from .pip import PipInstaller
from .npm import NpmInstaller

__all__ = ["BaseInstaller", "PipInstaller", "NpmInstaller"]
