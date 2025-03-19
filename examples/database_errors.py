#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库错误处理示例

演示如何使用错误处理机制处理数据库操作中的异常
"""

import os
import sys
import logging
from typing import List, Optional

# 添加项目根目录到PATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database import (
    session_scope,
    BaseModel,
    get_session,
    DatabaseError,
    QueryError,
    ValidationError,
    handle_database_error,
    safe_operation,
)
from backend.database.models import User

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@safe_operation("find_user")
def find_user(session, username: str) -> Optional[User]:
    """
    查找用户

    Args:
        session: 数据库会话
        username: 用户名

    Returns:
        用户对象或None

    Raises:
        QueryError: 查询执行错误
    """
    try:
        # 故意使用错误的SQL语法来触发异常
        result = session.execute(
            "SELECT * FORM users WHERE username = :username", {"username": username}
        )
        return result.first()
    except Exception as e:
        raise QueryError(
            message=f"Failed to find user: {username}",
            details={"username": username},
            cause=e,
        )


@safe_operation("create_user")
def create_user(session, username: str, email: str, password: str) -> User:
    """
    创建用户

    Args:
        session: 数据库会话
        username: 用户名
        email: 电子邮件
        password: 密码

    Returns:
        创建的用户对象

    Raises:
        ValidationError: 数据验证错误
    """
    # 验证用户名
    if not username or len(username) < 3:
        raise ValidationError(
            message="Invalid username",
            details={
                "field": "username",
                "value": username,
                "reason": "Username must be at least 3 characters long",
            },
        )

    # 验证电子邮件
    if not email or "@" not in email:
        raise ValidationError(
            message="Invalid email",
            details={
                "field": "email",
                "value": email,
                "reason": "Email must contain @",
            },
        )

    # 验证密码
    if not password or len(password) < 6:
        raise ValidationError(
            message="Invalid password",
            details={
                "field": "password",
                "reason": "Password must be at least 6 characters long",
            },
        )

    # 创建用户
    return User.create(
        session,
        username=username,
        email=email,
        password_hash=f"hashed_{password}",
        is_active=True,
    )


def demo_error_handling() -> None:
    """演示错误处理"""
    print("\n--- 错误处理示例 ---")

    with session_scope() as session:
        # 示例1：处理查询错误
        print("\n1. 处理查询错误:")
        try:
            user = find_user(session, "test_user")
            print(f"找到用户: {user}")
        except DatabaseError as e:
            print(f"查询错误: {e}")
            print(f"错误详情: {e.to_dict()}")

        # 示例2：处理验证错误
        print("\n2. 处理验证错误:")
        try:
            user = create_user(session, "", "invalid_email", "123")
            print(f"创建用户: {user}")
        except ValidationError as e:
            print(f"验证错误: {e}")
            print(f"错误详情: {e.to_dict()}")

        # 示例3：正常操作
        print("\n3. 正常操作:")
        try:
            user = create_user(session, "test_user", "test@example.com", "password123")
            print(f"创建用户成功: {user.username} ({user.email})")
        except DatabaseError as e:
            print(f"操作错误: {e}")


def main() -> None:
    """主函数"""
    try:
        demo_error_handling()
    except Exception as e:
        logger.exception("程序执行出错")


if __name__ == "__main__":
    main()
