#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库基础模型模块

提供基础ORM模型类和元数据定义
"""

import datetime
import uuid
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    ClassVar,
)

from sqlalchemy import Column, DateTime, Integer, String, inspect
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Query, Session

# 创建声明性基类
Base = declarative_base()

# 定义ModelMixin类型变量
M = TypeVar("M", bound="ModelMixin")
# 定义BaseModel类型变量
T = TypeVar("T", bound="BaseModel")
# 通用类型变量
K = TypeVar("K")

# 引入缓存装饰器
from .cache import cache_model


class ModelMixin:
    """模型公共功能混入类"""

    # 自动为表名添加前缀
    # 子类可以覆盖此类属性
    __table_prefix__: ClassVar[str] = ""

    # 自动为Id列设置名称
    # 子类可以覆盖此类属性
    __id_column__: ClassVar[str] = "id"

    # 排除的JSON字段
    # 子类可以覆盖此类属性
    __exclude_from_json__: ClassVar[set] = set(["_sa_instance_state"])

    @declared_attr
    def __tablename__(self) -> str:
        """自动生成表名"""
        # 将类名转换为蛇形命名
        cls_name = self.__class__.__name__
        name = "".join(
            ["_" + c.lower() if c.isupper() else c for c in cls_name]
        ).lstrip("_")
        # 添加表前缀
        prefix = getattr(self, "__table_prefix__", "")
        if prefix:
            name = f"{prefix}_{name}"
        return name

    @classmethod
    @cache_model(ttl=300)
    def get_by_id(cls: Type[M], session: Session, id_value: Any) -> Optional[M]:
        """
        通过ID获取记录

        Args:
            session: 数据库会话
            id_value: ID值

        Returns:
            找到的记录或None
        """
        return (
            session.query(cls)
            .filter(getattr(cls, cls.__id_column__) == id_value)
            .first()
        )

    @classmethod
    def get_all(cls: Type[M], session: Session) -> List[M]:
        """
        获取所有记录

        Args:
            session: 数据库会话

        Returns:
            记录列表
        """
        return session.query(cls).all()

    @classmethod
    def create(cls: Type[M], session: Session, **kwargs) -> M:
        """
        创建新记录

        Args:
            session: 数据库会话
            **kwargs: 模型字段值

        Returns:
            创建的记录
        """
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()
        return instance

    def update(self: M, session: Session, **kwargs) -> M:
        """
        更新记录

        Args:
            session: 数据库会话
            **kwargs: 要更新的字段值

        Returns:
            更新后的记录
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        session.flush()
        return self

    def delete(self, session: Session) -> None:
        """
        删除记录

        Args:
            session: 数据库会话
        """
        session.delete(self)
        session.flush()

    @classmethod
    def query(cls: Type[M], session: Session) -> Query:
        """
        获取查询对象

        Args:
            session: 数据库会话

        Returns:
            查询对象
        """
        return session.query(cls)

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        将模型转换为字典

        Args:
            exclude: 要排除的字段列表

        Returns:
            字典表示
        """
        if exclude is None:
            exclude = []

        result = {}
        for key, value in self.__dict__.items():
            if key in self.__exclude_from_json__ or key in exclude:
                continue

            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            elif isinstance(value, datetime.date):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)

            result[key] = value

        return result


class BaseModel(Base, ModelMixin):
    """
    基础模型类

    所有模型类的基类，提供通用字段和方法
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        """模型字符串表示"""
        pk = getattr(self, self.__id_column__)
        return f"<{self.__class__.__name__} {self.__id_column__}={pk}>"


class UUIDModel(Base, ModelMixin):
    """
    UUID主键模型类

    使用UUID作为主键的基类，提供通用字段和方法
    """

    __abstract__ = True
    __id_column__ = "id"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID主键",
    )
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        """模型字符串表示"""
        pk = getattr(self, self.__id_column__)
        pk_short = str(pk)[:8] + "..." if pk and len(str(pk)) > 8 else pk
        return f"<{self.__class__.__name__} {self.__id_column__}={pk_short}>"
