#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置监控功能示例

展示如何使用配置自动重载功能
"""

import time
import logging
from . import config


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def on_config_changed(old_value, new_value, key):
    """
    配置变更处理函数

    Args:
        old_value: 变更前的值
        new_value: 变更后的值
        key: 配置键
    """
    print(f"配置已变更: {key}")
    print(f"  - 原值: {old_value}")
    print(f"  - 新值: {new_value}")


def main():
    """主函数"""
    # 设置日志
    setup_logging()

    # 加载初始配置
    config.load()
    print("初始配置已加载")

    # 启用配置自动重载
    config.enable_auto_reload()
    print("已启用配置自动重载，请尝试修改配置文件...")
    print("支持的配置文件:")
    print("  - backend/config/default.yaml")
    print("  - backend/config/environments/{development,testing,production}.yaml")
    print("\n提示: 使用Ctrl+C退出程序")

    try:
        # 持续监控配置变化
        while True:
            # 每隔5秒输出一些配置值
            print("\n当前配置值:")
            print(f"  - 应用名称: {config.get('app.name')}")
            print(f"  - 调试模式: {config.get('app.debug')}")
            print(f"  - 数据库URL: {config.get('database.url')}")
            print(f"  - API端口: {config.get('api.port')}")

            # 等待5秒
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        # 确保正确停止监控
        config.disable_auto_reload()
        print("配置监控已停止")


if __name__ == "__main__":
    main()
