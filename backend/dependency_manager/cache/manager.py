#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存管理器

管理依赖包的本地缓存，实现包的离线存储和重用
"""

import os
import shutil
import logging
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.cache")


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录，默认为~/.smoothstack/cache
        """
        if cache_dir is None:
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(home_dir, ".smoothstack", "cache")

        self.cache_dir = cache_dir
        self.package_dir = os.path.join(cache_dir, "packages")
        self.metadata_file = os.path.join(cache_dir, "metadata.json")
        self.package_info = {}

        # 确保缓存目录存在
        self._ensure_cache_dir()

        # 加载缓存元数据
        self._load_metadata()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        os.makedirs(self.package_dir, exist_ok=True)

    def _load_metadata(self):
        """加载缓存元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.package_info = json.load(f)
                logger.debug(
                    f"Loaded cache metadata: {len(self.package_info)} packages"
                )
            except Exception as e:
                logger.error(f"Failed to load cache metadata: {e}")
                self.package_info = {}
        else:
            logger.debug("Cache metadata file does not exist yet")
            self.package_info = {}

    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.package_info, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved cache metadata: {len(self.package_info)} packages")
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def generate_cache_key(
        self,
        package_name: str,
        version: Optional[str] = None,
        installer_type: str = "pip",
    ) -> str:
        """
        生成缓存键

        Args:
            package_name: 包名
            version: 版本号
            installer_type: 安装器类型

        Returns:
            缓存键
        """
        key_parts = [installer_type, package_name]
        if version:
            key_parts.append(version)

        key_str = "-".join(key_parts)
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()

    def get_cache_path(self, cache_key: str) -> str:
        """
        获取缓存文件路径

        Args:
            cache_key: 缓存键

        Returns:
            缓存文件路径
        """
        return os.path.join(self.package_dir, cache_key)

    def has_package(
        self,
        package_name: str,
        version: Optional[str] = None,
        installer_type: str = "pip",
    ) -> bool:
        """
        检查包是否在缓存中

        Args:
            package_name: 包名
            version: 版本号
            installer_type: 安装器类型

        Returns:
            是否存在
        """
        cache_key = self.generate_cache_key(package_name, version, installer_type)
        return cache_key in self.package_info and os.path.exists(
            self.get_cache_path(cache_key)
        )

    def add_package(
        self,
        package_path: str,
        package_name: str,
        version: str,
        installer_type: str = "pip",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        添加包到缓存

        Args:
            package_path: 包文件路径
            package_name: 包名
            version: 版本号
            installer_type: 安装器类型
            metadata: 包元数据

        Returns:
            缓存键
        """
        cache_key = self.generate_cache_key(package_name, version, installer_type)
        cache_path = self.get_cache_path(cache_key)

        try:
            # 复制包文件到缓存
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            shutil.copy2(package_path, cache_path)

            # 更新元数据
            self.package_info[cache_key] = {
                "name": package_name,
                "version": version,
                "installer_type": installer_type,
                "added_time": time.time(),
                "file_size": os.path.getsize(cache_path),
                "access_count": 0,
                "last_access": None,
            }

            # 添加额外元数据
            if metadata:
                self.package_info[cache_key].update(metadata)

            # 保存元数据
            self._save_metadata()

            logger.info(f"Added package to cache: {package_name}@{version}")
            return cache_key
        except Exception as e:
            logger.error(f"Failed to add package to cache: {e}")
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except:
                    pass
            raise

    def get_package(
        self,
        package_name: str,
        version: Optional[str] = None,
        installer_type: str = "pip",
    ) -> Optional[str]:
        """
        从缓存获取包

        Args:
            package_name: 包名
            version: 版本号
            installer_type: 安装器类型

        Returns:
            包文件路径或None
        """
        cache_key = self.generate_cache_key(package_name, version, installer_type)

        if cache_key not in self.package_info:
            logger.debug(f"Package not in cache: {package_name}@{version}")
            return None

        cache_path = self.get_cache_path(cache_key)

        if not os.path.exists(cache_path):
            logger.warning(f"Package file missing from cache: {package_name}@{version}")
            del self.package_info[cache_key]
            self._save_metadata()
            return None

        # 更新访问计数和时间
        self.package_info[cache_key]["access_count"] += 1
        self.package_info[cache_key]["last_access"] = time.time()
        self._save_metadata()

        logger.debug(f"Retrieved package from cache: {package_name}@{version}")
        return cache_path

    def remove_package(
        self,
        package_name: str,
        version: Optional[str] = None,
        installer_type: str = "pip",
    ) -> bool:
        """
        从缓存删除包

        Args:
            package_name: 包名
            version: 版本号
            installer_type: 安装器类型

        Returns:
            是否删除成功
        """
        cache_key = self.generate_cache_key(package_name, version, installer_type)

        if cache_key not in self.package_info:
            logger.debug(
                f"Package not in cache, cannot remove: {package_name}@{version}"
            )
            return False

        cache_path = self.get_cache_path(cache_key)

        try:
            # 删除文件
            if os.path.exists(cache_path):
                os.remove(cache_path)

            # 更新元数据
            del self.package_info[cache_key]
            self._save_metadata()

            logger.info(f"Removed package from cache: {package_name}@{version}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove package from cache: {e}")
            return False

    def clean_cache(
        self, max_age_days: Optional[int] = None, max_size_mb: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        清理缓存

        Args:
            max_age_days: 最大保留天数
            max_size_mb: 最大缓存大小(MB)

        Returns:
            (清理的包数量, 释放的空间大小(bytes))
        """
        if not max_age_days and not max_size_mb:
            logger.debug("No cleaning criteria specified, skipping cache cleaning")
            return 0, 0

        # 按最后访问时间排序包
        sorted_packages = sorted(
            self.package_info.items(),
            key=lambda x: x[1].get("last_access") or x[1].get("added_time") or 0,
        )

        removed_count = 0
        freed_space = 0
        current_time = time.time()

        # 按时间清理
        if max_age_days:
            max_age_seconds = max_age_days * 24 * 60 * 60
            for cache_key, info in sorted_packages[:]:
                last_access = info.get("last_access") or info.get("added_time") or 0
                age = current_time - last_access

                if age > max_age_seconds:
                    cache_path = self.get_cache_path(cache_key)
                    if os.path.exists(cache_path):
                        file_size = os.path.getsize(cache_path)
                        os.remove(cache_path)
                        freed_space += file_size

                    del self.package_info[cache_key]
                    removed_count += 1
                    sorted_packages.remove((cache_key, info))

        # 按大小清理
        if max_size_mb:
            max_size_bytes = max_size_mb * 1024 * 1024
            current_size = sum(
                info.get("file_size", 0) for _, info in self.package_info.items()
            )

            # 如果超出大小限制，按最后访问时间删除最旧的包
            while current_size > max_size_bytes and sorted_packages:
                cache_key, info = sorted_packages.pop(0)
                cache_path = self.get_cache_path(cache_key)

                if os.path.exists(cache_path):
                    file_size = os.path.getsize(cache_path)
                    os.remove(cache_path)
                    freed_space += file_size
                    current_size -= file_size

                del self.package_info[cache_key]
                removed_count += 1

        # 保存元数据
        if removed_count > 0:
            self._save_metadata()
            logger.info(
                f"Cleaned cache: removed {removed_count} packages, freed {freed_space/1024/1024:.2f} MB"
            )

        return removed_count, freed_space

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        total_size = 0
        oldest_package_time = float("inf")
        newest_package_time = 0
        package_count = len(self.package_info)
        installer_types = {}

        for cache_key, info in self.package_info.items():
            # 计算总大小
            file_size = info.get("file_size", 0)
            total_size += file_size

            # 统计安装器类型
            installer_type = info.get("installer_type")
            if installer_type:
                installer_types[installer_type] = (
                    installer_types.get(installer_type, 0) + 1
                )

            # 最旧和最新的包
            added_time = info.get("added_time", 0)
            if added_time < oldest_package_time:
                oldest_package_time = added_time
            if added_time > newest_package_time:
                newest_package_time = added_time

        # 格式化时间
        if oldest_package_time == float("inf"):
            oldest_package_time = 0

        stats = {
            "package_count": package_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / 1024 / 1024,
            "installer_types": installer_types,
            "oldest_package_time": oldest_package_time,
            "newest_package_time": newest_package_time,
        }

        return stats

    def list_packages(self, installer_type: Optional[str] = None) -> List[Dict]:
        """
        列出缓存的包

        Args:
            installer_type: 安装器类型过滤

        Returns:
            包列表
        """
        result = []

        for cache_key, info in self.package_info.items():
            # 过滤安装器类型
            if installer_type and info.get("installer_type") != installer_type:
                continue

            # 检查文件是否存在
            cache_path = self.get_cache_path(cache_key)
            if not os.path.exists(cache_path):
                continue

            # 添加到结果
            package_info = {
                "cache_key": cache_key,
                "name": info.get("name"),
                "version": info.get("version"),
                "installer_type": info.get("installer_type"),
                "file_size": info.get("file_size"),
                "added_time": info.get("added_time"),
                "access_count": info.get("access_count"),
                "last_access": info.get("last_access"),
            }
            result.append(package_info)

        return result

    def get_status(self) -> Dict:
        """获取缓存状态"""
        return {
            "enabled": self.cache_enabled,
            "cache_dir": self.cache_dir,
            "cache_size": self.get_cache_size(),
            "usage": self.get_usage_stats(),
        }

    def get_cache_size(self) -> int:
        """获取缓存大小（字节）

        Returns:
            缓存大小（字节）
        """
        if not self.cache_enabled or not os.path.exists(self.cache_dir):
            return 0

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):  # 排除符号链接
                    total_size += os.path.getsize(fp)

        return total_size

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存详细信息

        Returns:
            缓存详细信息
        """
        if not self.cache_enabled or not os.path.exists(self.cache_dir):
            return {"count": 0, "items": []}

        # 获取缓存项统计
        cache_items = []
        item_count = 0

        # 遍历缓存目录
        for dirpath, dirnames, filenames in os.walk(self.cache_dir):
            for f in filenames:
                if f.endswith(".json"):  # 元数据文件
                    continue

                item_count += 1
                if len(cache_items) < 10:  # 只返回前10个
                    item_path = os.path.join(dirpath, f)
                    rel_path = os.path.relpath(item_path, self.cache_dir)

                    # 尝试读取元数据
                    meta_path = f"{item_path}.json"
                    meta_data = {}
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r") as meta_file:
                                meta_data = json.load(meta_file)
                        except Exception:
                            pass

                    cache_items.append(
                        {
                            "path": rel_path,
                            "size": os.path.getsize(item_path),
                            "accessed": meta_data.get("last_accessed", "unknown"),
                            "created": meta_data.get("created", "unknown"),
                        }
                    )

        return {"count": item_count, "items": cache_items}
