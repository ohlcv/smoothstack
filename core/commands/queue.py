#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
队列命令模块

提供队列相关的命令，包括：
- 队列配置
- 队列监控
- 队列管理
- 队列清理
"""

import os
import sys
import yaml
import click
import shutil
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class QueueCommand(BaseCommand):
    """队列命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.queue_dir = self.project_root / "queue"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def config(self, project_name: str, action: str, **kwargs):
        """队列配置"""
        try:
            self.info(f"队列配置: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查队列配置
            config_file = project_dir / "queue" / "config.yml"
            if not config_file.exists():
                config = {}
            else:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

            # 配置队列
            if action == "add":
                self._add_queue_config(config, **kwargs)
            elif action == "remove":
                self._remove_queue_config(config, **kwargs)
            elif action == "update":
                self._update_queue_config(config, **kwargs)
            elif action == "show":
                self._show_queue_config(config)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("队列配置已更新")

        except Exception as e:
            self.error(f"队列配置失败: {e}")
            raise

    def monitor(self, project_name: str):
        """队列监控"""
        try:
            self.info(f"队列监控: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查队列配置
            config_file = project_dir / "queue" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("队列配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 监控队列
            self._monitor_queue(config)

        except Exception as e:
            self.error(f"队列监控失败: {e}")
            raise

    def manage(
        self, project_name: str, action: str, queue_name: Optional[str] = None, **kwargs
    ):
        """队列管理"""
        try:
            self.info(f"队列管理: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查队列配置
            config_file = project_dir / "queue" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("队列配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 管理队列
            if action == "start":
                self._start_queue(config, queue_name)
            elif action == "stop":
                self._stop_queue(config, queue_name)
            elif action == "restart":
                self._restart_queue(config, queue_name)
            elif action == "status":
                self._status_queue(config, queue_name)
            elif action == "purge":
                self._purge_queue(config, queue_name)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

        except Exception as e:
            self.error(f"队列管理失败: {e}")
            raise

    def clean(self, project_name: str, queue_name: Optional[str] = None):
        """队列清理"""
        try:
            self.info(f"队列清理: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查队列配置
            config_file = project_dir / "queue" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("队列配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 清理队列
            self._clean_queue(config, queue_name)

            self.success("队列清理成功")

        except Exception as e:
            self.error(f"队列清理失败: {e}")
            raise

    def _add_queue_config(self, config: Dict[str, Any], **kwargs):
        """添加队列配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("队列名称不能为空")

            # 添加配置
            name = kwargs.pop("name")
            config[name] = kwargs

            self.success(f"添加队列配置成功: {name}")

        except Exception as e:
            self.error(f"添加队列配置失败: {e}")
            raise

    def _remove_queue_config(self, config: Dict[str, Any], **kwargs):
        """移除队列配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("队列名称不能为空")

            # 移除配置
            name = kwargs["name"]
            if name in config:
                del config[name]
                self.success(f"移除队列配置成功: {name}")
            else:
                self.warning(f"队列配置不存在: {name}")

        except Exception as e:
            self.error(f"移除队列配置失败: {e}")
            raise

    def _update_queue_config(self, config: Dict[str, Any], **kwargs):
        """更新队列配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("队列名称不能为空")

            # 更新配置
            name = kwargs.pop("name")
            if name in config:
                config[name].update(kwargs)
                self.success(f"更新队列配置成功: {name}")
            else:
                self.warning(f"队列配置不存在: {name}")

        except Exception as e:
            self.error(f"更新队列配置失败: {e}")
            raise

    def _show_queue_config(self, config: Dict[str, Any]):
        """显示队列配置"""
        try:
            if not config:
                self.info("未配置队列")
                return

            self.info("\n队列配置:")
            for name, queue in config.items():
                self.info(f"名称: {name}")
                for key, value in queue.items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"显示队列配置失败: {e}")
            raise

    def _monitor_queue(self, config: Dict[str, Any]):
        """监控队列"""
        try:
            # 获取系统资源
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            self.info("\n系统资源:")
            self.info(f"CPU使用率: {cpu_percent}%")
            self.info(f"内存使用率: {memory.percent}%")

            # 获取队列统计
            for name, queue in config.items():
                # 获取队列路径
                queue_path = Path(queue.get("path", ""))
                if not queue_path.exists():
                    self.warning(f"队列路径不存在: {queue_path}")
                    continue

                # 获取队列大小
                queue_size = self._get_dir_size(queue_path)
                self.info(f"\n队列 {name}:")
                self.info(f"路径: {queue_path}")
                self.info(f"大小: {queue_size}")

                # 获取队列统计
                if "type" in queue and queue["type"] == "rabbitmq":
                    self._monitor_rabbitmq_queue(queue)
                elif "type" in queue and queue["type"] == "kafka":
                    self._monitor_kafka_queue(queue)

        except Exception as e:
            self.error(f"监控队列失败: {e}")
            raise

    def _start_queue(self, config: Dict[str, Any], queue_name: Optional[str] = None):
        """启动队列"""
        try:
            # 启动指定队列
            if queue_name:
                if queue_name in config:
                    self._start_single_queue(config[queue_name])
                else:
                    self.warning(f"队列配置不存在: {queue_name}")
            else:
                # 启动所有队列
                for name, queue in config.items():
                    self._start_single_queue(queue)

        except Exception as e:
            self.error(f"启动队列失败: {e}")
            raise

    def _stop_queue(self, config: Dict[str, Any], queue_name: Optional[str] = None):
        """停止队列"""
        try:
            # 停止指定队列
            if queue_name:
                if queue_name in config:
                    self._stop_single_queue(config[queue_name])
                else:
                    self.warning(f"队列配置不存在: {queue_name}")
            else:
                # 停止所有队列
                for name, queue in config.items():
                    self._stop_single_queue(queue)

        except Exception as e:
            self.error(f"停止队列失败: {e}")
            raise

    def _restart_queue(self, config: Dict[str, Any], queue_name: Optional[str] = None):
        """重启队列"""
        try:
            # 重启指定队列
            if queue_name:
                if queue_name in config:
                    self._restart_single_queue(config[queue_name])
                else:
                    self.warning(f"队列配置不存在: {queue_name}")
            else:
                # 重启所有队列
                for name, queue in config.items():
                    self._restart_single_queue(queue)

        except Exception as e:
            self.error(f"重启队列失败: {e}")
            raise

    def _status_queue(self, config: Dict[str, Any], queue_name: Optional[str] = None):
        """队列状态"""
        try:
            # 获取指定队列状态
            if queue_name:
                if queue_name in config:
                    self._status_single_queue(config[queue_name])
                else:
                    self.warning(f"队列配置不存在: {queue_name}")
            else:
                # 获取所有队列状态
                for name, queue in config.items():
                    self._status_single_queue(queue)

        except Exception as e:
            self.error(f"获取队列状态失败: {e}")
            raise

    def _purge_queue(self, config: Dict[str, Any], queue_name: Optional[str] = None):
        """清空队列"""
        try:
            # 清空指定队列
            if queue_name:
                if queue_name in config:
                    self._purge_single_queue(config[queue_name])
                else:
                    self.warning(f"队列配置不存在: {queue_name}")
            else:
                # 清空所有队列
                for name, queue in config.items():
                    self._purge_single_queue(queue)

        except Exception as e:
            self.error(f"清空队列失败: {e}")
            raise

    def _clean_queue(self, config: Dict[str, Any], queue_name: Optional[str] = None):
        """清理队列"""
        try:
            # 清理指定队列
            if queue_name:
                if queue_name in config:
                    self._clean_single_queue(config[queue_name])
                else:
                    self.warning(f"队列配置不存在: {queue_name}")
            else:
                # 清理所有队列
                for name, queue in config.items():
                    self._clean_single_queue(queue)

        except Exception as e:
            self.error(f"清理队列失败: {e}")
            raise

    def _start_single_queue(self, queue: Dict[str, Any]):
        """启动单个队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 启动队列
            if "type" in queue:
                if queue["type"] == "rabbitmq":
                    self._start_rabbitmq_queue(queue)
                elif queue["type"] == "kafka":
                    self._start_kafka_queue(queue)
                else:
                    # 启动文件队列
                    self._start_file_queue(queue)

        except Exception as e:
            self.error(f"启动队列失败: {e}")
            raise

    def _stop_single_queue(self, queue: Dict[str, Any]):
        """停止单个队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 停止队列
            if "type" in queue:
                if queue["type"] == "rabbitmq":
                    self._stop_rabbitmq_queue(queue)
                elif queue["type"] == "kafka":
                    self._stop_kafka_queue(queue)
                else:
                    # 停止文件队列
                    self._stop_file_queue(queue)

        except Exception as e:
            self.error(f"停止队列失败: {e}")
            raise

    def _restart_single_queue(self, queue: Dict[str, Any]):
        """重启单个队列"""
        try:
            # 停止队列
            self._stop_single_queue(queue)

            # 启动队列
            self._start_single_queue(queue)

        except Exception as e:
            self.error(f"重启队列失败: {e}")
            raise

    def _status_single_queue(self, queue: Dict[str, Any]):
        """单个队列状态"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 获取队列状态
            if "type" in queue:
                if queue["type"] == "rabbitmq":
                    self._status_rabbitmq_queue(queue)
                elif queue["type"] == "kafka":
                    self._status_kafka_queue(queue)
                else:
                    # 获取文件队列状态
                    self._status_file_queue(queue)

        except Exception as e:
            self.error(f"获取队列状态失败: {e}")
            raise

    def _purge_single_queue(self, queue: Dict[str, Any]):
        """清空单个队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 清空队列
            if "type" in queue:
                if queue["type"] == "rabbitmq":
                    self._purge_rabbitmq_queue(queue)
                elif queue["type"] == "kafka":
                    self._purge_kafka_queue(queue)
                else:
                    # 清空文件队列
                    self._purge_file_queue(queue)

        except Exception as e:
            self.error(f"清空队列失败: {e}")
            raise

    def _clean_single_queue(self, queue: Dict[str, Any]):
        """清理单个队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 清理队列
            if "type" in queue:
                if queue["type"] == "rabbitmq":
                    self._clean_rabbitmq_queue(queue)
                elif queue["type"] == "kafka":
                    self._clean_kafka_queue(queue)
                else:
                    # 清理文件队列
                    self._clean_file_queue(queue)

        except Exception as e:
            self.error(f"清理队列失败: {e}")
            raise

    def _monitor_rabbitmq_queue(self, queue: Dict[str, Any]):
        """监控RabbitMQ队列"""
        try:
            # 获取RabbitMQ连接
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=queue.get("host", "localhost"),
                    port=queue.get("port", 5672),
                    credentials=pika.PlainCredentials(
                        username=queue.get("username", "guest"),
                        password=queue.get("password", "guest"),
                    ),
                )
            )

            # 获取通道
            channel = connection.channel()

            # 获取队列信息
            queue_name = queue.get("queue", "")
            queue_info = channel.queue_declare(queue=queue_name, passive=True)
            self.info("\nRabbitMQ队列信息:")
            self.info(f"队列名称: {queue_info.method.queue}")
            self.info(f"消息数量: {queue_info.method.message_count}")
            self.info(f"消费者数量: {queue_info.method.consumer_count}")

            # 关闭连接
            connection.close()

        except Exception as e:
            self.error(f"监控RabbitMQ队列失败: {e}")
            raise

    def _monitor_kafka_queue(self, queue: Dict[str, Any]):
        """监控Kafka队列"""
        try:
            # 获取Kafka连接
            from kafka import KafkaAdminClient, KafkaConsumer

            admin_client = KafkaAdminClient(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ]
            )

            # 获取主题信息
            topic_name = queue.get("topic", "")
            consumer = KafkaConsumer(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ],
                group_id=queue.get("group", "test-group"),
            )

            # 获取主题统计
            topic_stats = consumer.metrics()
            self.info("\nKafka主题信息:")
            self.info(f"主题名称: {topic_name}")
            self.info(f"分区数量: {len(consumer.partitions_for_topic(topic_name))}")
            self.info(
                f"消费者数量: {len(consumer.metrics()['consumer-group-metrics'])}"
            )

            # 关闭连接
            consumer.close()
            admin_client.close()

        except Exception as e:
            self.error(f"监控Kafka队列失败: {e}")
            raise

    def _start_rabbitmq_queue(self, queue: Dict[str, Any]):
        """启动RabbitMQ队列"""
        try:
            # 获取RabbitMQ连接
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=queue.get("host", "localhost"),
                    port=queue.get("port", 5672),
                    credentials=pika.PlainCredentials(
                        username=queue.get("username", "guest"),
                        password=queue.get("password", "guest"),
                    ),
                )
            )

            # 获取通道
            channel = connection.channel()

            # 创建队列
            queue_name = queue.get("queue", "")
            channel.queue_declare(queue=queue_name, durable=True)

            # 关闭连接
            connection.close()

            self.success(f"启动RabbitMQ队列成功: {queue_name}")

        except Exception as e:
            self.error(f"启动RabbitMQ队列失败: {e}")
            raise

    def _start_kafka_queue(self, queue: Dict[str, Any]):
        """启动Kafka队列"""
        try:
            # 获取Kafka连接
            from kafka import KafkaAdminClient, NewTopic

            admin_client = KafkaAdminClient(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ]
            )

            # 创建主题
            topic_name = queue.get("topic", "")
            topic = NewTopic(
                name=topic_name,
                num_partitions=queue.get("partitions", 1),
                replication_factor=queue.get("replication", 1),
            )
            admin_client.create_topics([topic])

            # 关闭连接
            admin_client.close()

            self.success(f"启动Kafka队列成功: {topic_name}")

        except Exception as e:
            self.error(f"启动Kafka队列失败: {e}")
            raise

    def _start_file_queue(self, queue: Dict[str, Any]):
        """启动文件队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                queue_path.mkdir(parents=True, exist_ok=True)

            self.success(f"启动文件队列成功: {queue_path}")

        except Exception as e:
            self.error(f"启动文件队列失败: {e}")
            raise

    def _stop_rabbitmq_queue(self, queue: Dict[str, Any]):
        """停止RabbitMQ队列"""
        try:
            # 获取RabbitMQ连接
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=queue.get("host", "localhost"),
                    port=queue.get("port", 5672),
                    credentials=pika.PlainCredentials(
                        username=queue.get("username", "guest"),
                        password=queue.get("password", "guest"),
                    ),
                )
            )

            # 获取通道
            channel = connection.channel()

            # 删除队列
            queue_name = queue.get("queue", "")
            channel.queue_delete(queue=queue_name)

            # 关闭连接
            connection.close()

            self.success(f"停止RabbitMQ队列成功: {queue_name}")

        except Exception as e:
            self.error(f"停止RabbitMQ队列失败: {e}")
            raise

    def _stop_kafka_queue(self, queue: Dict[str, Any]):
        """停止Kafka队列"""
        try:
            # 获取Kafka连接
            from kafka import KafkaAdminClient

            admin_client = KafkaAdminClient(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ]
            )

            # 删除主题
            topic_name = queue.get("topic", "")
            admin_client.delete_topics([topic_name])

            # 关闭连接
            admin_client.close()

            self.success(f"停止Kafka队列成功: {topic_name}")

        except Exception as e:
            self.error(f"停止Kafka队列失败: {e}")
            raise

    def _stop_file_queue(self, queue: Dict[str, Any]):
        """停止文件队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 停止队列
            for file in queue_path.glob("*"):
                if file.is_file():
                    file.unlink()

            self.success(f"停止文件队列成功: {queue_path}")

        except Exception as e:
            self.error(f"停止文件队列失败: {e}")
            raise

    def _status_rabbitmq_queue(self, queue: Dict[str, Any]):
        """RabbitMQ队列状态"""
        try:
            # 获取RabbitMQ连接
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=queue.get("host", "localhost"),
                    port=queue.get("port", 5672),
                    credentials=pika.PlainCredentials(
                        username=queue.get("username", "guest"),
                        password=queue.get("password", "guest"),
                    ),
                )
            )

            # 获取通道
            channel = connection.channel()

            # 获取队列状态
            queue_name = queue.get("queue", "")
            queue_info = channel.queue_declare(queue=queue_name, passive=True)
            self.info(f"\nRabbitMQ队列 {queue_name} 状态:")
            self.info(f"消息数量: {queue_info.method.message_count}")
            self.info(f"消费者数量: {queue_info.method.consumer_count}")
            self.info(f"状态: 运行中")

            # 关闭连接
            connection.close()

        except Exception as e:
            self.error(f"获取RabbitMQ队列状态失败: {e}")
            raise

    def _status_kafka_queue(self, queue: Dict[str, Any]):
        """Kafka队列状态"""
        try:
            # 获取Kafka连接
            from kafka import KafkaAdminClient, KafkaConsumer

            admin_client = KafkaAdminClient(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ]
            )

            # 获取主题状态
            topic_name = queue.get("topic", "")
            consumer = KafkaConsumer(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ],
                group_id=queue.get("group", "test-group"),
            )

            # 获取主题统计
            topic_stats = consumer.metrics()
            self.info(f"\nKafka队列 {topic_name} 状态:")
            self.info(f"分区数量: {len(consumer.partitions_for_topic(topic_name))}")
            self.info(
                f"消费者数量: {len(consumer.metrics()['consumer-group-metrics'])}"
            )
            self.info(f"状态: 运行中")

            # 关闭连接
            consumer.close()
            admin_client.close()

        except Exception as e:
            self.error(f"获取Kafka队列状态失败: {e}")
            raise

    def _status_file_queue(self, queue: Dict[str, Any]):
        """文件队列状态"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 获取队列状态
            file_count = len(list(queue_path.glob("*")))
            self.info(f"\n文件队列 {queue_path} 状态:")
            self.info(f"文件数量: {file_count}")
            self.info(f"状态: 运行中")

        except Exception as e:
            self.error(f"获取文件队列状态失败: {e}")
            raise

    def _purge_rabbitmq_queue(self, queue: Dict[str, Any]):
        """清空RabbitMQ队列"""
        try:
            # 获取RabbitMQ连接
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=queue.get("host", "localhost"),
                    port=queue.get("port", 5672),
                    credentials=pika.PlainCredentials(
                        username=queue.get("username", "guest"),
                        password=queue.get("password", "guest"),
                    ),
                )
            )

            # 获取通道
            channel = connection.channel()

            # 清空队列
            queue_name = queue.get("queue", "")
            channel.queue_purge(queue=queue_name)

            # 关闭连接
            connection.close()

            self.success(f"清空RabbitMQ队列成功: {queue_name}")

        except Exception as e:
            self.error(f"清空RabbitMQ队列失败: {e}")
            raise

    def _purge_kafka_queue(self, queue: Dict[str, Any]):
        """清空Kafka队列"""
        try:
            # 获取Kafka连接
            from kafka import KafkaAdminClient, KafkaConsumer

            admin_client = KafkaAdminClient(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ]
            )

            # 获取主题
            topic_name = queue.get("topic", "")
            consumer = KafkaConsumer(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ],
                group_id=queue.get("group", "test-group"),
            )

            # 清空主题
            consumer.seek_to_beginning()

            # 关闭连接
            consumer.close()
            admin_client.close()

            self.success(f"清空Kafka队列成功: {topic_name}")

        except Exception as e:
            self.error(f"清空Kafka队列失败: {e}")
            raise

    def _purge_file_queue(self, queue: Dict[str, Any]):
        """清空文件队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 清空队列
            for file in queue_path.glob("*"):
                if file.is_file():
                    file.unlink()

            self.success(f"清空文件队列成功: {queue_path}")

        except Exception as e:
            self.error(f"清空文件队列失败: {e}")
            raise

    def _clean_rabbitmq_queue(self, queue: Dict[str, Any]):
        """清理RabbitMQ队列"""
        try:
            # 获取RabbitMQ连接
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=queue.get("host", "localhost"),
                    port=queue.get("port", 5672),
                    credentials=pika.PlainCredentials(
                        username=queue.get("username", "guest"),
                        password=queue.get("password", "guest"),
                    ),
                )
            )

            # 获取通道
            channel = connection.channel()

            # 删除队列
            queue_name = queue.get("queue", "")
            channel.queue_delete(queue=queue_name)

            # 关闭连接
            connection.close()

            self.success(f"清理RabbitMQ队列成功: {queue_name}")

        except Exception as e:
            self.error(f"清理RabbitMQ队列失败: {e}")
            raise

    def _clean_kafka_queue(self, queue: Dict[str, Any]):
        """清理Kafka队列"""
        try:
            # 获取Kafka连接
            from kafka import KafkaAdminClient

            admin_client = KafkaAdminClient(
                bootstrap_servers=[
                    f"{queue.get('host', 'localhost')}:{queue.get('port', 9092)}"
                ]
            )

            # 删除主题
            topic_name = queue.get("topic", "")
            admin_client.delete_topics([topic_name])

            # 关闭连接
            admin_client.close()

            self.success(f"清理Kafka队列成功: {topic_name}")

        except Exception as e:
            self.error(f"清理Kafka队列失败: {e}")
            raise

    def _clean_file_queue(self, queue: Dict[str, Any]):
        """清理文件队列"""
        try:
            # 获取队列路径
            queue_path = Path(queue.get("path", ""))
            if not queue_path.exists():
                self.warning(f"队列路径不存在: {queue_path}")
                return

            # 清理队列
            shutil.rmtree(queue_path)
            queue_path.mkdir(parents=True, exist_ok=True)

            self.success(f"清理文件队列成功: {queue_path}")

        except Exception as e:
            self.error(f"清理文件队列失败: {e}")
            raise

    def _get_dir_size(self, directory: Path) -> str:
        """获取目录大小"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)

            # 转换为可读格式
            for unit in ["B", "KB", "MB", "GB"]:
                if total_size < 1024:
                    return f"{total_size:.2f}{unit}"
                total_size /= 1024

            return f"{total_size:.2f}TB"

        except Exception as e:
            self.error(f"获取目录大小失败: {e}")
            raise


# CLI命令
@click.group()
def queue():
    """队列命令"""
    pass


@queue.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="队列名称")
@click.option("--type", "-t", help="队列类型")
@click.option("--path", "-p", help="队列路径")
@click.option("--host", "-h", help="主机地址")
@click.option("--port", "-P", help="端口号")
@click.option("--username", "-u", help="用户名")
@click.option("--password", "-w", help="密码")
@click.option("--queue", "-q", help="队列名称")
@click.option("--topic", "-T", help="主题名称")
@click.option("--group", "-g", help="消费者组")
@click.option("--partitions", "-n", help="分区数量")
@click.option("--replication", "-r", help="副本数量")
def config(project_name: str, action: str, **kwargs):
    """队列配置"""
    cmd = QueueCommand()
    cmd.config(project_name, action, **kwargs)


@queue.command()
@click.argument("project_name")
def monitor(project_name: str):
    """队列监控"""
    cmd = QueueCommand()
    cmd.monitor(project_name)


@queue.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="队列名称")
def manage(project_name: str, action: str, name: Optional[str]):
    """队列管理"""
    cmd = QueueCommand()
    cmd.manage(project_name, action, name)


@queue.command()
@click.argument("project_name")
@click.option("--name", "-n", help="队列名称")
def clean(project_name: str, name: Optional[str]):
    """队列清理"""
    cmd = QueueCommand()
    cmd.clean(project_name, name)
