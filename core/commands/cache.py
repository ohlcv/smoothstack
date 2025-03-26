#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存命令模块

提供缓存相关的命令，包括：
- 缓存配置
- 缓存监控
- 缓存清理
- 缓存预热
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


class CacheCommand(BaseCommand):
    """缓存命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.cache_dir = self.project_root / "cache"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def config(self, project_name: str, action: str, **kwargs):
        """缓存配置"""
        try:
            self.info(f"缓存配置: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查缓存配置
            config_file = project_dir / "cache" / "config.yml"
            if not config_file.exists():
                config = {}
            else:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

            # 配置缓存
            if action == "add":
                self._add_cache_config(config, **kwargs)
            elif action == "remove":
                self._remove_cache_config(config, **kwargs)
            elif action == "update":
                self._update_cache_config(config, **kwargs)
            elif action == "show":
                self._show_cache_config(config)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("缓存配置已更新")

        except Exception as e:
            self.error(f"缓存配置失败: {e}")
            raise

    def monitor(self, project_name: str):
        """缓存监控"""
        try:
            self.info(f"缓存监控: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查缓存配置
            config_file = project_dir / "cache" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("缓存配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 监控缓存
            self._monitor_cache(config)

        except Exception as e:
            self.error(f"缓存监控失败: {e}")
            raise

    def clean(self, project_name: str, cache_name: Optional[str] = None):
        """缓存清理"""
        try:
            self.info(f"缓存清理: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查缓存配置
            config_file = project_dir / "cache" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("缓存配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 清理缓存
            self._clean_cache(config, cache_name)

            self.success("缓存清理成功")

        except Exception as e:
            self.error(f"缓存清理失败: {e}")
            raise

    def warmup(self, project_name: str, cache_name: Optional[str] = None):
        """缓存预热"""
        try:
            self.info(f"缓存预热: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查缓存配置
            config_file = project_dir / "cache" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("缓存配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 预热缓存
            self._warmup_cache(config, cache_name)

            self.success("缓存预热成功")

        except Exception as e:
            self.error(f"缓存预热失败: {e}")
            raise

    def _add_cache_config(self, config: Dict[str, Any], **kwargs):
        """添加缓存配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("缓存名称不能为空")

            # 添加配置
            name = kwargs.pop("name")
            config[name] = kwargs

            self.success(f"添加缓存配置成功: {name}")

        except Exception as e:
            self.error(f"添加缓存配置失败: {e}")
            raise

    def _remove_cache_config(self, config: Dict[str, Any], **kwargs):
        """移除缓存配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("缓存名称不能为空")

            # 移除配置
            name = kwargs["name"]
            if name in config:
                del config[name]
                self.success(f"移除缓存配置成功: {name}")
            else:
                self.warning(f"缓存配置不存在: {name}")

        except Exception as e:
            self.error(f"移除缓存配置失败: {e}")
            raise

    def _update_cache_config(self, config: Dict[str, Any], **kwargs):
        """更新缓存配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("缓存名称不能为空")

            # 更新配置
            name = kwargs.pop("name")
            if name in config:
                config[name].update(kwargs)
                self.success(f"更新缓存配置成功: {name}")
            else:
                self.warning(f"缓存配置不存在: {name}")

        except Exception as e:
            self.error(f"更新缓存配置失败: {e}")
            raise

    def _show_cache_config(self, config: Dict[str, Any]):
        """显示缓存配置"""
        try:
            if not config:
                self.info("未配置缓存")
                return

            self.info("\n缓存配置:")
            for name, cache in config.items():
                self.info(f"名称: {name}")
                for key, value in cache.items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"显示缓存配置失败: {e}")
            raise

    def _monitor_cache(self, config: Dict[str, Any]):
        """监控缓存"""
        try:
            # 获取系统内存
            memory = psutil.virtual_memory()
            self.info("\n系统内存:")
            self.info(f"总内存: {memory.total / 1024 / 1024 / 1024:.2f}GB")
            self.info(f"已用内存: {memory.used / 1024 / 1024 / 1024:.2f}GB")
            self.info(f"可用内存: {memory.available / 1024 / 1024 / 1024:.2f}GB")
            self.info(f"使用率: {memory.percent}%")

            # 获取缓存统计
            for name, cache in config.items():
                # 获取缓存路径
                cache_path = Path(cache.get("path", ""))
                if not cache_path.exists():
                    self.warning(f"缓存路径不存在: {cache_path}")
                    continue

                # 获取缓存大小
                cache_size = self._get_dir_size(cache_path)
                self.info(f"\n缓存 {name}:")
                self.info(f"路径: {cache_path}")
                self.info(f"大小: {cache_size}")

                # 获取缓存统计
                if "type" in cache and cache["type"] == "redis":
                    self._monitor_redis_cache(cache)
                elif "type" in cache and cache["type"] == "memcached":
                    self._monitor_memcached_cache(cache)

        except Exception as e:
            self.error(f"监控缓存失败: {e}")
            raise

    def _clean_cache(self, config: Dict[str, Any], cache_name: Optional[str] = None):
        """清理缓存"""
        try:
            # 清理指定缓存
            if cache_name:
                if cache_name in config:
                    self._clean_single_cache(config[cache_name])
                else:
                    self.warning(f"缓存配置不存在: {cache_name}")
            else:
                # 清理所有缓存
                for name, cache in config.items():
                    self._clean_single_cache(cache)

        except Exception as e:
            self.error(f"清理缓存失败: {e}")
            raise

    def _warmup_cache(self, config: Dict[str, Any], cache_name: Optional[str] = None):
        """预热缓存"""
        try:
            # 预热指定缓存
            if cache_name:
                if cache_name in config:
                    self._warmup_single_cache(config[cache_name])
                else:
                    self.warning(f"缓存配置不存在: {cache_name}")
            else:
                # 预热所有缓存
                for name, cache in config.items():
                    self._warmup_single_cache(cache)

        except Exception as e:
            self.error(f"预热缓存失败: {e}")
            raise

    def _clean_single_cache(self, cache: Dict[str, Any]):
        """清理单个缓存"""
        try:
            # 获取缓存路径
            cache_path = Path(cache.get("path", ""))
            if not cache_path.exists():
                self.warning(f"缓存路径不存在: {cache_path}")
                return

            # 清理缓存
            if "type" in cache:
                if cache["type"] == "redis":
                    self._clean_redis_cache(cache)
                elif cache["type"] == "memcached":
                    self._clean_memcached_cache(cache)
                else:
                    # 清理文件缓存
                    shutil.rmtree(cache_path)
                    cache_path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            self.error(f"清理缓存失败: {e}")
            raise

    def _warmup_single_cache(self, cache: Dict[str, Any]):
        """预热单个缓存"""
        try:
            # 获取缓存路径
            cache_path = Path(cache.get("path", ""))
            if not cache_path.exists():
                self.warning(f"缓存路径不存在: {cache_path}")
                return

            # 预热缓存
            if "type" in cache:
                if cache["type"] == "redis":
                    self._warmup_redis_cache(cache)
                elif cache["type"] == "memcached":
                    self._warmup_memcached_cache(cache)
                else:
                    # 预热文件缓存
                    self._warmup_file_cache(cache)

        except Exception as e:
            self.error(f"预热缓存失败: {e}")
            raise

    def _monitor_redis_cache(self, cache: Dict[str, Any]):
        """监控Redis缓存"""
        try:
            # 获取Redis连接
            import redis

            client = redis.Redis(
                host=cache.get("host", "localhost"),
                port=cache.get("port", 6379),
                db=cache.get("db", 0),
                password=cache.get("password", None),
            )

            # 获取Redis信息
            info = client.info()
            self.info("\nRedis信息:")
            self.info(f"版本: {info['redis_version']}")
            self.info(f"运行时间: {info['uptime_in_seconds']}秒")
            self.info(f"连接数: {info['connected_clients']}")
            self.info(f"内存使用: {info['used_memory_human']}")
            self.info(f"内存峰值: {info['used_memory_peak_human']}")
            self.info(
                f"命中率: {info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']):.2%}"
            )

        except Exception as e:
            self.error(f"监控Redis缓存失败: {e}")
            raise

    def _monitor_memcached_cache(self, cache: Dict[str, Any]):
        """监控Memcached缓存"""
        try:
            # 获取Memcached连接
            import memcache

            client = memcache.Client(
                [f"{cache.get('host', 'localhost')}:{cache.get('port', 11211)}"]
            )

            # 获取Memcached统计
            stats = client.get_stats()
            if stats:
                stats = stats[0][1]
                self.info("\nMemcached统计:")
                self.info(f"版本: {stats[b'version'].decode()}")
                self.info(f"运行时间: {stats[b'uptime'].decode()}秒")
                self.info(f"连接数: {stats[b'curr_connections'].decode()}")
                self.info(f"内存使用: {int(stats[b'bytes']) / 1024 / 1024:.2f}MB")
                self.info(
                    f"命中率: {int(stats[b'get_hits']) / (int(stats[b'get_hits']) + int(stats[b'get_misses'])):.2%}"
                )

        except Exception as e:
            self.error(f"监控Memcached缓存失败: {e}")
            raise

    def _clean_redis_cache(self, cache: Dict[str, Any]):
        """清理Redis缓存"""
        try:
            # 获取Redis连接
            import redis

            client = redis.Redis(
                host=cache.get("host", "localhost"),
                port=cache.get("port", 6379),
                db=cache.get("db", 0),
                password=cache.get("password", None),
            )

            # 清理缓存
            client.flushdb()

        except Exception as e:
            self.error(f"清理Redis缓存失败: {e}")
            raise

    def _clean_memcached_cache(self, cache: Dict[str, Any]):
        """清理Memcached缓存"""
        try:
            # 获取Memcached连接
            import memcache

            client = memcache.Client(
                [f"{cache.get('host', 'localhost')}:{cache.get('port', 11211)}"]
            )

            # 清理缓存
            client.flush_all()

        except Exception as e:
            self.error(f"清理Memcached缓存失败: {e}")
            raise

    def _warmup_redis_cache(self, cache: Dict[str, Any]):
        """预热Redis缓存"""
        try:
            # 获取Redis连接
            import redis

            client = redis.Redis(
                host=cache.get("host", "localhost"),
                port=cache.get("port", 6379),
                db=cache.get("db", 0),
                password=cache.get("password", None),
            )

            # 预热缓存
            if "warmup_data" in cache:
                for key, value in cache["warmup_data"].items():
                    client.set(key, value)

        except Exception as e:
            self.error(f"预热Redis缓存失败: {e}")
            raise

    def _warmup_memcached_cache(self, cache: Dict[str, Any]):
        """预热Memcached缓存"""
        try:
            # 获取Memcached连接
            import memcache

            client = memcache.Client(
                [f"{cache.get('host', 'localhost')}:{cache.get('port', 11211)}"]
            )

            # 预热缓存
            if "warmup_data" in cache:
                for key, value in cache["warmup_data"].items():
                    client.set(key, value)

        except Exception as e:
            self.error(f"预热Memcached缓存失败: {e}")
            raise

    def _warmup_file_cache(self, cache: Dict[str, Any]):
        """预热文件缓存"""
        try:
            # 获取缓存路径
            cache_path = Path(cache.get("path", ""))
            if not cache_path.exists():
                self.warning(f"缓存路径不存在: {cache_path}")
                return

            # 预热缓存
            if "warmup_data" in cache:
                for key, value in cache["warmup_data"].items():
                    file_path = cache_path / key
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(str(value))

        except Exception as e:
            self.error(f"预热文件缓存失败: {e}")
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
def cache():
    """缓存命令"""
    pass


@cache.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="缓存名称")
@click.option("--type", "-t", help="缓存类型")
@click.option("--path", "-p", help="缓存路径")
@click.option("--host", "-h", help="主机地址")
@click.option("--port", "-P", help="端口号")
@click.option("--db", "-d", help="数据库")
@click.option("--password", "-w", help="密码")
def config(project_name: str, action: str, **kwargs):
    """缓存配置"""
    cmd = CacheCommand()
    cmd.config(project_name, action, **kwargs)


@cache.command()
@click.argument("project_name")
def monitor(project_name: str):
    """缓存监控"""
    cmd = CacheCommand()
    cmd.monitor(project_name)


@cache.command()
@click.argument("project_name")
@click.option("--name", "-n", help="缓存名称")
def clean(project_name: str, name: Optional[str]):
    """缓存清理"""
    cmd = CacheCommand()
    cmd.clean(project_name, name)


@cache.command()
@click.argument("project_name")
@click.option("--name", "-n", help="缓存名称")
def warmup(project_name: str, name: Optional[str]):
    """缓存预热"""
    cmd = CacheCommand()
    cmd.warmup(project_name, name)
