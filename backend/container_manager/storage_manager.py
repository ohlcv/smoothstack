#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器持久化存储管理器

提供Docker卷和绑定挂载的管理功能
"""

import os
import time
import json
import logging
import tempfile
import shutil
import tarfile
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import docker
from docker.errors import DockerException, NotFound, APIError

# 配置日志
logger = logging.getLogger("smoothstack.container_manager.storage_manager")


class StorageManager:
    """容器持久化存储管理器"""

    def __init__(self):
        """初始化存储管理器"""
        try:
            self.client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except DockerException as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            raise

    def list_volumes(self, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        列出所有数据卷

        Args:
            filters: 过滤条件，如 {'dangling': True} 仅列出未使用的卷

        Returns:
            卷信息列表
        """
        try:
            volumes = self.client.volumes.list(filters=filters or {})
            result = []

            for volume in volumes:
                attrs = volume.attrs
                result.append(
                    {
                        "name": attrs["Name"],
                        "driver": attrs["Driver"],
                        "mountpoint": attrs["Mountpoint"],
                        "created": attrs["CreatedAt"],
                        "status": attrs["Status"] if "Status" in attrs else {},
                        "labels": attrs["Labels"] or {},
                        "scope": attrs["Scope"],
                        "size": (
                            self._get_volume_size(attrs["Mountpoint"])
                            if os.name != "nt"
                            else "Unknown"
                        ),
                    }
                )

            return result
        except DockerException as e:
            logger.error(f"列出数据卷时出错: {e}")
            return []

    def _get_volume_size(self, mountpoint: str) -> str:
        """
        获取卷的大小

        Args:
            mountpoint: 卷的挂载点路径

        Returns:
            格式化的卷大小字符串
        """
        try:
            if not os.path.exists(mountpoint):
                return "Unknown"

            total_size = 0
            for dirpath, dirnames, filenames in os.walk(mountpoint):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):  # 文件可能在遍历过程中被删除
                        total_size += os.path.getsize(fp)

            # 格式化大小
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if total_size < 1024.0:
                    return f"{total_size:.2f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.2f} PB"
        except Exception as e:
            logger.warning(f"获取卷大小时出错: {e}")
            return "Unknown"

    def create_volume(
        self,
        name: str,
        driver: str = "local",
        driver_opts: Dict = None,
        labels: Dict = None,
    ) -> Dict[str, Any]:
        """
        创建数据卷

        Args:
            name: 卷名称
            driver: 存储驱动
            driver_opts: 驱动选项
            labels: 卷标签

        Returns:
            卷信息
        """
        try:
            volume = self.client.volumes.create(
                name=name,
                driver=driver,
                driver_opts=driver_opts or {},
                labels=labels or {},
            )

            logger.info(f"创建数据卷成功: {name}")
            return {
                "name": volume.name,
                "driver": volume.attrs["Driver"],
                "mountpoint": volume.attrs["Mountpoint"],
                "created": volume.attrs["CreatedAt"],
                "labels": volume.attrs["Labels"] or {},
            }
        except DockerException as e:
            logger.error(f"创建数据卷失败: {e}")
            raise

    def remove_volume(self, name: str, force: bool = False) -> bool:
        """
        删除数据卷

        Args:
            name: 卷名称
            force: 是否强制删除

        Returns:
            删除成功返回True，否则返回False
        """
        try:
            volume = self.client.volumes.get(name)
            volume.remove(force=force)
            logger.info(f"删除数据卷成功: {name}")
            return True
        except NotFound:
            logger.warning(f"数据卷不存在: {name}")
            return False
        except APIError as e:
            if "volume is in use" in str(e):
                logger.error(f"数据卷正在使用中无法删除: {name}")
                # 查找使用此卷的容器
                containers = self._find_containers_using_volume(name)
                if containers:
                    logger.info(f"以下容器正在使用卷 {name}: {', '.join(containers)}")
                if force:
                    return self._force_remove_volume_and_containers(name, containers)
                return False
            logger.error(f"删除数据卷时出错: {e}")
            return False
        except Exception as e:
            logger.error(f"删除数据卷时出错: {e}")
            return False

    def _find_containers_using_volume(self, volume_name: str) -> List[str]:
        """
        查找使用指定卷的容器

        Args:
            volume_name: 卷名称

        Returns:
            容器名称列表
        """
        containers = []
        try:
            for container in self.client.containers.list(all=True):
                if container.attrs.get("Mounts"):
                    for mount in container.attrs["Mounts"]:
                        if (
                            mount.get("Type") == "volume"
                            and mount.get("Name") == volume_name
                        ):
                            containers.append(container.name)
        except Exception as e:
            logger.error(f"查找使用卷的容器时出错: {e}")
        return containers

    def _force_remove_volume_and_containers(
        self, volume_name: str, container_names: List[str]
    ) -> bool:
        """
        强制删除卷及使用它的容器

        Args:
            volume_name: 卷名称
            container_names: 使用该卷的容器名称列表

        Returns:
            删除成功返回True，否则返回False
        """
        try:
            # 停止并删除容器
            for container_name in container_names:
                try:
                    container = self.client.containers.get(container_name)
                    if container.status == "running":
                        logger.info(f"正在停止容器: {container_name}")
                        container.stop(timeout=10)
                    logger.info(f"正在删除容器: {container_name}")
                    container.remove(force=True)
                except Exception as e:
                    logger.error(f"处理容器 {container_name} 时出错: {e}")

            # 再次尝试删除卷
            self.client.volumes.get(volume_name).remove(force=True)
            logger.info(f"强制删除数据卷成功: {volume_name}")
            return True
        except Exception as e:
            logger.error(f"强制删除数据卷失败: {e}")
            return False

    def inspect_volume(self, name: str) -> Dict[str, Any]:
        """
        查看卷详情

        Args:
            name: 卷名称

        Returns:
            卷详细信息
        """
        try:
            volume = self.client.volumes.get(name)

            # 基本信息
            result = {
                "name": volume.name,
                "driver": volume.attrs["Driver"],
                "mountpoint": volume.attrs["Mountpoint"],
                "created": volume.attrs["CreatedAt"],
                "status": volume.attrs["Status"] if "Status" in volume.attrs else {},
                "labels": volume.attrs["Labels"] or {},
                "scope": volume.attrs["Scope"],
            }

            # 获取卷的大小
            if os.name != "nt":  # 仅在非Windows系统上尝试获取大小
                result["size"] = self._get_volume_size(volume.attrs["Mountpoint"])

            # 查找使用此卷的容器
            result["used_by"] = self._find_containers_using_volume(name)

            return result
        except NotFound:
            logger.warning(f"数据卷不存在: {name}")
            return {"error": f"数据卷不存在: {name}"}
        except Exception as e:
            logger.error(f"获取数据卷详情时出错: {e}")
            return {"error": str(e)}

    def prune_volumes(self) -> Dict[str, Any]:
        """
        清理未使用的卷

        Returns:
            清理结果，包含删除的卷和释放的空间
        """
        try:
            response = self.client.volumes.prune()
            logger.info(f"清理未使用的卷成功: {response}")
            return {
                "volumes_deleted": response.get("VolumesDeleted", []),
                "space_reclaimed": response.get("SpaceReclaimed", 0),
            }
        except Exception as e:
            logger.error(f"清理未使用的卷时出错: {e}")
            return {"error": str(e)}

    def backup_volume(self, volume_name: str, backup_path: str) -> bool:
        """
        备份卷数据到文件

        Args:
            volume_name: 卷名称
            backup_path: 备份文件路径

        Returns:
            备份成功返回True，否则返回False
        """
        temp_dir = None
        try:
            # 确保卷存在
            volume = self.client.volumes.get(volume_name)

            # 创建临时容器来访问卷
            temp_dir = tempfile.mkdtemp(prefix="volume_backup_")

            # 启动一个临时容器来备份卷数据
            container = self.client.containers.run(
                "alpine",
                "tar -cf /backup/volume_data.tar -C /volume .",
                volumes={
                    volume_name: {"bind": "/volume", "mode": "ro"},
                    temp_dir: {"bind": "/backup", "mode": "rw"},
                },
                detach=True,
                remove=True,
            )

            # 等待容器完成
            exit_code = container.wait()["StatusCode"]
            if exit_code != 0:
                logs = container.logs().decode("utf-8")
                logger.error(f"备份容器退出代码非零: {exit_code}, 日志: {logs}")
                return False

            # 将临时目录中的tar文件复制到指定位置
            temp_tar = os.path.join(temp_dir, "volume_data.tar")
            if os.path.exists(temp_tar):
                # 确保目标目录存在
                os.makedirs(
                    os.path.dirname(os.path.abspath(backup_path)), exist_ok=True
                )
                shutil.copy2(temp_tar, backup_path)
                logger.info(f"卷 {volume_name} 已备份到 {backup_path}")
                return True
            else:
                logger.error(f"备份文件未创建: {temp_tar}")
                return False

        except NotFound:
            logger.warning(f"数据卷不存在: {volume_name}")
            return False
        except Exception as e:
            logger.error(f"备份卷 {volume_name} 时出错: {e}")
            return False
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def restore_volume(
        self, backup_path: str, volume_name: str, create_if_missing: bool = True
    ) -> bool:
        """
        从备份文件恢复卷数据

        Args:
            backup_path: 备份文件路径
            volume_name: 卷名称
            create_if_missing: 如果卷不存在是否创建

        Returns:
            恢复成功返回True，否则返回False
        """
        temp_dir = None
        try:
            # 确认备份文件存在
            if not os.path.exists(backup_path):
                logger.error(f"备份文件不存在: {backup_path}")
                return False

            # 确保卷存在
            try:
                volume = self.client.volumes.get(volume_name)
            except NotFound:
                if create_if_missing:
                    volume = self.client.volumes.create(name=volume_name)
                    logger.info(f"创建数据卷: {volume_name}")
                else:
                    logger.warning(f"数据卷不存在且未指定创建: {volume_name}")
                    return False

            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="volume_restore_")

            # 将备份文件复制到临时目录
            dest_tar = os.path.join(temp_dir, "volume_data.tar")
            shutil.copy2(backup_path, dest_tar)

            # 启动一个临时容器来恢复卷数据
            container = self.client.containers.run(
                "alpine",
                "tar -xf /backup/volume_data.tar -C /volume",
                volumes={
                    volume_name: {"bind": "/volume", "mode": "rw"},
                    temp_dir: {"bind": "/backup", "mode": "ro"},
                },
                detach=True,
                remove=True,
            )

            # 等待容器完成
            exit_code = container.wait()["StatusCode"]
            if exit_code != 0:
                logs = container.logs().decode("utf-8")
                logger.error(f"恢复容器退出代码非零: {exit_code}, 日志: {logs}")
                return False

            logger.info(f"已从 {backup_path} 恢复卷 {volume_name}")
            return True

        except Exception as e:
            logger.error(f"恢复卷 {volume_name} 时出错: {e}")
            return False
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def list_container_volumes(self, container_id_or_name: str) -> List[Dict[str, Any]]:
        """
        列出容器使用的所有卷

        Args:
            container_id_or_name: 容器ID或名称

        Returns:
            挂载信息列表
        """
        try:
            container = self.client.containers.get(container_id_or_name)
            mounts = container.attrs.get("Mounts", [])

            result = []
            for mount in mounts:
                mount_info = {
                    "type": mount.get("Type"),
                    "source": mount.get("Source"),
                    "destination": mount.get("Destination"),
                    "mode": mount.get("Mode", "rw"),
                    "rw": mount.get("RW", True),
                    "propagation": mount.get("Propagation", ""),
                }

                # 如果是卷挂载，添加卷名称
                if mount.get("Type") == "volume":
                    mount_info["name"] = mount.get("Name")

                result.append(mount_info)

            return result
        except NotFound:
            logger.warning(f"容器不存在: {container_id_or_name}")
            return []
        except Exception as e:
            logger.error(f"获取容器卷信息时出错: {e}")
            return []

    def mount_volume(
        self,
        volume_name: str,
        container_id_or_name: str,
        container_path: str,
        mode: str = "rw",
    ) -> bool:
        """
        将卷挂载到容器（仅支持新创建的容器，无法动态挂载到已存在的容器）

        Args:
            volume_name: 卷名称
            container_id_or_name: 容器ID或名称
            container_path: 容器内挂载路径
            mode: 挂载模式，'rw'（读写）或'ro'（只读）

        Returns:
            成功返回True，失败返回False和错误信息
        """
        # 由于Docker不支持向正在运行的容器动态添加卷，这里只能提供信息
        logger.warning("Docker不支持向现有容器动态添加卷。请在创建容器时指定卷。")
        logger.info(
            f"要将卷 {volume_name} 挂载到容器 {container_id_or_name} 的 {container_path}，请使用以下命令:"
        )
        logger.info(f"docker run -v {volume_name}:{container_path}:{mode} ...")
        return False

    def unmount_volume(self, volume_name: str, container_id_or_name: str) -> bool:
        """
        从容器卸载卷（仅支持卸载后重新创建容器）

        Args:
            volume_name: 卷名称
            container_id_or_name: 容器ID或名称

        Returns:
            成功返回True，失败返回False
        """
        # 同样，Docker不支持从正在运行的容器动态卸载卷
        logger.warning("Docker不支持从现有容器动态卸载卷。请停止容器并重新创建。")
        return False

    def create_bind_mount(
        self,
        host_path: str,
        container_id_or_name: str,
        container_path: str,
        mode: str = "rw",
    ) -> bool:
        """
        创建绑定挂载（将主机路径挂载到容器）

        Args:
            host_path: 主机路径
            container_id_or_name: 容器ID或名称
            container_path: 容器内挂载路径
            mode: 挂载模式，'rw'（读写）或'ro'（只读）

        Returns:
            成功返回True，失败返回False
        """
        # 同样限制，只能在创建容器时指定
        logger.warning("Docker不支持向现有容器动态添加绑定挂载。请在创建容器时指定。")
        logger.info(
            f"要将主机路径 {host_path} 挂载到容器 {container_id_or_name} 的 {container_path}，请使用以下命令:"
        )
        logger.info(f"docker run -v {host_path}:{container_path}:{mode} ...")
        return False


# 单例模式获取存储管理器实例
_storage_manager_instance = None


def get_storage_manager() -> StorageManager:
    """
    获取存储管理器单例实例

    Returns:
        存储管理器实例
    """
    global _storage_manager_instance
    if _storage_manager_instance is None:
        _storage_manager_instance = StorageManager()
    return _storage_manager_instance
