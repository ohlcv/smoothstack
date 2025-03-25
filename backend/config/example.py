#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器使用示例

展示如何在应用程序中使用配置管理器
"""

import logging
from . import config


def setup_logging():
    """配置日志系统"""
    # 从配置中获取日志级别
    log_level_name = config.get("logging.level", "INFO")
    log_level = getattr(logging, log_level_name)

    # 从配置中获取日志格式
    log_format = config.get("logging.format")

    # 配置根日志记录器
    logging.basicConfig(level=log_level, format=log_format)

    # 获取应用的日志记录器
    logger = logging.getLogger("smoothstack")

    # 从配置中获取日志文件路径
    log_file = config.get("logging.file")
    if log_file:
        # 设置文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)

    return logger


def setup_database():
    """配置数据库连接"""
    # 从配置中获取数据库URL
    db_url = config.get("database.url")

    # 获取其他数据库配置
    pool_size = config.get("database.pool_size", 5)
    max_overflow = config.get("database.max_overflow", 10)
    echo = config.get("database.echo", False)

    # 这里只是示例，实际应用中可能会使用SQLAlchemy
    print(f"连接到数据库: {db_url}")
    print(f"连接池大小: {pool_size}")
    print(f"最大连接溢出: {max_overflow}")
    print(f"回显SQL: {echo}")


def setup_api():
    """配置API服务器"""
    # 从配置中获取API配置
    host = config.get("api.host", "0.0.0.0")
    port = config.get("api.port", 5000)
    debug = config.get("api.debug", False)
    cors_origins = config.get("api.cors_origins", ["*"])

    # 这里只是示例，实际应用中可能会使用FastAPI
    print(f"API服务器将在 {host}:{port} 上运行")
    print(f"调试模式: {debug}")
    print(f"CORS源: {cors_origins}")


def main():
    """主函数"""
    # 确保配置已加载
    config.load()

    # 设置日志
    logger = setup_logging()
    logger.info("应用程序启动")

    # 设置数据库
    setup_database()

    # 设置API
    setup_api()

    # 访问其他配置
    app_name = config.get("app.name")
    app_version = config.get("app.version")
    logger.info(f"运行 {app_name} v{app_version}")

    # 使用字典访问语法
    secret_key = config["security.secret_key"]
    logger.debug(f"使用密钥: {secret_key[:3]}..." if secret_key else "未设置密钥")

    # 检查配置是否存在
    if "cache.type" in config:
        cache_type = config["cache.type"]
        logger.info(f"使用缓存类型: {cache_type}")

    # 动态设置配置
    config.set("app.dynamic_setting", "动态值")
    logger.info(f"动态设置: {config.get('app.dynamic_setting')}")

    # 获取整个配置部分
    app_config = config.get("app")
    logger.debug(f"完整的应用配置: {app_config}")

    # 热重载配置（在配置文件更改后调用）
    # config.reload()


if __name__ == "__main__":
    main()
