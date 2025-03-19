#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置监控器

监控配置文件的变化并自动重新加载
"""

import os
import time
import logging
import threading
from typing import Callable, Dict, List, Optional, Set, cast
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

# 配置日志
logger = logging.getLogger("smoothstack.config.watcher")


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""

    def __init__(self, callback: Callable[[str], None]):
        """
        初始化处理器

        Args:
            callback: 文件变更时的回调函数
        """
        super().__init__()
        self.callback = callback
        # 用于防止重复触发
        self._last_modified_time: Dict[str, float] = {}
        # 最小触发间隔（秒）
        self._min_interval = 1.0

    def on_modified(self, event):
        """
        处理文件修改事件

        Args:
            event: 文件系统事件
        """
        if not isinstance(event, FileModifiedEvent):
            return

        # 确保文件路径是字符串类型
        file_path = str(event.src_path)
        current_time = time.time()
        last_time = self._last_modified_time.get(file_path, 0)

        # 检查是否满足最小间隔
        if current_time - last_time >= self._min_interval:
            self._last_modified_time[file_path] = current_time
            self.callback(file_path)


class ConfigChangeEvent:
    """配置变更事件"""

    def __init__(self, file_path: str, config_key: Optional[str] = None):
        """
        初始化事件

        Args:
            file_path: 变更的配置文件路径
            config_key: 变更的配置键（如果可以确定）
        """
        self.file_path = file_path
        self.config_key = config_key
        self.timestamp = time.time()


class ConfigWatcher:
    """
    配置监控器

    监控配置文件的变化并触发重新加载
    """

    def __init__(self, config_dir: str):
        """
        初始化监控器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.observer = Observer()
        self._handler: Optional[ConfigFileHandler] = None
        self._watched_paths: Set[str] = set()
        self._callbacks: List[Callable[[ConfigChangeEvent], None]] = []
        self._running = False
        self._lock = threading.Lock()

    def add_watch(self, path: str) -> None:
        """
        添加监控路径

        Args:
            path: 要监控的文件或目录路径
        """
        abs_path = str(Path(path).resolve())
        if abs_path not in self._watched_paths:
            self._watched_paths.add(abs_path)
            if self._running and self._handler is not None:
                self._setup_watch(abs_path)

    def add_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """
        添加配置变更回调函数

        Args:
            callback: 配置变更时调用的函数
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """
        移除配置变更回调函数

        Args:
            callback: 要移除的回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start(self) -> None:
        """启动监控器"""
        if self._running:
            return

        with self._lock:
            if not self._running:
                self._handler = ConfigFileHandler(self._on_file_changed)

                # 设置所有监控路径
                for path in self._watched_paths:
                    self._setup_watch(path)

                self.observer.start()
                self._running = True
                logger.info("配置监控器已启动")

    def stop(self) -> None:
        """停止监控器"""
        if not self._running:
            return

        with self._lock:
            if self._running:
                self.observer.stop()
                self.observer.join()
                self._running = False
                logger.info("配置监控器已停止")

    def _setup_watch(self, path: str) -> None:
        """
        设置文件监控

        Args:
            path: 要监控的路径
        """
        try:
            # 确保处理器已初始化
            if self._handler is not None:
                self.observer.schedule(self._handler, path, recursive=False)
                logger.debug(f"开始监控配置文件: {path}")
            else:
                logger.error("无法设置监控：处理器未初始化")
        except Exception as e:
            logger.error(f"设置配置文件监控失败: {path}, 错误: {e}")

    def _on_file_changed(self, file_path: str) -> None:
        """
        处理文件变更

        Args:
            file_path: 变更的文件路径
        """
        # 创建事件对象
        event = ConfigChangeEvent(file_path)

        # 调用所有回调函数
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"执行配置变更回调时出错: {e}")

    def __enter__(self):
        """支持上下文管理器"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.stop()
