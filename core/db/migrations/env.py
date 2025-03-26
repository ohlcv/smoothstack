#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alembic迁移环境主配置文件
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 添加父目录到sys.path，确保能导入backend包
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入基础模型和数据库连接
from backend.database.base import Base
from backend.database.connection import get_connection

# 从配置中获取元数据
# 这是用于反射目标数据库结构的元数据对象
target_metadata = Base.metadata

# 解析alembic.ini文件，获取配置
config = context.config

# 配置日志记录器
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline():
    """
    在离线模式下运行迁移

    这个函数不会创建任何连接，而是直接打印SQL到标准输出
    """
    # 使用当前数据库URL
    url = get_connection().get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    在在线模式下运行迁移

    这个函数会创建数据库连接并运行迁移
    """
    # 使用当前数据库引擎
    connectable = get_connection().get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据上下文调度函数
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
