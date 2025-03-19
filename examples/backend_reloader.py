#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
后端热重载辅助模块

为Python Web应用提供简易的热重载功能
适用于Flask, FastAPI等框架
"""

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from typing import List, Set, Optional, Callable, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend_reloader")


class Reloader:
    """Python应用热重载器"""

    def __init__(
        self,
        watch_paths: List[str],
        exclude_patterns: Optional[List[str]] = None,
        poll_interval: float = 1.0,
        debounce_ms: int = 1000,
    ):
        """
        初始化热重载器

        Args:
            watch_paths: 要监视的文件路径列表
            exclude_patterns: 排除的文件模式列表
            poll_interval: 轮询间隔(秒)
            debounce_ms: 防抖时间(毫秒)
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".git",
        ]
        self.poll_interval = poll_interval
        self.debounce_ms = debounce_ms
        self.last_reload_time = 0
        self.mtimes: Dict[str, float] = {}  # 文件修改时间缓存
        self._stop_event = threading.Event()
        self._watcher_thread = None
        self._reload_callback = None

    def start(self, reload_callback: Callable[[], None] = None) -> None:
        """
        启动文件监视器

        Args:
            reload_callback: 检测到文件变化时执行的回调函数
        """
        if self._watcher_thread and self._watcher_thread.is_alive():
            logger.warning("热重载器已经在运行")
            return

        self._reload_callback = reload_callback or self._default_reload
        self._stop_event.clear()
        self._watcher_thread = threading.Thread(
            target=self._watch_files,
            daemon=True,
        )
        self._watcher_thread.start()
        logger.info(
            f"已启动热重载器，监视路径: {', '.join(str(p) for p in self.watch_paths)}"
        )

    def stop(self) -> None:
        """停止文件监视器"""
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._stop_event.set()
            self._watcher_thread.join(timeout=5.0)
            logger.info("已停止热重载器")
        else:
            logger.warning("热重载器未运行")

    def _watch_files(self) -> None:
        """监视文件变化"""
        # 初始化修改时间缓存
        self._update_mtimes_cache()

        # 监视循环
        while not self._stop_event.is_set():
            if self._check_for_changes():
                # 检查防抖
                now = time.time() * 1000
                if now - self.last_reload_time >= self.debounce_ms:
                    self.last_reload_time = now
                    self._trigger_reload()

            # 等待下一次检查
            self._stop_event.wait(self.poll_interval)

    def _update_mtimes_cache(self) -> None:
        """更新文件修改时间缓存"""
        for path in self.watch_paths:
            if not path.exists():
                continue

            if path.is_file():
                self._update_file_mtime(path)
            else:
                for file_path in path.rglob("*"):
                    if file_path.is_file() and not self._is_excluded(file_path):
                        self._update_file_mtime(file_path)

    def _update_file_mtime(self, file_path: Path) -> None:
        """更新单个文件的修改时间"""
        try:
            mtime = file_path.stat().st_mtime
            self.mtimes[str(file_path)] = mtime
        except (OSError, IOError):
            # 忽略无法访问的文件
            pass

    def _check_for_changes(self) -> bool:
        """检查文件是否有变化"""
        for path in self.watch_paths:
            if not path.exists():
                continue

            if path.is_file():
                if self._check_file_changed(path):
                    return True
            else:
                for file_path in path.rglob("*"):
                    if file_path.is_file() and not self._is_excluded(file_path):
                        if self._check_file_changed(file_path):
                            return True

        return False

    def _check_file_changed(self, file_path: Path) -> bool:
        """检查单个文件是否有变化"""
        try:
            key = str(file_path)
            mtime = file_path.stat().st_mtime

            if key not in self.mtimes:
                # 新文件
                self.mtimes[key] = mtime
                return True

            if self.mtimes[key] != mtime:
                # 文件已修改
                self.mtimes[key] = mtime
                return True

        except (OSError, IOError):
            # 忽略无法访问的文件
            pass

        return False

    def _is_excluded(self, file_path: Path) -> bool:
        """检查文件是否应该被排除"""
        import fnmatch

        str_path = str(file_path)
        return any(
            fnmatch.fnmatch(str_path, pattern) for pattern in self.exclude_patterns
        )

    def _trigger_reload(self) -> None:
        """触发重载"""
        if self._reload_callback:
            try:
                logger.info("检测到文件变化，正在重载应用...")
                self._reload_callback()
            except Exception as e:
                logger.error(f"重载回调执行失败: {e}")

    def _default_reload(self) -> None:
        """默认重载行为：向主进程发送SIGHUP信号"""
        logger.info("发送SIGHUP信号重启应用")
        pid = os.getpid()
        os.kill(pid, signal.SIGHUP)


# Flask应用热重载集成
def setup_flask_reloader(
    app, watch_paths=None, exclude_patterns=None, debounce_ms=1000
):
    """为Flask应用设置热重载"""
    from flask import Flask

    if not isinstance(app, Flask):
        raise TypeError("app必须是Flask实例")

    # 默认监视当前工作目录
    watch_paths = watch_paths or [os.getcwd()]

    # 创建重载器
    reloader = Reloader(
        watch_paths=watch_paths,
        exclude_patterns=exclude_patterns,
        debounce_ms=debounce_ms,
    )

    # 定义重载回调
    def reload_flask_app():
        logger.info("正在重载Flask应用...")
        # Flask开发服务器自动重载机制
        os.environ["FLASK_ENV"] = "development"
        os.environ["FLASK_DEBUG"] = "1"

    # 在应用上下文中保存重载器
    app.reloader = reloader

    # 在应用启动前启动重载器
    @app.before_first_request
    def start_reloader():
        reloader.start(reload_callback=reload_flask_app)

    # 在应用关闭时停止重载器
    @app.teardown_appcontext
    def stop_reloader(exception=None):
        reloader.stop()

    return reloader


# FastAPI应用热重载集成
def setup_fastapi_reloader(
    app, watch_paths=None, exclude_patterns=None, debounce_ms=1000
):
    """为FastAPI应用设置热重载"""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("app必须是FastAPI实例")

    # 默认监视当前工作目录
    watch_paths = watch_paths or [os.getcwd()]

    # 创建重载器
    reloader = Reloader(
        watch_paths=watch_paths,
        exclude_patterns=exclude_patterns,
        debounce_ms=debounce_ms,
    )

    # 定义重载回调
    def reload_fastapi_app():
        logger.info("正在重载FastAPI应用...")
        # 使用uvicorn的重载机制
        os.environ["UVICORN_RELOAD"] = "1"

    # 在应用启动时启动重载器
    @app.on_event("startup")
    async def start_reloader():
        reloader.start(reload_callback=reload_fastapi_app)

    # 在应用关闭时停止重载器
    @app.on_event("shutdown")
    async def stop_reloader():
        reloader.stop()

    return reloader


if __name__ == "__main__":
    # 示例：独立重载器
    reload_paths = [os.getcwd()]
    exclude = ["*.pyc", "__pycache__", ".git"]

    reloader = Reloader(watch_paths=reload_paths, exclude_patterns=exclude)

    # 自定义重载行为
    def custom_reload():
        print("检测到文件变化，正在执行自定义重载...")
        # 在这里添加您的自定义重载逻辑

    try:
        # 启动重载器
        reloader.start(reload_callback=custom_reload)

        # 保持主线程运行
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # 优雅退出
        reloader.stop()
        print("已停止重载器")
