#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖管理系统使用示例

演示如何使用依赖管理系统进行包的安装、更新和源管理
"""

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from backend.dependency_manager import dependency_manager
from backend.dependency_manager.sources.source import SourceType
from backend.dependency_manager.sources.pypi import PyPISource


def main():
    """主函数"""
    print("===== 依赖管理系统示例 =====")

    # 检查源状态
    print("\n1. 检查当前源状态:")
    sources_status = dependency_manager.source_manager.get_status()
    for source_name, source_info in sources_status.items():
        print(f"  - {source_name}: {source_info['status']}")

    # 列出已安装的包
    print("\n2. 列出已安装的PIP包:")
    pip_packages = dependency_manager.list_packages(installer_type="pip")
    if pip_packages:
        for pkg in pip_packages[:5]:  # 只显示前5个
            print(f"  - {pkg['name']} {pkg['version']}")
        if len(pip_packages) > 5:
            print(f"  ... 共{len(pip_packages)}个包")
    else:
        print("  未找到任何包")

    # 添加新源
    print("\n3. 添加新的PyPI源:")
    try:
        new_source = PyPISource(
            name="tsinghua-pypi",
            url="https://pypi.tsinghua.edu.cn/simple",
            priority=50,
            group="china",
        )
        if dependency_manager.source_manager.add_source(new_source):
            print("  成功添加清华PyPI源")
        else:
            print("  添加源失败，可能已存在")
    except Exception as e:
        print(f"  添加源失败: {e}")

    # 切换源
    print("\n4. 切换到清华源:")
    if dependency_manager.switch_source("tsinghua-pypi", "pip"):
        print("  成功切换到清华源")
    else:
        print("  切换源失败")

    # 检查更新
    print("\n5. 检查包更新:")
    updates = dependency_manager.check_updates(installer_type="pip")
    if updates:
        print(f"  发现{len(updates)}个可更新的包:")
        for pkg in updates[:3]:  # 只显示前3个
            print(
                f"  - {pkg['name']}: {pkg.get('current', '?')} -> {pkg.get('latest', '?')}"
            )
        if len(updates) > 3:
            print(f"  ... 共{len(updates)}个包可更新")
    else:
        print("  未发现可更新的包")

    # 安装包示例
    print("\n6. 安装包示例(不实际执行):")
    print("  dependency_manager.install('requests', installer_type='pip')")
    print("  依赖管理器会自动选择最佳源并安装")

    # 卸载包示例
    print("\n7. 卸载包示例(不实际执行):")
    print("  dependency_manager.uninstall('unused-package', installer_type='pip')")

    # 获取系统状态
    print("\n8. 依赖管理系统状态:")
    status = dependency_manager.get_status()
    print(f"  - 已配置源数量: {len(status['sources'])}")
    print(f"  - 已加载安装器: {', '.join(status['installers'].keys())}")


if __name__ == "__main__":
    main()
