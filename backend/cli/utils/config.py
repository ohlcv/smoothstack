"""
配置管理模块，提供配置的读取、保存、导入和导出功能
"""

import os
import json
import yaml
import toml
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Union, cast
from enum import Enum, auto

from .logger import get_logger
from .errors import ConfigError, FileError, UserError

# 创建日志记录器
logger = get_logger("config")

# 配置文件名
CONFIG_FILENAME = "smoothstack.json"

# 全局配置目录
GLOBAL_CONFIG_DIR = Path.home() / ".smoothstack"

# 用户级配置文件路径
USER_CONFIG_PATH = GLOBAL_CONFIG_DIR / CONFIG_FILENAME


# 支持的导入/导出格式
class ConfigFormat(Enum):
    """配置文件格式"""

    JSON = auto()
    YAML = auto()
    TOML = auto()
    ENV = auto()  # 环境变量格式

    @classmethod
    def from_extension(cls, extension: str) -> "ConfigFormat":
        """
        根据文件扩展名获取格式

        Args:
            extension: 文件扩展名，如".json"

        Returns:
            对应的配置格式

        Raises:
            ConfigError: 不支持的文件格式
        """
        extension = extension.lower().lstrip(".")
        if extension in ("json", "jsonc"):
            return cls.JSON
        elif extension in ("yaml", "yml"):
            return cls.YAML
        elif extension in ("toml", "tml"):
            return cls.TOML
        elif extension in ("env", ""):
            return cls.ENV
        else:
            raise ConfigError(
                "不支持的配置文件格式",
                f"支持的格式：json, yaml, toml, env，当前格式：{extension}",
            )

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "ConfigFormat":
        """
        根据文件路径获取格式

        Args:
            path: 文件路径

        Returns:
            对应的配置格式

        Raises:
            ConfigError: 不支持的文件格式
        """
        path_str = str(path)
        _, ext = os.path.splitext(path_str)
        return cls.from_extension(ext)


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        # 确保全局配置目录存在
        GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """
        加载配置

        Raises:
            ConfigError: 配置文件损坏
        """
        # 检查配置文件是否存在
        if not USER_CONFIG_PATH.exists():
            logger.debug(f"配置文件不存在，创建新配置: {USER_CONFIG_PATH}")
            self.config = {}
            self.save()
            return

        # 加载配置文件
        try:
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logger.debug(f"成功加载配置文件: {USER_CONFIG_PATH}")
        except json.JSONDecodeError as e:
            raise ConfigError(
                "配置文件格式错误",
                f"请检查 {USER_CONFIG_PATH} 是否为有效的JSON格式: {str(e)}",
            )
        except Exception as e:
            raise ConfigError("无法加载配置文件", f"原因: {str(e)}")

    def save(self) -> None:
        """
        保存配置

        Raises:
            ConfigError: 保存配置失败
        """
        try:
            with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.debug(f"成功保存配置文件: {USER_CONFIG_PATH}")
        except Exception as e:
            raise ConfigError("保存配置失败", f"原因: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置项键名，支持点号分隔的嵌套键
            default: 默认值，当键不存在时返回

        Returns:
            配置项值或默认值
        """
        # 处理嵌套键
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项

        Args:
            key: 配置项键名，支持点号分隔的嵌套键
            value: 配置项值

        Raises:
            ConfigError: 设置嵌套配置时路径无效
        """
        # 处理嵌套键
        keys = key.split(".")

        # 处理根级别键
        if len(keys) == 1:
            self.config[key] = value
            return

        # 处理嵌套键
        config = self.config
        for k in keys[:-1]:
            # 创建嵌套字典（如果不存在）
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                raise ConfigError(
                    "无法设置配置项", f"路径 '{key}' 中的部分 '{k}' 不是字典"
                )
            config = config[k]

        # 设置最终键的值
        config[keys[-1]] = value

    def delete(self, key: str) -> bool:
        """
        删除配置项

        Args:
            key: 配置项键名，支持点号分隔的嵌套键

        Returns:
            是否成功删除

        Raises:
            ConfigError: 删除嵌套配置时路径无效
        """
        # 处理嵌套键
        keys = key.split(".")

        # 处理根级别键
        if len(keys) == 1:
            if key in self.config:
                del self.config[key]
                return True
            return False

        # 处理嵌套键
        config = self.config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                return False
            config = config[k]

        # 删除最终键
        if keys[-1] in config:
            del config[keys[-1]]
            return True
        return False

    def list(self, prefix: str = "") -> Dict[str, Any]:
        """
        列出配置项

        Args:
            prefix: 键前缀过滤器

        Returns:
            匹配前缀的配置项字典
        """
        if not prefix:
            return self.config

        result = {}
        prefix_parts = prefix.split(".")

        def collect_items(config: Dict[str, Any], path: List[str]) -> None:
            """
            递归收集匹配的配置项

            Args:
                config: 当前配置字典
                path: 当前路径
            """
            # 检查是否已经超过前缀长度
            if len(path) > len(prefix_parts):
                return

            # 检查当前路径是否与前缀匹配
            for i, part in enumerate(path):
                if i < len(prefix_parts) and part != prefix_parts[i]:
                    return

            # 如果路径与前缀完全匹配，收集所有子项
            if len(path) == len(prefix_parts):
                # 构建键名
                key = ".".join(path)
                if not key:
                    # 空前缀，返回整个配置
                    result.update(flatten_dict(config, ""))
                    return

                # 找到匹配的子配置
                sub_config = self.config
                for p in path:
                    if p not in sub_config:
                        return
                    sub_config = sub_config[p]

                # 添加到结果
                if isinstance(sub_config, dict):
                    # 对于字典，添加所有子项
                    result.update(flatten_dict(sub_config, key))
                else:
                    # 对于值，直接添加
                    result[key] = sub_config
                return

            # 继续递归
            if path and path[-1] in config and isinstance(config[path[-1]], dict):
                # 递归处理下一级
                sub_config = config[path[-1]]
                for k in sub_config:
                    collect_items(sub_config, path + [k])
            elif not path:
                # 从根开始
                for k in config:
                    collect_items(config, [k])

        collect_items(self.config, [])
        return result

    def import_config(
        self,
        file_path: Union[str, Path],
        format: Optional[ConfigFormat] = None,
        merge: bool = True,
    ) -> None:
        """
        从文件导入配置

        Args:
            file_path: 配置文件路径
            format: 配置文件格式，如果为None则根据文件扩展名判断
            merge: 是否合并配置，True为合并，False为替换

        Raises:
            FileError: 文件不存在或无法读取
            ConfigError: 文件格式错误
        """
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists():
            raise FileError("配置文件不存在", f"文件路径: {path}")

        # 确定配置格式
        if format is None:
            try:
                format = ConfigFormat.from_path(path)
            except ConfigError:
                # 默认为JSON
                format = ConfigFormat.JSON

        # 读取并解析配置文件
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # 根据格式解析
            if format == ConfigFormat.JSON:
                config_data = json.loads(content)
            elif format == ConfigFormat.YAML:
                config_data = yaml.safe_load(content)
            elif format == ConfigFormat.TOML:
                config_data = toml.loads(content)
            elif format == ConfigFormat.ENV:
                config_data = parse_env_file(content)
            else:
                raise ConfigError("不支持的配置格式", f"格式: {format}")

            # 检查解析结果
            if not isinstance(config_data, dict):
                raise ConfigError("配置文件格式无效", "配置必须是键值对形式")

            # 合并或替换配置
            if merge:
                deep_merge(self.config, config_data)
            else:
                self.config = config_data

            # 保存配置
            self.save()
            logger.info(f"成功从文件导入配置: {path}")

        except Exception as e:
            if isinstance(e, (FileError, ConfigError)):
                raise
            raise ConfigError("导入配置失败", f"原因: {str(e)}")

    def export_config(
        self, file_path: Union[str, Path], format: Optional[ConfigFormat] = None
    ) -> None:
        """
        导出配置到文件

        Args:
            file_path: 目标文件路径
            format: 配置文件格式，如果为None则根据文件扩展名判断

        Raises:
            ConfigError: 导出配置失败
        """
        path = Path(file_path)

        # 确定配置格式
        if format is None:
            try:
                format = ConfigFormat.from_path(path)
            except ConfigError:
                # 默认为JSON
                format = ConfigFormat.JSON

        # 导出配置
        try:
            # 根据格式序列化
            if format == ConfigFormat.JSON:
                content = json.dumps(self.config, ensure_ascii=False, indent=2)
            elif format == ConfigFormat.YAML:
                content = yaml.dump(self.config, allow_unicode=True, sort_keys=False)
            elif format == ConfigFormat.TOML:
                content = toml.dumps(self.config)
            elif format == ConfigFormat.ENV:
                content = generate_env_file(self.config)
            else:
                raise ConfigError("不支持的配置格式", f"格式: {format}")

            # 创建目录（如果不存在）
            path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"成功导出配置到文件: {path}")

        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            raise ConfigError("导出配置失败", f"原因: {str(e)}")


# 配置管理器单例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    获取配置管理器单例

    Returns:
        配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    将嵌套字典扁平化为带点号分隔的键

    Args:
        d: 嵌套字典
        prefix: 键前缀

    Returns:
        扁平化后的字典
    """
    result = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten_dict(v, key))
        else:
            result[key] = v
    return result


def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    深度合并两个字典

    Args:
        target: 目标字典（被修改）
        source: 源字典
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # 递归合并字典
            deep_merge(target[key], value)
        else:
            # 直接赋值
            target[key] = value


def parse_env_file(content: str) -> Dict[str, Any]:
    """
    解析环境变量格式的配置文件

    Args:
        content: 文件内容

    Returns:
        解析后的配置字典
    """
    result = {}
    for line in content.splitlines():
        # 去除空白和注释
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # 解析键值对
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # 去除引号
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]

            # 支持嵌套键
            if "." in key:
                keys = key.split(".")
                current = result
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                result[key] = value

    return result


def generate_env_file(config: Dict[str, Any]) -> str:
    """
    生成环境变量格式的配置文件

    Args:
        config: 配置字典

    Returns:
        环境变量格式的文件内容
    """
    lines = ["# Smoothstack Configuration"]
    flat_config = flatten_dict(config)

    for key, value in sorted(flat_config.items()):
        # 对字符串值添加引号
        if isinstance(value, str):
            value = f'"{value}"'
        lines.append(f"{key}={value}")

    return "\n".join(lines)
