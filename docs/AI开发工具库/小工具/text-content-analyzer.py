"""
文本内容分析工具 (Text Content Analyzer)

一个专门用于分析文本文件的工具，支持多种文本格式，包括:
- 纯文本文件 (*.txt)
- Markdown文件 (*.md)
- reStructuredText文件 (*.rst)
- 其他文本格式文件

功能特点:
- 基本统计: 字数、行数、段落数统计
- 结构分析: 标题层级、列表、表格等结构分析
- 关键词分析: 词频统计、关键词提取
- 链接分析: 检查链接有效性
- 格式一致性检查: 标点、空格使用一致性
- 重复内容检测: 发现文档内重复内容
"""

import os
import re
import fnmatch
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
from collections import Counter

# ================== 配置区域 ==================
CONFIG = {
    "target_path": r"C:\Users\Excoldinwarm\Desktop\Quant\CryptoSystem",  # 默认路径
    "output_format": "text",  # text/markdown/json
    "exclude_dirs": [
        "__pycache__",
        ".git",
        ".vscode",
        ".idea",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
    ],
    "exclude_files": [
        "*.pyc",
        "*.class",
        "*.o",
        "*.exe",
        "*.bin",
        "*.dll",
        "*.so",
        "*.a",
        "*.lib",
        "*.zip",
        "*.tar",
        "*.gz",
        "*.rar",
        "Thumbs.db",
        ".DS_Store",
    ],
    "include_patterns": ["*.txt", "*.md", "*.rst", "*.text", "*.markdown"],
    "show_hidden": False,
    "max_workers": 4,
    "max_file_size_mb": 10,
    "check_links": True,
    "find_duplicates": True,
    "extract_keywords": True,
    "min_keyword_length": 4,
    "max_keyword_count": 20,
}
# ================== 配置结束 ====================


@dataclass
class StructureInfo:
    """文本结构信息"""

    headings_count: int = 0
    heading_levels: Dict[int, int] = field(default_factory=dict)
    list_items_count: int = 0
    bullet_lists_count: int = 0
    numbered_lists_count: int = 0
    tables_count: int = 0
    code_blocks_count: int = 0
    blockquote_count: int = 0
    has_toc: bool = False


@dataclass
class LinkInfo:
    """链接信息"""

    total_links: int = 0
    external_links: int = 0
    internal_links: int = 0
    image_links: int = 0
    broken_links: List[str] = field(default_factory=list)


@dataclass
class ContentQuality:
    """内容质量指标"""

    has_duplicates: bool = False
    duplicate_paragraphs: List[str] = field(default_factory=list)
    inconsistent_punctuation: bool = False
    inconsistent_spacing: bool = False
    inconsistent_line_endings: bool = False


@dataclass
class FileStats:
    """文本文件统计信息"""

    word_count: int = 0
    character_count: int = 0
    character_count_no_spaces: int = 0
    line_count: int = 0
    paragraph_count: int = 0
    structure: StructureInfo = field(default_factory=StructureInfo)
    links: LinkInfo = field(default_factory=LinkInfo)
    quality: ContentQuality = field(default_factory=ContentQuality)
    top_keywords: List[Tuple[str, int]] = field(default_factory=list)
    unique_words_count: int = 0


@dataclass
class FileInfo:
    """文件信息"""

    path: str
    name: str
    type: str
    size: int
    stats: Optional[FileStats] = None


class TextAnalyzer:
    """文本分析器"""

    def __init__(self, file_path: Path, config: Dict):
        self.file_path = file_path
        self.config = config
        self.stats = FileStats()
        self.lines = []
        self.paragraphs = []

    def analyze(self) -> FileStats:
        """分析文本文件并返回统计信息"""
        if not self._read_file():
            return self.stats

        self._count_basics()
        self._analyze_structure()
        if self.config["check_links"]:
            self._analyze_links()
        self._analyze_quality()
        if self.config["extract_keywords"]:
            self._extract_keywords()

        return self.stats

    def _read_file(self) -> bool:
        """分块读取文件内容，成功返回True"""
        try:
            file_size = self.file_path.stat().st_size
            if file_size > self.config["max_file_size_mb"] * 1024 * 1024:
                return False

            self.lines = []
            self.paragraphs = []
            current_para = []
            content_buffer = ""  # 用于临时存储内容以进行结构分析

            with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:  # 逐行读取
                    line = line.rstrip("\n")
                    self.lines.append(line)
                    content_buffer += line + "\n"
                    if not line.strip() and current_para:
                        self.paragraphs.append("\n".join(current_para))
                        current_para = []
                    elif line.strip():
                        current_para.append(line)

                    # 限制内存使用
                    if len(content_buffer) > 1024 * 1024:  # 1MB缓冲区
                        content_buffer = content_buffer[-1024 * 1024 :]  # 保留最后1MB

                if current_para:
                    self.paragraphs.append("\n".join(current_para))

            self.content = content_buffer  # 用于后续分析的部分内容
            return True
        except Exception as e:
            print(f"读取文件错误: {self.file_path} - {str(e)}")
            return False

    def _count_basics(self):
        """计算基本统计数据"""
        self.stats.line_count = len(self.lines)
        self.stats.paragraph_count = len(self.paragraphs)
        self.stats.character_count = sum(len(line) for line in self.lines)
        self.stats.character_count_no_spaces = sum(
            len(re.sub(r"\s", "", line)) for line in self.lines
        )

        words = []
        for line in self.lines:
            words.extend(re.findall(r"\b\w+\b", line.lower()))
        self.stats.word_count = len(words)
        self.stats.unique_words_count = len(set(words))

    def _analyze_structure(self):
        """分析文档结构，仅支持Markdown"""
        is_markdown = self.file_path.suffix.lower() in [".md", ".markdown"]
        if not is_markdown:
            return

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)")
        list_bullet_pattern = re.compile(r"^\s*[-*+]\s+.+")
        list_numbered_pattern = re.compile(r"^\s*\d+\.\s+.+")
        table_row_pattern = re.compile(r"^\s*\|.+\|\s*$")
        table_separator_pattern = re.compile(r"^\s*\|[\s\-:|]+\|\s*$")
        code_block_pattern = re.compile(r"^\s*```")
        blockquote_pattern = re.compile(r"^\s*>\s")

        in_list = False
        current_list_type = None
        in_table = False
        in_code_block = False
        in_blockquote = False

        for i, line in enumerate(self.lines):
            # 标题
            match = heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                self.stats.structure.headings_count += 1
                self.stats.structure.heading_levels[level] = (
                    self.stats.structure.heading_levels.get(level, 0) + 1
                )

            # 列表
            bullet_match = list_bullet_pattern.match(line)
            numbered_match = list_numbered_pattern.match(line)
            if bullet_match:
                self.stats.structure.list_items_count += 1
                if not in_list or current_list_type != "bullet":
                    self.stats.structure.bullet_lists_count += 1
                    in_list = True
                    current_list_type = "bullet"
            elif numbered_match:
                self.stats.structure.list_items_count += 1
                if not in_list or current_list_type != "numbered":
                    self.stats.structure.numbered_lists_count += 1
                    in_list = True
                    current_list_type = "numbered"
            elif not line.strip():
                in_list = False
                current_list_type = None

            # 表格
            if table_separator_pattern.match(line):
                prev_is_table = i > 0 and table_row_pattern.match(self.lines[i - 1])
                next_is_table = i < len(self.lines) - 1 and table_row_pattern.match(
                    self.lines[i + 1]
                )
                if prev_is_table and next_is_table and not in_table:
                    self.stats.structure.tables_count += 1
                    in_table = True
            elif not line.strip():
                in_table = False

            # 代码块
            if code_block_pattern.match(line):
                if not in_code_block:
                    self.stats.structure.code_blocks_count += 1
                    in_code_block = True
                else:
                    in_code_block = False

            # 引用块
            if blockquote_pattern.match(line):
                if not in_blockquote:
                    self.stats.structure.blockquote_count += 1
                    in_blockquote = True
            elif not line.strip():
                in_blockquote = False

    def _analyze_links(self):
        """分析文档中的链接"""
        if self.file_path.suffix.lower() not in [".md", ".markdown"]:
            return

        md_link_pattern = re.compile(r"$$ ([^ $$]+)\]$$ ([^)]+) $$")
        links = md_link_pattern.findall(self.content)
        self.stats.links.total_links = len(links)
        for _, url in links:
            if url.startswith(("http://", "https://", "ftp://", "mailto:")):
                self.stats.links.external_links += 1
            else:
                self.stats.links.internal_links += 1
            if " " in url or url.endswith((".", ",", ")", "]", "}")):
                self.stats.links.broken_links.append(url)

    def _analyze_quality(self):
        """分析内容质量"""
        if self.config["find_duplicates"] and len(self.paragraphs) > 1:
            self._find_duplicates()
        self._check_consistency()

    def _find_duplicates(self):
        """查找重复段落"""
        paragraph_hashes = {}
        for para in self.paragraphs:
            if len(para.strip()) > 50:
                normalized = re.sub(r"\s+", " ", para.lower()).strip()
                para_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()
                if para_hash in paragraph_hashes:
                    self.stats.quality.has_duplicates = True
                    if para not in self.stats.quality.duplicate_paragraphs:
                        self.stats.quality.duplicate_paragraphs.append(
                            para[:150] + "..." if len(para) > 150 else para
                        )
                else:
                    paragraph_hashes[para_hash] = True

    def _check_consistency(self):
        """检查格式一致性"""
        content = "\n".join(self.lines)
        quotation_marks = re.findall(r'[""\'\'`´]', content)
        if quotation_marks and len(set(quotation_marks)) > 2:
            self.stats.quality.inconsistent_punctuation = True

        space_before_comma = re.search(r"\s,", content) is not None
        no_space_before_comma = re.search(r"[^\s],", content) is not None
        if space_before_comma and no_space_before_comma:
            self.stats.quality.inconsistent_spacing = True

        line_endings = set()
        if "\r\n" in content:
            line_endings.add("CRLF")
        if "\n" in content and "\r\n" not in content:
            line_endings.add("LF")
        if len(line_endings) > 1:
            self.stats.quality.inconsistent_line_endings = True

    def _extract_keywords(self):
        """提取文档关键词"""
        words = []
        for line in self.lines:
            words.extend(
                [
                    w
                    for w in re.findall(r"\b\w+\b", line.lower())
                    if len(w) >= self.config["min_keyword_length"]
                ]
            )
        word_freq = Counter(words)
        self.stats.top_keywords = word_freq.most_common(
            self.config["max_keyword_count"]
        )


class TextProjectAnalyzer:
    """文本项目分析器"""

    def __init__(self, config: Dict):
        self.config = config
        self.root_path = Path(config["target_path"]).resolve()

    def analyze(self) -> Dict:
        result = {
            "structure": [],
            "files": {},
            "total": {
                "file_count": 0,
                "total_size": 0,
                "word_count": 0,
                "character_count": 0,
                "line_count": 0,
                "paragraph_count": 0,
                "headings_count": 0,
                "tables_count": 0,
                "code_blocks_count": 0,
                "link_count": 0,
                "top_keywords": [],
            },
            "file_types": {},
        }

        all_keywords = Counter()
        for root, dirs, files in os.walk(self.root_path, topdown=True):
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]
            current_path = Path(root).relative_to(self.root_path)
            current_dir = self._create_dir_entry(current_path)

            with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
                futures = [
                    executor.submit(self._analyze_file, Path(root) / f)
                    for f in files
                    if self._should_process_file(f)
                ]
                for future in as_completed(futures):
                    file_info = future.result()
                    if file_info and file_info.stats:
                        current_dir["children"].append(
                            {
                                "name": file_info.name,
                                "path": file_info.path,
                                "type": "file",
                                "size": file_info.size,
                            }
                        )
                        result["files"][file_info.path] = {
                            "name": file_info.name,
                            "type": file_info.type,
                            "size": file_info.size,
                            "stats": asdict(file_info.stats),
                        }
                        self._update_totals(result["total"], file_info)
                        file_ext = Path(file_info.name).suffix.lower()
                        if file_ext:
                            result["file_types"][file_ext] = (
                                result["file_types"].get(file_ext, 0) + 1
                            )
                        if file_info.stats.top_keywords:
                            for word, count in file_info.stats.top_keywords:
                                all_keywords[word] += count

            if current_dir["children"] or current_path == Path("."):
                result["structure"].append(current_dir)

        result["total"]["top_keywords"] = all_keywords.most_common(
            self.config["max_keyword_count"]
        )
        return result

    def _should_exclude_dir(self, dir_name: str) -> bool:
        if not self.config["show_hidden"] and dir_name.startswith("."):
            return True
        return any(fnmatch.fnmatch(dir_name, p) for p in self.config["exclude_dirs"])

    def _should_process_file(self, file_name: str) -> bool:
        if not self.config["show_hidden"] and file_name.startswith("."):
            return False
        if any(fnmatch.fnmatch(file_name, p) for p in self.config["exclude_files"]):
            return False
        return any(
            fnmatch.fnmatch(file_name, p) for p in self.config["include_patterns"]
        )

    def _create_dir_entry(self, rel_path: Path) -> Dict:
        return {
            "path": str(rel_path),
            "name": rel_path.name if rel_path != Path(".") else self.root_path.name,
            "type": "directory",
            "children": [],
        }

    def _analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        try:
            rel_path = str(file_path.relative_to(self.root_path))
            file_info = FileInfo(
                path=rel_path,
                name=file_path.name,
                type=file_path.suffix.lower()[1:] if file_path.suffix else "unknown",
                size=file_path.stat().st_size,
            )
            analyzer = TextAnalyzer(file_path, self.config)
            file_info.stats = analyzer.analyze()
            return file_info
        except Exception as e:
            print(f"分析文件错误: {file_path} - {str(e)}")
            return None

    def _update_totals(self, total: Dict, file_info: FileInfo):
        stats = file_info.stats
        total["file_count"] += 1
        total["total_size"] += file_info.size
        total["word_count"] += stats.word_count
        total["character_count"] += stats.character_count
        total["line_count"] += stats.line_count
        total["paragraph_count"] += stats.paragraph_count
        total["headings_count"] += stats.structure.headings_count
        total["tables_count"] += stats.structure.tables_count
        total["code_blocks_count"] += stats.structure.code_blocks_count
        total["link_count"] += stats.links.total_links


class OutputFormatter:
    """格式化分析结果输出"""

    @staticmethod
    def format(result: Dict, config: Dict) -> str:
        formatters = {
            "text": OutputFormatter._text_format,
            "markdown": OutputFormatter._markdown_format,
            "json": OutputFormatter._json_format,
        }
        return formatters[config["output_format"]](result, config)

    @staticmethod
    def _text_format(result: Dict, config: Dict) -> str:
        output = ["===== 文本内容分析 =====\n"]
        output.append("=== 项目结构 ===")
        for entry in result["structure"]:
            OutputFormatter._format_entry(entry, result, output, 0)

        total = result["total"]
        output.append("\n=== 项目摘要 ===")
        output.append(f"分析的文件数: {total['file_count']}")
        output.append(f"总大小: {OutputFormatter._format_size(total['total_size'])}")
        output.append(f"总单词数: {total['word_count']:,}")
        output.append(f"总字符数: {total['character_count']:,}")
        output.append(f"总行数: {total['line_count']:,}")
        output.append(f"总段落数: {total['paragraph_count']:,}")

        if (
            total["headings_count"]
            or total["tables_count"]
            or total["code_blocks_count"]
        ):
            output.append("\n=== 结构元素统计 ===")
            if total["headings_count"]:
                output.append(f"标题总数: {total['headings_count']}")
            if total["tables_count"]:
                output.append(f"表格总数: {total['tables_count']}")
            if total["code_blocks_count"]:
                output.append(f"代码块总数: {total['code_blocks_count']}")
            if total["link_count"]:
                output.append(f"链接总数: {total['link_count']}")

        if total["top_keywords"]:
            output.append("\n=== 最常见的关键词 ===")
            for word, count in total["top_keywords"]:
                output.append(f"{word}: {count} 次")

        return "\n".join(output)

    @staticmethod
    def _format_entry(entry: Dict, result: Dict, output: List, level: int):
        indent = "    " * level
        prefix = f"{indent}|-- "
        if entry["type"] == "directory":
            output.append(f"{prefix}{entry['name']}/")
            for child in sorted(
                entry.get("children", []), key=lambda x: (x["type"], x["name"])
            ):
                OutputFormatter._format_entry_child(child, result, output, level + 1)
        else:
            file_info = OutputFormatter._file_info(
                entry, result["files"].get(entry["path"], {})
            )
            output.append(f"{prefix}{entry['name']} {file_info}")

    @staticmethod
    def _format_entry_child(entry: Dict, result: Dict, output: List, level: int):
        indent = "    " * level
        prefix = f"{indent}|-- "
        file_info = result["files"].get(entry["path"], {})
        info_str = OutputFormatter._file_info(entry, file_info)
        output.append(f"{prefix}{entry['name']} {info_str}")

    @staticmethod
    def _file_info(entry: Dict, file_info: Dict) -> str:
        info = []
        stats = file_info.get("stats", {})
        if stats.get("word_count", 0) > 0:
            info.append(f"{stats['word_count']:,}词")
        if stats.get("line_count", 0) > 0:
            info.append(f"{stats['line_count']:,}行")
        if entry.get("size"):
            info.append(f"{OutputFormatter._format_size(entry['size'])}")
        return f"({', '.join(info)})" if info else ""

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"

    @staticmethod
    def _markdown_format(result: Dict, config: Dict) -> str:
        output = ["# 文本内容分析报告\n", "## 项目摘要"]
        total = result["total"]
        output.append(f"- **分析的文件数**: {total['file_count']}")
        output.append(
            f"- **总大小**: {OutputFormatter._format_size(total['total_size'])}"
        )
        output.append(f"- **总单词数**: {total['word_count']:,}")
        output.append(f"- **总字符数**: {total['character_count']:,}")
        output.append(f"- **总行数**: {total['line_count']:,}")
        output.append(f"- **总段落数**: {total['paragraph_count']:,}")
        if total["top_keywords"]:
            output.append("\n## 最常见的关键词")
            output.append("| 关键词 | 出现次数 |")
            output.append("|--------|----------|")
            for word, count in total["top_keywords"]:
                output.append(f"| {word} | {count} |")
        return "\n".join(output)

    @staticmethod
    def _json_format(result: Dict, config: Dict) -> str:
        return json.dumps(result, indent=2, ensure_ascii=False)


def parse_args():
    parser = argparse.ArgumentParser(description="文本内容分析工具")
    parser.add_argument("path", nargs="?", default=".", help="要分析的文本项目路径")
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="输出格式",
    )
    parser.add_argument("--max-workers", type=int, default=4, help="最大并行工作线程数")
    parser.add_argument(
        "--max-file-size", type=int, default=10, help="最大文件大小(MB)"
    )
    args = parser.parse_args()

    CONFIG["target_path"] = args.path
    CONFIG["output_format"] = args.format
    CONFIG["max_workers"] = args.max_workers
    CONFIG["max_file_size_mb"] = args.max_file_size
    return args


if __name__ == "__main__":
    try:
        args = parse_args()
        analyzer = TextProjectAnalyzer(CONFIG)
        result = analyzer.analyze()
        print(OutputFormatter.format(result, CONFIG))
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"错误: {str(e)}")
