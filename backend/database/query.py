#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库查询构建器

提供流式API简化复杂查询构建，支持条件查询、排序、分页等操作
"""

import datetime
import inspect
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union, cast

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import ClauseElement

from .base import BaseModel

# 定义类型变量
T = TypeVar("T", bound=BaseModel)


class SortDirection(str, Enum):
    """排序方向枚举"""

    ASC = "asc"
    DESC = "desc"


class QueryBuilder(Generic[T]):
    """
    查询构建器

    提供流式API简化查询构建
    """

    def __init__(self, model_class: Type[T], session: Session):
        """
        初始化查询构建器

        Args:
            model_class: 模型类
            session: 数据库会话
        """
        self._model_class = model_class
        self._session = session
        self._query = session.query(model_class)
        self._conditions: List[ClauseElement] = []
        self._order_by: List[Any] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._joins: List[Tuple[Any, Any]] = []
        self._group_by: List[Any] = []
        self._having: List[ClauseElement] = []
        self._distinct_on: Optional[List[Any]] = None

    def filter(self, *conditions: ClauseElement) -> "QueryBuilder[T]":
        """
        添加过滤条件

        Args:
            *conditions: 过滤条件

        Returns:
            查询构建器
        """
        self._conditions.extend(conditions)
        return self

    def filter_by(self, **kwargs) -> "QueryBuilder[T]":
        """
        通过关键字参数添加过滤条件

        Args:
            **kwargs: 字段名和值

        Returns:
            查询构建器
        """
        for key, value in kwargs.items():
            if value is not None:
                self._conditions.append(getattr(self._model_class, key) == value)
        return self

    def order_by(self, *criteria) -> "QueryBuilder[T]":
        """
        添加排序条件

        Args:
            *criteria: 排序条件

        Returns:
            查询构建器
        """
        self._order_by.extend(criteria)
        return self

    def order_by_field(
        self, field_name: str, direction: SortDirection = SortDirection.ASC
    ) -> "QueryBuilder[T]":
        """
        按字段名排序

        Args:
            field_name: 字段名
            direction: 排序方向

        Returns:
            查询构建器
        """
        field = getattr(self._model_class, field_name)
        if direction == SortDirection.DESC:
            self._order_by.append(desc(field))
        else:
            self._order_by.append(asc(field))
        return self

    def limit(self, value: int) -> "QueryBuilder[T]":
        """
        设置返回记录数上限

        Args:
            value: 上限值

        Returns:
            查询构建器
        """
        self._limit = value
        return self

    def offset(self, value: int) -> "QueryBuilder[T]":
        """
        设置偏移量

        Args:
            value: 偏移量

        Returns:
            查询构建器
        """
        self._offset = value
        return self

    def join(self, target, *props) -> "QueryBuilder[T]":
        """
        添加关联查询

        Args:
            target: 关联目标
            *props: 关联属性

        Returns:
            查询构建器
        """
        self._joins.append((target, props))
        return self

    def group_by(self, *criteria) -> "QueryBuilder[T]":
        """
        添加分组条件

        Args:
            *criteria: 分组条件

        Returns:
            查询构建器
        """
        self._group_by.extend(criteria)
        return self

    def having(self, *criteria) -> "QueryBuilder[T]":
        """
        添加HAVING条件

        Args:
            *criteria: HAVING条件

        Returns:
            查询构建器
        """
        self._having.extend(criteria)
        return self

    def distinct(self, *expressions) -> "QueryBuilder[T]":
        """
        设置去重表达式

        Args:
            *expressions: 去重表达式

        Returns:
            查询构建器
        """
        if expressions:
            self._distinct_on = list(expressions)
        return self

    def build(self) -> Query:
        """
        构建查询对象

        Returns:
            查询对象
        """
        query = self._query

        # 应用关联
        for target, props in self._joins:
            query = query.join(target, *props)

        # 应用条件
        if self._conditions:
            query = query.filter(and_(*self._conditions))

        # 应用去重
        if self._distinct_on is not None:
            query = query.distinct(*self._distinct_on)

        # 应用分组
        if self._group_by:
            query = query.group_by(*self._group_by)

        # 应用HAVING
        if self._having:
            query = query.having(*self._having)

        # 应用排序
        if self._order_by:
            query = query.order_by(*self._order_by)

        # 应用分页
        if self._limit is not None:
            query = query.limit(self._limit)

        if self._offset is not None:
            query = query.offset(self._offset)

        return query

    def count(self) -> int:
        """
        获取记录数

        Returns:
            记录数
        """
        return self.build().count()

    def first(self) -> Optional[T]:
        """
        获取第一条记录

        Returns:
            第一条记录或None
        """
        return self.build().first()

    def all(self) -> List[T]:
        """
        获取所有记录

        Returns:
            记录列表
        """
        return self.build().all()

    def paginate(
        self, page: int = 1, per_page: int = 20
    ) -> Tuple[List[T], int, int, int]:
        """
        分页查询

        Args:
            page: 页码，从1开始
            per_page: 每页记录数

        Returns:
            (记录列表, 总记录数, 总页数, 当前页码)
        """
        if page < 1:
            page = 1

        if per_page < 1:
            per_page = 1

        query = self.build()

        # 获取总记录数
        total = query.count()

        # 计算总页数
        pages = (total + per_page - 1) // per_page

        # 获取当前页记录
        items = query.limit(per_page).offset((page - 1) * per_page).all()

        return items, total, pages, page

    def exists(self) -> bool:
        """
        判断是否存在满足条件的记录

        Returns:
            是否存在
        """
        return self.build().limit(1).count() > 0

    def update(self, values: Dict[str, Any]) -> int:
        """
        更新记录

        Args:
            values: 更新值

        Returns:
            更新记录数
        """
        return self.build().update(values, synchronize_session=False)

    def delete(self) -> int:
        """
        删除记录

        Returns:
            删除记录数
        """
        return self.build().delete(synchronize_session=False)


def query(model_class: Type[T], session: Session) -> QueryBuilder[T]:
    """
    创建查询构建器

    Args:
        model_class: 模型类
        session: 数据库会话

    Returns:
        查询构建器
    """
    return QueryBuilder(model_class, session)
