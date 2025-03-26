"""
优化版Python代码库分析工具

专用于分析Python项目的强化工具，提供详细的代码质量报告：
- 项目结构和组织分析
- 代码质量与复杂度指标
- 模块依赖关系分析
- Python特有反模式检测
- 命名规范检查
- 质量评分系统
- 彩色终端输出

作者: Claude
版本: 2.0.0
"""

import os
import ast
import fnmatch
import json
import re
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict


# ================== 配置 ==================
CONFIG = {
    "target_path": r".",  # 默认为当前目录
    "output_format": "text",  # text/markdown/json
    "exclude_dirs": [
        "__pycache__",
        ".git",
        ".vscode",
        ".idea",
        "venv",
        "env",
        ".env",
        ".venv",
        "virtualenv",
        "node_modules",
        "logs",
        "dist",
        "build",
        "*.egg-info",
    ],
    "exclude_files": [
        "*.pyc",
        "*.pyo",
        "*.log",
        "*.tmp",
        "*.bak",
        "*.zip",
        "*.7z",
        "Thumbs.db",
        ".DS_Store",
        ".gitignore",
    ],
    "include_patterns": ["*.py"],  # 默认只包括Python文件
    "show_hidden": False,
    "max_workers": 4,
    "max_file_size_mb": 10,  # 跳过大于此大小的文件
    "detailed_imports": True,  # 分析导入依赖
    "detect_antipatterns": True,  # 寻找常见反模式
    "calculate_complexity": True,  # 计算循环复杂度
    "analyze_docstrings": True,  # 检查文档字符串
    "check_naming": True,  # 检查命名规范
    "color_output": True,  # 彩色终端输出
}
# ================== 配置结束 ====================


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
            return sys.getwindowsversion().major >= 10
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


@dataclass
class NamingStats:
    """Python命名规范统计"""

    good_names: int = 0
    bad_names: int = 0
    snake_case_vars: int = 0
    camel_case_vars: int = 0
    pascal_case_classes: int = 0
    non_pascal_classes: int = 0
    naming_issues: List[str] = field(default_factory=list)


@dataclass
class CodeQuality:
    """Python特定代码质量指标"""

    has_docstring: bool = False
    has_type_hints: bool = False
    has_tests: bool = False
    antipatterns_count: int = 0
    antipatterns: List[str] = field(default_factory=list)
    naming_stats: NamingStats = field(default_factory=NamingStats)


@dataclass
class FileStats:
    """Python文件统计信息"""

    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    docstring_lines: int = 0
    cyclomatic_complexity: int = 0
    class_count: int = 0
    function_count: int = 0
    method_count: int = 0

    import_count: int = 0
    imports: Dict[str, List[str]] = field(default_factory=dict)

    quality: CodeQuality = field(default_factory=CodeQuality)
    quality_score: float = 0.0


@dataclass
class ModuleInfo:
    """Python模块信息"""

    name: str
    path: str
    is_package: bool = False
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    public_symbols: List[str] = field(default_factory=list)
    stats: Optional[FileStats] = None


class AntiPatternDetector:
    """检测Python代码中的常见反模式"""

    PATTERNS = {
        "bare_except": (r"except\s*:", "使用裸except语句"),
        "mutable_default": (
            r"def\s+\w+\s*\(.*=\s*\[\s*\].*\)|\(.*=\s*\{\s*\}.*\)",
            "使用可变默认参数",
        ),
        "global_statement": (r"\bglobal\b", "使用global语句"),
        "eval_usage": (r"\beval\(", "使用eval()函数"),
        "exec_usage": (r"\bexec\(", "使用exec()函数"),
        "wildcard_import": (r"from\s+[\w.]+\s+import\s+\*", "使用通配符导入"),
        "exit_call": (r"\bexit\(", "使用exit()而非sys.exit()"),
        "print_debugging": (r"\bprint\(", "可能存在调试用print语句"),
        "hardcoded_path": (r"(?<!['\"])\/\w+(?=\/|$)|[A-Za-z]:\\", "硬编码文件路径"),
        "nested_function": (
            r"def\s+\w+\s*\([^)]*\):\s*[^\n]*\n\s+def\s+",
            "嵌套函数定义",
        ),
        "too_many_arguments": (r"def\s+\w+\s*\([^)]{80,}\)", "函数参数过多"),
    }

    @staticmethod
    def find_antipatterns(code: str) -> List[Tuple[str, str]]:
        """在代码中查找反模式

        返回包含（行，描述）的元组列表
        """
        antipatterns = []
        for name, (pattern, description) in AntiPatternDetector.PATTERNS.items():
            if name == "print_debugging" and "debugging" in code.lower():
                # 跳过调试模块中的print
                continue

            matches = re.finditer(pattern, code)
            for match in matches:
                line_start = code[: match.start()].count("\n") + 1
                line = (
                    code.splitlines()[line_start - 1]
                    if line_start <= len(code.splitlines())
                    else ""
                )
                antipatterns.append((f"第{line_start}行: {line.strip()}", description))

        return antipatterns


class NamingConventionChecker:
    """Python命名规范检查器"""

    SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
    PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
    CAMEL_CASE_PATTERN = re.compile(r"^[a-z][a-zA-Z0-9]*$")

    @staticmethod
    def check_class_name(name: str) -> bool:
        """检查类名是否符合PEP8（PascalCase）"""
        return bool(NamingConventionChecker.PASCAL_CASE_PATTERN.match(name))

    @staticmethod
    def check_function_name(name: str) -> bool:
        """检查函数名是否符合PEP8（snake_case）

        包括以下合法命名规则：
        - 普通函数/方法：使用snake_case (如 my_function)
        - 私有函数/方法：单下划线前缀加snake_case (如 _private_method)
        - 魔术方法：双下划线前缀和后缀 (如 __init__)
        - 私有特殊方法：双下划线前缀但非魔术方法 (如 __private_method)
        """
        # 魔术方法（前后双下划线）是有效的命名
        if name.startswith("__") and name.endswith("__"):
            return True

        # 私有方法（以单下划线开头）是有效的命名
        if name.startswith("_") and not name.startswith("__"):
            # 检查下划线后面的部分是否符合snake_case
            return len(name) > 1 and (
                NamingConventionChecker.SNAKE_CASE_PATTERN.match(name[1:])
                or name[1:].islower()  # 单个字母也可以
            )

        # 类内私有方法（以双下划线开头但不以双下划线结尾）是有效的命名
        if name.startswith("__") and not name.endswith("__"):
            # 检查双下划线后面的部分是否符合snake_case
            return len(name) > 2 and (
                NamingConventionChecker.SNAKE_CASE_PATTERN.match(name[2:])
                or name[2:].islower()  # 单个字母也可以
            )

        # 常规函数名检查
        return bool(NamingConventionChecker.SNAKE_CASE_PATTERN.match(name))

    @staticmethod
    def check_variable_name(name: str) -> bool:
        """检查变量名是否符合PEP8（snake_case）

        包括以下合法命名规则：
        - 普通变量：使用snake_case (如 my_var)
        - 私有变量：单下划线前缀加snake_case (如 _private_var)
        - 类内私有变量：双下划线前缀 (如 __private_var)
        - 常量：全大写加下划线 (如 MAX_VALUE)
        - 魔术变量：双下划线前缀和后缀 (如 __all__)
        """
        # 常量使用全大写
        if name.isupper():
            return True

        # 魔术变量（前后双下划线）是有效的命名
        if name.startswith("__") and name.endswith("__"):
            return True

        # 私有变量（以单下划线开头）是有效的命名
        if name.startswith("_") and not name.startswith("__"):
            # 空名称后缀不是有效名称
            if len(name) <= 1:
                return False

            # 检查下划线后面的部分是否符合snake_case
            remainder = name[1:]
            return (
                NamingConventionChecker.SNAKE_CASE_PATTERN.match(remainder)
                or remainder.islower()  # 单个字母也可以
            )

        # 类内私有变量（以双下划线开头）是有效的命名
        if name.startswith("__"):
            # 空名称后缀不是有效名称
            if len(name) <= 2:
                return False

            # 检查双下划线后面的部分是否符合snake_case
            remainder = name[2:]
            return (
                NamingConventionChecker.SNAKE_CASE_PATTERN.match(remainder)
                or remainder.islower()  # 单个字母也可以
            )

        # 常规变量名检查
        return bool(NamingConventionChecker.SNAKE_CASE_PATTERN.match(name))

    @staticmethod
    def check_constant_name(name: str) -> bool:
        """检查常量名是否符合PEP8（大写加下划线）"""
        return name.isupper()

    @staticmethod
    def get_name_case_type(name: str) -> str:
        """识别名称的命名风格"""
        if name.startswith("_") and not name.startswith("__"):
            # 私有成员（单下划线前缀）
            remainder = name[1:]
            if (
                NamingConventionChecker.SNAKE_CASE_PATTERN.match(remainder)
                or remainder.islower()
            ):
                return "私有成员(单下划线前缀)"
            else:
                return f"私有成员(命名不规范)"

        if name.startswith("__") and name.endswith("__"):
            # 魔术方法/变量
            return "魔术方法/变量"

        if name.startswith("__"):
            # 类内私有成员（双下划线前缀）
            remainder = name[2:]
            if (
                NamingConventionChecker.SNAKE_CASE_PATTERN.match(remainder)
                or remainder.islower()
            ):
                return "类内私有成员(双下划线前缀)"
            else:
                return f"类内私有成员(命名不规范)"

        if name.isupper():
            # 常量
            return "常量(全大写)"

        if NamingConventionChecker.SNAKE_CASE_PATTERN.match(name):
            return "snake_case"
        elif NamingConventionChecker.PASCAL_CASE_PATTERN.match(name):
            return "PascalCase"
        elif NamingConventionChecker.CAMEL_CASE_PATTERN.match(name):
            return "camelCase"
        else:
            return "其他"


class QualityScoreCalculator:
    """计算代码质量评分"""

    # 权重配置
    WEIGHTS = {
        "complexity": 0.2,  # 复杂度
        "docstrings": 0.15,  # 文档字符串
        "comments": 0.1,  # 注释
        "antipatterns": 0.25,  # 反模式
        "naming": 0.15,  # 命名规范
        "type_hints": 0.15,  # 类型提示
    }

    @staticmethod
    def calculate_file_score(stats: FileStats) -> float:
        """为文件计算质量评分（0-100）"""
        # 初始化各项分数
        scores = {}

        # 计算复杂度得分 (低复杂度 = 高分)
        if stats.function_count + stats.method_count > 0:
            complexity_per_function = stats.cyclomatic_complexity / (
                stats.function_count + stats.method_count
            )
            if complexity_per_function <= 5:
                scores["complexity"] = 100
            elif complexity_per_function <= 10:
                scores["complexity"] = 80
            elif complexity_per_function <= 15:
                scores["complexity"] = 60
            elif complexity_per_function <= 20:
                scores["complexity"] = 40
            else:
                scores["complexity"] = 20
        else:
            scores["complexity"] = 100  # 没有函数的文件默认为100

        # 文档字符串得分
        if stats.class_count + stats.function_count + stats.method_count > 0:
            if stats.quality.has_docstring:
                docstring_ratio = stats.docstring_lines / (
                    stats.class_count + stats.function_count + stats.method_count
                )
                if docstring_ratio >= 3:
                    scores["docstrings"] = 100
                elif docstring_ratio >= 2:
                    scores["docstrings"] = 80
                elif docstring_ratio >= 1:
                    scores["docstrings"] = 60
                else:
                    scores["docstrings"] = 40
            else:
                scores["docstrings"] = 0
        else:
            scores["docstrings"] = 100  # 没有类和函数的文件默认为100

        # 注释得分
        if stats.code_lines > 0:
            comment_ratio = stats.comment_lines / stats.code_lines
            if comment_ratio >= 0.2:
                scores["comments"] = 100
            elif comment_ratio >= 0.15:
                scores["comments"] = 80
            elif comment_ratio >= 0.1:
                scores["comments"] = 60
            elif comment_ratio >= 0.05:
                scores["comments"] = 40
            else:
                scores["comments"] = 20
        else:
            scores["comments"] = 100  # 没有代码的文件默认为100

        # 反模式得分 (少反模式 = 高分)
        if stats.quality.antipatterns_count == 0:
            scores["antipatterns"] = 100
        elif stats.quality.antipatterns_count <= 2:
            scores["antipatterns"] = 80
        elif stats.quality.antipatterns_count <= 5:
            scores["antipatterns"] = 60
        elif stats.quality.antipatterns_count <= 10:
            scores["antipatterns"] = 40
        else:
            scores["antipatterns"] = 20

        # 命名规范得分
        if (
            stats.quality.naming_stats.good_names + stats.quality.naming_stats.bad_names
            > 0
        ):
            naming_ratio = stats.quality.naming_stats.good_names / (
                stats.quality.naming_stats.good_names
                + stats.quality.naming_stats.bad_names
            )
            scores["naming"] = min(100, naming_ratio * 100)
        else:
            scores["naming"] = 100  # 没有需要检查命名的元素

        # 类型提示得分
        scores["type_hints"] = 100 if stats.quality.has_type_hints else 0

        # 计算加权总分
        weighted_score = sum(
            scores[key] * QualityScoreCalculator.WEIGHTS[key] for key in scores
        )
        return round(weighted_score, 1)

    @staticmethod
    def get_score_category(score: float) -> Tuple[str, str]:
        """获取分数等级和颜色"""
        if score >= 90:
            return "优秀", Colors.GREEN
        elif score >= 80:
            return "良好", Colors.CYAN
        elif score >= 70:
            return "良好", Colors.BLUE
        elif score >= 60:
            return "待改进", Colors.YELLOW
        else:
            return "需重构", Colors.RED


class PythonModuleAnalyzer:
    """分析Python模块（使用AST）"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.stats = FileStats()
        self.module_ast = None
        self.code_content = ""

    def analyze(self) -> FileStats:
        """分析Python文件并返回统计信息"""
        if not self._read_file():
            return self.stats

        # 统计基本指标
        self._count_lines()

        # 解析AST
        if not self._parse_ast():
            return self.stats

        # 执行AST分析
        if self.module_ast:
            self._analyze_ast()

        # 检测反模式
        if CONFIG["detect_antipatterns"]:
            self._detect_antipatterns()

        # 计算质量评分
        self.stats.quality_score = QualityScoreCalculator.calculate_file_score(
            self.stats
        )

        return self.stats

    def _read_file(self) -> bool:
        """读取文件内容，成功返回True"""
        try:
            file_size = self.file_path.stat().st_size
            if file_size > CONFIG["max_file_size_mb"] * 1024 * 1024:
                return False

            with open(self.file_path, "r", encoding="utf-8") as f:
                self.code_content = f.read()
            return True
        except Exception as e:
            return False

    def _count_lines(self):
        """统计文件中不同类型的行"""
        lines = self.code_content.splitlines()
        self.stats.total_lines = len(lines)

        in_docstring = False
        docstring_delimiter = None

        for line in lines:
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                self.stats.blank_lines += 1
                continue

            # 处理文档字符串
            if in_docstring:
                self.stats.docstring_lines += 1
                if stripped.endswith(docstring_delimiter):
                    in_docstring = False
                continue

            # 文档字符串开始
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_delimiter = stripped[:3]
                in_docstring = True
                self.stats.docstring_lines += 1
                if stripped.endswith(docstring_delimiter) and len(stripped) > 3:
                    in_docstring = False
                continue

            # 注释
            if stripped.startswith("#"):
                self.stats.comment_lines += 1
                continue

            # 代码行
            self.stats.code_lines += 1

    def _parse_ast(self) -> bool:
        """解析文件为AST，成功返回True"""
        try:
            self.module_ast = ast.parse(self.code_content, filename=str(self.file_path))
            return True
        except SyntaxError:
            return False

    def _analyze_ast(self):
        """分析AST获取各种指标"""
        if not self.module_ast:
            return

        # 初始化计数器
        class_counter = 0
        function_counter = 0
        method_counter = 0
        complexity = 0
        has_docstring = False
        has_type_hints = False
        imports = {}

        # 命名规范统计
        naming_stats = NamingStats()

        # 检查模块文档字符串
        if (
            len(self.module_ast.body) > 0
            and isinstance(self.module_ast.body[0], ast.Expr)
            and isinstance(self.module_ast.body[0].value, ast.Str)
        ):
            has_docstring = True

        # 遍历AST
        for node in ast.walk(self.module_ast):
            # 统计类
            if isinstance(node, ast.ClassDef):
                class_counter += 1

                # 检查类命名
                if CONFIG["check_naming"]:
                    if NamingConventionChecker.check_class_name(node.name):
                        naming_stats.good_names += 1
                        naming_stats.pascal_case_classes += 1
                    else:
                        naming_stats.bad_names += 1
                        naming_stats.non_pascal_classes += 1
                        naming_stats.naming_issues.append(
                            f"类名 '{node.name}' 不符合PascalCase规范"
                        )

                # 检查类文档字符串
                if (
                    len(node.body) > 0
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Str)
                ):
                    has_docstring = True

            # 统计函数和方法
            elif isinstance(node, ast.FunctionDef):
                # 检查函数命名
                if CONFIG["check_naming"]:
                    if NamingConventionChecker.check_function_name(node.name):
                        naming_stats.good_names += 1
                    else:
                        # 跳过魔术方法
                        if not (
                            node.name.startswith("__") and node.name.endswith("__")
                        ):
                            naming_stats.bad_names += 1
                            naming_stats.naming_issues.append(
                                f"函数名 '{node.name}' 不符合snake_case规范"
                            )

                # 检查是否为方法（类内部的函数）
                is_method = False
                for parent in ast.walk(self.module_ast):
                    if isinstance(parent, ast.ClassDef) and node in parent.body:
                        is_method = True
                        method_counter += 1
                        break

                if not is_method:
                    function_counter += 1

                # 检查函数文档字符串
                if (
                    len(node.body) > 0
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Str)
                ):
                    has_docstring = True

                # 检查类型注解
                if node.returns or any(arg.annotation for arg in node.args.args):
                    has_type_hints = True

                # 计算复杂度（简化版）
                complexity += 1  # 基础复杂度
                for inner_node in ast.walk(node):
                    if isinstance(
                        inner_node,
                        (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler),
                    ):
                        complexity += 1
                    elif isinstance(inner_node, ast.BoolOp) and isinstance(
                        inner_node.op, (ast.And, ast.Or)
                    ):
                        complexity += len(inner_node.values) - 1

            # 检查变量命名和类型注解
            elif isinstance(node, ast.Assign):
                if CONFIG["check_naming"]:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if NamingConventionChecker.check_variable_name(target.id):
                                naming_stats.good_names += 1
                                naming_stats.snake_case_vars += 1
                            else:
                                # 跳过魔术变量和常量
                                if (
                                    not (
                                        target.id.startswith("__")
                                        and target.id.endswith("__")
                                    )
                                    and not target.id.isupper()
                                ):
                                    naming_stats.bad_names += 1
                                    case_type = (
                                        NamingConventionChecker.get_name_case_type(
                                            target.id
                                        )
                                    )
                                    if case_type == "camelCase":
                                        naming_stats.camel_case_vars += 1
                                    naming_stats.naming_issues.append(
                                        f"变量名 '{target.id}' 不符合snake_case规范，使用了{case_type}"
                                    )

            # 检查带类型注解的变量
            elif isinstance(node, ast.AnnAssign) and node.annotation:
                has_type_hints = True

                if CONFIG["check_naming"] and isinstance(node.target, ast.Name):
                    if NamingConventionChecker.check_variable_name(node.target.id):
                        naming_stats.good_names += 1
                    else:
                        # 跳过魔术变量和常量
                        if (
                            not (
                                node.target.id.startswith("__")
                                and node.target.id.endswith("__")
                            )
                            and not node.target.id.isupper()
                        ):
                            naming_stats.bad_names += 1
                            naming_stats.naming_issues.append(
                                f"变量名 '{node.target.id}' 不符合snake_case规范"
                            )

            # 收集导入信息
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_name = name.name
                        alias = name.asname or module_name
                        imports.setdefault(module_name, []).append(alias)
                else:  # ImportFrom
                    if node.module:  # 跳过无模块的相对导入
                        for name in node.names:
                            if name.name == "*":
                                imports.setdefault(node.module, []).append("*")
                            else:
                                imported_name = name.name
                                alias = name.asname or imported_name
                                full_name = f"{node.module}.{imported_name}"
                                imports.setdefault(node.module, []).append(
                                    imported_name
                                )

        # 更新统计信息
        self.stats.class_count = class_counter
        self.stats.function_count = function_counter
        self.stats.method_count = method_counter
        self.stats.cyclomatic_complexity = complexity
        self.stats.quality.has_docstring = has_docstring
        self.stats.quality.has_type_hints = has_type_hints
        self.stats.import_count = sum(len(names) for names in imports.values())
        self.stats.imports = imports
        self.stats.quality.naming_stats = naming_stats

    def _detect_antipatterns(self):
        """检测代码中的反模式"""
        if not self.code_content:
            return

        antipatterns = AntiPatternDetector.find_antipatterns(self.code_content)
        self.stats.quality.antipatterns_count = len(antipatterns)
        self.stats.quality.antipatterns = [
            f"{desc}: {line}" for line, desc in antipatterns
        ]


class PythonProjectAnalyzer:
    """分析整个Python项目目录"""

    def __init__(self, config: Dict):
        self.config = config
        self.root_path = Path(config["target_path"]).resolve()
        self.modules: Dict[str, ModuleInfo] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.start_time = time.time()

    def analyze(self) -> Dict:
        """分析整个项目

        返回包含分析结果的字典
        """
        print(f"{Colors.CYAN}开始分析项目: {Colors.BOLD}{self.root_path}{Colors.RESET}")

        result = {
            "structure": [],
            "stats": {},
            "modules": {},
            "dependencies": {},
            "total": {
                "files": 0,
                "total_lines": 0,
                "code_lines": 0,
                "comment_lines": 0,
                "blank_lines": 0,
                "docstring_lines": 0,
                "complexity": 0,
                "classes": 0,
                "functions": 0,
                "methods": 0,
                "imports": 0,
                "antipatterns": 0,
                "naming_issues": 0,
                "quality_score": 0.0,
            },
            "quality_summary": {},
        }

        # 第一步：发现所有Python模块
        print(f"{Colors.BLUE}正在查找所有Python模块...{Colors.RESET}")
        self._discover_modules()

        # 第二步：分析文件并构建目录结构
        print(f"{Colors.BLUE}正在分析文件内容...{Colors.RESET}")
        files_processed = 0

        for root, dirs, files in os.walk(self.root_path, topdown=True):
            # 根据排除模式过滤目录
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]

            # 为当前路径创建目录项
            current_path = Path(root).relative_to(self.root_path)
            current_dir = self._create_dir_entry(current_path)

            # 处理当前目录中的文件
            filterd_files = [f for f in files if self._should_process_file(f)]
            total_files = len(filterd_files)

            with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
                futures = []
                for f in filterd_files:
                    futures.append(executor.submit(self._analyze_file, Path(root) / f))

                for i, future in enumerate(as_completed(futures)):
                    file_entry, stats_dict = future.result()
                    files_processed += 1

                    if file_entry:
                        current_dir["children"].append(file_entry)
                        result["stats"][file_entry["path"]] = stats_dict
                        self._update_total_stats(result["total"], stats_dict)

                    # 每处理10个文件显示一次进度
                    if files_processed % 10 == 0 or files_processed == total_files:
                        elapsed = time.time() - self.start_time
                        print(
                            f"\r{Colors.CYAN}已处理 {files_processed} 个文件 "
                            f"({round(elapsed, 1)}秒){Colors.RESET}",
                            end="",
                        )
                        sys.stdout.flush()

            # 将当前目录添加到结构中
            if current_dir["children"] or current_path == Path("."):
                result["structure"].append(current_dir)

        print(f"\n{Colors.GREEN}文件分析完成!{Colors.RESET}")

        # 构建模块关系
        print(f"{Colors.BLUE}正在构建模块依赖关系...{Colors.RESET}")
        self._build_module_relationships()

        # 计算项目总体质量评分
        print(f"{Colors.BLUE}正在计算质量评分...{Colors.RESET}")
        if result["total"]["files"] > 0:
            result["total"]["quality_score"] = self._calculate_project_score(result)

        # 生成质量摘要
        result["quality_summary"] = self._generate_quality_summary(result)

        # 添加模块和依赖关系到结果
        result["modules"] = {
            name: asdict(module) for name, module in self.modules.items()
        }
        result["dependencies"] = {
            source: list(targets) for source, targets in self.dependencies.items()
        }

        elapsed = time.time() - self.start_time
        print(f"{Colors.GREEN}分析完成! 耗时: {round(elapsed, 2)}秒{Colors.RESET}")

        return result

    def _calculate_project_score(self, result: Dict) -> float:
        """计算项目整体质量评分"""
        if not result["stats"]:
            return 0.0

        # 计算所有文件的加权平均分
        total_lines = 0
        weighted_sum = 0

        for path, stats in result["stats"].items():
            if not isinstance(stats, dict):
                continue

            file_lines = stats.get("total_lines", 0)
            file_score = stats.get("quality_score", 0)

            if file_lines > 0 and file_score > 0:
                total_lines += file_lines
                weighted_sum += file_lines * file_score

        if total_lines == 0:
            return 0.0

        return round(weighted_sum / total_lines, 1)

    def _generate_quality_summary(self, result: Dict) -> Dict:
        """生成项目质量摘要"""
        total = result["total"]
        total_files = total["files"]

        if total_files == 0:
            return {}

        # 计算总体质量评分
        score = result["total"]["quality_score"]
        score_category, score_color = QualityScoreCalculator.get_score_category(score)

        # 计算文档覆盖率
        files_with_docstrings = 0
        for stats in result["stats"].values():
            if isinstance(stats, dict) and stats.get("quality", {}).get(
                "has_docstring", False
            ):
                files_with_docstrings += 1

        docstring_coverage = (
            round((files_with_docstrings / total_files) * 100, 1)
            if total_files > 0
            else 0
        )

        # 计算类型提示覆盖率
        files_with_type_hints = 0
        for stats in result["stats"].values():
            if isinstance(stats, dict) and stats.get("quality", {}).get(
                "has_type_hints", False
            ):
                files_with_type_hints += 1

        type_hint_coverage = (
            round((files_with_type_hints / total_files) * 100, 1)
            if total_files > 0
            else 0
        )

        # 获取平均复杂度
        avg_complexity = (
            round(total["complexity"] / (total["functions"] + total["methods"]), 1)
            if (total["functions"] + total["methods"]) > 0
            else 0
        )

        # 计算代码注释比例
        comment_ratio = (
            round(total["comment_lines"] / total["code_lines"] * 100, 1)
            if total["code_lines"] > 0
            else 0
        )

        return {
            "quality_score": score,
            "quality_category": score_category,
            "files_with_docstrings_percent": docstring_coverage,
            "files_with_type_hints_percent": type_hint_coverage,
            "average_complexity": avg_complexity,
            "comment_to_code_ratio": comment_ratio,
            "total_antipatterns": total["antipatterns"],
            "total_naming_issues": total["naming_issues"],
        }

    def _discover_modules(self):
        """第一步：发现项目中的所有Python模块"""
        for root, dirs, files in os.walk(self.root_path, topdown=True):
            # 根据排除模式过滤目录
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]

            rel_path = Path(root).relative_to(self.root_path)
            module_path = str(rel_path).replace(os.sep, ".")

            # 检查当前目录是否为包
            has_init = "__init__.py" in files
            if has_init:
                # 这个目录是一个包
                package_name = module_path if module_path != "." else ""
                self.modules[package_name] = ModuleInfo(
                    name=package_name,
                    path=str(rel_path / "__init__.py"),
                    is_package=True,
                )

            # 处理目录中的所有Python文件
            for f in files:
                if f.endswith(".py") and not self._is_excluded(
                    f, self.config["exclude_files"]
                ):
                    if f == "__init__.py":
                        continue  # 上面已经处理过了

                    # 计算模块名
                    if module_path == ".":
                        module_name = f[:-3]  # 移除.py
                    else:
                        module_name = f"{module_path}.{f[:-3]}"

                    self.modules[module_name] = ModuleInfo(
                        name=module_name, path=str(rel_path / f), is_package=False
                    )

    def _build_module_relationships(self):
        """基于导入关系构建模块之间的依赖关系"""
        # 首先，将模块路径转换为名称以便查找
        path_to_name = {mod.path: name for name, mod in self.modules.items()}

        # 对于每个模块，检查其导入项
        for module_name, module_info in self.modules.items():
            if not module_info.stats or not module_info.stats.imports:
                continue

            # 如果需要，初始化依赖跟踪
            if module_name not in self.dependencies:
                self.dependencies[module_name] = set()

            # 处理导入项
            for imported_module, imported_items in module_info.stats.imports.items():
                # 跳过标准库和第三方模块
                if imported_module in module_name or any(
                    imported_module.startswith(f"{mod_name}.")
                    for mod_name in self.modules
                ):
                    # 找到一个项目本地导入
                    self.dependencies[module_name].add(imported_module)

                    # 更新目标模块的 "imported_by"
                    if imported_module in self.modules:
                        self.modules[imported_module].imported_by.append(module_name)

    def _should_exclude_dir(self, dir_name: str) -> bool:
        """检查一个目录是否应该被排除"""
        if not self.config["show_hidden"] and dir_name.startswith("."):
            return True
        return self._is_excluded(dir_name, self.config["exclude_dirs"])

    def _should_process_file(self, file_name: str) -> bool:
        """检查一个文件是否应该被处理"""
        if not self.config["show_hidden"] and file_name.startswith("."):
            return False
        if self._is_excluded(file_name, self.config["exclude_files"]):
            return False
        return self._should_include(file_name)

    def _is_excluded(self, name: str, patterns: List[str]) -> bool:
        """检查一个名称是否匹配任何排除模式"""
        return any(fnmatch.fnmatch(name, p) for p in patterns)

    def _should_include(self, name: str) -> bool:
        """检查一个名称是否匹配任何包含模式"""
        if not self.config["include_patterns"]:
            return True
        return any(fnmatch.fnmatch(name, p) for p in self.config["include_patterns"])

    def _create_dir_entry(self, rel_path: Path) -> Dict:
        """为结果结构创建一个目录条目"""
        return {
            "path": str(rel_path),
            "name": rel_path.name if rel_path != Path(".") else self.root_path.name,
            "type": "directory",
            "children": [],
        }

    def _analyze_file(self, file_path: Path) -> Tuple[Dict, Dict]:
        """分析单个Python文件

        返回一个元组(file_entry, stats_dict)
        """
        try:
            rel_path = str(file_path.relative_to(self.root_path))

            # 为结构创建文件条目
            file_entry = {
                "path": rel_path,
                "name": file_path.name,
                "type": "file",
                "size": file_path.stat().st_size,
            }

            # 跳过非Python文件或太大的文件
            if (
                not file_path.suffix == ".py"
                or file_path.stat().st_size
                > self.config["max_file_size_mb"] * 1024 * 1024
            ):
                return file_entry, {"total_lines": 0}

            # 分析Python文件
            analyzer = PythonModuleAnalyzer(file_path)
            stats = analyzer.analyze()
            stats_dict = asdict(stats)

            # 使用统计信息更新模块信息
            module_rel_path = rel_path.replace(os.sep, "/")
            for name, module in self.modules.items():
                if module.path == module_rel_path:
                    module.stats = stats
                    break

            return file_entry, stats_dict
        except Exception as e:
            # 即使分析失败也返回条目
            return {
                "path": str(file_path.relative_to(self.root_path)),
                "name": file_path.name,
                "type": "file",
                "size": file_path.stat().st_size if file_path.exists() else 0,
                "error": str(e),
            }, {"total_lines": 0}

    def _update_total_stats(self, total: Dict, stats: Dict):
        """使用文件统计信息更新总体统计信息"""
        total["files"] += 1
        total["total_lines"] += stats.get("total_lines", 0)
        total["code_lines"] += stats.get("code_lines", 0)
        total["comment_lines"] += stats.get("comment_lines", 0)
        total["blank_lines"] += stats.get("blank_lines", 0)
        total["docstring_lines"] += stats.get("docstring_lines", 0)
        total["complexity"] += stats.get("cyclomatic_complexity", 0)
        total["classes"] += stats.get("class_count", 0)
        total["functions"] += stats.get("function_count", 0)
        total["methods"] += stats.get("method_count", 0)
        total["imports"] += stats.get("import_count", 0)

        quality = stats.get("quality", {})
        if isinstance(quality, dict):
            if "antipatterns_count" in quality:
                total["antipatterns"] += quality["antipatterns_count"]

            naming_stats = quality.get("naming_stats", {})
            if isinstance(naming_stats, dict) and "naming_issues" in naming_stats:
                total["naming_issues"] += len(naming_stats["naming_issues"])


class DependencyVisualizer:
    """使用ASCII字符创建简单的依赖关系可视化"""

    @staticmethod
    def create_dependency_matrix(
        dependencies: Dict[str, List[str]], modules: List[str]
    ) -> List[List[str]]:
        """创建一个依赖关系矩阵

        返回一个二维数组，每个单元格包含依赖类型的符号
        """
        # 准备模块列表（按字母排序）
        sorted_modules = sorted(modules)

        # 创建空矩阵
        matrix = []
        for i in range(len(sorted_modules)):
            row = []
            for j in range(len(sorted_modules)):
                row.append(" ")
            matrix.append(row)

        # 填充矩阵
        for i, source in enumerate(sorted_modules):
            for j, target in enumerate(sorted_modules):
                if i == j:
                    matrix[i][j] = "X"  # 自引用
                elif source in dependencies and target in dependencies[source]:
                    matrix[i][j] = "●"  # 依赖

        return matrix, sorted_modules

    @staticmethod
    def generate_ascii_dependency_graph(dependencies: Dict[str, List[str]]) -> str:
        """生成ASCII依赖关系图

        返回一个字符串表示的依赖图
        """
        if not dependencies:
            return "没有发现依赖关系"

        # 获取所有模块
        all_modules = set(dependencies.keys())
        for deps in dependencies.values():
            all_modules.update(deps)

        # 过滤掉标准库和外部库
        project_modules = [mod for mod in all_modules if "." in mod or len(mod) < 15]

        # 如果模块太多，只显示顶级模块
        if len(project_modules) > 20:
            top_modules = set()
            for mod in project_modules:
                top_mod = mod.split(".")[0]
                top_modules.add(top_mod)

            # 重建依赖关系
            top_dependencies = {}
            for source, targets in dependencies.items():
                source_top = source.split(".")[0]
                if source_top not in top_dependencies:
                    top_dependencies[source_top] = set()

                for target in targets:
                    target_top = target.split(".")[0]
                    if source_top != target_top:
                        top_dependencies[source_top].add(target_top)

            # 转换为列表
            for source, targets in top_dependencies.items():
                top_dependencies[source] = list(targets)

            dependencies = top_dependencies
            project_modules = list(top_modules)

        # 针对小型项目的简单依赖图
        if len(project_modules) <= 10:
            return DependencyVisualizer._generate_simple_graph(
                dependencies, project_modules
            )

        # 针对大型项目的矩阵依赖图
        return DependencyVisualizer._generate_matrix_graph(
            dependencies, project_modules
        )

    @staticmethod
    def _generate_simple_graph(
        dependencies: Dict[str, List[str]], modules: List[str]
    ) -> str:
        """为项目生成简单的节点和边树形图"""
        lines = ["依赖关系图（每个模块依赖的其他模块）:"]

        # 按有依赖关系的模块排序
        sorted_modules = sorted(
            [m for m in modules if m in dependencies and dependencies.get(m)]
        )

        # 如果没有依赖关系，添加提示
        if not sorted_modules:
            lines.append("未发现模块间依赖关系")
            return "\n".join(lines)

        # 为每个模块生成其依赖树
        for source in sorted_modules:
            deps = dependencies.get(source, [])
            if deps:
                lines.append(f"{source} 依赖:")
                for i, target in enumerate(sorted(deps)):
                    if i == len(deps) - 1:
                        lines.append(f"  └── {target}")
                    else:
                        lines.append(f"  ├── {target}")

        return "\n".join(lines)

    @staticmethod
    def _generate_matrix_graph(
        dependencies: Dict[str, List[str]], modules: List[str]
    ) -> str:
        """为大型项目生成依赖关系矩阵"""
        matrix, sorted_modules = DependencyVisualizer.create_dependency_matrix(
            dependencies, modules
        )

        lines = ["依赖关系矩阵:"]

        # 创建列标题（使用缩写）
        max_name_length = min(10, max(len(mod) for mod in sorted_modules))
        header = "    "  # 左侧空间

        # 添加列标签
        for j, mod in enumerate(sorted_modules):
            name = mod[:max_name_length]
            header += f"{j:02d} "

        lines.append(header)
        lines.append("    " + "-" * (len(sorted_modules) * 3))

        # 添加矩阵行
        for i, mod in enumerate(sorted_modules):
            name = mod[:max_name_length]
            row = f"{i:02d}| "

            for j in range(len(sorted_modules)):
                row += f" {matrix[i][j]} "

            lines.append(row)

        # 添加图例
        lines.append("")
        lines.append("图例:")
        lines.append("X = 自引用")
        lines.append("● = 依赖关系")

        # 添加模块索引
        lines.append("")
        lines.append("模块索引:")
        for i, mod in enumerate(sorted_modules):
            lines.append(f"{i:02d} = {mod}")

        return "\n".join(lines)


class OutputFormatter:
    """格式化分析结果输出"""

    @staticmethod
    def format(result: Dict, config: Dict) -> str:
        """根据配置的输出格式格式化结果"""
        formatters = {
            "text": OutputFormatter._text_format,
            "markdown": OutputFormatter._markdown_format,
            "json": OutputFormatter._json_format,
        }
        return formatters[config["output_format"]](result, config)

    @staticmethod
    def _text_format(result: Dict, config: Dict) -> str:
        """格式化结果为纯文本"""
        output = [
            f"{Colors.BOLD}{Colors.CYAN}===== Python项目分析报告 ====={Colors.RESET}\n"
        ]

        # 质量评分摘要
        output.append(f"{Colors.BOLD}项目质量评分{Colors.RESET}")
        summary = result.get("quality_summary", {})
        if summary:
            score = summary.get("quality_score", 0)
            category = summary.get("quality_category", "未知")
            category_color = QualityScoreCalculator.get_score_category(score)[1]

            output.append(
                f"总体质量: {category_color}{score} - {category}{Colors.RESET}"
            )
            output.append(
                f"文档覆盖率: {summary.get('files_with_docstrings_percent', 0)}%"
            )
            output.append(
                f"类型提示覆盖率: {summary.get('files_with_type_hints_percent', 0)}%"
            )
            output.append(f"平均复杂度: {summary.get('average_complexity', 0)}")
            output.append(f"注释比例: {summary.get('comment_to_code_ratio', 0)}%")
            output.append(f"反模式问题: {summary.get('total_antipatterns', 0)}")
            output.append(f"命名规范问题: {summary.get('total_naming_issues', 0)}")
            output.append("")

        # 摘要统计 - 移到这里，在质量评分摘要之后，项目结构之前
        output.append(f"{Colors.BOLD}{Colors.BLUE}=== 项目摘要 ==={Colors.RESET}")
        total = result["total"]
        output.append(f"分析的文件数: {total['files']}")
        output.append(f"总行数: {total['total_lines']}")
        output.append(
            f"代码行: {total['code_lines']} ({OutputFormatter._percentage(total['code_lines'], total['total_lines'])}%)"
        )
        output.append(
            f"注释行: {total['comment_lines']} ({OutputFormatter._percentage(total['comment_lines'], total['total_lines'])}%)"
        )
        output.append(
            f"文档字符串行: {total['docstring_lines']} ({OutputFormatter._percentage(total['docstring_lines'], total['total_lines'])}%)"
        )
        output.append(
            f"空行: {total['blank_lines']} ({OutputFormatter._percentage(total['blank_lines'], total['total_lines'])}%)"
        )
        output.append(f"类数量: {total['classes']}")
        output.append(f"函数数量: {total['functions']}")
        output.append(f"方法数量: {total['methods']}")
        output.append(f"总复杂度: {total['complexity']}")
        output.append(f"检测到的反模式: {total['antipatterns']}")
        output.append(f"命名规范问题: {total['naming_issues']}")
        output.append("")  # 增加一个空行分隔两个部分

        # 项目结构
        output.append(f"{Colors.BOLD}{Colors.BLUE}=== 项目结构 ==={Colors.RESET}")
        for entry in result["structure"]:
            OutputFormatter._format_entry(entry, result, output, 0)

        # 模块依赖关系可视化
        if config["detailed_imports"] and result["dependencies"]:
            output.append(
                f"\n{Colors.BOLD}{Colors.BLUE}=== 模块依赖关系 ==={Colors.RESET}"
            )

            # 生成ASCII依赖图
            dependency_graph = DependencyVisualizer.generate_ascii_dependency_graph(
                result["dependencies"]
            )
            output.append(dependency_graph)

        # 最复杂的文件
        if result["stats"]:
            output.append(
                f"\n{Colors.BOLD}{Colors.BLUE}=== 前10个最复杂的文件 ==={Colors.RESET}"
            )
            complex_files = sorted(
                [
                    (
                        path,
                        stats.get("cyclomatic_complexity", 0),
                        stats.get("quality_score", 0),
                    )
                    for path, stats in result["stats"].items()
                    if isinstance(stats, dict)
                ],
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            for path, complexity, score in complex_files:
                score_color = QualityScoreCalculator.get_score_category(score)[1]
                output.append(
                    f"{path}: 复杂度 {complexity}, 质量评分: {score_color}{score}{Colors.RESET}"
                )

        # 反模式摘要
        if config["detect_antipatterns"]:
            antipattern_files = []
            for path, stats in result["stats"].items():
                if not isinstance(stats, dict):
                    continue
                quality = stats.get("quality", {})
                if (
                    isinstance(quality, dict)
                    and quality.get("antipatterns_count", 0) > 0
                ):
                    antipattern_files.append(
                        (
                            path,
                            quality["antipatterns_count"],
                            quality.get("antipatterns", []),
                        )
                    )

            if antipattern_files:
                output.append(
                    f"\n{Colors.BOLD}{Colors.YELLOW}=== 含有反模式的文件 ==={Colors.RESET}"
                )
                for path, count, patterns in sorted(
                    antipattern_files, key=lambda x: x[1], reverse=True
                )[:10]:
                    output.append(f"{path}: {count} 个反模式")
                    for pattern in patterns[:3]:  # 只显示前3个
                        output.append(f"  - {pattern}")
                    if len(patterns) > 3:
                        output.append(f"  - ... 还有 {len(patterns) - 3} 个")

        # 命名规范问题
        if config["check_naming"]:
            naming_issue_files = []
            for path, stats in result["stats"].items():
                if not isinstance(stats, dict):
                    continue
                quality = stats.get("quality", {})
                if not isinstance(quality, dict):
                    continue
                naming_stats = quality.get("naming_stats", {})
                if (
                    isinstance(naming_stats, dict)
                    and naming_stats.get("bad_names", 0) > 0
                ):
                    naming_issue_files.append(
                        (
                            path,
                            naming_stats["bad_names"],
                            naming_stats.get("naming_issues", []),
                        )
                    )

            if naming_issue_files:
                output.append(
                    f"\n{Colors.BOLD}{Colors.YELLOW}=== 命名规范问题 ==={Colors.RESET}"
                )
                for path, count, issues in sorted(
                    naming_issue_files, key=lambda x: x[1], reverse=True
                )[:10]:
                    output.append(f"{path}: {count} 个命名规范问题")
                    for issue in issues[:3]:  # 只显示前3个
                        output.append(f"  - {issue}")
                    if len(issues) > 3:
                        output.append(f"  - ... 还有 {len(issues) - 3} 个")

        return "\n".join(output)

    @staticmethod
    def _percentage(part, total):
        """计算百分比，保留1位小数"""
        return round((part / total) * 100, 1) if total else 0

    @staticmethod
    def _format_entry(entry: Dict, result: Dict, output: List, level: int):
        """格式化目录或文件条目为文本输出"""
        indent = "    " * level
        prefix = f"{indent}|-- "

        if entry["type"] == "directory":
            output.append(f"{prefix}{Colors.BLUE}{entry['name']}/{Colors.RESET}")
            for child in sorted(
                entry.get("children", []),
                key=lambda x: (x["type"] != "directory", x["name"]),
            ):
                OutputFormatter._format_entry(child, result, output, level + 1)
        else:
            file_info = OutputFormatter._file_info(entry, result)
            if entry["name"].endswith(".py"):
                output.append(
                    f"{prefix}{Colors.CYAN}{entry['name']}{Colors.RESET} {file_info}"
                )
            else:
                output.append(f"{prefix}{entry['name']} {file_info}")

    @staticmethod
    def _file_info(entry: Dict, result: Dict) -> str:
        """格式化文件信息用于显示"""
        stats = result["stats"].get(entry["path"])
        if not isinstance(stats, dict):
            return ""

        info = []
        score = stats.get("quality_score", 0)

        if score > 0:
            score_category, score_color = QualityScoreCalculator.get_score_category(
                score
            )
            info.append(f"质量: {score_color}{score}{Colors.RESET}")

        if stats.get("total_lines", 0) > 0:
            info.append(f"{stats['total_lines']}行")

            if "class_count" in stats and stats["class_count"] > 0:
                info.append(f"{stats['class_count']}类")

            if "function_count" in stats and stats["function_count"] > 0:
                info.append(f"{stats['function_count']}函数")

            if "method_count" in stats and stats["method_count"] > 0:
                info.append(f"{stats['method_count']}方法")

            if "cyclomatic_complexity" in stats and stats["cyclomatic_complexity"] > 0:
                complexity = stats["cyclomatic_complexity"]
                if complexity > 30:
                    info.append(f"复杂度: {Colors.RED}{complexity}{Colors.RESET}")
                elif complexity > 15:
                    info.append(f"复杂度: {Colors.YELLOW}{complexity}{Colors.RESET}")
                else:
                    info.append(f"复杂度: {complexity}")

            quality = stats.get("quality", {})
            if isinstance(quality, dict):
                if quality.get("antipatterns_count", 0) > 0:
                    count = quality["antipatterns_count"]
                    info.append(f"{Colors.YELLOW}{count}个反模式{Colors.RESET}")

                naming_stats = quality.get("naming_stats", {})
                if (
                    isinstance(naming_stats, dict)
                    and naming_stats.get("bad_names", 0) > 0
                ):
                    count = naming_stats["bad_names"]
                    info.append(f"{Colors.YELLOW}{count}个命名问题{Colors.RESET}")

        if entry.get("size"):
            info.append(f"{OutputFormatter._format_size(entry['size'])}")

        return f"({', '.join(info)})" if info else ""

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小使其易于阅读"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"

    @staticmethod
    def _markdown_format(result: Dict, config: Dict) -> str:
        """格式化结果为Markdown"""
        config_no_color = config.copy()
        config_no_color["color_output"] = False

        # 生成没有颜色代码的纯文本
        Colors.disable()
        text = OutputFormatter._text_format(result, config_no_color)

        # 恢复颜色支持
        if config["color_output"] and Colors.supports_color():
            Colors.RESET = "\033[0m"
            Colors.BOLD = "\033[1m"
            Colors.RED = "\033[31m"
            Colors.GREEN = "\033[32m"
            Colors.YELLOW = "\033[33m"
            Colors.BLUE = "\033[34m"
            Colors.MAGENTA = "\033[35m"
            Colors.CYAN = "\033[36m"
            Colors.GRAY = "\033[90m"

        return f"# Python项目分析报告\n\n```\n{text}\n```"

    @staticmethod
    def _json_format(result: Dict, config: Dict) -> str:
        """格式化结果为JSON"""
        return json.dumps(result, indent=2, ensure_ascii=False)


def parse_args():
    """解析命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description="Python代码库分析工具")
    parser.add_argument(
        "path", nargs="?", default=".", help="Python项目路径（默认：当前目录）"
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="输出格式",
    )
    parser.add_argument("--max-workers", type=int, default=4, help="最大并行工作线程数")
    parser.add_argument(
        "--max-file-size", type=int, default=10, help="要分析的最大文件大小（MB）"
    )
    parser.add_argument(
        "--no-antipatterns",
        action="store_false",
        dest="detect_antipatterns",
        help="禁用反模式检测",
    )
    parser.add_argument(
        "--no-complexity",
        action="store_false",
        dest="calculate_complexity",
        help="禁用复杂度计算",
    )
    parser.add_argument(
        "--no-docstrings",
        action="store_false",
        dest="analyze_docstrings",
        help="禁用文档字符串分析",
    )
    parser.add_argument(
        "--no-imports",
        action="store_false",
        dest="detailed_imports",
        help="禁用详细导入分析",
    )
    parser.add_argument(
        "--no-naming",
        action="store_false",
        dest="check_naming",
        help="禁用命名规范检查",
    )
    parser.add_argument(
        "--no-color", action="store_false", dest="color_output", help="禁用彩色输出"
    )
    parser.add_argument("--show-hidden", action="store_true", help="包含隐藏文件和目录")

    # 新增参数，用于直接指定排除目录和文件
    parser.add_argument("--exclude-dirs", type=str, help="要排除的目录列表，逗号分隔")
    parser.add_argument(
        "--exclude-files", type=str, help="要排除的文件模式列表，逗号分隔"
    )
    parser.add_argument(
        "--include-patterns",
        type=str,
        default="*.py",
        help="要包含的文件模式列表，逗号分隔，默认为 *.py",
    )

    args = parser.parse_args()

    # 使用命令行参数更新配置
    CONFIG["target_path"] = args.path
    CONFIG["output_format"] = args.format
    CONFIG["max_workers"] = args.max_workers
    CONFIG["max_file_size_mb"] = args.max_file_size
    CONFIG["detect_antipatterns"] = args.detect_antipatterns
    CONFIG["calculate_complexity"] = args.calculate_complexity
    CONFIG["analyze_docstrings"] = args.analyze_docstrings
    CONFIG["detailed_imports"] = args.detailed_imports
    CONFIG["check_naming"] = args.check_naming
    CONFIG["color_output"] = args.color_output
    CONFIG["show_hidden"] = args.show_hidden

    # 处理排除目录参数
    if args.exclude_dirs:
        CONFIG["exclude_dirs"] = [dir.strip() for dir in args.exclude_dirs.split(",")]

    # 处理排除文件参数
    if args.exclude_files:
        CONFIG["exclude_files"] = [
            pattern.strip() for pattern in args.exclude_files.split(",")
        ]

    # 处理包含模式参数
    if args.include_patterns:
        CONFIG["include_patterns"] = [
            pattern.strip() for pattern in args.include_patterns.split(",")
        ]

    return args


# 在 if __name__ == "__main__": 部分进行如下修改
if __name__ == "__main__":
    try:
        # 保存用户自定义的目标路径（如果已设置）
        user_target_path = CONFIG.get("target_path", ".")

        # 解析命令行参数
        args = parse_args()

        # 如果命令行未指定路径但用户在代码中已设置了路径，则恢复用户设置
        if args.path == "." and user_target_path != ".":
            CONFIG["target_path"] = user_target_path

        # 禁用彩色输出（如果需要）
        if not CONFIG["color_output"]:
            Colors.disable()

        print(
            # f"{Colors.CYAN}正在分析路径: {Colors.BOLD}{CONFIG['target_path']}{Colors.RESET}"
        )

        # 运行分析
        analyzer = PythonProjectAnalyzer(CONFIG)
        result = analyzer.analyze()

        # 输出结果
        print(OutputFormatter.format(result, CONFIG))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}操作被用户取消{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}错误: {str(e)}{Colors.RESET}")
        import traceback

        traceback.print_exc()
