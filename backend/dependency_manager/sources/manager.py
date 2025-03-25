#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
源管理器

管理所有依赖源，提供源的添加、删除、切换等功能
"""

import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any

from backend.config import config
from .source import Source, SourceType, SourceStatus
from .pypi import PyPISource
from .npm import NPMSource

# 配置日志
logger = logging.getLogger("smoothstack.dependency_manager.sources.manager")


class SourceManager:
    """源管理器"""

    def __init__(self):
        """初始化源管理器"""
        logger.info("Initializing source manager")

        # 初始化源集合
        self.sources: Dict[str, Source] = {}
        self.source_groups: Dict[str, List[str]] = {}
        self.installer_sources: Dict[str, List[str]] = {
            "pip": [],
            "npm": [],
        }

        # 加载默认源配置
        self._load_default_sources()

        logger.info(f"Source manager initialized with {len(self.sources)} sources")

    def _load_default_sources(self):
        """加载默认源配置"""
        # 加载系统预设源
        self._add_preset_sources()

        # 加载用户自定义源
        self._load_custom_sources()

    def _add_preset_sources(self):
        """添加系统预设源"""
        # PyPI源
        self.add_source(
            PyPISource(
                name="pypi-official",
                url="https://pypi.org/simple",
                priority=100,
                group="global",
            )
        )

        self.add_source(
            PyPISource(
                name="pypi-tsinghua",
                url="https://pypi.tuna.tsinghua.edu.cn/simple",
                priority=50,
                group="china",
            )
        )

        self.add_source(
            PyPISource(
                name="pypi-aliyun",
                url="https://mirrors.aliyun.com/pypi/simple",
                priority=60,
                group="china",
            )
        )

        # NPM源
        self.add_source(
            NPMSource(
                name="npm-official",
                url="https://registry.npmjs.org",
                priority=100,
                group="global",
            )
        )

        self.add_source(
            NPMSource(
                name="npm-taobao",
                url="https://registry.npmmirror.com",
                priority=50,
                group="china",
            )
        )

    def _load_custom_sources(self):
        """加载用户自定义源"""
        # 从配置中加载自定义源
        custom_sources = config.get("dependency_manager.sources", {})
        for name, source_config in custom_sources.items():
            if name in self.sources:
                # 跳过已存在的源
                continue

            source_type = source_config.get("type")
            if source_type == "pypi":
                self.add_source(
                    PyPISource(
                        name=name,
                        url=source_config.get("url"),
                        priority=source_config.get("priority", 200),
                        group=source_config.get("group", "custom"),
                        enabled=source_config.get("enabled", True),
                    )
                )
            elif source_type == "npm":
                self.add_source(
                    NPMSource(
                        name=name,
                        url=source_config.get("url"),
                        priority=source_config.get("priority", 200),
                        group=source_config.get("group", "custom"),
                        enabled=source_config.get("enabled", True),
                    )
                )

    def add_source(self, source: Source) -> bool:
        """
        添加源

        Args:
            source: 源对象

        Returns:
            是否添加成功
        """
        if source.name in self.sources:
            logger.warning(f"Source '{source.name}' already exists")
            return False

        self.sources[source.name] = source

        # 添加到源分组
        if source.group not in self.source_groups:
            self.source_groups[source.group] = []
        self.source_groups[source.group].append(source.name)

        # 添加到安装器源列表
        if source.type == SourceType.PYPI:
            self.installer_sources["pip"].append(source.name)
        elif source.type == SourceType.NPM:
            self.installer_sources["npm"].append(source.name)

        logger.info(f"Source '{source.name}' added")
        return True

    def remove_source(self, name: str) -> bool:
        """
        删除源

        Args:
            name: 源名称

        Returns:
            是否删除成功
        """
        if name not in self.sources:
            logger.warning(f"Source '{name}' not found")
            return False

        source = self.sources[name]

        # 从源分组中删除
        if (
            source.group in self.source_groups
            and name in self.source_groups[source.group]
        ):
            self.source_groups[source.group].remove(name)

        # 从安装器源列表中删除
        if source.type == SourceType.PYPI and name in self.installer_sources["pip"]:
            self.installer_sources["pip"].remove(name)
        elif source.type == SourceType.NPM and name in self.installer_sources["npm"]:
            self.installer_sources["npm"].remove(name)

        # 删除源
        del self.sources[name]

        logger.info(f"Source '{name}' removed")
        return True

    def get_source(self, name: str) -> Optional[Source]:
        """
        获取源

        Args:
            name: 源名称

        Returns:
            源对象，如果不存在则返回None
        """
        return self.sources.get(name)

    def get_sources_by_group(self, group: str) -> List[Source]:
        """
        获取分组下的所有源

        Args:
            group: 分组名称

        Returns:
            源列表
        """
        if group not in self.source_groups:
            return []

        return [
            self.sources[name]
            for name in self.source_groups[group]
            if name in self.sources
        ]

    def get_sources_by_installer(self, installer_type: str) -> List[Source]:
        """
        获取安装器支持的所有源

        Args:
            installer_type: 安装器类型

        Returns:
            源列表
        """
        if installer_type not in self.installer_sources:
            return []

        return [
            self.sources[name]
            for name in self.installer_sources[installer_type]
            if name in self.sources
        ]

    def get_best_source(self, installer_type: str) -> Optional[Source]:
        """
        获取最优源

        Args:
            installer_type: 安装器类型

        Returns:
            最优源，如果没有可用源则返回None
        """
        sources = self.get_sources_by_installer(installer_type)
        if not sources:
            return None

        # 按优先级对源进行排序
        sources.sort(key=lambda s: s.priority)

        # 检查源的可用性，返回第一个可用的源
        for source in sources:
            if source.is_available():
                return source

        # 如果没有可用源，重新检查所有源的健康状态
        self.check_all_health(installer_type)

        # 再次尝试查找可用源
        for source in sources:
            if source.is_available():
                return source

        # 如果仍然没有可用源，返回第一个源（即使它不可用）
        logger.warning(
            f"No available source for '{installer_type}', using first source"
        )
        return sources[0] if sources else None

    def switch_source(
        self, source_name: str, installer_type: Optional[str] = None
    ) -> bool:
        """
        切换源

        Args:
            source_name: 源名称
            installer_type: 安装器类型，如果为None则对所有支持该源的安装器生效

        Returns:
            是否切换成功
        """
        if source_name not in self.sources:
            logger.error(f"Source '{source_name}' not found")
            return False

        source = self.sources[source_name]
        source.enable()

        # 获取待切换的安装器类型列表
        installer_types = []
        if installer_type:
            installer_types = [installer_type]
        else:
            if source.type == SourceType.PYPI:
                installer_types = ["pip"]
            elif source.type == SourceType.NPM:
                installer_types = ["npm"]

        # 无效的安装器类型
        if not installer_types:
            logger.error(f"No installer supports source '{source_name}'")
            return False

        # 对每个安装器进行源切换
        for installer in installer_types:
            # 将其他源的优先级降低
            for other_name in self.installer_sources.get(installer, []):
                if other_name != source_name and other_name in self.sources:
                    other_source = self.sources[other_name]
                    # 降低优先级，确保当前源优先级最高
                    if other_source.priority <= source.priority:
                        other_source.priority = source.priority + 10

            logger.info(
                f"Switched to source '{source_name}' for installer '{installer}'"
            )

        return True

    def check_health(self, source_name: str) -> SourceStatus:
        """
        检查源的健康状态

        Args:
            source_name: 源名称

        Returns:
            源状态
        """
        if source_name not in self.sources:
            logger.error(f"Source '{source_name}' not found")
            return SourceStatus.ERROR

        source = self.sources[source_name]
        status = source.check_health()
        logger.info(f"Source '{source_name}' health check: {status.name}")
        return status

    def check_all_health(
        self, installer_type: Optional[str] = None
    ) -> Dict[str, SourceStatus]:
        """
        检查所有源的健康状态

        Args:
            installer_type: 安装器类型，如果为None则检查所有源

        Returns:
            源名称到状态的映射
        """
        sources_to_check = []
        if installer_type:
            sources_to_check = [
                self.sources[name]
                for name in self.installer_sources.get(installer_type, [])
                if name in self.sources
            ]
        else:
            sources_to_check = list(self.sources.values())

        results = {}
        for source in sources_to_check:
            status = source.check_health()
            results[source.name] = status

        return results

    def get_status(self) -> Dict[str, Any]:
        """
        获取源管理器状态

        Returns:
            状态信息
        """
        return {
            "sources": {
                name: source.get_status_dict() for name, source in self.sources.items()
            },
            "groups": self.source_groups,
            "installer_sources": self.installer_sources,
        }

    def switch_active_source(self, source_name: str, installer_type: str) -> bool:
        """
        切换指定安装器类型的活动源

        Args:
            source_name: 源名称
            installer_type: 安装器类型

        Returns:
            切换是否成功
        """
        if source_name not in self.sources:
            logger.error(f"Source '{source_name}' not found")
            return False

        source = self.sources[source_name]
        installer_type_map = {"pip": SourceType.PYPI, "npm": SourceType.NPM}

        # 检查源类型是否与安装器类型匹配
        expected_type = installer_type_map.get(installer_type)
        if not expected_type or source.type != expected_type:
            logger.error(
                f"Source '{source_name}' type '{source.type}' does not match installer type '{installer_type}'"
            )
            return False

        # 将当前所有同类型源的active标志设为False
        for s in self.sources.values():
            if s.type == source.type:
                s.active = False

        # 将目标源的active标志设为True
        source.active = True
        logger.info(
            f"Switched active source to '{source_name}' for installer '{installer_type}'"
        )
        return True

    def check_all_sources(self) -> None:
        """检查所有源的健康状态"""
        logger.info("Checking health of all sources")
        for source in self.sources.values():
            try:
                source.check_health()
            except Exception as e:
                logger.error(f"Failed to check health of source '{source.name}': {e}")
                # 标记为UNKNOWN状态，不抛出异常以继续检查其他源
                source.status = SourceStatus.UNKNOWN
