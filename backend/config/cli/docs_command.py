#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文档生成命令行工具

提供从命令行生成配置文档的功能
"""

import os
import sys
import argparse
from pathlib import Path

# 确保可以导入配置模块
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config.docs_generator import ConfigDocsGenerator, DocumentFormat


def generate_docs():
    """生成配置文档的命令行工具"""
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
    parser.add_argument(
        "--open",
        "-p",
        action="store_true",
        help="生成后尝试打开文档（仅适用于指定了输出文件）",
    )

    args = parser.parse_args()

    # 创建文档生成器
    generator = ConfigDocsGenerator()

    # 确定格式
    doc_format = args.format
    for fmt in DocumentFormat:
        if fmt.value == doc_format:
            doc_format = fmt
            break

    # 生成文档
    content = generator.generate_docs(format=doc_format, output_file=args.output)

    # 如果没有指定输出文件，则输出到标准输出
    if not args.output:
        print(content)
    else:
        print(f"文档已生成: {args.output}")

        # 如果指定了 --open 参数，尝试打开文档
        if args.open:
            try:
                import webbrowser

                if doc_format == DocumentFormat.HTML:
                    # HTML文档，用浏览器打开
                    webbrowser.open(f"file://{os.path.abspath(args.output)}")
                else:
                    # 其他格式，尝试使用系统默认应用打开
                    if sys.platform.startswith("darwin"):  # macOS
                        os.system(f"open {args.output}")
                    elif sys.platform.startswith("win"):  # Windows
                        os.system(f"start {args.output}")
                    elif sys.platform.startswith("linux"):  # Linux
                        os.system(f"xdg-open {args.output}")
                    else:
                        print("无法自动打开文档，请手动打开。")
            except Exception as e:
                print(f"尝试打开文档时出错: {e}")


if __name__ == "__main__":
    generate_docs()
