#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通信管理器

管理容器间通信，支持多种通信方式，包括Redis、直接Socket、Docker网络和共享卷
"""

import os
import json
import time
import socket
import logging
import threading
import hashlib
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import docker

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.communication_manager")


class CommunicationManager:
    """
    通信管理器类

    管理容器间的各种通信方式，支持配置不同通信渠道
    """

    # 消息类型常量
    MSG_TYPE_COMMAND = "command"
    MSG_TYPE_EVENT = "event"
    MSG_TYPE_DATA = "data"
    MSG_TYPE_HEARTBEAT = "heartbeat"

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化通信管理器

        Args:
            config_dir: 存储通信配置的目录，默认为~/.smoothstack/comm
        """
        self.config_dir = config_dir or os.path.expanduser("~/.smoothstack/comm")
        os.makedirs(self.config_dir, exist_ok=True)

        # 存储所有通信频道
        self.channels: Dict[str, Dict[str, Any]] = {}

        # 加载现有配置
        self.load_configurations()

        # Docker客户端
        self.docker_client = docker.from_env()

        # 后台线程
        self.bg_thread = None
        self.should_stop = threading.Event()

        # 启动后台维护线程
        self.start_bg_thread()

        logger.info("通信管理器初始化成功")

    def __del__(self):
        """析构函数，确保线程正确停止"""
        self.cleanup()

    def cleanup(self):
        """清理资源"""
        if self.bg_thread and self.bg_thread.is_alive():
            self.should_stop.set()
            self.bg_thread.join(timeout=2)
            logger.debug("通信管理器后台线程已停止")

    def start_bg_thread(self):
        """启动后台线程管理通信任务"""
        if self.bg_thread and self.bg_thread.is_alive():
            return

        self.should_stop.clear()
        self.bg_thread = threading.Thread(target=self._bg_worker, daemon=True)
        self.bg_thread.start()
        logger.debug("通信管理器后台线程已启动")

    def _bg_worker(self):
        """后台工作线程，处理心跳和监控等任务"""
        while not self.should_stop.is_set():
            try:
                # 更新通信频道状态
                self._update_channels_status()

                # 发送心跳消息
                self._send_heartbeats()

            except Exception as e:
                logger.error(f"通信管理器后台任务出错: {str(e)}")

            # 休眠一段时间
            time.sleep(5)

    def _update_channels_status(self):
        """更新所有通信频道的状态"""
        for channel_name, channel_info in self.channels.items():
            try:
                # 检查通信频道状态
                active = self._check_channel_status(channel_name, channel_info)
                channel_info["active"] = active
            except Exception as e:
                logger.error(f"更新频道 '{channel_name}' 状态失败: {str(e)}")
                channel_info["active"] = False

    def _check_channel_status(
        self, channel_name: str, channel_info: Dict[str, Any]
    ) -> bool:
        """检查特定通信频道的状态"""
        config = channel_info["config"]
        channel_type = config["type"]

        # 根据不同类型的通信方式检查状态
        if channel_type == "redis":
            # 尝试连接Redis以验证状态
            try:
                import redis

                r = redis.Redis(
                    host=config["redis_host"],
                    port=config["redis_port"],
                    db=config["redis_db"],
                    password=config.get("redis_password"),
                )
                r.ping()
                return True
            except Exception:
                return False

        elif channel_type == "direct":
            # 对于直接Socket通信，检查端口是否开放
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                result = s.connect_ex((config["host"], config["port"]))
                s.close()
                return result == 0
            except Exception:
                return False

        elif channel_type == "docker_network":
            # 检查Docker网络是否存在
            try:
                networks = self.docker_client.networks.list(
                    names=[config["network_name"]]
                )
                return len(networks) > 0
            except Exception:
                return False

        elif channel_type == "volume":
            # 检查Docker卷是否存在
            try:
                volumes = self.docker_client.volumes.list(
                    filters={"name": config["volume_name"]}
                )
                return len(volumes) > 0
            except Exception:
                return False

        return False

    def _send_heartbeats(self):
        """发送心跳消息到所有活跃的通信频道"""
        for channel_name, channel_info in self.channels.items():
            if channel_info["active"]:
                try:
                    self.publish_message(
                        channel_name=channel_name,
                        message="heartbeat",
                        message_type=self.MSG_TYPE_HEARTBEAT,
                        source_container="",
                        target_containers=[],
                    )
                except Exception as e:
                    logger.debug(f"发送心跳到频道 '{channel_name}' 失败: {str(e)}")

    def load_configurations(self):
        """从配置目录加载现有的通信配置"""
        config_dir = Path(self.config_dir)

        if not config_dir.exists():
            return

        for file_path in config_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                channel_name = file_path.stem
                self.channels[channel_name] = {
                    "name": channel_name,
                    "config": config,
                    "active": False,  # 初始状态为非活跃，等待后台线程检查
                    "subscribers": 0,  # 初始无订阅者
                }
                logger.debug(f"已加载通信配置: {channel_name}")
            except Exception as e:
                logger.error(f"加载通信配置 {file_path} 失败: {str(e)}")

    def save_configuration(self, channel_name: str):
        """保存通信配置到文件"""
        if channel_name not in self.channels:
            return False

        config_path = os.path.join(self.config_dir, f"{channel_name}.json")

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.channels[channel_name]["config"],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            logger.debug(f"已保存通信配置: {channel_name}")
            return True
        except Exception as e:
            logger.error(f"保存通信配置 {channel_name} 失败: {str(e)}")
            return False

    def configure_redis_communication(
        self,
        channel_name: str,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        container_names: Optional[List[str]] = None,
    ) -> bool:
        """
        配置基于Redis的通信频道

        Args:
            channel_name: 通信频道名称
            host: Redis主机地址
            port: Redis端口
            db: Redis数据库索引
            password: Redis密码
            container_names: 参与通信的容器名称列表

        Returns:
            bool: 配置是否成功
        """
        try:
            # 验证Redis连接
            try:
                import redis

                r = redis.Redis(host=host, port=port, db=db, password=password)
                r.ping()
            except ImportError:
                logger.warning("Redis模块未安装，无法验证连接")
            except Exception as e:
                logger.warning(f"Redis连接测试失败: {str(e)}")

            # 创建配置
            config = {
                "type": "redis",
                "redis_host": host,
                "redis_port": port,
                "redis_db": db,
                "container_names": container_names or [],
                "created_at": time.time(),
            }

            if password:
                config["redis_password"] = password

            # 存储配置
            self.channels[channel_name] = {
                "name": channel_name,
                "config": config,
                "active": True,  # 假设初始状态为活跃
                "subscribers": 0,
            }

            # 保存到文件
            self.save_configuration(channel_name)
            logger.info(f"已配置Redis通信频道: {channel_name}")
            return True

        except Exception as e:
            logger.error(f"配置Redis通信频道失败: {str(e)}")
            return False

    def configure_direct_communication(
        self,
        channel_name: str,
        protocol: str = "tcp",
        host: str = "0.0.0.0",
        port: int = 5555,
        container_names: Optional[List[str]] = None,
    ) -> bool:
        """
        配置基于直接Socket的通信频道

        Args:
            channel_name: 通信频道名称
            protocol: 通信协议 (tcp/udp)
            host: 监听主机地址
            port: 监听端口
            container_names: 参与通信的容器名称列表

        Returns:
            bool: 配置是否成功
        """
        try:
            # 创建配置
            config = {
                "type": "direct",
                "protocol": protocol,
                "host": host,
                "port": port,
                "container_names": container_names or [],
                "created_at": time.time(),
            }

            # 存储配置
            self.channels[channel_name] = {
                "name": channel_name,
                "config": config,
                "active": True,  # 假设初始状态为活跃
                "subscribers": 0,
            }

            # 保存到文件
            self.save_configuration(channel_name)
            logger.info(f"已配置直接Socket通信频道: {channel_name}")
            return True

        except Exception as e:
            logger.error(f"配置直接Socket通信频道失败: {str(e)}")
            return False

    def configure_docker_network_communication(
        self,
        channel_name: str,
        network_name: str,
        container_names: List[str],
    ) -> bool:
        """
        配置基于Docker网络的通信频道

        Args:
            channel_name: 通信频道名称
            network_name: Docker网络名称
            container_names: 参与通信的容器名称列表

        Returns:
            bool: 配置是否成功
        """
        try:
            # 验证Docker网络存在
            try:
                networks = self.docker_client.networks.list(names=[network_name])
                if not networks:
                    logger.warning(f"Docker网络 '{network_name}' 不存在")
            except Exception as e:
                logger.warning(f"无法验证Docker网络: {str(e)}")

            # 创建配置
            config = {
                "type": "docker_network",
                "network_name": network_name,
                "container_names": container_names,
                "created_at": time.time(),
            }

            # 存储配置
            self.channels[channel_name] = {
                "name": channel_name,
                "config": config,
                "active": True,  # 假设初始状态为活跃
                "subscribers": 0,
            }

            # 保存到文件
            self.save_configuration(channel_name)
            logger.info(f"已配置Docker网络通信频道: {channel_name}")
            return True

        except Exception as e:
            logger.error(f"配置Docker网络通信频道失败: {str(e)}")
            return False

    def configure_volume_communication(
        self,
        channel_name: str,
        volume_name: str,
        mount_path: str = "/shared",
        container_names: Optional[List[str]] = None,
    ) -> bool:
        """
        配置基于共享卷的通信频道

        Args:
            channel_name: 通信频道名称
            volume_name: Docker卷名称
            mount_path: 容器内挂载路径
            container_names: 参与通信的容器名称列表

        Returns:
            bool: 配置是否成功
        """
        try:
            # 验证Docker卷存在
            try:
                volumes = self.docker_client.volumes.list(filters={"name": volume_name})
                if not volumes:
                    logger.warning(f"Docker卷 '{volume_name}' 不存在")
            except Exception as e:
                logger.warning(f"无法验证Docker卷: {str(e)}")

            # 创建配置
            config = {
                "type": "volume",
                "volume_name": volume_name,
                "mount_path": mount_path,
                "container_names": (
                    container_names if container_names is not None else []
                ),
                "created_at": time.time(),
            }

            # 存储配置
            self.channels[channel_name] = {
                "name": channel_name,
                "config": config,
                "active": True,  # 假设初始状态为活跃
                "subscribers": 0,
            }

            # 保存到文件
            self.save_configuration(channel_name)
            logger.info(f"已配置共享卷通信频道: {channel_name}")
            return True

        except Exception as e:
            logger.error(f"配置共享卷通信频道失败: {str(e)}")
            return False

    def publish_message(
        self,
        channel_name: str,
        message: str,
        message_type: str = MSG_TYPE_DATA,
        source_container: str = "",
        target_containers: Optional[List[str]] = None,
    ) -> bool:
        """
        发布消息到指定通信频道

        Args:
            channel_name: 通信频道名称
            message: 消息内容
            message_type: 消息类型
            source_container: 源容器名称
            target_containers: 目标容器名称列表

        Returns:
            bool: 发布是否成功
        """
        if channel_name not in self.channels:
            logger.error(f"通信频道 '{channel_name}' 不存在")
            return False

        channel_info = self.channels[channel_name]
        if not channel_info["active"]:
            logger.error(f"通信频道 '{channel_name}' 不活跃")
            return False

        config = channel_info["config"]
        channel_type = config["type"]

        # 构建消息对象
        message_obj = {
            "id": self._generate_message_id(),
            "type": message_type,
            "content": message,
            "timestamp": time.time(),
            "source": source_container,
            "targets": target_containers,
        }

        # 根据通信类型发送消息
        try:
            if channel_type == "redis":
                return self._publish_redis_message(channel_name, config, message_obj)
            elif channel_type == "direct":
                return self._publish_direct_message(channel_name, config, message_obj)
            elif channel_type == "docker_network":
                return self._publish_network_message(channel_name, config, message_obj)
            elif channel_type == "volume":
                return self._publish_volume_message(channel_name, config, message_obj)
            else:
                logger.error(f"不支持的通信类型: {channel_type}")
                return False
        except Exception as e:
            logger.error(f"发布消息到频道 '{channel_name}' 失败: {str(e)}")
            return False

    def _generate_message_id(self) -> str:
        """生成唯一的消息ID"""
        return hashlib.md5(
            f"{time.time()}-{os.getpid()}-{threading.get_ident()}".encode()
        ).hexdigest()

    def _publish_redis_message(
        self, channel_name: str, config: Dict[str, Any], message_obj: Dict[str, Any]
    ) -> bool:
        """通过Redis发布消息"""
        try:
            import redis

            r = redis.Redis(
                host=config["redis_host"],
                port=config["redis_port"],
                db=config["redis_db"],
                password=config.get("redis_password"),
            )
            r.publish(f"smoothstack:comm:{channel_name}", json.dumps(message_obj))
            return True
        except ImportError:
            logger.error("Redis模块未安装，无法发布消息")
            return False
        except Exception as e:
            logger.error(f"Redis发布消息失败: {str(e)}")
            return False

    def _publish_direct_message(
        self, channel_name: str, config: Dict[str, Any], message_obj: Dict[str, Any]
    ) -> bool:
        """通过直接Socket发布消息"""
        try:
            host = config["host"]
            port = config["port"]
            protocol = config["protocol"]

            message_json = json.dumps(message_obj).encode("utf-8")

            if protocol == "tcp":
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.sendall(message_json)
                s.close()
            elif protocol == "udp":
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(message_json, (host, port))
                s.close()

            return True
        except Exception as e:
            logger.error(f"直接Socket发布消息失败: {str(e)}")
            return False

    def _publish_network_message(
        self, channel_name: str, config: Dict[str, Any], message_obj: Dict[str, Any]
    ) -> bool:
        """通过Docker网络发布消息"""
        # 目前使用Docker执行命令将消息广播到网络
        try:
            network_name = config["network_name"]
            container_names = config["container_names"]

            message_json = json.dumps(message_obj)

            # 使用Docker网络通信逻辑
            # 这里是简化实现，实际应用可能需要更复杂的方案
            for container_name in container_names:
                try:
                    container = self.docker_client.containers.get(container_name)
                    # 将消息写入容器的共享内存或临时文件
                    command = (
                        f"echo '{message_json}' > /tmp/smoothstack_comm_{channel_name}"
                    )
                    container.exec_run(command)
                except Exception as e:
                    logger.warning(f"发送消息到容器 '{container_name}' 失败: {str(e)}")

            return True
        except Exception as e:
            logger.error(f"Docker网络发布消息失败: {str(e)}")
            return False

    def _publish_volume_message(
        self, channel_name: str, config: Dict[str, Any], message_obj: Dict[str, Any]
    ) -> bool:
        """通过共享卷发布消息"""
        try:
            volume_name = config["volume_name"]
            mount_path = config["mount_path"]
            container_names = config["container_names"]

            message_json = json.dumps(message_obj)
            message_id = message_obj["id"]

            # 选择一个容器来写入消息
            if container_names:
                container_name = container_names[0]
                try:
                    container = self.docker_client.containers.get(container_name)
                    # 将消息写入共享卷
                    msg_path = f"{mount_path}/messages/{message_id}.json"
                    command = f"mkdir -p {mount_path}/messages && echo '{message_json}' > {msg_path}"
                    container.exec_run(command)
                    return True
                except Exception as e:
                    logger.error(f"写入消息到共享卷失败: {str(e)}")

            return False
        except Exception as e:
            logger.error(f"共享卷发布消息失败: {str(e)}")
            return False

    def list_channels(self) -> List[Dict[str, Any]]:
        """
        列出所有配置的通信频道

        Returns:
            List[Dict[str, Any]]: 通信频道信息列表
        """
        return [channel_info for channel_info in self.channels.values()]

    def get_channel_info(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定通信频道的详细信息

        Args:
            channel_name: 通信频道名称

        Returns:
            Optional[Dict[str, Any]]: 通信频道信息，不存在则返回None
        """
        return self.channels.get(channel_name)

    def remove_channel(self, channel_name: str) -> bool:
        """
        移除通信频道

        Args:
            channel_name: 通信频道名称

        Returns:
            bool: 是否成功移除
        """
        if channel_name not in self.channels:
            logger.error(f"通信频道 '{channel_name}' 不存在")
            return False

        try:
            # 移除内存中的配置
            self.channels.pop(channel_name)

            # 移除配置文件
            config_path = os.path.join(self.config_dir, f"{channel_name}.json")
            if os.path.exists(config_path):
                os.remove(config_path)

            logger.info(f"已移除通信频道: {channel_name}")
            return True
        except Exception as e:
            logger.error(f"移除通信频道 '{channel_name}' 失败: {str(e)}")
            return False


# 全局通信管理器实例
_global_comm_manager = None


def get_communication_manager() -> CommunicationManager:
    """
    获取全局通信管理器实例

    Returns:
        CommunicationManager: 通信管理器实例
    """
    global _global_comm_manager

    if _global_comm_manager is None:
        _global_comm_manager = CommunicationManager()

    return _global_comm_manager
