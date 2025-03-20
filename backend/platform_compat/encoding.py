"""
编码处理模块

提供跨平台的编码处理功能，处理Windows和Unix系统的编码差异。
"""

import os
import sys
import codecs
from pathlib import Path
from typing import Optional, Union, BinaryIO, cast, Any

try:
    import chardet  # type: ignore

    HAS_CHARDET = True
except ImportError:
    print("请安装chardet: pip install chardet")
    HAS_CHARDET = False


def get_system_encoding() -> str:
    """
    获取系统默认编码

    Returns:
        系统默认编码
    """
    if sys.platform == "win32":
        # Windows默认使用GBK编码
        return "gbk"
    else:
        # Unix系统默认使用UTF-8编码
        return "utf-8"


def get_file_encoding(file_path: Union[str, Path], default: str = "utf-8") -> str:
    """
    检测文件编码

    Args:
        file_path: 文件路径
        default: 默认编码

    Returns:
        文件编码
    """
    try:
        # 读取文件的前4KB来检测编码
        with open(file_path, "rb") as f:
            raw = f.read(4096)
            if not raw:
                return default

            # 检查BOM标记
            if raw.startswith(codecs.BOM_UTF8):
                return "utf-8-sig"
            elif raw.startswith(codecs.BOM_UTF16_LE):
                return "utf-16-le"
            elif raw.startswith(codecs.BOM_UTF16_BE):
                return "utf-16-be"
            elif raw.startswith(codecs.BOM_UTF32_LE):
                return "utf-32-le"
            elif raw.startswith(codecs.BOM_UTF32_BE):
                return "utf-32-be"

            # 使用chardet检测编码
            if HAS_CHARDET:
                result = chardet.detect(raw)
                if result["encoding"] and result["confidence"] > 0.7:
                    return result["encoding"].lower()

            # 如果没有chardet或检测结果不可靠，返回默认编码
            return default
    except Exception as e:
        print(f"检测文件编码失败: {e}")
        return default


def convert_to_utf8(
    content: Union[str, bytes], source_encoding: Optional[str] = None
) -> str:
    """
    将内容转换为UTF-8编码

    Args:
        content: 要转换的内容
        source_encoding: 源编码，如果为None则自动检测

    Returns:
        UTF-8编码的字符串
    """
    try:
        if isinstance(content, str):
            return content

        content_bytes = cast(bytes, content)  # 类型转换以满足mypy
        if not source_encoding:
            if HAS_CHARDET:
                result = chardet.detect(content_bytes)
                source_encoding = result["encoding"] if result["encoding"] else "utf-8"
            else:
                source_encoding = "utf-8"

        return content_bytes.decode(source_encoding)
    except Exception as e:
        print(f"转换到UTF-8失败: {e}")
        return content_bytes.decode("utf-8", errors="replace")


def normalize_newlines(content: str) -> str:
    """
    标准化换行符，统一使用LF

    Args:
        content: 要处理的内容

    Returns:
        标准化后的内容
    """
    # 将所有换行符转换为LF
    return content.replace("\r\n", "\n").replace("\r", "\n")


def get_bom_header(encoding: str) -> bytes:
    """
    获取指定编码的BOM标记

    Args:
        encoding: 编码名称

    Returns:
        BOM标记字节序列
    """
    encoding = encoding.lower()
    if encoding == "utf-8-sig":
        return codecs.BOM_UTF8
    elif encoding == "utf-16-le":
        return codecs.BOM_UTF16_LE
    elif encoding == "utf-16-be":
        return codecs.BOM_UTF16_BE
    elif encoding == "utf-32-le":
        return codecs.BOM_UTF32_LE
    elif encoding == "utf-32-be":
        return codecs.BOM_UTF32_BE
    else:
        return b""


def write_file_with_encoding(
    file_path: Union[str, Path],
    content: Union[str, bytes],
    encoding: str = "utf-8",
    add_bom: bool = False,
    newline: Optional[str] = None,
) -> bool:
    """
    以指定编码写入文件

    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 目标编码
        add_bom: 是否添加BOM标记
        newline: 换行符类型（None表示使用系统默认）

    Returns:
        是否写入成功
    """
    try:
        # 确保内容是字符串
        if isinstance(content, bytes):
            content = convert_to_utf8(content)

        # 标准化换行符
        content_str = cast(str, content)  # 类型转换以满足mypy
        if newline is None:
            content_str = normalize_newlines(content_str)
        elif newline == "\r\n":
            content_str = content_str.replace("\n", "\r\n")
        elif newline == "\r":
            content_str = content_str.replace("\n", "\r")

        # 写入文件
        mode = "wb" if add_bom else "w"
        with open(file_path, mode) as f:
            if add_bom:
                f.write(get_bom_header(encoding))
                f.write(content_str.encode(encoding))
            else:
                f.write(content_str)
        return True
    except Exception as e:
        print(f"写入文件失败: {e}")
        return False


def read_file_with_encoding(
    file_path: Union[str, Path],
    encoding: Optional[str] = None,
    normalize_nl: bool = True,
) -> Optional[str]:
    """
    以指定编码读取文件

    Args:
        file_path: 文件路径
        encoding: 文件编码，如果为None则自动检测
        normalize_nl: 是否标准化换行符

    Returns:
        文件内容，如果读取失败则返回None
    """
    try:
        # 如果没有指定编码，先检测文件编码
        if not encoding:
            encoding = get_file_encoding(file_path)

        # 读取文件内容
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()

        # 标准化换行符
        if normalize_nl:
            content = normalize_newlines(content)

        return content
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None
