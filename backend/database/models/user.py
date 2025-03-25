#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户模型模块

定义用户相关的ORM模型
"""

import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

from ..base import BaseModel


class User(BaseModel):
    """
    用户模型

    存储用户基本信息
    """

    # 表前缀
    __table_prefix__ = "sys"

    # 表注释
    __table_args__ = {"comment": "系统用户表"}

    # 用户名
    username = Column(String(50), nullable=False, unique=True, comment="用户名")

    # 密码哈希
    password_hash = Column(String(128), nullable=False, comment="密码哈希")

    # 电子邮件
    email = Column(String(100), nullable=False, unique=True, comment="电子邮件")

    # 真实姓名
    real_name = Column(String(50), nullable=True, comment="真实姓名")

    # 手机号码
    phone = Column(String(20), nullable=True, comment="手机号码")

    # 用户状态
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 是否为管理员
    is_admin = Column(Boolean, default=False, comment="是否为管理员")

    # 最后登录时间
    last_login_at = Column("last_login_at", nullable=True, comment="最后登录时间")

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<User username={self.username}, email={self.email}>"

    @classmethod
    def get_by_username(cls, session, username: str) -> Optional["User"]:
        """
        通过用户名获取用户

        Args:
            session: 数据库会话
            username: 用户名

        Returns:
            用户对象或None
        """
        return session.query(cls).filter(cls.username == username).first()

    @classmethod
    def get_by_email(cls, session, email: str) -> Optional["User"]:
        """
        通过电子邮件获取用户

        Args:
            session: 数据库会话
            email: 电子邮件

        Returns:
            用户对象或None
        """
        return session.query(cls).filter(cls.email == email).first()

    def check_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码

        Returns:
            密码是否正确
        """
        # 实际项目中，应该使用专门的密码哈希库进行验证
        # 这里为了示例，仅返回None
        return False

    def set_password(self, password: str) -> None:
        """
        设置密码

        Args:
            password: 明文密码
        """
        # 实际项目中，应该使用专门的密码哈希库进行哈希
        # 这里为了示例，仅设置一个占位符
        self.password_hash = f"hashed_{password}"
