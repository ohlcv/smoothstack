#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨容器通信示例程序

本示例演示如何使用Smoothstack跨容器通信功能，包括不同通信方式和消息类型
"""

import os
import sys
import time
import json
import logging
import argparse
import threading
import random
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("communication_example")

# 尝试导入通信管理器
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from backend.container_manager.communication_manager import (
        get_communication_manager,
        CommunicationManager,
    )
except ImportError as e:
    logger.error(f"无法导入通信管理器: {str(e)}")
    logger.error(
        "请确保 backend/container_manager/communication_manager.py 存在且可导入"
    )
    sys.exit(1)


class CommunicationExample:
    """通信示例类"""

    def __init__(self, container_name: str = "local"):
        """
        初始化通信示例

        Args:
            container_name: 本地容器名称，用于标识消息来源
        """
        self.container_name = container_name
        self.comm_manager = get_communication_manager()
        self.running = False
        self.threads = []

        logger.info(f"通信示例初始化完成，容器名称: {container_name}")

    def setup_redis_example(self, host: str = "localhost", port: int = 6379):
        """
        设置Redis通信示例

        Args:
            host: Redis主机地址
            port: Redis端口
        """
        # 配置Redis通信频道
        success = self.comm_manager.configure_redis_communication(
            channel_name="redis_example",
            host=host,
            port=port,
            db=0,
            container_names=[self.container_name],
        )

        if success:
            logger.info("Redis通信频道 'redis_example' 配置成功")
        else:
            logger.error("Redis通信频道配置失败")

    def setup_direct_example(self, host: str = "0.0.0.0", port: int = 5555):
        """
        设置直接Socket通信示例

        Args:
            host: 绑定主机地址
            port: 绑定端口
        """
        # 配置直接Socket通信频道
        success = self.comm_manager.configure_direct_communication(
            channel_name="direct_example",
            protocol="tcp",
            host=host,
            port=port,
            container_names=[self.container_name],
        )

        if success:
            logger.info("直接Socket通信频道 'direct_example' 配置成功")
        else:
            logger.error("直接Socket通信频道配置失败")

    def setup_network_example(self, network_name: str, container_names: List[str]):
        """
        设置Docker网络通信示例

        Args:
            network_name: Docker网络名称
            container_names: 参与通信的容器名称列表
        """
        # 配置Docker网络通信频道
        success = self.comm_manager.configure_docker_network_communication(
            channel_name="network_example",
            network_name=network_name,
            container_names=container_names,
        )

        if success:
            logger.info(f"Docker网络通信频道 'network_example' 配置成功")
            logger.info(f"参与容器: {', '.join(container_names)}")
        else:
            logger.error("Docker网络通信频道配置失败")

    def setup_volume_example(self, volume_name: str, container_names: List[str]):
        """
        设置共享卷通信示例

        Args:
            volume_name: Docker卷名称
            container_names: 参与通信的容器名称列表
        """
        # 配置共享卷通信频道
        success = self.comm_manager.configure_volume_communication(
            channel_name="volume_example",
            volume_name=volume_name,
            mount_path="/shared",
            container_names=container_names,
        )

        if success:
            logger.info(f"共享卷通信频道 'volume_example' 配置成功")
            logger.info(f"参与容器: {', '.join(container_names)}")
        else:
            logger.error("共享卷通信频道配置失败")

    def start_message_producer(self, channel_name: str, interval: float = 5.0):
        """
        启动消息发布者线程

        Args:
            channel_name: 通信频道名称
            interval: 发布间隔（秒）
        """

        def producer_task():
            logger.info(f"消息发布者线程启动，频道: {channel_name}")
            message_count = 0

            while self.running:
                try:
                    # 生成随机消息
                    message_count += 1
                    message_type = random.choice(
                        [
                            self.comm_manager.MSG_TYPE_COMMAND,
                            self.comm_manager.MSG_TYPE_EVENT,
                            self.comm_manager.MSG_TYPE_DATA,
                        ]
                    )

                    message_content = self._generate_message_content(
                        message_type, message_count
                    )

                    # 发布消息
                    success = self.comm_manager.publish_message(
                        channel_name=channel_name,
                        message=json.dumps(message_content),
                        message_type=message_type,
                        source_container=self.container_name,
                        target_containers=None,  # 广播给所有容器
                    )

                    if success:
                        logger.info(
                            f"发布消息成功, 频道: {channel_name}, 类型: {message_type}, ID: {message_count}"
                        )
                    else:
                        logger.error(f"发布消息失败, 频道: {channel_name}")

                except Exception as e:
                    logger.error(f"发布消息异常: {str(e)}")

                # 等待下一次发布
                time.sleep(interval)

            logger.info(f"消息发布者线程结束，频道: {channel_name}")

        # 创建并启动线程
        thread = threading.Thread(
            target=producer_task, daemon=True, name=f"producer-{channel_name}"
        )
        thread.start()
        self.threads.append(thread)

    def _generate_message_content(
        self, message_type: str, message_id: int
    ) -> Dict[str, Any]:
        """
        生成消息内容

        Args:
            message_type: 消息类型
            message_id: 消息ID

        Returns:
            Dict[str, Any]: 消息内容
        """
        if message_type == self.comm_manager.MSG_TYPE_COMMAND:
            # 命令消息
            commands = [
                "restart",
                "shutdown",
                "update",
                "status",
                "configure",
                "backup",
                "restore",
                "migrate",
                "deploy",
            ]
            return {
                "id": message_id,
                "command": random.choice(commands),
                "parameters": {
                    "priority": random.choice(["high", "medium", "low"]),
                    "timeout": random.randint(10, 300),
                    "async": random.choice([True, False]),
                },
                "timestamp": time.time(),
            }

        elif message_type == self.comm_manager.MSG_TYPE_EVENT:
            # 事件消息
            events = [
                "started",
                "stopped",
                "error",
                "warning",
                "info",
                "resource_low",
                "update_available",
                "connection_lost",
            ]
            return {
                "id": message_id,
                "event": random.choice(events),
                "severity": random.choice(["critical", "warning", "info"]),
                "details": f"模拟事件 #{message_id} 从 {self.container_name}",
                "timestamp": time.time(),
            }

        else:  # MSG_TYPE_DATA
            # 数据消息
            data_types = ["metrics", "logs", "config", "user_data", "system_state"]
            data_type = random.choice(data_types)

            if data_type == "metrics":
                return {
                    "id": message_id,
                    "data_type": data_type,
                    "metrics": {
                        "cpu": random.uniform(0, 100),
                        "memory": random.uniform(0, 100),
                        "disk": random.uniform(0, 100),
                        "network": {
                            "in": random.uniform(0, 1000),
                            "out": random.uniform(0, 1000),
                        },
                    },
                    "timestamp": time.time(),
                }
            elif data_type == "logs":
                log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                log_entries = []
                for _ in range(random.randint(1, 5)):
                    log_entries.append(
                        {
                            "level": random.choice(log_levels),
                            "message": f"Log message #{random.randint(1000, 9999)}",
                            "timestamp": time.time() - random.uniform(0, 60),
                        }
                    )
                return {
                    "id": message_id,
                    "data_type": data_type,
                    "logs": log_entries,
                    "timestamp": time.time(),
                }
            else:
                return {
                    "id": message_id,
                    "data_type": data_type,
                    "content": f"随机数据内容 #{message_id}",
                    "size": random.randint(100, 10000),
                    "timestamp": time.time(),
                }

    def show_channel_list(self):
        """显示所有通信频道"""
        channels = self.comm_manager.list_channels()

        if not channels:
            logger.info("未找到通信频道")
            return

        logger.info("=== 通信频道列表 ===")
        for channel in channels:
            channel_name = channel["name"]
            config = channel["config"]
            channel_type = config["type"]
            active = "活跃" if channel["active"] else "停止"

            logger.info(f"频道: {channel_name}")
            logger.info(f"  类型: {channel_type}")
            logger.info(f"  状态: {active}")
            logger.info(f"  订阅者: {channel['subscribers']}")

            # 根据通信类型显示详情
            if channel_type == "redis":
                logger.info(
                    f"  Redis服务器: {config['redis_host']}:{config['redis_port']}"
                )
            elif channel_type == "direct":
                logger.info(
                    f"  Socket: {config['protocol']}://{config['host']}:{config['port']}"
                )
            elif channel_type == "docker_network":
                logger.info(f"  Docker网络: {config['network_name']}")
            elif channel_type == "volume":
                logger.info(f"  共享卷: {config['volume_name']}")
                logger.info(f"  挂载路径: {config['mount_path']}")

            logger.info(
                "  参与容器: "
                + (
                    ", ".join(config["container_names"])
                    if config["container_names"]
                    else "无"
                )
            )
            logger.info("---")

    def start(self):
        """启动通信示例"""
        self.running = True

        # 显示通信频道列表
        self.show_channel_list()

        # 启动消息发布者
        channels = self.comm_manager.list_channels()
        for channel in channels:
            if channel["active"]:
                self.start_message_producer(
                    channel["name"], interval=random.uniform(5, 15)
                )

        logger.info("通信示例已启动")

    def stop(self):
        """停止通信示例"""
        self.running = False

        # 等待线程结束
        for thread in self.threads:
            thread.join(timeout=2)

        logger.info("通信示例已停止")


def demo_single_container():
    """单容器演示"""
    example = CommunicationExample("container1")

    # 设置Redis通信
    example.setup_redis_example()

    # 设置直接Socket通信
    example.setup_direct_example()

    # 启动示例
    example.start()

    try:
        # 运行一段时间
        logger.info("示例程序运行中，按Ctrl+C停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("用户中断，正在停止...")
    finally:
        example.stop()


def demo_multi_container():
    """多容器演示（模拟）"""
    # 创建多个示例实例模拟多容器
    containers = ["container1", "container2", "container3"]
    examples = []

    # 共享的网络和卷名称
    network_name = "demo_network"
    volume_name = "demo_volume"

    # 初始化每个容器的通信
    for container_name in containers:
        example = CommunicationExample(container_name)

        # 设置Redis通信
        example.setup_redis_example()

        # 设置网络通信
        example.setup_network_example(network_name, containers)

        # 设置卷通信
        example.setup_volume_example(volume_name, containers)

        examples.append(example)

    # 启动所有示例
    for example in examples:
        example.start()

    try:
        # 运行一段时间
        logger.info("多容器示例程序运行中，按Ctrl+C停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("用户中断，正在停止...")
    finally:
        # 停止所有示例
        for example in examples:
            example.stop()


def demo_real_container():
    """实际容器环境演示

    注意：此函数在实际容器环境中运行
    需要设置环境变量 CONTAINER_NAME 来标识当前容器
    """
    container_name = os.environ.get("CONTAINER_NAME", "unknown")
    logger.info(f"在容器 '{container_name}' 中运行示例")

    example = CommunicationExample(container_name)

    # 在实际容器环境中，通信配置通常通过命令行完成
    # 这里我们只打印调试信息
    example.show_channel_list()

    # 启动示例
    example.start()

    try:
        # 运行一段时间
        logger.info("容器中的示例程序运行中，按Ctrl+C停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("用户中断，正在停止...")
    finally:
        example.stop()


def run_demo(mode: str = "single"):
    """
    运行通信示例演示

    Args:
        mode: 演示模式，可选 'single' (单容器), 'multi' (多容器模拟), 'real' (实际容器)
    """
    logger.info(f"启动通信示例演示，模式: {mode}")

    if mode == "single":
        demo_single_container()
    elif mode == "multi":
        demo_multi_container()
    elif mode == "real":
        demo_real_container()
    else:
        logger.error(f"未知的演示模式: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoothstack跨容器通信示例程序")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["single", "multi", "real"],
        default="single",
        help="演示模式: single (单容器), multi (多容器模拟), real (实际容器)",
    )

    args = parser.parse_args()
    run_demo(args.mode)
