#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目目录分析工具

功能：
- 递归分析项目目录结构
- 生成可视化目录树
- 统计各类文件分布
- 识别常见项目结构模式
- 分析文件大小分布
- 检测可能存在问题的目录结构

作者: Claude
版本: 1.0.0
"""

import os
import sys
import time
import json
import argparse
import datetime
import fnmatch
import re
import shutil
from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor


# ================== 配置 ==================
DEFAULT_CONFIG = {
    "target_path": ".",  # 默认为当前目录
    "output_format": "text",  # text/markdown/json/html
    "exclude_dirs": [
        "__pycache__",
        ".git",
        ".svn",
        ".hg",
        ".idea",
        ".vscode",
        "node_modules",
        "venv",
        "env",
        ".env",
        ".venv",
        "dist",
        "build",
        "target",  # Java/Rust 构建目录
        "bin",  # 二进制文件目录
        "obj",  # C# 构建目录
    ],
    "exclude_files": [
        "*.pyc",
        "*.pyo",
        "*.class",
        "*.o",
        "*.obj",
        "*.exe",
        "*.dll",
        "*.so",
        "*.dylib",
        "*.log",
        "*.tmp",
        "*.bak",
        "*.swp",
        "*.DS_Store",
        "Thumbs.db",
    ],
    "max_depth": 10,  # 最大递归深度
    "show_hidden": False,  # 是否显示隐藏文件和目录
    "size_limit": 100,  # 单个文件最大大小(MB)，超过则只记录大小不分析内容
    "max_workers": 4,  # 最大工作线程数
    "color_output": True,  # 彩色终端输出
    "detect_patterns": True,  # 检测项目结构模式
    "count_lines": False,  # 是否统计文本文件行数（可能较慢）
}


# ================== 文件类型配置 ==================
FILE_TYPES = {
    # 源代码文件
    "python": [".py", ".pyx", ".pyw", ".ipynb"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"],
    "java": [".java", ".kt", ".groovy", ".scala"],
    "c_cpp": [".c", ".cpp", ".h", ".hpp", ".cc", ".cxx"],
    "c_sharp": [".cs", ".vb"],
    "go": [".go"],
    "rust": [".rs"],
    "php": [".php", ".php3", ".php4", ".php5", ".phtml"],
    "ruby": [".rb", ".erb"],
    "swift": [".swift"],
    "shell": [".sh", ".bash", ".zsh", ".fish"],
    "powershell": [".ps1", ".psm1", ".psd1"],
    "sql": [".sql"],
    "r": [".r", ".R"],
    "markdown": [".md", ".markdown"],
    # 配置文件
    "config": [
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".conf",
        ".cfg",
        ".properties",
        ".env",
    ],
    # 文档
    "document": [
        ".txt",
        ".rtf",
        ".doc",
        ".docx",
        ".odt",
        ".pdf",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    ],
    # 网页相关
    "web": [".html", ".htm", ".xhtml", ".css", ".less", ".sass", ".scss"],
    # 图片
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"],
    # 音频
    "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"],
    # 视频
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    # 压缩文件
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    # 其他二进制文件
    "binary": [".bin", ".dat", ".exe", ".dll", ".so", ".dylib"],
}

# 映射文件类型到分组类别
FILE_GROUPS = {
    "代码文件": [
        "python",
        "javascript",
        "java",
        "c_cpp",
        "c_sharp",
        "go",
        "rust",
        "php",
        "ruby",
        "swift",
        "shell",
        "powershell",
        "sql",
        "r",
    ],
    "配置文件": ["config"],
    "文档文件": ["document", "markdown"],
    "Web文件": ["web"],
    "媒体文件": ["image", "audio", "video"],
    "存档文件": ["archive"],
    "二进制文件": ["binary"],
}

# 反向映射扩展名到文件类型
EXT_TO_TYPE = {}
for file_type, extensions in FILE_TYPES.items():
    for ext in extensions:
        EXT_TO_TYPE[ext] = file_type

# ================== 项目结构模式 ==================
PROJECT_PATTERNS = {
    "python_package": {
        "markers": ["setup.py", "requirements.txt", "pyproject.toml"],
        "dirs": ["tests", "docs"],
        "description": "Python包项目",
    },
    "django": {
        "markers": ["manage.py", "settings.py"],
        "dirs": ["templates", "static", "media"],
        "description": "Django Web项目",
    },
    "flask": {
        "markers": ["app.py", "wsgi.py"],
        "files_content": [("*.py", "from flask import")],
        "description": "Flask Web项目",
    },
    "react": {
        "markers": ["package.json"],
        "files_content": [("package.json", '"react":')],
        "dirs": ["src", "public"],
        "description": "React前端项目",
    },
    "vue": {
        "markers": ["package.json"],
        "files_content": [("package.json", '"vue":')],
        "description": "Vue.js前端项目",
    },
    "node": {
        "markers": ["package.json", "node_modules"],
        "dirs": ["src", "dist"],
        "description": "Node.js项目",
    },
    "maven": {
        "markers": ["pom.xml"],
        "dirs": ["src/main/java", "src/test/java"],
        "description": "Maven Java项目",
    },
    "gradle": {
        "markers": ["build.gradle", "settings.gradle", "gradlew"],
        "dirs": ["src/main/java", "src/test/java"],
        "description": "Gradle Java项目",
    },
    "android": {
        "markers": ["AndroidManifest.xml", "build.gradle"],
        "dirs": ["res", "java"],
        "description": "Android应用项目",
    },
    "ios": {
        "markers": ["Info.plist", "AppDelegate.swift", "AppDelegate.m"],
        "dirs": ["Assets.xcassets"],
        "description": "iOS应用项目",
    },
    "dotnet": {
        "markers": ["*.csproj", "*.sln"],
        "dirs": ["Properties", "Controllers"],
        "description": ".NET项目",
    },
    "laravel": {
        "markers": ["artisan", "composer.json"],
        "dirs": ["app", "resources", "routes"],
        "description": "Laravel PHP项目",
    },
    "rails": {
        "markers": ["Gemfile", "config/routes.rb"],
        "dirs": ["app", "config", "db"],
        "description": "Ruby on Rails项目",
    },
    "go_module": {
        "markers": ["go.mod", "go.sum"],
        "dirs": ["cmd", "pkg", "internal"],
        "description": "Go模块项目",
    },
    "rust_cargo": {
        "markers": ["Cargo.toml"],
        "dirs": ["src", "target"],
        "description": "Rust Cargo项目",
    },
    "docker": {
        "markers": ["Dockerfile", "docker-compose.yml"],
        "description": "Docker容器项目",
    },
    "jupyter": {"markers": ["*.ipynb"], "description": "Jupyter Notebook项目"},
}


# =================== 终端颜色支持 ===================
class Colors:
    """终端ANSI颜色代码"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    @staticmethod
    def supports_color():
        """检测当前终端是否支持颜色"""
        # Windows 10以上的cmd和PowerShell支持颜色
        # Linux和macOS终端通常支持颜色
        platform = sys.platform
        if platform == "win32":
            import platform as plat

            version = plat.version()  # 获取Windows版本字符串
            return int(version.split(".")[0]) >= 10
        return True

    @staticmethod
    def disable():
        """禁用颜色输出"""
        for attr in dir(Colors):
            if (
                not attr.startswith("_")
                and attr != "disable"
                and attr != "supports_color"
            ):
                setattr(Colors, attr, "")


# 如果终端不支持颜色，则禁用
if not Colors.supports_color():
    Colors.disable()


class DirectoryNode:
    """目录节点，用于构建目录树"""

    def __init__(self, name, path, is_dir=False, size=0):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.children = []
        self.depth = path.count(os.sep)

    def add_child(self, child):
        """添加子节点"""
        self.children.append(child)

    def get_size(self):
        """计算总大小（包括所有子节点）"""
        if not self.is_dir:
            return self.size
        return sum(child.get_size() for child in self.children)


class FileTypeStats:
    """文件类型统计"""

    def __init__(self):
        self.type_counts = defaultdict(int)
        self.type_sizes = defaultdict(int)
        self.extension_counts = defaultdict(int)
        self.largest_files = []  # 列表，每项为 (path, size)
        self.total_files = 0
        self.total_dirs = 0
        self.total_size = 0
        self.total_lines = 0
        self.empty_dirs = []
        self.problematic_names = []  # 可能有问题的文件/目录名
        self.top_level_dirs = []

    def update_type_stats(self, file_path, size):
        """更新文件类型统计"""
        self.total_files += 1
        self.total_size += size

        # 记录最大文件
        self.largest_files.append((file_path, size))
        self.largest_files.sort(key=lambda x: x[1], reverse=True)
        if len(self.largest_files) > 10:
            self.largest_files.pop()

        # 统计文件类型
        ext = os.path.splitext(file_path)[1].lower()
        self.extension_counts[ext] += 1

        # 映射到文件类型组
        file_type = EXT_TO_TYPE.get(ext, "其他")
        self.type_counts[file_type] += 1
        self.type_sizes[file_type] += size


class DirectoryAnalyzer:
    """目录分析器"""

    def __init__(self, config):
        self.config = config
        self.root_path = os.path.abspath(config["target_path"])
        self.stats = FileTypeStats()
        self.root_node = None
        self.patterns_detected = []
        self.start_time = time.time()
        self.max_name_lengths = {}  # 跟踪每个目录深度的最长文件名

    def analyze(self):
        """分析目录"""
        print(f"{Colors.CYAN}开始分析目录: {Colors.BOLD}{self.root_path}{Colors.RESET}")

        # 检查路径是否存在
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"目录不存在: {self.root_path}")

        # 创建根节点
        self.root_node = DirectoryNode(
            os.path.basename(self.root_path), self.root_path, True
        )

        # 扫描目录树
        self._scan_directory(self.root_path, self.root_node, 0)

        # 检测项目结构模式
        if self.config["detect_patterns"]:
            self._detect_project_patterns()

        # 记录顶级目录
        self._analyze_top_level()

        # 检测可能有问题的文件名
        self._find_problematic_names()

        return {
            "stats": {
                "total_files": self.stats.total_files,
                "total_dirs": self.stats.total_dirs,
                "total_size": self.stats.total_size,
                "total_lines": self.stats.total_lines,
                "type_counts": dict(self.stats.type_counts),
                "type_sizes": dict(self.stats.type_sizes),
                "extension_counts": dict(self.stats.extension_counts),
            },
            "largest_files": self.stats.largest_files,
            "empty_dirs": self.stats.empty_dirs,
            "problematic_names": self.stats.problematic_names,
            "patterns_detected": self.patterns_detected,
            "top_level_dirs": self.stats.top_level_dirs,
            "directory_tree": self.root_node,
        }

    def _scan_directory(self, dir_path, parent_node, depth):
        """递归扫描目录"""
        # 检查最大深度
        if depth > self.config["max_depth"]:
            return

        try:
            # 列出目录内容
            items = os.listdir(dir_path)

            # 空目录检查
            if not items:
                self.stats.empty_dirs.append(dir_path)
                return

            # 创建子目录和文件节点
            dirs = []
            files = []

            for item in items:
                # 跳过隐藏文件/目录
                if item.startswith(".") and not self.config["show_hidden"]:
                    continue

                item_path = os.path.join(dir_path, item)

                if os.path.isdir(item_path):
                    # 检查排除目录
                    if any(
                        fnmatch.fnmatch(item, pattern)
                        for pattern in self.config["exclude_dirs"]
                    ):
                        continue

                    # 创建目录节点
                    dir_node = DirectoryNode(item, item_path, True)
                    dirs.append((item_path, dir_node))
                    parent_node.add_child(dir_node)
                    self.stats.total_dirs += 1

                else:  # 文件
                    # 检查排除文件
                    if any(
                        fnmatch.fnmatch(item, pattern)
                        for pattern in self.config["exclude_files"]
                    ):
                        continue

                    # 获取文件大小
                    try:
                        size = os.path.getsize(item_path)
                    except (OSError, PermissionError):
                        size = 0

                    # 创建文件节点
                    file_node = DirectoryNode(item, item_path, False, size)
                    parent_node.add_child(file_node)
                    files.append(item_path)

                    # 更新统计信息
                    self.stats.update_type_stats(item_path, size)

                    # 跟踪最长文件名
                    name_length = len(item)
                    if name_length > self.max_name_lengths.get(depth, 0):
                        self.max_name_lengths[depth] = name_length

                    # 统计行数（可选）
                    if (
                        self.config["count_lines"]
                        and self._is_text_file(item_path)
                        and size < (self.config["size_limit"] * 1024 * 1024)
                    ):
                        try:
                            with open(
                                item_path, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                line_count = sum(1 for _ in f)
                                self.stats.total_lines += line_count
                        except:
                            pass  # 忽略读取错误

            # 递归处理子目录
            for dir_path, dir_node in dirs:
                self._scan_directory(dir_path, dir_node, depth + 1)

        except (PermissionError, OSError) as e:
            print(f"{Colors.YELLOW}警告: 无法访问目录 {dir_path}: {e}{Colors.RESET}")

    def _is_text_file(self, file_path):
        """判断文件是否为文本文件（基于扩展名）"""
        ext = os.path.splitext(file_path)[1].lower()
        text_file_types = [
            "python",
            "javascript",
            "java",
            "c_cpp",
            "c_sharp",
            "go",
            "rust",
            "php",
            "ruby",
            "swift",
            "shell",
            "powershell",
            "sql",
            "r",
            "config",
            "web",
            "markdown",
        ]

        file_type = EXT_TO_TYPE.get(ext)
        return file_type in text_file_types

    def _detect_project_patterns(self):
        """检测项目结构模式"""
        markers_found = defaultdict(int)
        dirs_found = defaultdict(int)

        # 查找标记文件和目录
        for root, dirs, files in os.walk(self.root_path):
            # 检查目录名
            for pattern_name, pattern_data in PROJECT_PATTERNS.items():
                pattern_dirs = pattern_data.get("dirs", [])
                for pattern_dir in pattern_dirs:
                    for d in dirs:
                        if fnmatch.fnmatch(d, pattern_dir):
                            dirs_found[(pattern_name, pattern_dir)] += 1

            # 检查文件名
            for pattern_name, pattern_data in PROJECT_PATTERNS.items():
                markers = pattern_data.get("markers", [])
                for marker in markers:
                    for file in files:
                        if fnmatch.fnmatch(file, marker):
                            markers_found[(pattern_name, marker)] += 1

            # 限制深度
            if root.count(os.sep) - self.root_path.count(os.sep) >= 2:
                dirs[:] = []  # 跳过更深层次的目录

        # 统计每个模式的匹配度
        pattern_scores = defaultdict(int)
        for (pattern_name, _), count in markers_found.items():
            pattern_scores[pattern_name] += count * 2  # 标记文件权重高

        for (pattern_name, _), count in dirs_found.items():
            pattern_scores[pattern_name] += count

        # 选择匹配度高的模式
        for pattern_name, score in sorted(
            pattern_scores.items(), key=lambda x: x[1], reverse=True
        ):
            if score >= 2:  # 至少需要一个强匹配或两个弱匹配
                self.patterns_detected.append(
                    {
                        "name": pattern_name,
                        "description": PROJECT_PATTERNS[pattern_name]["description"],
                        "confidence": min(
                            100, score * 10
                        ),  # 转换为百分比信心度，最高100%
                    }
                )

    def _find_problematic_names(self):
        """查找可能有问题的文件或目录名"""
        problem_patterns = [
            (r"[\s]+", "包含空格"),
            (r"[^\x00-\x7F]+", "包含非ASCII字符"),
            (r"[\\/:*?\"<>|]+", "包含特殊字符"),
            (r"^\.+$", "只包含点号"),
            (r"^[\s\.]", "以空格或点开头"),
            (r".{100,}", "名称过长(>100字符)"),
        ]

        for root, dirs, files in os.walk(self.root_path):
            # 检查目录名
            for d in dirs[:]:  # 创建副本防止修改迭代器
                for pattern, reason in problem_patterns:
                    if re.search(pattern, d):
                        full_path = os.path.join(root, d)
                        rel_path = os.path.relpath(full_path, self.root_path)
                        if rel_path != ".":
                            self.stats.problematic_names.append(
                                {
                                    "path": rel_path,
                                    "name": d,
                                    "reason": reason,
                                    "is_dir": True,
                                }
                            )
                        break

            # 检查文件名
            for f in files:
                for pattern, reason in problem_patterns:
                    if re.search(pattern, f):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, self.root_path)
                        self.stats.problematic_names.append(
                            {
                                "path": rel_path,
                                "name": f,
                                "reason": reason,
                                "is_dir": False,
                            }
                        )
                        break

    def _analyze_top_level(self):
        """分析顶级目录的组成"""
        root_items = [
            os.path.join(self.root_path, item) for item in os.listdir(self.root_path)
        ]

        dirs = [item for item in root_items if os.path.isdir(item)]

        for d in dirs:
            dir_name = os.path.basename(d)

            # 跳过隐藏文件/目录
            if dir_name.startswith(".") and not self.config["show_hidden"]:
                continue

            # 检查排除目录
            if any(
                fnmatch.fnmatch(dir_name, pattern)
                for pattern in self.config["exclude_dirs"]
            ):
                continue

            # 统计子文件数量
            file_count = 0
            dir_size = 0

            for root, _, files in os.walk(d):
                for f in files:
                    if any(
                        fnmatch.fnmatch(f, pattern)
                        for pattern in self.config["exclude_files"]
                    ):
                        continue

                    file_path = os.path.join(root, f)
                    try:
                        file_count += 1
                        dir_size += os.path.getsize(file_path)
                    except:
                        pass

            self.stats.top_level_dirs.append(
                {
                    "name": dir_name,
                    "path": os.path.relpath(d, self.root_path),
                    "file_count": file_count,
                    "size": dir_size,
                    "size_percent": (
                        0
                        if self.stats.total_size == 0
                        else round(dir_size / self.stats.total_size * 100, 1)
                    ),
                }
            )

        # 按大小排序
        self.stats.top_level_dirs.sort(key=lambda x: x["size"], reverse=True)


class OutputFormatter:
    """格式化输出"""

    @staticmethod
    def format(result, config):
        """根据配置选择格式化方法"""
        formatters = {
            "text": OutputFormatter.format_text,
            "markdown": OutputFormatter.format_markdown,
            "json": OutputFormatter.format_json,
        }

        return formatters[config["output_format"]](result, config)

    @staticmethod
    def format_text(result, config):
        """格式化为文本输出"""
        output = []

        # 添加标题
        output.append(
            f"{Colors.BOLD}{Colors.CYAN}===== 项目目录分析报告 ====={Colors.RESET}"
        )
        output.append(f"分析路径: {Colors.BOLD}{config['target_path']}{Colors.RESET}")
        output.append(
            f"分析时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        output.append("")

        # 基本统计
        stats = result["stats"]
        output.append(f"{Colors.BOLD}{Colors.BLUE}基本统计{Colors.RESET}")
        output.append(f"文件总数: {stats['total_files']}")
        output.append(f"目录总数: {stats['total_dirs']}")
        output.append(f"总大小: {OutputFormatter.format_size(stats['total_size'])}")
        if config["count_lines"]:
            output.append(f"总行数: {stats['total_lines']:,}")
        output.append("")

        # 项目结构模式
        if result["patterns_detected"]:
            output.append(
                f"{Colors.BOLD}{Colors.BLUE}检测到的项目结构模式{Colors.RESET}"
            )
            for pattern in result["patterns_detected"]:
                confidence_color = (
                    Colors.GREEN if pattern["confidence"] > 70 else Colors.YELLOW
                )
                output.append(
                    f"- {pattern['description']} ({confidence_color}{pattern['confidence']}%匹配度{Colors.RESET})"
                )
            output.append("")

        # 顶级目录统计
        if result["top_level_dirs"]:
            output.append(f"{Colors.BOLD}{Colors.BLUE}顶级目录分析{Colors.RESET}")
            output.append(f"{'目录名':<20} {'文件数':<10} {'大小':<12} {'占比':<8}")
            output.append("-" * 50)
            for d in result["top_level_dirs"]:
                size_str = OutputFormatter.format_size(d["size"])
                output.append(
                    f"{d['name']:<20} {d['file_count']:<10} {size_str:<12} {d['size_percent']}%"
                )
            output.append("")

        # 文件类型统计
        output.append(f"{Colors.BOLD}{Colors.BLUE}文件类型统计{Colors.RESET}")
        output.append(f"{'类型':<15} {'文件数':<10} {'总大小':<12} {'平均大小':<12}")
        output.append("-" * 50)

        sorted_types = sorted(
            stats["type_counts"].items(),
            key=lambda x: stats["type_sizes"].get(x[0], 0),
            reverse=True,
        )

        for file_type, count in sorted_types:
            total_size = stats["type_sizes"].get(file_type, 0)
            avg_size = total_size / count if count > 0 else 0

            # 查找这个文件类型所属的组
            group = "其他"
            for g, types in FILE_GROUPS.items():
                if file_type in types:
                    group = g
                    break

            output.append(
                f"{file_type:<15} {count:<10} {OutputFormatter.format_size(total_size):<12} {OutputFormatter.format_size(avg_size):<12}"
            )
        output.append("")

        # 扩展名统计（只显示前10个）
        output.append(f"{Colors.BOLD}{Colors.BLUE}常见文件扩展名{Colors.RESET}")
        sorted_exts = sorted(
            stats["extension_counts"].items(), key=lambda x: x[1], reverse=True
        )[:10]
        for ext, count in sorted_exts:
            output.append(f"- {ext or '(无扩展名)'}: {count} 个文件")
        output.append("")

        # 最大文件
        output.append(f"{Colors.BOLD}{Colors.BLUE}最大文件{Colors.RESET}")
        for path, size in result["largest_files"]:
            rel_path = os.path.relpath(path, config["target_path"])
            output.append(f"- {rel_path}: {OutputFormatter.format_size(size)}")
        output.append("")

        # 空目录
        if result["empty_dirs"]:
            output.append(f"{Colors.BOLD}{Colors.YELLOW}空目录{Colors.RESET}")
            for path in result["empty_dirs"][:10]:  # 只显示前10个
                rel_path = os.path.relpath(path, config["target_path"])
                output.append(f"- {rel_path}")
            if len(result["empty_dirs"]) > 10:
                output.append(f"... 还有 {len(result['empty_dirs']) - 10} 个空目录")
            output.append("")

        # 可能有问题的文件名
        if result["problematic_names"]:
            output.append(
                f"{Colors.BOLD}{Colors.YELLOW}可能有问题的文件/目录名{Colors.RESET}"
            )
            for item in result["problematic_names"][:10]:  # 只显示前10个
                type_str = "目录" if item["is_dir"] else "文件"
                output.append(f"- {item['path']} ({type_str}, {item['reason']})")
            if len(result["problematic_names"]) > 10:
                output.append(
                    f"... 还有 {len(result['problematic_names']) - 10} 个问题命名"
                )
            output.append("")

        # 目录树
        output.append(f"{Colors.BOLD}{Colors.BLUE}目录结构{Colors.RESET}")
        OutputFormatter._format_directory_tree(result["directory_tree"], output, "", "")

        return "\n".join(output)

    @staticmethod
    def _format_directory_tree(node, output, prefix, child_prefix):
        """格式化目录树为文本"""
        # 添加当前节点
        if node.is_dir:
            output.append(f"{prefix}{Colors.BLUE}{node.name}/{Colors.RESET}")
        else:
            size_str = f" ({OutputFormatter.format_size(node.size)})"
            output.append(f"{prefix}{node.name}{Colors.GRAY}{size_str}{Colors.RESET}")

        # 处理子节点
        children = sorted(node.children, key=lambda x: (not x.is_dir, x.name.lower()))
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            new_prefix = child_prefix + ("└── " if is_last else "├── ")
            new_child_prefix = child_prefix + ("    " if is_last else "│   ")

            OutputFormatter._format_directory_tree(
                child, output, new_prefix, new_child_prefix
            )

    @staticmethod
    def format_markdown(result, config):
        """格式化为Markdown输出"""
        # 禁用颜色输出以防干扰Markdown
        Colors.disable()
        text_output = OutputFormatter.format_text(result, config)

        # 添加Markdown封装
        return f"# 项目目录分析报告\n\n```\n{text_output}\n```"

    @staticmethod
    def format_json(result, config):
        """格式化为JSON输出"""
        # 转换为可序列化的对象
        serializable_result = OutputFormatter._prepare_for_serialization(result)
        return json.dumps(serializable_result, indent=2, ensure_ascii=False)

    @staticmethod
    def _prepare_for_serialization(obj):
        """递归转换对象为可JSON序列化的格式"""
        if isinstance(obj, dict):
            return {
                k: OutputFormatter._prepare_for_serialization(v) for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [OutputFormatter._prepare_for_serialization(item) for item in obj]
        elif isinstance(obj, DirectoryNode):
            return {
                "name": obj.name,
                "path": obj.path,
                "is_dir": obj.is_dir,
                "size": obj.size,
                "children": [
                    OutputFormatter._prepare_for_serialization(child)
                    for child in obj.children
                ],
            }
        else:
            return obj

    @staticmethod
    def format_size(size_bytes):
        """格式化文件大小为可读形式"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="项目目录分析工具")

    parser.add_argument("path", nargs="?", default=".", help="要分析的目录路径")
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "markdown", "json"],
        default="text",
        help="输出格式 (默认: text)",
    )
    parser.add_argument(
        "--max-depth",
        "-d",
        type=int,
        default=DEFAULT_CONFIG["max_depth"],
        help=f"最大递归深度 (默认: {DEFAULT_CONFIG['max_depth']})",
    )
    parser.add_argument(
        "--show-hidden", "-s", action="store_true", help="显示隐藏文件和目录"
    )
    parser.add_argument("--no-color", action="store_true", help="禁用彩色输出")
    parser.add_argument(
        "--count-lines", "-l", action="store_true", help="统计文本文件行数"
    )
    parser.add_argument(
        "--max-workers",
        "-w",
        type=int,
        default=DEFAULT_CONFIG["max_workers"],
        help=f"最大工作线程数 (默认: {DEFAULT_CONFIG['max_workers']})",
    )

    args = parser.parse_args()

    # 更新配置
    config = DEFAULT_CONFIG.copy()
    config["target_path"] = args.path
    config["output_format"] = args.output
    config["max_depth"] = args.max_depth
    config["show_hidden"] = args.show_hidden
    config["color_output"] = not args.no_color
    config["count_lines"] = args.count_lines
    config["max_workers"] = args.max_workers

    return config


def main():
    """主程序"""
    try:
        # 解析命令行参数
        config = parse_args()

        # 如果禁用彩色输出
        if not config["color_output"]:
            Colors.disable()

        # 创建分析器并运行
        analyzer = DirectoryAnalyzer(config)
        start_time = time.time()
        result = analyzer.analyze()
        end_time = time.time()

        # 输出结果
        output = OutputFormatter.format(result, config)
        print(output)

        # 显示运行时间
        print(
            f"\n{Colors.CYAN}分析完成！耗时: {end_time - start_time:.2f} 秒{Colors.RESET}"
        )

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}操作被用户取消{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}错误: {str(e)}{Colors.RESET}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
