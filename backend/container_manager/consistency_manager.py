#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器环境一致性验证管理器

提供容器与宿主环境一致性检查、修复和基准线管理功能
"""

import os
import sys
import json
import logging
import platform
import subprocess
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

import docker
import pkg_resources

# 配置日志
logger = logging.getLogger(__name__)


class ConsistencyManager:
    """
    容器环境一致性验证管理器

    提供容器与宿主环境的一致性检查、问题修复和基准线管理功能
    """

    def __init__(self, container_manager=None):
        """
        初始化 ConsistencyManager

        Args:
            container_manager: 容器管理器实例，如果为None则使用默认实例
        """
        from . import container_manager as default_container_manager

        self.container_manager = container_manager or default_container_manager
        self.docker_client = docker.from_env()
        self._config_dir = Path.home() / ".smoothstack" / "consistency"
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def get_host_env_info(self) -> Dict[str, Any]:
        """
        获取宿主环境信息

        Returns:
            包含宿主环境详细信息的字典
        """
        try:
            return {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                    "packages": self._get_host_python_packages(),
                },
                "node": self._get_host_node_version() or "",
                "npm_packages": self._get_host_npm_packages(),
                "env_vars": self._get_host_env_vars(),
            }
        except Exception as e:
            logger.warning(f"获取宿主环境信息时出错: {e}")
            return {
                "platform": {},
                "python": {"version": "", "implementation": "", "packages": {}},
                "node": "",
                "npm_packages": {},
                "env_vars": {},
            }

    def get_container_env_info(self, container_id_or_name: str) -> Dict[str, Any]:
        """
        获取指定容器的环境信息

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            包含容器环境详细信息的字典
        """
        try:
            container = self.docker_client.containers.get(container_id_or_name)

            # 安全地获取镜像标签
            image_tags = (
                container.image.tags
                if container.image and hasattr(container.image, "tags")
                else []
            )
            image_tag = image_tags[0] if image_tags else str(container.image or "")

            return {
                "name": container.name or "",
                "id": container.id[:12] if container.id else "",
                "status": container.status or "",
                "image": image_tag,
                "created": container.attrs.get("Created", ""),
                "platform": self._get_container_platform_info(container),
                "python": self._get_container_python_info(container),
                "node": self._get_container_node_version(container) or "",
                "npm_packages": self._get_container_npm_packages(container),
                "env_vars": self._get_container_env_vars(container),
                "ports": self._get_container_port_mappings(container),
            }
        except Exception as e:
            logger.error(f"获取容器 {container_id_or_name} 环境信息时出错: {e}")
            return {
                "name": "",
                "id": "",
                "status": "",
                "image": "",
                "created": "",
                "platform": {},
                "python": {"version": "", "packages": {}},
                "node": "",
                "npm_packages": {},
                "env_vars": {},
                "ports": [],
            }

    def _get_host_python_packages(self) -> Dict[str, str]:
        """获取宿主环境的Python包及其版本"""
        try:
            return {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        except Exception as e:
            logger.warning(f"获取宿主Python包时出错: {e}")
            return {}

    def _get_container_python_info(self, container) -> Dict[str, Any]:
        """获取容器内Python环境信息"""
        try:
            result = container.exec_run("python3 -V")
            version = (
                result.output.decode("utf-8").strip()
                if result.exit_code == 0
                else "未知"
            )

            result = container.exec_run("pip list")
            packages = {}
            if result.exit_code == 0:
                for line in result.output.decode("utf-8").split("\n")[2:-1]:
                    parts = line.split()
                    if len(parts) >= 2:
                        packages[parts[0]] = parts[1]

            return {"version": version, "packages": packages}
        except Exception as e:
            logger.warning(f"获取容器Python信息时出错: {e}")
            return {"version": "", "packages": {}}

    def _get_host_node_version(self) -> Optional[str]:
        """获取宿主环境的Node.js版本"""
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, check=False
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_container_node_version(self, container) -> Optional[str]:
        """获取容器内的Node.js版本"""
        try:
            result = container.exec_run("node --version")
            return (
                result.output.decode("utf-8").strip() if result.exit_code == 0 else None
            )
        except Exception:
            return None

    def _get_host_npm_packages(self) -> Dict[str, str]:
        """获取宿主环境的NPM包及其版本"""
        try:
            result = subprocess.run(
                ["npm", "list", "--global", "--depth=0", "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                packages_data = json.loads(result.stdout)
                return {
                    name: version.get("version", "未知")
                    for name, version in packages_data.get("dependencies", {}).items()
                }
            return {}
        except Exception as e:
            logger.warning(f"获取宿主NPM包时出错: {e}")
            return {}

    def _get_container_npm_packages(self, container) -> Dict[str, str]:
        """获取容器内的NPM包及其版本"""
        try:
            result = container.exec_run("npm list --global --depth=0 --json")
            if result.exit_code == 0:
                packages_data = json.loads(result.output.decode("utf-8"))
                return {
                    name: version.get("version", "未知")
                    for name, version in packages_data.get("dependencies", {}).items()
                }
            return {}
        except Exception as e:
            logger.warning(f"获取容器NPM包时出错: {e}")
            return {}

    def _get_host_env_vars(self) -> Dict[str, str]:
        """获取宿主环境变量"""
        return dict(os.environ)

    def _get_container_env_vars(self, container) -> Dict[str, str]:
        """获取容器环境变量"""
        try:
            result = container.exec_run("env")
            if result.exit_code == 0:
                return dict(
                    line.split("=", 1)
                    for line in result.output.decode("utf-8").split("\n")
                    if "=" in line
                )
            return {}
        except Exception as e:
            logger.warning(f"获取容器环境变量时出错: {e}")
            return {}

    def _get_container_platform_info(self, container) -> Dict[str, str]:
        """获取容器平台信息"""
        try:
            result = container.exec_run("uname -a")
            platform_info = (
                result.output.decode("utf-8").strip()
                if result.exit_code == 0
                else "未知"
            )
            return {"platform_info": platform_info}
        except Exception as e:
            logger.warning(f"获取容器平台信息时出错: {e}")
            return {"platform_info": ""}

    def _get_container_port_mappings(self, container) -> List[Dict[str, Any]]:
        """获取容器端口映射"""
        try:
            # 安全地获取网络设置和端口信息
            network_settings = container.attrs.get("NetworkSettings", {}) or {}
            ports = network_settings.get("Ports", {}) or {}

            result = []
            for container_port, host_ports in ports.items():
                # 如果host_ports为None或空列表，添加空的host_ports
                if not host_ports:
                    result.append({"container_port": container_port, "host_ports": []})
                else:
                    # 确保host_ports是一个列表
                    host_ports_list = (
                        host_ports if isinstance(host_ports, list) else [host_ports]
                    )

                    host_port_list = []
                    for host_port_info in host_ports_list:
                        # 确保host_port_info不为None
                        if host_port_info:
                            # 使用安全的字典访问方法
                            host_port_list.append(
                                {
                                    "HostIp": str(host_port_info.get("HostIp", "")),
                                    "HostPort": str(host_port_info.get("HostPort", "")),
                                }
                            )

                    result.append(
                        {"container_port": container_port, "host_ports": host_port_list}
                    )

            return result
        except Exception as e:
            logger.warning(f"获取容器端口映射时出错: {e}")
            return []

    def check_dependency_consistency(
        self, host_info: Dict[str, Any], container_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查依赖包一致性

        Args:
            host_info: 宿主环境信息
            container_info: 容器环境信息

        Returns:
            依赖包不一致的问题列表
        """
        issues = []

        # 检查Python包一致性
        host_python_packages = host_info.get("python", {}).get("packages", {})
        container_python_packages = container_info.get("python", {}).get("packages", {})

        for pkg, host_version in host_python_packages.items():
            container_version = container_python_packages.get(pkg)

            if not container_version:
                issues.append(
                    {
                        "type": "python_package_missing_in_container",
                        "package": pkg,
                        "host_version": host_version,
                        "severity": "error",
                    }
                )
            elif host_version != container_version:
                issues.append(
                    {
                        "type": "python_package_version_mismatch",
                        "package": pkg,
                        "host_version": host_version,
                        "container_version": container_version,
                        "severity": "warning",
                    }
                )

        for pkg, container_version in container_python_packages.items():
            if pkg not in host_python_packages:
                issues.append(
                    {
                        "type": "python_package_missing_in_host",
                        "package": pkg,
                        "container_version": container_version,
                        "severity": "info",
                    }
                )

        # 检查Node.js版本一致性
        host_node_version = host_info.get("node")
        container_node_version = container_info.get("node")

        if (
            host_node_version
            and container_node_version
            and host_node_version != container_node_version
        ):
            issues.append(
                {
                    "type": "node_version_mismatch",
                    "host_version": host_node_version,
                    "container_version": container_node_version,
                    "severity": "warning",
                }
            )

        # 检查NPM包一致性
        host_npm_packages = host_info.get("npm_packages", {})
        container_npm_packages = container_info.get("npm_packages", {})

        for pkg, host_version in host_npm_packages.items():
            container_version = container_npm_packages.get(pkg)

            if not container_version:
                issues.append(
                    {
                        "type": "npm_package_missing_in_container",
                        "package": pkg,
                        "host_version": host_version,
                        "severity": "error",
                    }
                )
            elif host_version != container_version:
                issues.append(
                    {
                        "type": "npm_package_version_mismatch",
                        "package": pkg,
                        "host_version": host_version,
                        "container_version": container_version,
                        "severity": "warning",
                    }
                )

        for pkg, container_version in container_npm_packages.items():
            if pkg not in host_npm_packages:
                issues.append(
                    {
                        "type": "npm_package_missing_in_host",
                        "package": pkg,
                        "container_version": container_version,
                        "severity": "info",
                    }
                )

        return issues

    def check_env_var_consistency(
        self,
        host_info: Dict[str, Any],
        container_info: Dict[str, Any],
        env_var_whitelist: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        检查环境变量一致性

        Args:
            host_info: 宿主环境信息
            container_info: 容器环境信息
            env_var_whitelist: 需要检查的环境变量白名单，如果为None则检查所有环境变量

        Returns:
            一致性问题列表
        """
        issues = []

        host_env_vars = host_info.get("env_vars", {})
        container_env_vars = container_info.get("env_vars", {})

        # 如果指定了白名单，则只检查白名单中的环境变量
        if env_var_whitelist:
            host_env_vars = {
                k: v for k, v in host_env_vars.items() if k in env_var_whitelist
            }
            container_env_vars = {
                k: v for k, v in container_env_vars.items() if k in env_var_whitelist
            }

        # 检查宿主环境中的环境变量是否在容器中存在并一致
        for var_name, host_value in host_env_vars.items():
            if var_name in container_env_vars:
                container_value = container_env_vars[var_name]
                if host_value != container_value:
                    issues.append(
                        {
                            "type": "env_var_value_mismatch",
                            "variable": var_name,
                            "host_value": host_value,
                            "container_value": container_value,
                            "severity": "warning",
                        }
                    )
            else:
                issues.append(
                    {
                        "type": "env_var_missing_in_container",
                        "variable": var_name,
                        "host_value": host_value,
                        "severity": "info",
                    }
                )

        # 检查容器中的环境变量是否在宿主环境中存在
        for var_name in container_env_vars:
            if var_name not in host_env_vars:
                issues.append(
                    {
                        "type": "env_var_missing_in_host",
                        "variable": var_name,
                        "container_value": container_env_vars[var_name],
                        "severity": "info",
                    }
                )

        return issues

    def check_port_mapping_consistency(
        self, container_id_or_name: str
    ) -> List[Dict[str, Any]]:
        """
        检查端口映射一致性

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            一致性问题列表
        """
        issues = []

        try:
            container = self.docker_client.containers.get(container_id_or_name)
            container_ports = container.attrs.get("NetworkSettings", {}).get(
                "Ports", {}
            )

            # 检查端口映射是否有效
            for container_port, host_bindings in container_ports.items():
                # 跳过未映射的端口
                if not host_bindings:
                    continue

                container_port_num = container_port.split("/")[0]

                for binding in host_bindings:
                    host_ip = binding.get("HostIp", "0.0.0.0")
                    host_port = binding.get("HostPort")

                    # 检查端口是否可以访问
                    if host_port:
                        import socket

                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex(
                            (
                                host_ip if host_ip != "0.0.0.0" else "127.0.0.1",
                                int(host_port),
                            )
                        )
                        sock.close()

                        if result != 0:
                            issues.append(
                                {
                                    "type": "port_mapping_inaccessible",
                                    "container_port": container_port_num,
                                    "host_ip": host_ip,
                                    "host_port": host_port,
                                    "severity": "error",
                                }
                            )
        except Exception as e:
            logger.error(f"检查端口映射时出错: {e}")

        return issues

    def check_file_sync_consistency(
        self, container_id_or_name: str, host_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        检查文件同步一致性

        Args:
            container_id_or_name: 容器ID或名称
            host_paths: 宿主机上需要检查的路径列表

        Returns:
            一致性问题列表
        """
        issues = []

        try:
            container = self.docker_client.containers.get(container_id_or_name)

            # 获取容器的卷映射信息
            mounts = container.attrs.get("Mounts", [])
            volume_mappings = {}

            for mount in mounts:
                if mount.get("Type") == "bind":
                    host_path = mount.get("Source", "")
                    container_path = mount.get("Destination", "")
                    volume_mappings[host_path] = container_path

            # 检查指定的宿主路径是否已映射到容器
            for host_path in host_paths:
                host_path_abs = os.path.abspath(host_path)

                if not os.path.exists(host_path_abs):
                    issues.append(
                        {
                            "type": "host_path_not_exist",
                            "host_path": host_path_abs,
                            "severity": "error",
                        }
                    )
                    continue

                # 查找映射的容器路径
                mapped_container_path = None
                for src, dest in volume_mappings.items():
                    if os.path.commonpath([host_path_abs, src]) == src:
                        mapped_container_path = dest
                        break

                if not mapped_container_path:
                    issues.append(
                        {
                            "type": "host_path_not_mapped",
                            "host_path": host_path_abs,
                            "severity": "error",
                        }
                    )
                    continue

                # 检查文件是否同步（简化版，只检查文件是否存在）
                relative_path = (
                    os.path.relpath(host_path_abs, src) if mapped_container_path else ""
                )
                container_path = (
                    os.path.join(mapped_container_path, relative_path)
                    if mapped_container_path
                    else ""
                )

                if container_path:
                    # 检查容器中文件是否存在
                    exec_result = container.exec_run(
                        f"test -e {container_path} && echo exists || echo not_exists"
                    )
                    if "not_exists" in exec_result.output.decode("utf-8"):
                        issues.append(
                            {
                                "type": "file_not_synced_to_container",
                                "host_path": host_path_abs,
                                "container_path": container_path,
                                "severity": "warning",
                            }
                        )

                    # 如果是文件，检查内容是否一致（通过比较文件大小和修改时间简化实现）
                    if os.path.isfile(host_path_abs):
                        host_file_info = {
                            "size": os.path.getsize(host_path_abs),
                            "mtime": os.path.getmtime(host_path_abs),
                        }

                        exec_result = container.exec_run(
                            f"stat -c '%s %Y' {container_path}"
                        )
                        container_file_info_str = exec_result.output.decode(
                            "utf-8"
                        ).strip()

                        if (
                            container_file_info_str
                            and "No such file" not in container_file_info_str
                        ):
                            try:
                                container_size, container_mtime = map(
                                    int, container_file_info_str.split()
                                )
                                container_file_info = {
                                    "size": container_size,
                                    "mtime": container_mtime,
                                }

                                if (
                                    host_file_info["size"]
                                    != container_file_info["size"]
                                ):
                                    issues.append(
                                        {
                                            "type": "file_content_mismatch",
                                            "host_path": host_path_abs,
                                            "container_path": container_path,
                                            "host_size": host_file_info["size"],
                                            "container_size": container_file_info[
                                                "size"
                                            ],
                                            "severity": "warning",
                                        }
                                    )
                            except Exception as e:
                                logger.warning(f"无法比较文件信息: {e}")
        except Exception as e:
            logger.error(f"检查文件同步一致性时出错: {e}")

        return issues

    def run_consistency_check(
        self,
        container_id_or_name: str,
        check_dependencies: bool = True,
        check_env_vars: bool = True,
        check_ports: bool = True,
        check_files: bool = True,
        host_paths: Optional[List[str]] = None,
        env_var_whitelist: Optional[List[str]] = None,
        generate_report: bool = True,
    ) -> Dict[str, Any]:
        """
        运行完整的一致性检查

        Args:
            container_id_or_name: 容器ID或名称
            check_dependencies: 是否检查依赖包一致性
            check_env_vars: 是否检查环境变量一致性
            check_ports: 是否检查端口映射一致性
            check_files: 是否检查文件同步一致性
            host_paths: 需要检查文件同步的宿主路径列表
            env_var_whitelist: 环境变量检查白名单
            generate_report: 是否生成报告文件

        Returns:
            一致性检查结果
        """
        host_info = self.get_host_env_info()
        container_info = self.get_container_env_info(container_id_or_name)

        issues = []

        if check_dependencies:
            dependency_issues = self.check_dependency_consistency(
                host_info, container_info
            )
            issues.extend(dependency_issues)

        if check_env_vars:
            env_var_issues = self.check_env_var_consistency(
                host_info, container_info, env_var_whitelist
            )
            issues.extend(env_var_issues)

        if check_ports:
            port_issues = self.check_port_mapping_consistency(container_id_or_name)
            issues.extend(port_issues)

        if check_files and host_paths:
            file_issues = self.check_file_sync_consistency(
                container_id_or_name, host_paths
            )
            issues.extend(file_issues)

        result = {
            "timestamp": datetime.now().isoformat(),
            "container": {
                "id": container_info["id"],
                "name": container_info["name"],
                "image": container_info["image"],
            },
            "checks_performed": {
                "dependencies": check_dependencies,
                "environment_variables": check_env_vars,
                "port_mappings": check_ports,
                "file_sync": check_files,
            },
            "issues": issues,
            "issue_summary": {
                "total": len(issues),
                "by_severity": {
                    "error": len([i for i in issues if i.get("severity") == "error"]),
                    "warning": len(
                        [i for i in issues if i.get("severity") == "warning"]
                    ),
                    "info": len([i for i in issues if i.get("severity") == "info"]),
                },
                "by_type": {
                    issue_type: len([i for i in issues if i.get("type") == issue_type])
                    for issue_type in set(i.get("type", "") for i in issues)
                },
            },
        }

        if generate_report:
            report_file = (
                self._config_dir
                / f"consistency_report_{container_info['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(result, f, indent=2)
            result["report_file"] = str(report_file)

        return result

    def fix_consistency_issues(
        self,
        container_id_or_name: str,
        issues: List[Dict[str, Any]],
        auto_fix: bool = False,
    ) -> Dict[str, Any]:
        """
        修复容器环境一致性问题

        Args:
            container_id_or_name: 容器ID或名称
            issues: 需要修复的问题列表
            auto_fix: 是否自动修复问题

        Returns:
            修复结果的详细信息
        """
        try:
            container = self.docker_client.containers.get(container_id_or_name)
            fix_results = []
            total_issues = len(issues)
            fixed_count = 0

            for issue in issues:
                fix_result = {"issue": issue, "fixed": False}

                try:
                    if issue.get("type") == "python_package_missing_in_container":
                        if auto_fix:
                            # 在容器中安装缺失的Python包
                            pkg_name = issue.get("package", "")
                            host_version = issue.get("host_version", "")
                            if pkg_name and host_version:
                                result = container.exec_run(
                                    f"pip install {pkg_name}=={host_version}"
                                )
                                fix_result["fixed"] = result.exit_code == 0
                                fix_result["fix_method"] = "pip_install"

                    elif issue.get("type") == "python_package_version_mismatch":
                        if auto_fix:
                            # 更新容器中的Python包版本
                            pkg_name = issue.get("package", "")
                            host_version = issue.get("host_version", "")
                            if pkg_name and host_version:
                                result = container.exec_run(
                                    f"pip install --upgrade {pkg_name}=={host_version}"
                                )
                                fix_result["fixed"] = result.exit_code == 0
                                fix_result["fix_method"] = "pip_upgrade"

                    elif issue.get("type") == "file_not_synced_to_container":
                        host_path = issue.get("host_path", "")
                        container_path = issue.get("container_path", "")

                        if host_path and container_path and os.path.exists(host_path):
                            fix_result["fix_method"] = "copy_file_to_container"

                            with open(host_path, "rb") as src_file:
                                content = src_file.read()

                            tar_stream = self._create_tar_archive_from_content(
                                {os.path.basename(container_path): content}
                            )

                            container_dir = os.path.dirname(container_path)
                            container.exec_run(f"mkdir -p {container_dir}")
                            put_result = container.put_archive(
                                container_dir, tar_stream
                            )
                            fix_result["fixed"] = put_result

                except Exception as e:
                    fix_result["error"] = str(e)

                fix_results.append(fix_result)
                if fix_result.get("fixed"):
                    fixed_count += 1

            return {
                "container": {
                    "name": container.name if container.name else "",
                    "id": container.id[:12] if container.id else "",
                },
                "timestamp": datetime.now().isoformat(),
                "auto_fix": auto_fix,
                "summary": {
                    "total_issues": total_issues,
                    "fixed": fixed_count,
                    "failed": total_issues - fixed_count,
                },
                "fix_results": fix_results,
            }

        except Exception as e:
            logger.error(f"修复容器 {container_id_or_name} 一致性问题时出错: {e}")
            return {
                "error": str(e),
                "container": container_id_or_name,
            }

    def _create_tar_archive_from_content(
        self, file_content_map: Dict[str, bytes]
    ) -> bytes:
        """
        从文件内容映射创建tar归档

        Args:
            file_content_map: 文件名到文件内容的映射

        Returns:
            tar归档的字节内容
        """
        import tarfile
        import io

        tar_stream = io.BytesIO()

        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            for file_name, content in file_content_map.items():
                tarinfo = tarfile.TarInfo(name=file_name)
                tarinfo.size = len(content)

                content_io = io.BytesIO(content)
                tar.addfile(tarinfo, content_io)

        tar_stream.seek(0)
        return tar_stream.read()

    def save_baseline(
        self, container_id_or_name: str, baseline_name: str
    ) -> Dict[str, Any]:
        """
        保存容器环境基准线

        Args:
            container_id_or_name: 容器ID或名称
            baseline_name: 基准线名称

        Returns:
            基准线保存结果
        """
        try:
            host_info = self.get_host_env_info() or {}
            container_info = self.get_container_env_info(container_id_or_name) or {}

            baseline = {
                "name": baseline_name,
                "timestamp": datetime.now().isoformat(),
                "container": container_info,
                "host": host_info,
            }

            baseline_file = self._config_dir / f"baseline_{baseline_name}.json"
            with open(baseline_file, "w") as f:
                json.dump(baseline, f, indent=2)

            return {
                "name": baseline_name,
                "timestamp": baseline["timestamp"],
                "baseline_file": str(baseline_file),
                "container": container_info,
            }

        except Exception as e:
            logger.error(f"保存基准线 {baseline_name} 时出错: {e}")
            return {"error": str(e)}

    def compare_with_baseline(
        self, container_id_or_name: str, baseline_name: str
    ) -> Dict[str, Any]:
        """
        将当前容器环境与基准线比较

        Args:
            container_id_or_name: 容器ID或名称
            baseline_name: 基准线名称

        Returns:
            比较结果
        """
        try:
            # 读取基准线文件
            baseline_file = self._config_dir / f"baseline_{baseline_name}.json"
            if not baseline_file.exists():
                return {"error": f"基准线 {baseline_name} 不存在"}

            with open(baseline_file, "r") as f:
                baseline = json.load(f)

            # 获取当前容器和主机环境信息
            current_host_info = self.get_host_env_info() or {}
            current_container_info = (
                self.get_container_env_info(container_id_or_name) or {}
            )

            # 安全地获取基准线信息，提供默认值
            baseline_host_info = baseline.get("host", {})
            baseline_container_info = baseline.get("container", {})

            # 检查各项一致性
            current_issues = self.check_dependency_consistency(
                current_host_info, current_container_info
            )
            baseline_issues = self.check_dependency_consistency(
                baseline_host_info, baseline_container_info
            )

            # 比较新增和已解决的问题
            new_issues = [
                issue for issue in current_issues if issue not in baseline_issues
            ]
            resolved_issues = [
                issue for issue in baseline_issues if issue not in current_issues
            ]

            return {
                "baseline_name": baseline_name,
                "baseline_timestamp": baseline.get("timestamp", ""),
                "current_timestamp": datetime.now().isoformat(),
                "container": current_container_info,
                "baseline_container": baseline_container_info,
                "current_issues_count": len(current_issues),
                "baseline_issues_count": len(baseline_issues),
                "summary": {
                    "new_issues": len(new_issues),
                    "resolved_issues": len(resolved_issues),
                    "net_change": len(new_issues) - len(resolved_issues),
                },
                "new_issues": new_issues,
                "resolved_issues": resolved_issues,
            }

        except Exception as e:
            logger.error(f"比较基准线 {baseline_name} 时出错: {e}")
            return {"error": str(e)}

    def list_baselines(self) -> List[Dict[str, Any]]:
        """
        列出所有已保存的基准线

        Returns:
            基准线列表，每个基准线包含名称、时间戳等信息
        """
        try:
            baselines = []
            for baseline_file in self._config_dir.glob("baseline_*.json"):
                try:
                    with open(baseline_file, "r") as f:
                        baseline_data = json.load(f)
                        baselines.append(
                            {
                                "name": baseline_data.get("name", ""),
                                "timestamp": baseline_data.get("timestamp", ""),
                                "container": baseline_data.get("container", {}),
                                "file_path": str(baseline_file),
                            }
                        )
                except Exception as e:
                    logger.warning(f"读取基准线文件 {baseline_file} 时出错: {e}")

            return sorted(baselines, key=lambda x: x.get("timestamp", ""), reverse=True)
        except Exception as e:
            logger.error(f"列出基准线时出错: {e}")
            return []

    def delete_baseline(self, baseline_name: str) -> Dict[str, Any]:
        """
        删除指定的基准线

        Args:
            baseline_name: 基准线名称

        Returns:
            删除操作的结果
        """
        try:
            baseline_file = self._config_dir / f"baseline_{baseline_name}.json"
            if not baseline_file.exists():
                return {"error": f"基准线 {baseline_name} 不存在"}

            baseline_file.unlink()
            return {
                "success": True,
                "message": f"基准线 {baseline_name} 已删除",
                "baseline_name": baseline_name,
            }
        except Exception as e:
            logger.error(f"删除基准线 {baseline_name} 时出错: {e}")
            return {"error": str(e)}

    def generate_consistency_report(
        self,
        container_id_or_name: str,
        report_format: str = "json",
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """
        生成容器环境一致性报告

        Args:
            container_id_or_name: 容器ID或名称
            report_format: 报告格式，支持 'json' 或 'html'
            include_details: 是否包含详细信息

        Returns:
            报告生成结果
        """
        try:
            # 运行完整的一致性检查
            check_result = self.run_consistency_check(
                container_id_or_name, generate_report=False  # 我们将在这里生成报告
            )

            # 获取容器和主机环境信息
            container_info = self.get_container_env_info(container_id_or_name)
            host_info = self.get_host_env_info()

            # 构建报告数据
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "container": container_info,
                "host": host_info if include_details else None,
                "check_result": check_result,
                "summary": {
                    "total_issues": len(check_result.get("issues", [])),
                    "severity_counts": check_result.get("issue_summary", {}).get(
                        "by_severity", {}
                    ),
                    "type_counts": check_result.get("issue_summary", {}).get(
                        "by_type", {}
                    ),
                },
            }

            # 生成报告文件
            report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            container_name = container_info.get("name", "unknown")

            if report_format == "html":
                report_file = (
                    self._config_dir
                    / f"consistency_report_{container_name}_{report_time}.html"
                )
                self._generate_html_report(report_data, report_file)
            else:  # json format
                report_file = (
                    self._config_dir
                    / f"consistency_report_{container_name}_{report_time}.json"
                )
                with open(report_file, "w") as f:
                    json.dump(report_data, f, indent=2)

            return {
                "success": True,
                "report_file": str(report_file),
                "format": report_format,
                "container": container_info,
                "summary": report_data["summary"],
            }

        except Exception as e:
            logger.error(f"生成一致性报告时出错: {e}")
            return {"error": str(e)}

    def _generate_html_report(
        self, report_data: Dict[str, Any], output_file: Path
    ) -> None:
        """
        生成HTML格式的报告

        Args:
            report_data: 报告数据
            output_file: 输出文件路径
        """
        try:
            # 创建HTML报告模板
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Container Consistency Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
                    .section { margin: 20px 0; }
                    .issue { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }
                    .error { border-left-color: #ff4444; }
                    .warning { border-left-color: #ffbb33; }
                    .info { border-left-color: #33b5e5; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f5f5f5; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Container Consistency Report</h1>
                    <p>Generated: {timestamp}</p>
                    <p>Container: {container_name} ({container_id})</p>
                </div>

                <div class="section">
                    <h2>Summary</h2>
                    <table>
                        <tr><th>Total Issues</th><td>{total_issues}</td></tr>
                        <tr><th>Errors</th><td>{error_count}</td></tr>
                        <tr><th>Warnings</th><td>{warning_count}</td></tr>
                        <tr><th>Info</th><td>{info_count}</td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>Issues</h2>
                    {issues_html}
                </div>

                <div class="section">
                    <h2>Environment Details</h2>
                    {env_details_html}
                </div>
            </body>
            </html>
            """

            # 生成问题列表HTML
            issues_html = ""
            for issue in report_data.get("check_result", {}).get("issues", []):
                severity = issue.get("severity", "info")
                issues_html += f"""
                <div class="issue {severity}">
                    <h3>{issue.get("type", "Unknown Issue")}</h3>
                    <p><strong>Severity:</strong> {severity}</p>
                    {"".join(f"<p><strong>{k}:</strong> {v}</p>" for k, v in issue.items() if k not in ["type", "severity"])}
                </div>
                """

            # 生成环境详情HTML
            env_details_html = "<h3>Container Environment</h3>"
            container_info = report_data.get("container", {})
            env_details_html += "<table>"
            for key, value in container_info.items():
                if isinstance(value, dict):
                    env_details_html += f"<tr><th colspan='2'>{key}</th></tr>"
                    for sub_key, sub_value in value.items():
                        env_details_html += (
                            f"<tr><td>{sub_key}</td><td>{sub_value}</td></tr>"
                        )
                else:
                    env_details_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
            env_details_html += "</table>"

            # 填充模板
            html_content = html_template.format(
                timestamp=report_data.get("timestamp", ""),
                container_name=report_data.get("container", {}).get("name", "Unknown"),
                container_id=report_data.get("container", {}).get("id", "Unknown"),
                total_issues=report_data.get("summary", {}).get("total_issues", 0),
                error_count=report_data.get("summary", {})
                .get("severity_counts", {})
                .get("error", 0),
                warning_count=report_data.get("summary", {})
                .get("severity_counts", {})
                .get("warning", 0),
                info_count=report_data.get("summary", {})
                .get("severity_counts", {})
                .get("info", 0),
                issues_html=issues_html,
                env_details_html=env_details_html,
            )

            # 写入文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

        except Exception as e:
            logger.error(f"生成HTML报告时出错: {e}")
            raise


# 创建单例实例
consistency_manager = ConsistencyManager()
