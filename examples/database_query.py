#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库查询构建器和缓存示例

演示如何使用查询构建器和缓存功能进行数据库操作
"""

import os
import sys
import time
from typing import List

# 添加项目根目录到PATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database import (
    session_scope,
    BaseModel,
    get_session,
    QueryBuilder,
    query,
    SortDirection,
    ModelCache,
    QueryCache,
    cached_query,
    get_registry,
)
from backend.database.models import User


def create_test_users() -> None:
    """创建测试用户数据"""
    with session_scope() as session:
        # 检查是否已经有用户
        if session.query(User).count() > 0:
            print("已存在测试用户，跳过创建")
            return

        # 创建测试用户
        for i in range(1, 11):
            user = User.create(
                session,
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash=f"hashed_password{i}",
                real_name=f"Test User {i}",
                is_active=True,
                is_admin=i == 1,  # 第一个用户是管理员
            )
            print(f"创建用户: {user.username}")


def demo_query_builder() -> None:
    """演示查询构建器的使用"""
    print("\n--- 查询构建器示例 ---")

    with session_scope() as session:
        # 创建查询构建器
        builder = QueryBuilder(User, session)

        # 构建查询: 查找活跃的非管理员用户
        users = (
            builder.filter(User.is_active == True, User.is_admin == False)
            .order_by_field("username", SortDirection.ASC)
            .limit(5)
            .all()
        )

        print(f"找到 {len(users)} 个活跃的非管理员用户:")
        for user in users:
            print(f"- {user.username} ({user.email})")

        # 使用helper函数简化查询
        active_admins = (
            query(User, session).filter_by(is_active=True, is_admin=True).all()
        )

        print(f"\n找到 {len(active_admins)} 个活跃的管理员用户:")
        for user in active_admins:
            print(f"- {user.username} ({user.email})")

        # 分页查询
        page, per_page = 1, 3
        items, total, pages, current_page = query(User, session).paginate(
            page, per_page
        )

        print(f"\n分页查询结果 (第 {current_page}/{pages} 页, 共 {total} 条记录):")
        for user in items:
            print(f"- {user.username} ({user.email})")


def demo_model_cache() -> None:
    """演示模型缓存的使用"""
    print("\n--- 模型缓存示例 ---")

    with session_scope() as session:
        # 获取缓存统计
        cache_stats = lambda: get_registry().get_cache("model").get_stats()

        # 查询前的缓存统计
        before_stats = cache_stats()

        # 第一次查询: 应该从数据库加载并缓存
        start_time = time.time()
        user1 = User.get_by_id(session, 1)
        first_query_time = time.time() - start_time

        if user1:
            print(f"第一次查询用户 {user1.username}: 耗时 {first_query_time:.6f} 秒")

        # 第二次查询: 应该从缓存加载
        start_time = time.time()
        user1_again = User.get_by_id(session, 1)
        second_query_time = time.time() - start_time

        if user1_again:
            print(
                f"第二次查询用户 {user1_again.username}: 耗时 {second_query_time:.6f} 秒"
            )
            print(f"加速比: {first_query_time / second_query_time:.2f}x")

        # 查询后的缓存统计
        after_stats = cache_stats()
        print(f"\n缓存统计:")
        print(f"- 缓存命中: {after_stats['hits'] - before_stats['hits']}")
        print(f"- 缓存未命中: {after_stats['misses'] - before_stats['misses']}")
        print(f"- 缓存设置: {after_stats['sets'] - before_stats['sets']}")


def demo_query_cache() -> None:
    """演示查询缓存的使用"""
    print("\n--- 查询缓存示例 ---")

    @cached_query(ttl=60)
    def find_active_users(session) -> List[User]:
        """查找活跃用户"""
        print("执行数据库查询...")
        return session.query(User).filter(User.is_active == True).all()

    with session_scope() as session:
        # 第一次调用: 执行数据库查询
        start_time = time.time()
        users1 = find_active_users(session)
        first_query_time = time.time() - start_time

        print(f"第一次查询返回 {len(users1)} 个用户, 耗时 {first_query_time:.6f} 秒")

        # 第二次调用: 应该使用缓存
        start_time = time.time()
        users2 = find_active_users(session)
        second_query_time = time.time() - start_time

        print(f"第二次查询返回 {len(users2)} 个用户, 耗时 {second_query_time:.6f} 秒")
        print(f"加速比: {first_query_time / second_query_time:.2f}x")

        # 查询缓存统计
        cache_stats = get_registry().get_cache("query").get_stats()
        print(f"\n查询缓存统计:")
        print(f"- 缓存命中: {cache_stats['hits']}")
        print(f"- 缓存未命中: {cache_stats['misses']}")
        print(f"- 缓存设置: {cache_stats['sets']}")


def main() -> None:
    """主函数"""
    # 创建测试数据
    create_test_users()

    # 演示查询构建器
    demo_query_builder()

    # 演示模型缓存
    demo_model_cache()

    # 演示查询缓存
    demo_query_cache()


if __name__ == "__main__":
    main()
