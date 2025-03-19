#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文档生成器

从配置验证器中提取信息，生成配置文档
"""

import os
import json
import yaml
import inspect
from typing import Any, Dict, List, Optional, Set, Type, Union
from pathlib import Path
from enum import Enum

from .schema import (
    ConfigSchema,
    AppConfigSchema,
    DatabaseConfigSchema,
    ApiConfigSchema,
    LoggingConfigSchema,
    SecurityConfigSchema,
)


class DocumentFormat(str, Enum):
    """文档格式枚举"""

    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    HTML = "html"


class ConfigDocsGenerator:
    """
    配置文档生成器

    从配置验证器中提取信息，生成不同格式的配置文档
    """

    def __init__(self):
        """初始化文档生成器"""
        # 配置验证器映射
        self.validators = {
            "app": AppConfigSchema,
            "database": DatabaseConfigSchema,
            "api": ApiConfigSchema,
            "logging": LoggingConfigSchema,
            "security": SecurityConfigSchema,
        }

    def generate_docs(
        self,
        format: DocumentFormat = DocumentFormat.MARKDOWN,
        output_file: Optional[str] = None,
    ) -> str:
        """
        生成配置文档

        Args:
            format: 文档格式
            output_file: 输出文件路径，如果不指定则返回生成的文档字符串

        Returns:
            生成的文档内容
        """
        # 调用对应的文档生成方法
        if format == DocumentFormat.MARKDOWN:
            content = self._generate_markdown()
        elif format == DocumentFormat.JSON:
            content = self._generate_json()
        elif format == DocumentFormat.YAML:
            content = self._generate_yaml()
        elif format == DocumentFormat.HTML:
            content = self._generate_html()
        else:
            raise ValueError(f"不支持的文档格式: {format}")

        # 如果指定了输出文件，则写入文件
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def _get_schema_info(self, schema_class: Type[ConfigSchema]) -> Dict[str, Any]:
        """
        获取配置验证器的信息

        Args:
            schema_class: 配置验证器类

        Returns:
            包含字段信息的字典
        """
        result = {
            "name": schema_class.__name__,
            "description": inspect.getdoc(schema_class),
            "fields": {},
        }

        # 遍历所有字段
        for field_name, field in schema_class.__fields__.items():
            field_info = {
                "type": self._get_field_type(field),
                "description": field.field_info.description,
                "default": field.default if field.default is not ... else None,
                "required": field.required,
            }

            # 添加范围限制信息
            if hasattr(field.field_info, "ge") and field.field_info.ge is not None:
                field_info["min"] = field.field_info.ge
            if hasattr(field.field_info, "le") and field.field_info.le is not None:
                field_info["max"] = field.field_info.le

            # 如果是枚举类型，添加可选值
            if hasattr(field.type_, "__members__"):
                field_info["choices"] = list(field.type_.__members__.keys())

            result["fields"][field_name] = field_info

        return result

    def _get_field_type(self, field) -> str:
        """
        获取字段类型的字符串表示

        Args:
            field: Pydantic字段

        Returns:
            字段类型的字符串表示
        """
        # 处理枚举类型
        if hasattr(field.type_, "__members__"):
            return f"Enum({', '.join(field.type_.__members__.keys())})"

        # 处理列表类型
        if hasattr(field.type_, "__origin__") and field.type_.__origin__ is list:
            inner_type = field.type_.__args__[0].__name__
            return f"List[{inner_type}]"

        # 处理可选类型
        if hasattr(field.type_, "__origin__") and field.type_.__origin__ is Union:
            if type(None) in field.type_.__args__:
                inner_types = [
                    t.__name__ for t in field.type_.__args__ if t is not type(None)
                ]
                return f"Optional[{', '.join(inner_types)}]"

        # 处理基本类型
        return field.type_.__name__

    def _generate_markdown(self) -> str:
        """
        生成Markdown格式的文档

        Returns:
            Markdown文档内容
        """
        lines = ["# Smoothstack 配置文档", ""]
        lines.append("本文档自动从配置验证器中生成，包含所有配置项的详细信息。")
        lines.append("")

        # 添加目录
        lines.append("## 目录")
        lines.append("")
        for section_name in self.validators:
            schema_class = self.validators[section_name]
            section_title = schema_class.__name__.replace("ConfigSchema", "")
            lines.append(f"- [{section_title}配置](#user-content-{section_name}配置)")
        lines.append("")

        # 遍历所有配置部分
        for section_name, schema_class in self.validators.items():
            schema_info = self._get_schema_info(schema_class)

            # 添加部分标题和描述
            section_title = schema_class.__name__.replace("ConfigSchema", "")
            lines.append(f"## {section_title}配置 {{{section_name}}}")
            lines.append("")
            lines.append(
                schema_info["description"].split("\n")[0]
            )  # 只取第一行作为简介
            lines.append("")

            # 添加字段表格
            lines.append("| 配置项 | 类型 | 默认值 | 必填 | 描述 |")
            lines.append("| --- | --- | --- | --- | --- |")

            # 遍历所有字段
            for field_name, field_info in schema_info["fields"].items():
                # 格式化默认值
                default_value = field_info["default"]
                if default_value is None and field_info["required"]:
                    default_str = "无（必填）"
                elif default_value is None:
                    default_str = "无"
                elif isinstance(default_value, str):
                    default_str = f'`"{default_value}"`'
                elif isinstance(default_value, (list, dict)):
                    default_str = f"`{json.dumps(default_value, ensure_ascii=False)}`"
                else:
                    default_str = f"`{default_value}`"

                # 格式化必填状态
                required_str = "是" if field_info["required"] else "否"

                # 格式化描述，添加范围限制和可选值信息
                description = field_info["description"]
                if "min" in field_info and "max" in field_info:
                    description += (
                        f"<br>范围：{field_info['min']} ~ {field_info['max']}"
                    )
                elif "min" in field_info:
                    description += f"<br>最小值：{field_info['min']}"
                elif "max" in field_info:
                    description += f"<br>最大值：{field_info['max']}"

                if "choices" in field_info:
                    description += f"<br>可选值：{', '.join(field_info['choices'])}"

                # 添加字段行
                lines.append(
                    f"| {field_name} | {field_info['type']} | {default_str} | {required_str} | {description} |"
                )

            lines.append("")

        # 添加使用示例
        lines.append("## 使用示例")
        lines.append("")
        lines.append("### YAML配置文件")
        lines.append("")
        lines.append("```yaml")
        lines.append("# 应用配置")
        lines.append("app:")
        lines.append('  name: "my-app"')
        lines.append('  version: "1.0.0"')
        lines.append("  debug: true")
        lines.append("")
        lines.append("# 数据库配置")
        lines.append("database:")
        lines.append('  url: "sqlite:///data/my-app.db"')
        lines.append("  pool_size: 10")
        lines.append("```")
        lines.append("")
        lines.append("### 环境变量")
        lines.append("")
        lines.append("```bash")
        lines.append("# 应用环境")
        lines.append("ENV=development")
        lines.append("")
        lines.append("# 应用配置")
        lines.append("SMOOTHSTACK_APP_NAME=my-app")
        lines.append("SMOOTHSTACK_APP_VERSION=1.0.0")
        lines.append("SMOOTHSTACK_APP_DEBUG=true")
        lines.append("")
        lines.append("# 数据库配置")
        lines.append("SMOOTHSTACK_DATABASE_URL=sqlite:///data/my-app.db")
        lines.append("SMOOTHSTACK_DATABASE_POOL_SIZE=10")
        lines.append("```")
        lines.append("")
        lines.append("### Python代码中访问配置")
        lines.append("")
        lines.append("```python")
        lines.append("from smoothstack.config import config")
        lines.append("")
        lines.append("# 获取配置值")
        lines.append('app_name = config.get("app.name")')
        lines.append('db_url = config.get("database.url")')
        lines.append("")
        lines.append("# 设置配置值")
        lines.append('config.set("app.debug", True)')
        lines.append("```")

        return "\n".join(lines)

    def _generate_json(self) -> str:
        """
        生成JSON格式的文档

        Returns:
            JSON文档内容
        """
        result = {
            "title": "Smoothstack配置文档",
            "description": "自动从配置验证器中生成的配置文档",
            "sections": {},
        }

        # 遍历所有配置部分
        for section_name, schema_class in self.validators.items():
            result["sections"][section_name] = self._get_schema_info(schema_class)

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _generate_yaml(self) -> str:
        """
        生成YAML格式的文档

        Returns:
            YAML文档内容
        """
        result = {
            "title": "Smoothstack配置文档",
            "description": "自动从配置验证器中生成的配置文档",
            "sections": {},
        }

        # 遍历所有配置部分
        for section_name, schema_class in self.validators.items():
            result["sections"][section_name] = self._get_schema_info(schema_class)

        return yaml.dump(result, sort_keys=False, allow_unicode=True)

    def _generate_html(self) -> str:
        """
        生成HTML格式的文档

        Returns:
            HTML文档内容
        """
        # 先生成Markdown，然后尝试转换为HTML
        try:
            import markdown

            md_content = self._generate_markdown()
            html_content = markdown.markdown(
                md_content, extensions=["tables", "fenced_code"]
            )

            # 添加基本的HTML结构和样式
            return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smoothstack配置文档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #0066cc;
            margin-top: 24px;
        }}
        h1 {{
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: Consolas, Monaco, "Andale Mono", monospace;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""
        except ImportError:
            # 如果没有markdown模块，返回简单的HTML
            return f"<html><body><pre>{self._generate_markdown()}</pre></body></html>"


# 用于命令行执行
def main():
    """命令行入口点"""
    import argparse

    parser = argparse.ArgumentParser(description="生成Smoothstack配置文档")
    parser.add_argument(
        "--format",
        "-f",
        choices=[f.value for f in DocumentFormat],
        default=DocumentFormat.MARKDOWN.value,
        help="文档格式",
    )
    parser.add_argument(
        "--output", "-o", help="输出文件路径，如果不指定则输出到标准输出"
    )

    args = parser.parse_args()

    generator = ConfigDocsGenerator()
    content = generator.generate_docs(format=args.format, output_file=args.output)

    if not args.output:
        print(content)


if __name__ == "__main__":
    main()
