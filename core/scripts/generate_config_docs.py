#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文档生成脚本

快速生成配置文档的便捷脚本
"""

import os
import sys
from pathlib import Path

# 确保可以导入配置模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入文档生成命令
from backend.config.cli.docs_command import generate_docs

if __name__ == "__main__":
    generate_docs()
