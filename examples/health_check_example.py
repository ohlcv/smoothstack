#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器健康检查示例

演示如何使用健康检查功能监控容器状态
"""

import time
import json
import logging
from datetime import datetime

from backend.container_manager.manager import ContainerManager
from backend.container_manager.health_checker import (
    get_health_checker,
    HealthStatus,
    ResourceThresholds,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("health_check_example")


def display_container_health(result):
    """显示容器健康状态"""
    status_display = {
        HealthStatus.HEALTHY: "健康",
        HealthStatus.WARNING: "警告",
        HealthStatus.UNHEALTHY: "不健康",
        HealthStatus.UNKNOWN: "未知",
        HealthStatus.STARTING: "启动中",
    }.get(result.status, result.status)

    status_color = {
        HealthStatus.HEALTHY: "\033[92m",  # 绿色
        HealthStatus.WARNING: "\033[93m",  # 黄色
        HealthStatus.UNHEALTHY: "\033[91m",  # 红色
        HealthStatus.UNKNOWN: "\033[94m",  # 蓝色
        HealthStatus.STARTING: "\033[96m",  # 青色
    }.get(result.status, "\033[0m")

    end_color = "\033[0m"

    print(f"容器: {result.container_name} ({result.container_id[:12]})")
    print(f"检查时间: {result.check_time}")
    print(f"状态: {status_color}{status_display}{end_color}")
    print(f"消息: {result.message}")

    # 显示详细信息
    if result.details:
        print("\n详细信息:")

        # Docker健康检查状态
        docker_health = result.details.get("docker_health_status")
        if docker_health:
            print(f"Docker健康检查状态: {docker_health}")

        # 资源使用情况
        stats = result.details.get("stats", {})
        if stats:
            print("\n资源使用情况:")

            # CPU
            cpu = stats.get("cpu", {})
            if cpu:
                cpu_usage = cpu.get("usage_percent", 0)
                cpu_color = "\033[92m"  # 默认绿色
                if cpu_usage >= 95:
                    cpu_color = "\033[91m"  # 红色
                elif cpu_usage >= 80:
                    cpu_color = "\033[93m"  # 黄色

                print(f"CPU使用率: {cpu_color}{cpu_usage:.2f}%{end_color}")

            # 内存
            memory = stats.get("memory", {})
            if memory:
                memory_usage = memory.get("usage", 0)
                memory_limit = memory.get("limit", 0)
                memory_percent = memory.get("usage_percent", 0)

                # 格式化内存大小
                def format_bytes(size):
                    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                        if size < 1024.0 or unit == "PB":
                            return f"{size:.2f} {unit}"
                        size /= 1024.0

                formatted_usage = format_bytes(memory_usage)
                formatted_limit = format_bytes(memory_limit)

                memory_color = "\033[92m"  # 默认绿色
                if memory_percent >= 95:
                    memory_color = "\033[91m"  # 红色
                elif memory_percent >= 80:
                    memory_color = "\033[93m"  # 黄色

                print(
                    f"内存使用: {formatted_usage} / {formatted_limit} "
                    f"({memory_color}{memory_percent:.2f}%{end_color})"
                )

            # 网络
            network = stats.get("network", {})
            if network:
                rx_bytes = network.get("rx_bytes", 0)
                tx_bytes = network.get("tx_bytes", 0)

                print(f"网络接收: {format_bytes(rx_bytes)}")
                print(f"网络发送: {format_bytes(tx_bytes)}")

            # 进程数
            pid = stats.get("pid", 0)
            if pid:
                print(f"进程数: {pid}")

    print("-" * 50)


def main():
    """主函数"""
    logger.info("容器健康检查示例")

    # 初始化容器管理器
    container_manager = ContainerManager()

    # 获取健康检查器
    health_checker = get_health_checker()

    # 自定义健康检查配置
    health_checker.update_config(
        thresholds={
            "cpu_warning": 70.0,  # CPU使用率警告阈值
            "cpu_critical": 90.0,  # CPU使用率严重阈值
            "memory_warning": 70.0,  # 内存使用率警告阈值
            "memory_critical": 90.0,  # 内存使用率严重阈值
            "restart_threshold": 2,  # 重启次数阈值
        },
        notification={
            "enabled": True,  # 启用通知
            "notify_on_warning": True,  # 警告状态时通知
            "notification_interval": 60,  # 通知间隔(秒)
        },
        check_interval=30,  # 检查间隔(秒)
    )

    try:
        # 获取所有运行中的容器
        containers = container_manager.list_containers(filters={"status": "running"})

        if not containers:
            logger.warning("没有运行中的容器。请先启动一些容器再运行此示例。")
            return

        logger.info(f"找到 {len(containers)} 个运行中的容器")

        # 选择前3个容器进行监控
        monitor_containers = containers[: min(3, len(containers))]

        # 添加容器到监控列表
        for container in monitor_containers:
            health_checker.add_container(container.id)
            logger.info(f"已添加容器 {container.name} ({container.id[:12]}) 到监控列表")

        # 执行首次健康检查
        print("\n执行首次健康检查:")
        for container in monitor_containers:
            result = health_checker.check_container_health(container.id)
            display_container_health(result)

        # 启动监控服务
        logger.info("启动健康检查监控服务...")
        health_checker.start_monitoring()

        # 等待一段时间，让监控服务收集数据
        logger.info("监控服务运行中，按 Ctrl+C 停止...")

        try:
            # 每10秒显示一次健康报告
            for _ in range(5):  # 运行约50秒
                time.sleep(10)

                # 获取健康报告
                report = health_checker.get_health_report()
                summary = report.get("summary", {})

                print("\n健康状态统计:")
                print(f"总计: {summary.get('total', 0)}")
                print(f"健康: {summary.get('healthy', 0)}")
                print(f"警告: {summary.get('warning', 0)}")
                print(f"不健康: {summary.get('unhealthy', 0)}")
                print(f"未知: {summary.get('unknown', 0)}")

                # 显示每个容器的详细健康状态
                print("\n容器健康详情:")
                for container in monitor_containers:
                    result = health_checker.check_container_health(container.id)
                    display_container_health(result)

        except KeyboardInterrupt:
            logger.info("用户中断，停止示例...")

        finally:
            # 停止监控服务
            logger.info("停止健康检查监控服务...")
            health_checker.stop_monitoring()

    except Exception as e:
        logger.error(f"发生错误: {e}")

    logger.info("示例结束")


if __name__ == "__main__":
    main()
