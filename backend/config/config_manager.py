#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器

负责加载、验证和管理应用程序配置
"""

import os
import sys
import yaml
import json
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# 导入配置验证模块
from .schema import (
    SchemaError,
    AppConfigSchema,
    DatabaseConfigSchema,
    ApiConfigSchema,
    LoggingConfigSchema,
    SecurityConfigSchema,
)

# 导入配置监控器
from .watcher import ConfigWatcher, ConfigChangeEvent

# 配置日志
logger = logging.getLogger("smoothstack.config")


class ConfigManager:
    """
    配置管理器类

    负责加载配置文件、环境变量，并提供统一的配置访问接口
    """

    def __init__(self):
        """初始化配置管理器"""
        # 配置数据存储
        self._config: Dict[str, Any] = {}

        # 确定项目根目录
        self.root_dir = self._find_root_dir()

        # 环境名称 (development, testing, production)
        self.env = os.getenv("ENV", "development")

        # 是否已经加载配置
        self._loaded = False

        # 配置验证器映射
        self._validators = {
            "app": AppConfigSchema,
            "database": DatabaseConfigSchema,
            "api": ApiConfigSchema,
            "logging": LoggingConfigSchema,
            "security": SecurityConfigSchema,
        }

        # 配置监控器
        self._watcher = None
        self._auto_reload = False

    def _find_root_dir(self) -> Path:
        """
        查找项目根目录

        通过向上查找 .git 目录或其他标志文件来确定
        """
        current_dir = Path(__file__).resolve().parent

        # 向上查找，直到找到项目根目录或到达文件系统根目录
        max_levels = 5  # 限制向上查找的层级数
        for _ in range(max_levels):
            # 检查常见的项目根目录标志
            if (current_dir / ".git").exists() or (
                current_dir / "pyproject.toml"
            ).exists():
                return current_dir

            # 检查是否已经到达文件系统根目录
            parent_dir = current_dir.parent
            if parent_dir == current_dir:
                break

            current_dir = parent_dir

        # 如果无法确定，使用当前工作目录
        logger.warning("无法确定项目根目录，使用当前工作目录")
        return Path.cwd()

    def load(self, force: bool = False) -> None:
        """
        加载所有配置

        Args:
            force: 是否强制重新加载配置
        """
        if self._loaded and not force:
            return

        # 加载顺序：默认配置 -> 环境配置 -> .env 文件 -> 环境变量
        self._load_default_config()
        self._load_environment_config()
        self._load_dotenv()
        self._load_environment_variables()

        # 验证配置
        self._validate_config()

        self._loaded = True
        logger.info(f"配置加载完成，当前环境：{self.env}")

    def _load_default_config(self) -> None:
        """加载默认配置"""
        default_config_path = self.root_dir / "backend" / "config" / "default.yaml"

        if default_config_path.exists():
            with open(default_config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.debug("已加载默认配置")
        else:
            logger.warning(f"默认配置文件不存在: {default_config_path}")
            self._config = {}

    def _load_environment_config(self) -> None:
        """加载特定环境的配置"""
        env_config_path = (
            self.root_dir / "backend" / "config" / "environments" / f"{self.env}.yaml"
        )

        if env_config_path.exists():
            with open(env_config_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}

            # 递归合并配置
            self._merge_configs(self._config, env_config)
            logger.debug(f"已加载 {self.env} 环境配置")
        else:
            logger.warning(f"环境配置文件不存在: {env_config_path}")

    def _load_dotenv(self) -> None:
        """加载 .env 文件中的环境变量"""
        env_file = self.root_dir / ".env"
        env_local_file = self.root_dir / f".env.{self.env}"

        # 优先加载通用 .env 文件
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
            logger.debug("已加载 .env 文件")

        # 然后加载环境特定的 .env 文件（如果存在）
        if env_local_file.exists():
            load_dotenv(dotenv_path=env_local_file, override=True)
            logger.debug(f"已加载 .env.{self.env} 文件")

    def _load_environment_variables(self) -> None:
        """
        从环境变量加载配置

        约定：环境变量以 SMOOTHSTACK_ 为前缀
        例如：SMOOTHSTACK_DATABASE_URL 将映射到 config["database"]["url"]
        """
        prefix = "SMOOTHSTACK_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀并将键转换为小写
                config_key = key[len(prefix) :].lower()

                # 按 '_' 分割键，创建嵌套字典路径
                parts = config_key.split("_")

                # 使用嵌套字典更新配置
                self._set_nested_value(self._config, parts, value)

        logger.debug("已加载环境变量配置")

    def _validate_config(self) -> None:
        """
        验证配置

        使用配置验证器检查配置值的类型和范围
        """
        for section, validator_class in self._validators.items():
            if section in self._config:
                try:
                    # 使用验证器验证配置部分
                    validated = validator_class.validate_config(self._config[section])
                    # 更新配置部分
                    self._config[section] = validated
                    logger.debug(f"已验证 '{section}' 配置部分")
                except SchemaError as e:
                    logger.error(f"配置验证失败 ('{section}'): {str(e)}")
                    # 在开发环境中，验证失败时打印详细信息
                    if self.env == "development":
                        logger.debug(f"配置内容: {self._config[section]}")

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        递归合并两个配置字典

        Args:
            base: 基础配置字典（将被修改）
            override: 覆盖配置字典
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 如果两者都是字典，递归合并
                self._merge_configs(base[key], value)
            else:
                # 否则直接覆盖
                base[key] = value

    def _set_nested_value(self, config: Dict[str, Any], keys: list, value: str) -> None:
        """
        在嵌套字典中设置值

        Args:
            config: 配置字典
            keys: 嵌套键路径
            value: 要设置的值
        """
        if not keys:
            return

        # 取出第一个键
        current_key = keys[0]

        if len(keys) == 1:
            # 如果是最后一个键，直接设置值
            # 尝试转换值的类型（布尔值、整数、浮点数）
            config[current_key] = self._convert_value_type(value)
        else:
            # 如果不是最后一个键，继续递归
            if current_key not in config or not isinstance(config[current_key], dict):
                config[current_key] = {}

            self._set_nested_value(config[current_key], keys[1:], value)

    def _convert_value_type(self, value: Any) -> Any:
        """
        尝试将字符串转换为适当的类型

        Args:
            value: 要转换的值

        Returns:
            转换后的值
        """
        # 如果已经不是字符串，直接返回
        if not isinstance(value, str):
            return value

        # 检查布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 检查整数
        try:
            return int(value)
        except ValueError:
            pass

        # 检查浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 检查 JSON
        try:
            return json.loads(value)
        except (ValueError, json.JSONDecodeError):
            pass

        # 默认返回原始字符串
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键，例如 "database.url"
            default: 如果键不存在，返回的默认值

        Returns:
            配置值或默认值
        """
        # 确保配置已加载
        if not self._loaded:
            self.load()

        # 分割键并查找值
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 要设置的值
        """
        # 确保配置已加载
        if not self._loaded:
            self.load()

        # 分割键并设置值
        parts = key.split(".")
        self._set_nested_value(self._config, parts, value)

        # 设置值后重新验证相关配置部分
        if parts and parts[0] in self._validators:
            section = parts[0]
            try:
                validated = self._validators[section].validate_config(
                    self._config[section]
                )
                self._config[section] = validated
            except SchemaError as e:
                logger.error(f"配置验证失败 ('{section}'): {str(e)}")

    def as_dict(self) -> Dict[str, Any]:
        """
        将配置作为字典返回

        Returns:
            配置字典的副本
        """
        # 确保配置已加载
        if not self._loaded:
            self.load()

        # 返回配置字典的深拷贝
        return dict(self._config)

    def reload(self) -> None:
        """
        重新加载配置

        用于在运行时更新配置（热重载）
        """
        self.load(force=True)
        logger.info("配置已重新加载")

    def __getitem__(self, key: str) -> Any:
        """实现字典下标访问语法"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """实现字典赋值语法"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """实现 'in' 操作符"""
        return self.get(key) is not None

    def enable_auto_reload(self) -> None:
        """启用配置自动重载"""
        if self._watcher is None:
            # 创建配置监控器
            config_dir = self.root_dir / "backend" / "config"
            self._watcher = ConfigWatcher(str(config_dir))

            # 添加配置文件监控
            self._watcher.add_watch(str(config_dir / "default.yaml"))
            self._watcher.add_watch(str(config_dir / "environments"))

            # 添加配置变更回调
            self._watcher.add_callback(self._on_config_changed)

            # 启动监控器
            self._watcher.start()
            self._auto_reload = True
            logger.info("已启用配置自动重载")

    def disable_auto_reload(self) -> None:
        """禁用配置自动重载"""
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
            self._auto_reload = False
            logger.info("已禁用配置自动重载")

    def _on_config_changed(self, event: ConfigChangeEvent) -> None:
        """
        处理配置文件变更

        Args:
            event: 配置变更事件
        """
        try:
            # 重新加载配置
            self.reload()
            logger.info(f"检测到配置文件变更，已重新加载: {event.file_path}")
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")

    def __del__(self):
        """析构函数"""
        # 确保监控器被正确停止
        self.disable_auto_reload()
