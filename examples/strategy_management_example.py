#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多容器策略管理示例

演示如何使用策略管理器创建、部署和管理多容器应用
"""

import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path

from backend.container_manager.strategy_manager import get_strategy_manager
from backend.container_manager.models.strategy import (
    DeploymentStrategy,
    ResourceAllocationPolicy,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("strategy_example")


def print_separator(title=None):
    """打印分隔符"""
    width = 80
    if title:
        print("\n" + "=" * 10 + f" {title} " + "=" * (width - len(title) - 12) + "\n")
    else:
        print("\n" + "=" * width + "\n")


def print_dict(data, indent=0):
    """漂亮地打印字典"""
    for key, value in data.items():
        if isinstance(value, dict):
            print(" " * indent + f"{key}:")
            print_dict(value, indent + 2)
        elif isinstance(value, list):
            print(" " * indent + f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    print_dict(item, indent + 2)
                else:
                    print(" " * (indent + 2) + f"- {item}")
        else:
            print(" " * indent + f"{key}: {value}")


def example_create_wordpress_strategy():
    """示例1: 创建WordPress策略"""
    print_separator("创建WordPress策略")

    strategy_manager = get_strategy_manager()

    # 检查是否已存在
    strategy_name = "wordpress-demo"
    strategy = strategy_manager.get_strategy(strategy_name)
    if strategy:
        logger.info(f"策略 '{strategy_name}' 已存在，将删除并重新创建")
        strategy_manager.delete_strategy(strategy_name)

    # 创建WordPress部署策略
    logger.info(f"创建策略 '{strategy_name}'")
    strategy = strategy_manager.create_strategy(
        name=strategy_name,
        description="WordPress示例部署，包含MySQL数据库和WordPress应用",
        restart_policy="unless-stopped",
    )

    # 添加MySQL容器配置
    mysql_config = {
        "name": "db",
        "image": "mysql:5.7",
        "environment": {
            "MYSQL_ROOT_PASSWORD": "wordpress",
            "MYSQL_DATABASE": "wordpress",
            "MYSQL_USER": "wordpress",
            "MYSQL_PASSWORD": "wordpress",
        },
        "volumes": ["mysql_data:/var/lib/mysql"],
        "is_critical": True,  # 标记为关键容器
    }
    strategy.add_container_config(mysql_config)
    logger.info("已添加MySQL容器配置")

    # 添加WordPress容器配置
    wordpress_config = {
        "name": "wordpress",
        "image": "wordpress:latest",
        "environment": {
            "WORDPRESS_DB_HOST": "db",
            "WORDPRESS_DB_USER": "wordpress",
            "WORDPRESS_DB_PASSWORD": "wordpress",
            "WORDPRESS_DB_NAME": "wordpress",
        },
        "ports": ["8080:80"],
        "volumes": ["wordpress_data:/var/www/html"],
    }
    strategy.add_container_config(wordpress_config)
    logger.info("已添加WordPress容器配置")

    # 添加依赖关系
    strategy.add_dependency("wordpress", "db")
    logger.info("已添加依赖关系: wordpress -> db")

    # 设置资源策略
    resource_policy = strategy.resource_policy

    # 全局资源限制
    resource_policy.global_limits = {"memory": "512m", "cpu": "0.5"}

    # MySQL特定资源限制
    resource_policy.container_specific_limits["db"] = {"memory": "256m", "cpu": "0.3"}

    # WordPress特定资源限制
    resource_policy.container_specific_limits["wordpress"] = {
        "memory": "256m",
        "cpu": "0.2",
    }

    # 保存策略
    strategy_manager.update_strategy(
        name=strategy_name,
        resource_policy=resource_policy.to_dict(),
    )
    logger.info("已设置资源策略")

    # 显示策略详情
    strategy_dict = strategy.to_dict()
    print("\n创建的策略详情:")
    print_dict(strategy_dict)

    return strategy_name


def example_deploy_strategy(strategy_name):
    """示例2: 部署策略"""
    print_separator("部署策略")

    strategy_manager = get_strategy_manager()

    # 部署策略
    deployment_name = f"{strategy_name}-instance"
    logger.info(f"部署策略 '{strategy_name}' 为 '{deployment_name}'")

    # 设置环境变量
    env_vars = {
        "db": {"MYSQL_ROOT_PASSWORD": "example_password"},
        "wordpress": {"WORDPRESS_DB_PASSWORD": "example_password"},
    }

    result = strategy_manager.deploy_strategy(
        strategy_name=strategy_name,
        deployment_name=deployment_name,
        environment_variables=env_vars,
    )

    # 检查部署结果
    if "error" in result:
        logger.error(f"部署失败: {result['error']}")
        return None

    if result.get("status") == "success":
        logger.info(f"部署成功: {result.get('message', '')}")
    elif result.get("status") == "partial":
        logger.warning(f"部分部署成功: {result.get('message', '')}")
        if result.get("errors"):
            logger.warning("错误详情:")
            for container, error in result["errors"].items():
                logger.warning(f"  {container}: {error}")
    else:
        logger.error(f"部署失败: {result.get('message', '')}")
        return None

    # 显示创建的容器
    if result.get("containers"):
        print("\n创建的容器:")
        for container, info in result["containers"].items():
            print(
                f"  {container}: {info['name']} ({info['id'][:12]}) - {info['status']}"
            )

    return deployment_name


def example_list_deployments():
    """示例3: 列出所有部署"""
    print_separator("列出所有部署")

    strategy_manager = get_strategy_manager()

    deployments = strategy_manager.list_strategy_deployments()
    if not deployments:
        logger.info("未找到策略部署")
        return

    print(f"找到 {len(deployments)} 个部署:")
    for deployment in deployments:
        print(f"\n部署名称: {deployment.get('deployment_name')}")
        print(f"策略名称: {deployment.get('strategy_name')}")
        print(f"状态: {deployment.get('status')}")
        print(f"容器数量: {deployment.get('container_count')}")
        print(f"创建时间: {deployment.get('created_at')}")

        if deployment.get("containers"):
            print("容器:")
            for container in deployment["containers"]:
                print(f"  - {container.get('name')} ({container.get('status')})")


def example_inspect_deployment(deployment_name):
    """示例4: 查看部署详情"""
    print_separator("查看部署详情")

    strategy_manager = get_strategy_manager()

    deployment = strategy_manager.inspect_deployment(deployment_name)

    if "error" in deployment:
        logger.error(f"查看部署详情失败: {deployment['error']}")
        return

    print(f"部署: {deployment['deployment_name']}")
    print(f"策略: {deployment['strategy_name']}")
    print(f"状态: {deployment['status']}")
    print(f"容器数量: {deployment['container_count']}")

    print("\n容器:")
    for container in deployment["containers"]:
        print(f"\n  名称: {container.get('name')}")
        print(f"  状态: {container.get('status')}")
        print(f"  镜像: {container.get('image')}")

        if container.get("networks"):
            print(f"  网络: {', '.join(container.get('networks', []))}")

        if container.get("ports"):
            print(f"  端口: {', '.join(container.get('ports', []))}")


def example_stop_deployment(deployment_name):
    """示例5: 停止部署"""
    print_separator("停止部署")

    strategy_manager = get_strategy_manager()

    logger.info(f"停止部署 '{deployment_name}'")
    result = strategy_manager.stop_strategy(deployment_name)

    if result.get("status") == "success":
        logger.info(result.get("message", "停止成功"))
    elif result.get("status") == "partial":
        logger.warning(result.get("message", "部分容器停止失败"))
        if result.get("errors"):
            logger.warning("错误详情:")
            for container, error in result["errors"].items():
                logger.warning(f"  {container}: {error}")
    else:
        logger.error(result.get("message", "停止失败"))


def example_remove_deployment(deployment_name):
    """示例6: 移除部署"""
    print_separator("移除部署")

    strategy_manager = get_strategy_manager()

    logger.info(f"移除部署 '{deployment_name}'")
    result = strategy_manager.remove_strategy_deployment(deployment_name, force=True)

    if result.get("status") == "success":
        logger.info(result.get("message", "移除成功"))
    elif result.get("status") == "partial":
        logger.warning(result.get("message", "部分容器移除失败"))
        if result.get("errors"):
            logger.warning("错误详情:")
            for container, error in result["errors"].items():
                logger.warning(f"  {container}: {error}")
    else:
        logger.error(result.get("message", "移除失败"))


def example_export_strategy(strategy_name):
    """示例7: 导出策略配置"""
    print_separator("导出策略配置")

    strategy_manager = get_strategy_manager()
    strategy = strategy_manager.get_strategy(strategy_name)

    if not strategy:
        logger.error(f"策略 '{strategy_name}' 不存在")
        return

    output_file = f"{strategy_name}_exported.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(strategy.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"策略 '{strategy_name}' 已导出到 {output_file}")
    except Exception as e:
        logger.error(f"导出策略失败: {e}")


def example_delete_strategy(strategy_name):
    """示例8: 删除策略"""
    print_separator("删除策略")

    strategy_manager = get_strategy_manager()

    logger.info(f"删除策略 '{strategy_name}'")
    success = strategy_manager.delete_strategy(strategy_name)

    if success:
        logger.info(f"成功删除策略 '{strategy_name}'")
    else:
        logger.error(f"删除策略 '{strategy_name}' 失败")


def run_all_examples():
    """运行所有示例"""
    # 示例1: 创建WordPress策略
    strategy_name = example_create_wordpress_strategy()

    # 示例2: 部署策略
    deployment_name = example_deploy_strategy(strategy_name)
    if not deployment_name:
        logger.error("部署失败，无法继续后续示例")
        return

    # 等待容器启动
    logger.info("等待容器启动...")
    time.sleep(5)

    # 示例3: 列出所有部署
    example_list_deployments()

    # 示例4: 查看部署详情
    example_inspect_deployment(deployment_name)

    # 示例5: 停止部署
    example_stop_deployment(deployment_name)

    # 示例6: 移除部署
    example_remove_deployment(deployment_name)

    # 示例7: 导出策略配置
    example_export_strategy(strategy_name)

    # 示例8: 删除策略
    example_delete_strategy(strategy_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="多容器策略管理示例")
    parser.add_argument("--example", type=int, help="运行特定示例 (1-8)")

    args = parser.parse_args()

    if args.example:
        if args.example == 1:
            example_create_wordpress_strategy()
        elif args.example == 2:
            strategy_name = "wordpress-demo"
            example_deploy_strategy(strategy_name)
        elif args.example == 3:
            example_list_deployments()
        elif args.example == 4:
            deployment_name = "wordpress-demo-instance"
            example_inspect_deployment(deployment_name)
        elif args.example == 5:
            deployment_name = "wordpress-demo-instance"
            example_stop_deployment(deployment_name)
        elif args.example == 6:
            deployment_name = "wordpress-demo-instance"
            example_remove_deployment(deployment_name)
        elif args.example == 7:
            strategy_name = "wordpress-demo"
            example_export_strategy(strategy_name)
        elif args.example == 8:
            strategy_name = "wordpress-demo"
            example_delete_strategy(strategy_name)
        else:
            logger.error(f"无效的示例编号: {args.example}")
    else:
        run_all_examples()
