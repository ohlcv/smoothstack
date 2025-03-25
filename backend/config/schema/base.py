#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置验证基类

定义配置验证的基础类和工具
"""

from typing import Any, Dict, List, Optional, Set, Type, Union
from pydantic import BaseModel, ValidationError, validator, root_validator


class SchemaError(Exception):
    """配置验证错误"""

    pass


class ConfigSchema(BaseModel):
    """
    配置验证基类

    提供配置验证的基本功能和接口
    """

    # 更新为Pydantic V2的配置方式
    model_config = {
        # 允许额外属性，不验证的属性会被保留
        "extra": "allow",
        # 启用任意类型验证，允许验证复杂类型
        "arbitrary_types_allowed": True,
        # 移除已废弃的smart_union选项
    }

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置字典

        Args:
            config: 要验证的配置字典

        Returns:
            验证后的配置字典

        Raises:
            SchemaError: 如果配置验证失败
        """
        try:
            # 使用 Pydantic 进行验证
            validated = cls(**config)
            # 返回验证后的字典
            return validated.dict(exclude_unset=True)
        except ValidationError as e:
            # 将 Pydantic 的验证错误转换为自定义错误
            errors = []
            for error in e.errors():
                location = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{location}: {error['msg']}")

            error_msg = "\n".join(errors)
            raise SchemaError(f"配置验证失败:\n{error_msg}")

    @classmethod
    def get_required_fields(cls) -> Set[str]:
        """
        获取必填字段列表

        Returns:
            必填字段名集合
        """
        required_fields = set()
        for field_name, field in cls.__fields__.items():
            if field.required:
                required_fields.add(field_name)
        return required_fields
