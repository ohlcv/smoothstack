#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器管理器使用示例

展示如何使用容器管理器来管理Docker容器
"""

import time
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 导入容器管理器
from backend.container_manager import container_manager


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)


def check_docker_service():
    """检查Docker服务状态"""
    print_section("检查Docker服务状态")

    success, message = container_manager.check_docker_service()
    print(f"Docker服务状态: {'正常' if success else '异常'}")
    print(f"详细信息: {message}")

    if not success:
        print("\n请确保Docker服务已经启动。")
        return False

    return True


def list_containers():
    """列出容器"""
    print_section("列出容器")

    # 获取所有容器
    containers = container_manager.list_containers()

    if not containers:
        print("没有找到容器")
        return []

    print(f"找到 {len(containers)} 个容器:\n")

    # 打印容器信息
    for i, container in enumerate(containers):
        print(
            f"{i+1}. {container.name or '未命名'} ({container.id[:12] if container.id else 'N/A'})"
        )
        print(f"   镜像: {container.image or '未知'}")
        print(f"   状态: {container.status.name}")
        print(f"   创建时间: {container.created_at or '未知'}")
        if container.ports:
            ports_str = ", ".join(
                f"{host_port}->{container_port}"
                for host_port, container_port in container.ports.items()
            )
            print(f"   端口映射: {ports_str}")
        print()

    return containers


def container_lifecycle_demo():
    """容器生命周期管理示例"""
    print_section("容器生命周期管理示例")

    # 检查是否有容器可以用于演示
    containers = container_manager.list_containers()

    if not containers:
        print("没有找到容器，无法进行演示")
        print("提示: 可以使用以下命令创建一个测试容器:")
        print("  docker run -d --name smoothstack-test nginx")
        return

    # 选择第一个容器进行演示
    container = containers[0]

    # 确保容器ID不为None
    if not container.id:
        print("容器ID为空，无法进行演示")
        return

    container_id = container.id  # 确保容器ID为str类型

    print(f"选择容器 '{container.name or '未命名'}' 进行演示\n")

    # 获取容器详细信息
    print("1. 获取容器详细信息")
    container_info = container_manager.get_container(container_id)
    if container_info:
        print(f"   容器名称: {container_info.name or '未命名'}")
        print(f"   容器状态: {container_info.status.name}")
        if container_info.ip_address:
            print(f"   IP地址: {container_info.ip_address}")
    print()

    # 获取容器统计信息
    print("2. 获取容器统计信息")
    success, stats = container_manager.get_container_stats(container_id)
    if success:
        print(f"   CPU使用率: {stats['cpu']['usage_percent']:.2f}%")
        print(f"   内存使用率: {stats['memory']['usage_percent']:.2f}%")
        print(f"   网络接收: {stats['network']['rx_bytes'] / (1024*1024):.2f} MB")
        print(f"   网络发送: {stats['network']['tx_bytes'] / (1024*1024):.2f} MB")
    print()

    # 获取容器日志
    print("3. 获取容器日志 (前5行)")
    success, logs = container_manager.get_container_logs(container_id, tail=5)
    if success and logs:
        for log in logs[:5]:
            print(f"   {log}")
    print()

    # 容器生命周期操作
    if container.status.name == "RUNNING":
        print("4. 停止容器")
        success, message = container_manager.stop_container(container_id)
        print(f"   结果: {message}")
        print("   等待2秒...")
        time.sleep(2)

        print("\n5. 启动容器")
        success, message = container_manager.start_container(container_id)
        print(f"   结果: {message}")
        print("   等待2秒...")
        time.sleep(2)

        print("\n6. 重启容器")
        success, message = container_manager.restart_container(container_id)
        print(f"   结果: {message}")
    else:
        print("4. 启动容器")
        success, message = container_manager.start_container(container_id)
        print(f"   结果: {message}")
        print("   等待2秒...")
        time.sleep(2)

        print("\n5. 重启容器")
        success, message = container_manager.restart_container(container_id)
        print(f"   结果: {message}")
        print("   等待2秒...")
        time.sleep(2)

        print("\n6. 停止容器")
        success, message = container_manager.stop_container(container_id)
        print(f"   结果: {message}")

    # 检查容器状态
    print("\n7. 检查最终容器状态")
    container_info = container_manager.get_container(container_id)
    if container_info:
        print(f"   容器名称: {container_info.name or '未命名'}")
        print(f"   容器状态: {container_info.status.name}")


def main():
    """主函数"""
    print_section("容器管理器示例")
    print("本示例演示如何使用容器管理器来管理Docker容器")
    print("确保Docker服务已启动")

    # 检查Docker服务
    if not check_docker_service():
        return

    # 列出容器
    list_containers()

    # 容器生命周期管理示例
    container_lifecycle_demo()

    print_section("示例结束")


if __name__ == "__main__":
    main()
