#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络命令模块

提供网络相关的命令，包括：
- 网络配置
- 网络监控
- 网络诊断
- 网络安全
"""

import os
import sys
import yaml
import click
import socket
import subprocess
import netifaces
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NetworkCommand(BaseCommand):
    """网络命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.network_dir = self.project_root / "network"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.network_dir.mkdir(parents=True, exist_ok=True)

    def config(self, project_name: str, action: str, **kwargs):
        """网络配置"""
        try:
            self.info(f"网络配置: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查网络配置
            config_file = project_dir / "network" / "config.yml"
            if not config_file.exists():
                config = {}
            else:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

            # 配置网络
            if action == "add":
                self._add_network_config(config, **kwargs)
            elif action == "remove":
                self._remove_network_config(config, **kwargs)
            elif action == "update":
                self._update_network_config(config, **kwargs)
            elif action == "show":
                self._show_network_config(config)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success("网络配置已更新")

        except Exception as e:
            self.error(f"网络配置失败: {e}")
            raise

    def monitor(self, project_name: str):
        """网络监控"""
        try:
            self.info(f"网络监控: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查网络配置
            config_file = project_dir / "network" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("网络配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 监控网络
            self._monitor_network(config)

        except Exception as e:
            self.error(f"网络监控失败: {e}")
            raise

    def diagnose(self, project_name: str, target: str):
        """网络诊断"""
        try:
            self.info(f"网络诊断: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查网络配置
            config_file = project_dir / "network" / "config.yml"
            if not config_file.exists():
                raise RuntimeError("网络配置不存在")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 诊断网络
            self._diagnose_network(config, target)

        except Exception as e:
            self.error(f"网络诊断失败: {e}")
            raise

    def security(self, project_name: str, action: str, **kwargs):
        """网络安全"""
        try:
            self.info(f"网络安全: {project_name}")

            # 检查项目目录
            project_dir = self.projects_dir / project_name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {project_name}")

            # 检查安全配置
            security_file = project_dir / "network" / "security.yml"
            if not security_file.exists():
                security = {}
            else:
                with open(security_file, "r", encoding="utf-8") as f:
                    security = yaml.safe_load(f)

            # 配置安全
            if action == "add":
                self._add_security_config(security, **kwargs)
            elif action == "remove":
                self._remove_security_config(security, **kwargs)
            elif action == "update":
                self._update_security_config(security, **kwargs)
            elif action == "show":
                self._show_security_config(security)
            else:
                raise RuntimeError(f"不支持的操作: {action}")

            # 保存配置
            with open(security_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(security, f, default_flow_style=False)

            self.success("安全配置已更新")

        except Exception as e:
            self.error(f"网络安全配置失败: {e}")
            raise

    def _add_network_config(self, config: Dict[str, Any], **kwargs):
        """添加网络配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("网络名称不能为空")

            # 添加配置
            name = kwargs.pop("name")
            config[name] = kwargs

            self.success(f"添加网络配置成功: {name}")

        except Exception as e:
            self.error(f"添加网络配置失败: {e}")
            raise

    def _remove_network_config(self, config: Dict[str, Any], **kwargs):
        """移除网络配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("网络名称不能为空")

            # 移除配置
            name = kwargs["name"]
            if name in config:
                del config[name]
                self.success(f"移除网络配置成功: {name}")
            else:
                self.warning(f"网络配置不存在: {name}")

        except Exception as e:
            self.error(f"移除网络配置失败: {e}")
            raise

    def _update_network_config(self, config: Dict[str, Any], **kwargs):
        """更新网络配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("网络名称不能为空")

            # 更新配置
            name = kwargs.pop("name")
            if name in config:
                config[name].update(kwargs)
                self.success(f"更新网络配置成功: {name}")
            else:
                self.warning(f"网络配置不存在: {name}")

        except Exception as e:
            self.error(f"更新网络配置失败: {e}")
            raise

    def _show_network_config(self, config: Dict[str, Any]):
        """显示网络配置"""
        try:
            if not config:
                self.info("未配置网络")
                return

            self.info("\n网络配置:")
            for name, network in config.items():
                self.info(f"名称: {name}")
                for key, value in network.items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"显示网络配置失败: {e}")
            raise

    def _monitor_network(self, config: Dict[str, Any]):
        """监控网络"""
        try:
            # 获取网络接口
            interfaces = netifaces.interfaces()

            self.info("\n网络接口:")
            for interface in interfaces:
                # 获取地址
                addrs = netifaces.ifaddresses(interface)
                self.info(f"接口: {interface}")
                for addr_type, addr_info in addrs.items():
                    for addr in addr_info:
                        self.info(f"  {addr_type}: {addr['addr']}")

            # 获取默认网关
            gateways = netifaces.gateways()
            self.info("\n默认网关:")
            for addr_type, gateway in gateways.items():
                self.info(f"{addr_type}: {gateway}")

            # 获取DNS服务器
            try:
                with open("/etc/resolv.conf", "r") as f:
                    dns = [
                        line.split()[1] for line in f if line.startswith("nameserver")
                    ]
                self.info("\nDNS服务器:")
                for server in dns:
                    self.info(server)
            except Exception:
                self.warning("无法获取DNS服务器")

        except Exception as e:
            self.error(f"监控网络失败: {e}")
            raise

    def _diagnose_network(self, config: Dict[str, Any], target: str):
        """诊断网络"""
        try:
            # 解析目标
            try:
                ip = socket.gethostbyname(target)
            except socket.gaierror:
                self.error(f"无法解析目标: {target}")
                return

            self.info(f"\n目标: {target} ({ip})")

            # Ping测试
            self.info("\nPing测试:")
            try:
                result = subprocess.run(
                    ["ping", "-c", "4", target], capture_output=True, text=True
                )
                self.info(result.stdout)
            except Exception as e:
                self.error(f"Ping测试失败: {e}")

            # Traceroute测试
            self.info("\nTraceroute测试:")
            try:
                result = subprocess.run(
                    ["traceroute", target], capture_output=True, text=True
                )
                self.info(result.stdout)
            except Exception as e:
                self.error(f"Traceroute测试失败: {e}")

            # DNS测试
            self.info("\nDNS测试:")
            try:
                result = subprocess.run(
                    ["nslookup", target], capture_output=True, text=True
                )
                self.info(result.stdout)
            except Exception as e:
                self.error(f"DNS测试失败: {e}")

        except Exception as e:
            self.error(f"诊断网络失败: {e}")
            raise

    def _add_security_config(self, security: Dict[str, Any], **kwargs):
        """添加安全配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("安全规则名称不能为空")

            # 添加配置
            name = kwargs.pop("name")
            security[name] = kwargs

            self.success(f"添加安全规则成功: {name}")

        except Exception as e:
            self.error(f"添加安全规则失败: {e}")
            raise

    def _remove_security_config(self, security: Dict[str, Any], **kwargs):
        """移除安全配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("安全规则名称不能为空")

            # 移除配置
            name = kwargs["name"]
            if name in security:
                del security[name]
                self.success(f"移除安全规则成功: {name}")
            else:
                self.warning(f"安全规则不存在: {name}")

        except Exception as e:
            self.error(f"移除安全规则失败: {e}")
            raise

    def _update_security_config(self, security: Dict[str, Any], **kwargs):
        """更新安全配置"""
        try:
            # 检查必要参数
            if "name" not in kwargs:
                raise RuntimeError("安全规则名称不能为空")

            # 更新配置
            name = kwargs.pop("name")
            if name in security:
                security[name].update(kwargs)
                self.success(f"更新安全规则成功: {name}")
            else:
                self.warning(f"安全规则不存在: {name}")

        except Exception as e:
            self.error(f"更新安全规则失败: {e}")
            raise

    def _show_security_config(self, security: Dict[str, Any]):
        """显示安全配置"""
        try:
            if not security:
                self.info("未配置安全规则")
                return

            self.info("\n安全规则:")
            for name, rule in security.items():
                self.info(f"名称: {name}")
                for key, value in rule.items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"显示安全规则失败: {e}")
            raise


# CLI命令
@click.group()
def network():
    """网络命令"""
    pass


@network.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="网络名称")
@click.option("--type", "-t", help="网络类型")
@click.option("--subnet", "-s", help="子网")
@click.option("--gateway", "-g", help="网关")
def config(project_name: str, action: str, **kwargs):
    """网络配置"""
    cmd = NetworkCommand()
    cmd.config(project_name, action, **kwargs)


@network.command()
@click.argument("project_name")
def monitor(project_name: str):
    """网络监控"""
    cmd = NetworkCommand()
    cmd.monitor(project_name)


@network.command()
@click.argument("project_name")
@click.argument("target")
def diagnose(project_name: str, target: str):
    """网络诊断"""
    cmd = NetworkCommand()
    cmd.diagnose(project_name, target)


@network.command()
@click.argument("project_name")
@click.argument("action")
@click.option("--name", "-n", help="规则名称")
@click.option("--type", "-t", help="规则类型")
@click.option("--source", "-s", help="源地址")
@click.option("--destination", "-d", help="目标地址")
@click.option("--port", "-p", help="端口")
@click.option("--action", "-a", help="动作")
def security(project_name: str, action: str, **kwargs):
    """网络安全"""
    cmd = NetworkCommand()
    cmd.security(project_name, action, **kwargs)
