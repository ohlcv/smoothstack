#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络配置示例

演示如何使用Smoothstack的网络配置功能
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

# 将项目根目录添加到Python路径，以便导入backend模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.container_manager.network_manager import NetworkManager
from backend.container_manager.models.service_group import ServiceNetwork, NetworkMode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("network_config_example")


def create_custom_network():
    """
    创建自定义网络示例
    """
    logger.info("=== 创建自定义网络示例 ===")

    # 初始化网络管理器
    network_manager = NetworkManager()

    # 创建高性能网络
    high_perf_network = ServiceNetwork(
        name="my_high_perf_network",
        driver="bridge",
        subnet="172.30.0.0/16",
        gateway="172.30.0.1",
        enable_ipv6=False,
        internal=False,
        labels={
            "smoothstack.network_type": "high_performance",
            "smoothstack.description": "高性能网络示例",
            "app": "example_app",
            "environment": "testing",
        },
    )

    # 创建网络
    logger.info(f"创建高性能网络: {high_perf_network.name}")
    success, message, network_id = network_manager.create_network(high_perf_network)
    logger.info(f"结果: {message}")

    if not success:
        logger.error("创建网络失败")
        return None

    logger.info(f"网络ID: {network_id}")
    return high_perf_network.name


def create_from_template():
    """
    从模板创建网络示例
    """
    logger.info("=== 从模板创建网络示例 ===")

    # 初始化网络管理器
    network_manager = NetworkManager()

    # 列出可用的网络模板
    templates = network_manager.list_templates()
    logger.info(f"可用的网络模板: {[t.get('name') for t in templates]}")

    # 从隔离网络模板创建网络
    template_name = "isolated"
    network_name = "my_isolated_db_network"

    logger.info(f"从模板 '{template_name}' 创建网络: {network_name}")
    success, message, network_id = network_manager.create_network_from_template(
        template_name=template_name,
        network_name=network_name,
        subnet="172.31.0.0/16",
        gateway="172.31.0.1",
        custom_options={"com.docker.network.bridge.host_binding_ipv4": "0.0.0.0"},
    )
    logger.info(f"结果: {message}")

    if not success:
        logger.error("从模板创建网络失败")
        return None

    logger.info(f"网络ID: {network_id}")
    return network_name


def create_containers_with_network(network_name: str):
    """
    创建带有网络的容器

    Args:
        network_name: 网络名称
    """
    if not network_name:
        logger.error("未提供网络名称")
        return

    logger.info(f"=== 创建带有网络 '{network_name}' 的容器示例 ===")

    # 使用Docker CLI创建容器
    import subprocess

    # 创建服务器容器
    server_cmd = [
        "docker",
        "run",
        "--name",
        "network_demo_server",
        "-d",
        "--network",
        network_name,
        "--label",
        "example=network_demo",
        "alpine",
        "sh",
        "-c",
        "apk add --no-cache nginx && nginx -g 'daemon off;'",
    ]

    logger.info("创建服务器容器")
    try:
        result = subprocess.run(server_cmd, capture_output=True, text=True, check=True)
        server_id = result.stdout.strip()
        logger.info(f"服务器容器ID: {server_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"创建服务器容器失败: {e.stderr}")
        logger.info("尝试清理已存在的同名容器")
        try:
            subprocess.run(
                ["docker", "rm", "-f", "network_demo_server"],
                capture_output=True,
                check=False,
            )
            # 重试
            result = subprocess.run(
                server_cmd, capture_output=True, text=True, check=True
            )
            server_id = result.stdout.strip()
            logger.info(f"服务器容器ID: {server_id}")
        except subprocess.CalledProcessError as e2:
            logger.error(f"重试失败: {e2.stderr}")
            return

    # 创建客户端容器
    client_cmd = [
        "docker",
        "run",
        "--name",
        "network_demo_client",
        "-d",
        "--network",
        network_name,
        "--label",
        "example=network_demo",
        "alpine",
        "sh",
        "-c",
        "apk add --no-cache curl && while true; do sleep 10; done",
    ]

    logger.info("创建客户端容器")
    try:
        result = subprocess.run(client_cmd, capture_output=True, text=True, check=True)
        client_id = result.stdout.strip()
        logger.info(f"客户端容器ID: {client_id}")
    except subprocess.CalledProcessError as e:
        logger.error(f"创建客户端容器失败: {e.stderr}")
        logger.info("尝试清理已存在的同名容器")
        try:
            subprocess.run(
                ["docker", "rm", "-f", "network_demo_client"],
                capture_output=True,
                check=False,
            )
            # 重试
            result = subprocess.run(
                client_cmd, capture_output=True, text=True, check=True
            )
            client_id = result.stdout.strip()
            logger.info(f"客户端容器ID: {client_id}")
        except subprocess.CalledProcessError as e2:
            logger.error(f"重试失败: {e2.stderr}")
            # 清理服务器容器
            subprocess.run(
                ["docker", "rm", "-f", "network_demo_server"],
                capture_output=True,
                check=False,
            )
            return


def test_container_connectivity():
    """
    测试容器连接性
    """
    logger.info("=== 测试容器连接性 ===")

    # 初始化网络管理器
    network_manager = NetworkManager()

    # 测试连接性
    success, message = network_manager.check_network_connectivity(
        source_container="network_demo_client", target_container="network_demo_server"
    )

    if success:
        logger.info(f"连接测试成功: {message}")

        # 使用客户端容器访问服务器容器的Web服务
        import subprocess

        logger.info("尝试从客户端容器访问服务器容器的Web服务")

        cmd = [
            "docker",
            "exec",
            "network_demo_client",
            "sh",
            "-c",
            "curl -s -I http://network_demo_server",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"HTTP响应: \n{result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"HTTP请求失败: {e.stderr}")
    else:
        logger.error(f"连接测试失败: {message}")


def show_network_details(network_name: str):
    """
    显示网络详情

    Args:
        network_name: 网络名称
    """
    if not network_name:
        logger.error("未提供网络名称")
        return

    logger.info(f"=== 显示网络 '{network_name}' 详情 ===")

    # 初始化网络管理器
    network_manager = NetworkManager()

    # 获取网络详情
    details = network_manager.get_network_details(network_name)
    if not details:
        logger.error(f"网络 '{network_name}' 不存在")
        return

    # 打印网络基本信息
    logger.info(f"网络名称: {details['name']}")
    logger.info(f"网络ID: {details['id']}")
    logger.info(f"驱动: {details['driver']}")
    logger.info(f"范围: {details['scope']}")
    logger.info(f"内部网络: {'是' if details['internal'] else '否'}")

    if "subnet" in details:
        logger.info(f"子网: {details['subnet']}")
    if "gateway" in details:
        logger.info(f"网关: {details['gateway']}")

    # 打印连接的容器信息
    if details.get("connected_containers"):
        logger.info("\n连接的容器:")
        for name, container in details["connected_containers"].items():
            logger.info(f"  - {name}")
            logger.info(f"    ID: {container['id'][:12]}")
            logger.info(f"    IPv4: {container['ipv4_address']}")
            logger.info(f"    MAC: {container['mac_address']}")
    else:
        logger.info("\n无容器连接到此网络")


def create_network_template():
    """
    创建自定义网络模板示例
    """
    logger.info("=== 创建自定义网络模板示例 ===")

    # 初始化网络管理器
    network_manager = NetworkManager()

    # 创建自定义模板数据
    template_data = {
        "name": "custom_webapp",
        "description": "自定义Web应用网络模板",
        "driver": "bridge",
        "subnet": "172.32.0.0/16",
        "gateway": "172.32.0.1",
        "enable_ipv6": False,
        "internal": False,
        "options": {
            "com.docker.network.bridge.default_bridge": "false",
            "com.docker.network.bridge.enable_icc": "true",
            "com.docker.network.bridge.enable_ip_masquerade": "true",
            "com.docker.network.bridge.host_binding_ipv4": "0.0.0.0",
            "com.docker.network.bridge.name": "smoothstack_webapp",
            "com.docker.network.driver.mtu": "1500",
        },
        "labels": {
            "smoothstack.network_type": "webapp",
            "smoothstack.description": "自定义Web应用网络模板",
            "smoothstack.version": "1.0",
        },
    }

    # 保存模板
    if network_manager.save_template(template_data):
        logger.info(f"已创建网络模板: {template_data['name']}")

        # 显示模板列表
        templates = network_manager.list_templates()
        logger.info(f"当前可用的网络模板: {[t.get('name') for t in templates]}")
    else:
        logger.error(f"创建网络模板失败")


def cleanup():
    """
    清理资源
    """
    logger.info("=== 清理资源 ===")

    # 初始化网络管理器
    network_manager = NetworkManager()

    # 删除容器
    import subprocess

    containers = ["network_demo_server", "network_demo_client"]
    for container in containers:
        logger.info(f"删除容器: {container}")
        subprocess.run(
            ["docker", "rm", "-f", container], capture_output=True, check=False
        )

    # 删除网络
    networks = ["my_high_perf_network", "my_isolated_db_network"]
    for network in networks:
        logger.info(f"删除网络: {network}")
        success, message = network_manager.delete_network(network)
        logger.info(f"结果: {message}")

    # 删除自定义模板
    template = "custom_webapp"
    logger.info(f"删除网络模板: {template}")
    if network_manager.delete_template(template):
        logger.info(f"已删除网络模板: {template}")
    else:
        logger.info(f"删除网络模板失败或模板不存在: {template}")


def main():
    """
    主函数，演示网络配置功能
    """
    logger.info("开始演示网络配置功能")

    try:
        # 创建自定义网络
        high_perf_network = create_custom_network()

        # 从模板创建网络
        isolated_network = create_from_template()

        # 创建自定义网络模板
        create_network_template()

        # 确保网络创建成功后才继续
        if high_perf_network:
            # 创建带有网络的容器
            create_containers_with_network(high_perf_network)

            # 等待容器启动
            logger.info("等待容器启动...")
            time.sleep(5)

            # 测试容器连接性
            test_container_connectivity()

            # 显示网络详情
            show_network_details(high_perf_network)
        else:
            logger.error("无法创建网络，跳过容器测试")

        # 等待用户输入后清理资源
        input("\n按回车键清理示例资源...")
    finally:
        # 清理资源
        cleanup()

    logger.info("网络配置功能演示完成")


if __name__ == "__main__":
    main()
