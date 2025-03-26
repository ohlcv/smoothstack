#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker配置管理模块

提供Docker配置的管理功能，包括：
- 配置文件的读写和验证
- 环境变量的管理
- 网络和卷的配置
"""

import os
import yaml
from typing import Dict, Optional, Any, Union, List
from pathlib import Path


class DockerConfig:
    """Docker配置管理类"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.compose_file = self.config_dir / "docker-compose.yml"
        self.env_file = self.config_dir / ".env"

    def load_compose_config(self) -> Dict[str, Any]:
        """加载Docker Compose配置"""
        try:
            if not self.compose_file.exists():
                return {}

            with open(self.compose_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}

        except Exception as e:
            raise RuntimeError(f"加载Docker Compose配置失败: {e}")

    def save_compose_config(self, config: Dict[str, Any]) -> None:
        """保存Docker Compose配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.compose_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            raise RuntimeError(f"保存Docker Compose配置失败: {e}")

    def load_env_vars(self) -> Dict[str, str]:
        """加载环境变量"""
        env_vars = {}

        try:
            if not self.env_file.exists():
                return env_vars

            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip().strip("\"'")
                        except ValueError:
                            continue

            return env_vars

        except Exception as e:
            raise RuntimeError(f"加载环境变量失败: {e}")

    def save_env_vars(self, env_vars: Dict[str, str]) -> None:
        """保存环境变量"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.env_file, "w", encoding="utf-8") as f:
                for key, value in sorted(env_vars.items()):
                    f.write(f"{key}={value}\n")

        except Exception as e:
            raise RuntimeError(f"保存环境变量失败: {e}")

    def update_service_config(
        self, service_name: str, config_updates: Dict[str, Any]
    ) -> None:
        """更新服务配置"""
        try:
            compose_config = self.load_compose_config()

            if "services" not in compose_config:
                compose_config["services"] = {}

            if service_name not in compose_config["services"]:
                compose_config["services"][service_name] = {}

            service_config = compose_config["services"][service_name]
            self._deep_update(service_config, config_updates)

            self.save_compose_config(compose_config)

        except Exception as e:
            raise RuntimeError(f"更新服务配置失败: {e}")

    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """递归更新字典"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v

    def create_network(self, network_name: str, config: Dict[str, Any]) -> None:
        """创建网络配置"""
        try:
            compose_config = self.load_compose_config()

            if "networks" not in compose_config:
                compose_config["networks"] = {}

            compose_config["networks"][network_name] = config
            self.save_compose_config(compose_config)

        except Exception as e:
            raise RuntimeError(f"创建网络配置失败: {e}")

    def create_volume(self, volume_name: str, config: Dict[str, Any]) -> None:
        """创建卷配置"""
        try:
            compose_config = self.load_compose_config()

            if "volumes" not in compose_config:
                compose_config["volumes"] = {}

            compose_config["volumes"][volume_name] = config
            self.save_compose_config(compose_config)

        except Exception as e:
            raise RuntimeError(f"创建卷配置失败: {e}")

    def validate(self) -> bool:
        """验证配置"""
        try:
            # 验证Docker Compose配置
            compose_config = self.load_compose_config()
            if not isinstance(compose_config, dict):
                raise ValueError("Docker Compose配置必须是一个字典")

            # 验证服务配置
            if "services" in compose_config:
                if not isinstance(compose_config["services"], dict):
                    raise ValueError("services配置必须是一个字典")

                for service_name, service_config in compose_config["services"].items():
                    if not isinstance(service_config, dict):
                        raise ValueError(f"服务 {service_name} 的配置必须是一个字典")

            # 验证网络配置
            if "networks" in compose_config:
                if not isinstance(compose_config["networks"], dict):
                    raise ValueError("networks配置必须是一个字典")

            # 验证卷配置
            if "volumes" in compose_config:
                if not isinstance(compose_config["volumes"], dict):
                    raise ValueError("volumes配置必须是一个字典")

            # 验证环境变量
            env_vars = self.load_env_vars()
            for key, value in env_vars.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("环境变量的键和值必须是字符串")

            return True

        except Exception as e:
            raise RuntimeError(f"配置验证失败: {e}")

    def get_service_names(self) -> List[str]:
        """获取所有服务名称"""
        try:
            compose_config = self.load_compose_config()
            return list(compose_config.get("services", {}).keys())
        except Exception as e:
            raise RuntimeError(f"获取服务名称失败: {e}")

    def get_network_names(self) -> List[str]:
        """获取所有网络名称"""
        try:
            compose_config = self.load_compose_config()
            return list(compose_config.get("networks", {}).keys())
        except Exception as e:
            raise RuntimeError(f"获取网络名称失败: {e}")

    def get_volume_names(self) -> List[str]:
        """获取所有卷名称"""
        try:
            compose_config = self.load_compose_config()
            return list(compose_config.get("volumes", {}).keys())
        except Exception as e:
            raise RuntimeError(f"获取卷名称失败: {e}")
