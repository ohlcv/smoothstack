#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境热重载管理器

提供前端和后端的热重载配置和管理功能
"""

import os
import json
import time  # 添加time模块导入
import logging
import threading
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import docker
from docker.errors import DockerException, NotFound, APIError

from backend.container_manager.manager import ContainerManager

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.dev_reload_manager")


class DevReloadManager:
    """开发环境热重载管理器"""

    def __init__(self):
        """初始化热重载管理器"""
        try:
            self.container_manager = ContainerManager()
            self.client = self.container_manager.client
            self._reload_configs = {}  # 存储热重载配置
            self._watchers = {}  # 存储文件监视器
            self._reload_lock = threading.RLock()  # 保护配置数据的锁

            # 创建配置存储目录
            self._config_dir = Path.home() / ".smoothstack" / "dev_reload"
            self._config_dir.mkdir(parents=True, exist_ok=True)

            # 加载已保存的配置
            self._load_configs()

            logger.info("热重载管理器初始化成功")
        except Exception as e:
            logger.error(f"热重载管理器初始化失败: {e}")
            raise

    def _load_configs(self) -> None:
        """加载已保存的热重载配置"""
        try:
            config_files = list(self._config_dir.glob("*.json"))
            for file_path in config_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        container_name = file_path.stem
                        self._reload_configs[container_name] = config_data
                        logger.debug(f"已加载容器 '{container_name}' 的热重载配置")
                except Exception as e:
                    logger.error(f"加载配置文件 {file_path} 失败: {e}")

            logger.info(f"已加载 {len(self._reload_configs)} 个热重载配置")
        except Exception as e:
            logger.error(f"加载热重载配置失败: {e}")

    def _save_config(self, container_name: str, config: Dict[str, Any]) -> bool:
        """保存热重载配置到文件"""
        try:
            file_path = self._config_dir / f"{container_name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.debug(f"容器 '{container_name}' 的热重载配置已保存到 {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存容器 '{container_name}' 的热重载配置失败: {e}")
            return False

    def configure_frontend_reload(
        self,
        container_name: str,
        watch_paths: List[str],
        vite_config: Optional[Dict[str, Any]] = None,  # 修复类型
        hmr_port: int = 3000,
        hmr_host: str = "0.0.0.0",
    ) -> bool:
        """
        配置前端热重载

        Args:
            container_name: 容器名称
            watch_paths: 需要监视的文件路径列表
            vite_config: Vite配置，如果不指定则使用默认配置
            hmr_port: HMR服务端口
            hmr_host: HMR服务主机地址

        Returns:
            是否配置成功
        """
        with self._reload_lock:
            try:
                # 检查容器是否存在
                container = self.client.containers.get(container_name)

                # 准备热重载配置
                reload_config = {
                    "type": "frontend",
                    "watch_paths": watch_paths,
                    "vite_config": vite_config
                    or {
                        "server": {
                            "host": hmr_host,
                            "port": hmr_port,
                            "hmr": {
                                "host": hmr_host,
                                "port": hmr_port,
                                "protocol": "ws",
                                "clientPort": hmr_port,
                            },
                            "watch": {
                                "usePolling": True,
                                "interval": 100,
                            },
                        },
                    },
                }

                # 保存配置
                self._reload_configs[container_name] = reload_config
                if not self._save_config(container_name, reload_config):
                    return False

                # 更新容器配置
                logger.info(f"更新容器 '{container_name}' 环境变量")

                # 将环境变量传递给容器内的进程，无需重启容器
                # 注意：这种方式不会持久化环境变量，但足够用于热重载场景
                container.exec_run(
                    f"export VITE_HMR_HOST={hmr_host} VITE_HMR_PORT={hmr_port}",
                    detach=True,
                )

                logger.info(f"已为容器 '{container_name}' 配置前端热重载")

                return True

            except Exception as e:
                logger.error(f"配置容器 '{container_name}' 的前端热重载失败: {e}")
                return False

    def configure_backend_reload(
        self,
        container_name: str,
        watch_paths: List[str],
        reload_command: Optional[str] = None,  # 修复类型
        exclude_patterns: Optional[List[str]] = None,  # 修复类型
        debounce_ms: int = 1000,
    ) -> bool:
        """
        配置后端热重载

        Args:
            container_name: 容器名称
            watch_paths: 需要监视的文件路径列表
            reload_command: 重载命令，如果不指定则使用默认命令
            exclude_patterns: 排除的文件模式列表
            debounce_ms: 重载延迟时间（毫秒）

        Returns:
            是否配置成功
        """
        with self._reload_lock:
            try:
                # 检查容器是否存在
                container = self.client.containers.get(container_name)

                # 准备热重载配置
                reload_config = {
                    "type": "backend",
                    "watch_paths": watch_paths,
                    "reload_command": reload_command
                    or "kill -HUP 1",  # 默认发送HUP信号
                    "exclude_patterns": exclude_patterns
                    or [
                        "*.pyc",
                        "__pycache__",
                        "*.swp",
                        "*.swx",
                        ".git",
                    ],
                    "debounce_ms": debounce_ms,
                }

                # 保存配置
                self._reload_configs[container_name] = reload_config
                if not self._save_config(container_name, reload_config):
                    return False

                # 更新容器配置
                logger.info(f"更新容器 '{container_name}' 环境变量")

                # 将环境变量传递给容器内的进程，无需重启容器
                # 注意：这种方式不会持久化环境变量，但足够用于热重载场景
                container.exec_run(
                    f"export PYTHON_RELOAD=1 PYTHONUNBUFFERED=1", detach=True
                )

                logger.info(f"已为容器 '{container_name}' 配置后端热重载")

                return True

            except Exception as e:
                logger.error(f"配置容器 '{container_name}' 的后端热重载失败: {e}")
                return False

    def start_reload(self, container_name: str) -> bool:
        """
        启动容器的热重载

        Args:
            container_name: 容器名称

        Returns:
            是否启动成功
        """
        with self._reload_lock:
            try:
                # 检查容器是否存在
                container = self.client.containers.get(container_name)

                # 检查是否有热重载配置
                if container_name not in self._reload_configs:
                    logger.error(f"容器 '{container_name}' 没有热重载配置")
                    return False

                config = self._reload_configs[container_name]
                reload_type = config["type"]

                if reload_type == "frontend":
                    # 启动Vite开发服务器
                    vite_config = config["vite_config"]
                    cmd = f"npm run dev -- --config {json.dumps(vite_config)}"
                    container.exec_run(
                        cmd,
                        detach=True,
                        environment={"NODE_ENV": "development"},
                    )
                    logger.info(f"已启动容器 '{container_name}' 的前端热重载")

                elif reload_type == "backend":
                    # 启动文件监视器
                    watch_paths = config["watch_paths"]
                    reload_command = config["reload_command"]
                    exclude_patterns = config["exclude_patterns"]
                    debounce_ms = config.get("debounce_ms", 1000)

                    # 创建监视器线程
                    watcher = threading.Thread(
                        target=self._watch_files,
                        args=(
                            container_name,
                            watch_paths,
                            reload_command,
                            exclude_patterns,
                            debounce_ms,
                        ),
                        daemon=True,
                    )
                    self._watchers[container_name] = watcher
                    watcher.start()

                    logger.info(f"已启动容器 '{container_name}' 的后端热重载")

                return True

            except Exception as e:
                logger.error(f"启动容器 '{container_name}' 的热重载失败: {e}")
                return False

    def stop_reload(self, container_name: str) -> bool:
        """
        停止容器的热重载

        Args:
            container_name: 容器名称

        Returns:
            是否停止成功
        """
        with self._reload_lock:
            try:
                # 检查容器是否存在
                container = self.client.containers.get(container_name)

                # 检查是否有热重载配置
                if container_name not in self._reload_configs:
                    logger.error(f"容器 '{container_name}' 没有热重载配置")
                    return False

                config = self._reload_configs[container_name]
                reload_type = config["type"]

                if reload_type == "frontend":
                    # 停止Vite开发服务器
                    container.exec_run("pkill -f vite", detach=True)
                    logger.info(f"已停止容器 '{container_name}' 的前端热重载")

                elif reload_type == "backend":
                    # 停止文件监视器
                    if container_name in self._watchers:
                        # 移除监视器线程
                        del self._watchers[container_name]
                        logger.info(f"已停止容器 '{container_name}' 的后端热重载")

                return True

            except Exception as e:
                logger.error(f"停止容器 '{container_name}' 的热重载失败: {e}")
                return False

    def _watch_files(
        self,
        container_name: str,
        watch_paths: List[str],
        reload_command: str,
        exclude_patterns: List[str],
        debounce_ms: int = 1000,
    ) -> None:
        """
        监视文件变化并触发重载

        Args:
            container_name: 容器名称
            watch_paths: 监视的文件路径列表
            reload_command: 重载命令
            exclude_patterns: 排除的文件模式列表
            debounce_ms: 重载延迟时间（毫秒）
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileSystemEvent
            import fnmatch

            class ReloadHandler(FileSystemEventHandler):
                def __init__(
                    self, container, reload_command, exclude_patterns, debounce_ms
                ):
                    self.container = container
                    self.reload_command = reload_command
                    self.exclude_patterns = exclude_patterns
                    self.last_reload = 0
                    self.debounce_ms = debounce_ms  # 防抖时间

                def on_any_event(self, event: FileSystemEvent):
                    # 检查是否应该忽略此文件
                    if hasattr(event, "src_path") and any(
                        fnmatch.fnmatch(str(event.src_path), pattern)  # 转为字符串处理
                        for pattern in self.exclude_patterns
                    ):
                        return

                    # 防抖处理
                    now = time.time() * 1000
                    if now - self.last_reload < self.debounce_ms:
                        return

                    self.last_reload = now

                    try:
                        # 执行重载命令
                        self.container.exec_run(self.reload_command, detach=True)
                        logger.debug(
                            f"容器 '{self.container.name}' 执行重载命令: {self.reload_command}"
                        )
                    except Exception as e:
                        logger.error(f"执行重载命令失败: {e}")

            # 获取容器
            container = self.client.containers.get(container_name)

            # 创建事件处理器
            handler = ReloadHandler(
                container, reload_command, exclude_patterns, debounce_ms
            )

            # 创建观察者
            observer = Observer()
            for path in watch_paths:
                observer.schedule(handler, path, recursive=True)

            # 启动观察者
            observer.start()
            logger.info(f"已启动容器 '{container_name}' 的文件监视器")

            # 等待停止信号
            while container_name in self._watchers:
                time.sleep(1)

            # 停止观察者
            observer.stop()
            observer.join()

        except Exception as e:
            logger.error(f"文件监视器运行失败: {e}")

    def list_reload_configs(self) -> List[Dict[str, Any]]:
        """
        列出所有热重载配置

        Returns:
            配置列表
        """
        with self._reload_lock:
            return [
                {
                    "container_name": name,
                    "config": config,
                    "active": name in self._watchers,
                }
                for name, config in self._reload_configs.items()
            ]

    def get_reload_config(self, container_name: str) -> Optional[Dict[str, Any]]:
        """
        获取容器的热重载配置

        Args:
            container_name: 容器名称

        Returns:
            热重载配置，如不存在则返回None
        """
        with self._reload_lock:
            if container_name not in self._reload_configs:
                return None

            return {
                "container_name": container_name,
                "config": self._reload_configs[container_name],
                "active": container_name in self._watchers,
            }

    def remove_reload_config(self, container_name: str) -> bool:
        """
        移除容器的热重载配置

        Args:
            container_name: 容器名称

        Returns:
            是否移除成功
        """
        with self._reload_lock:
            if container_name not in self._reload_configs:
                logger.warning(f"容器 '{container_name}' 没有热重载配置")
                return False

            # 如果正在运行，先停止
            if container_name in self._watchers:
                self.stop_reload(container_name)

            # 删除配置文件
            file_path = self._config_dir / f"{container_name}.json"
            if file_path.exists():
                file_path.unlink()

            # 从内存中移除
            del self._reload_configs[container_name]

            logger.info(f"已移除容器 '{container_name}' 的热重载配置")
            return True


# 单例模式获取热重载管理器实例
_dev_reload_manager_instance = None


def get_dev_reload_manager() -> DevReloadManager:
    """
    获取热重载管理器单例实例

    Returns:
        热重载管理器实例
    """
    global _dev_reload_manager_instance
    if _dev_reload_manager_instance is None:
        _dev_reload_manager_instance = DevReloadManager()
    return _dev_reload_manager_instance
