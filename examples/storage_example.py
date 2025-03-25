#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器持久化存储示例

演示如何使用持久化存储功能管理Docker卷
"""

import os
import sys
import time
import logging
from datetime import datetime

from backend.container_manager.manager import ContainerManager
from backend.container_manager.storage_manager import get_storage_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("storage_example")


def format_size(size_bytes):
    """格式化字节大小为人类可读格式"""
    if size_bytes == 0 or size_bytes == "Unknown":
        return "0 B"

    if isinstance(size_bytes, str):
        return size_bytes

    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"


def print_volume_info(volume):
    """打印卷信息"""
    print(f"名称: {volume.get('name', 'N/A')}")
    print(f"驱动: {volume.get('driver', 'N/A')}")
    print(f"挂载点: {volume.get('mountpoint', 'N/A')}")
    print(f"创建时间: {volume.get('created', 'N/A')}")

    if "size" in volume:
        print(f"大小: {volume.get('size', 'Unknown')}")

    if "labels" in volume and volume["labels"]:
        print("标签:")
        for k, v in volume["labels"].items():
            print(f"  {k}: {v}")

    print("-" * 50)


def main():
    """主函数"""
    logger.info("容器持久化存储示例")

    # 初始化容器管理器
    container_manager = ContainerManager()

    # 获取存储管理器
    storage_manager = get_storage_manager()

    # 示例1: 列出现有卷
    logger.info("列出所有数据卷")
    volumes = storage_manager.list_volumes()
    print(f"找到 {len(volumes)} 个数据卷:")
    for volume in volumes:
        print_volume_info(volume)

    # 示例2: 创建新卷
    volume_name = f"test-volume-{int(time.time())}"
    logger.info(f"创建新卷: {volume_name}")
    try:
        volume = storage_manager.create_volume(
            name=volume_name, labels={"purpose": "demo", "created_by": "smoothstack"}
        )
        print(f"成功创建卷 {volume_name}:")
        print_volume_info(volume)
    except Exception as e:
        logger.error(f"创建卷失败: {e}")
        return

    # 示例3: 查看卷详情
    logger.info(f"获取卷详情: {volume_name}")
    volume_info = storage_manager.inspect_volume(volume_name)
    print("卷详情:")
    print(f"名称: {volume_info.get('name', 'N/A')}")
    print(f"驱动: {volume_info.get('driver', 'N/A')}")
    print(f"挂载点: {volume_info.get('mountpoint', 'N/A')}")
    print(f"创建时间: {volume_info.get('created', 'N/A')}")
    print(f"标签: {volume_info.get('labels', {})}")
    print(f"使用此卷的容器: {volume_info.get('used_by', [])}")
    print("-" * 50)

    # 示例4: 创建使用此卷的容器
    logger.info(f"创建使用卷 {volume_name} 的容器")
    container_name = f"volume-test-{int(time.time())}"

    try:
        container = container_manager.client.containers.run(
            "alpine",
            "sh -c 'echo \"Hello from volume\" > /data/test.txt && sleep 60'",
            name=container_name,
            volumes={volume_name: {"bind": "/data", "mode": "rw"}},
            detach=True,
        )
        logger.info(f"创建的容器ID: {container.id}")
        logger.info(f"容器 {container_name} 正在运行并写入数据到卷 {volume_name}")

        # 等待容器写入数据
        time.sleep(5)

        # 示例5: 列出容器的挂载点
        logger.info(f"列出容器 {container_name} 的挂载点")
        mounts = storage_manager.list_container_volumes(container.id)
        print(f"容器 {container_name} 的挂载点:")
        for mount in mounts:
            print(f"类型: {mount.get('type', 'N/A')}")
            print(f"源: {mount.get('source', 'N/A')}")
            print(f"目标: {mount.get('destination', 'N/A')}")
            print(f"模式: {mount.get('mode', 'N/A')}")
            print("-" * 30)

        # 示例6: 备份卷数据
        backup_path = os.path.join(os.getcwd(), "volume_backup.tar")
        logger.info(f"备份卷 {volume_name} 到 {backup_path}")
        if storage_manager.backup_volume(volume_name, backup_path):
            logger.info(f"备份成功，文件大小: {os.path.getsize(backup_path)} 字节")
        else:
            logger.error("备份失败")

        # 停止并移除测试容器
        logger.info(f"停止并移除容器 {container_name}")
        container.stop()
        container.remove()
        logger.info(f"容器 {container_name} 已移除")

        # 示例7: 移除卷并创建新卷
        new_volume_name = f"{volume_name}-restored"
        logger.info(f"移除卷 {volume_name}")
        if storage_manager.remove_volume(volume_name):
            logger.info(f"卷 {volume_name} 已移除")
        else:
            logger.error(f"无法移除卷 {volume_name}")

        # 示例8: 从备份恢复卷
        logger.info(f"从备份恢复到新卷 {new_volume_name}")
        if storage_manager.restore_volume(backup_path, new_volume_name):
            logger.info(f"卷 {new_volume_name} 已从备份恢复")

            # 示例9: 验证恢复的数据
            logger.info("创建容器以验证恢复的数据")
            verify_container = container_manager.client.containers.run(
                "alpine",
                "cat /data/test.txt",
                volumes={new_volume_name: {"bind": "/data", "mode": "ro"}},
                remove=True,
            )
            output = verify_container.decode("utf-8").strip()
            logger.info(f"恢复的卷中的文件内容: {output}")

            # 清理恢复的卷
            logger.info(f"清理恢复的卷 {new_volume_name}")
            storage_manager.remove_volume(new_volume_name)
        else:
            logger.error(f"从备份恢复卷 {new_volume_name} 失败")

        # 示例10: 清理备份文件
        if os.path.exists(backup_path):
            os.remove(backup_path)
            logger.info(f"备份文件 {backup_path} 已删除")

    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        # 清理
        try:
            container_manager.client.containers.get(container_name).remove(force=True)
        except:
            pass
        try:
            storage_manager.remove_volume(volume_name)
        except:
            pass
        try:
            storage_manager.remove_volume(new_volume_name)
        except:
            pass
        if os.path.exists(backup_path):
            os.remove(backup_path)

    logger.info("示例结束")


if __name__ == "__main__":
    main()
