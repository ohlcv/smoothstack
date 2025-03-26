"""
代码分析命令
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional
from .base import BaseCommand


class AnalyzeCommand(BaseCommand):
    """代码分析命令类"""

    def __init__(self):
        super().__init__()
        self.analyzer_script = (
            self.project_root
            / "core"
            / "scripts"
            / "python-codebase-analyzer-optimized.py"
        )
        self.cache_dir = self.project_root / ".cache" / "analyze"
        self.cache_file = self.cache_dir / "results.json"

    def analyze(self, output_format: str = "text", output_file: Optional[str] = None):
        """分析代码库"""
        self.info("开始分析代码库...")

        if not self.analyzer_script.exists():
            raise RuntimeError(f"分析脚本不存在: {self.analyzer_script}")

        # 计算代码库哈希值
        code_hash = self._calculate_code_hash()

        # 检查缓存
        if self._check_cache(code_hash):
            self.info("使用缓存的分析结果")
            self._load_cache(output_format, output_file)
            return

        try:
            # 构建命令
            cmd = [sys.executable, str(self.analyzer_script)]

            # 添加输出格式参数
            if output_format in ["text", "markdown", "json"]:
                cmd.extend(["--format", output_format])

            # 添加输出文件参数
            if output_file:
                cmd.extend(["--output", output_file])

            # 运行分析脚本
            import subprocess

            subprocess.run(cmd, check=True)

            # 保存缓存
            self._save_cache(code_hash)

            self.success("代码分析完成")
        except subprocess.CalledProcessError as e:
            self.error(f"代码分析失败: {str(e)}")
            raise
        except Exception as e:
            self.error(f"发生错误: {str(e)}")
            raise

    def _calculate_code_hash(self) -> str:
        """计算代码库哈希值"""
        self.info("计算代码库哈希值...")

        # 创建哈希对象
        hasher = hashlib.sha256()

        # 遍历代码文件
        for root, _, files in os.walk(self.project_root):
            # 跳过某些目录
            if any(skip in root for skip in [".git", ".venv", "__pycache__", ".cache"]):
                continue

            # 处理文件
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "rb") as f:
                            hasher.update(f.read())
                    except Exception as e:
                        self.warning(f"无法读取文件 {file_path}: {e}")

        return hasher.hexdigest()

    def _check_cache(self, code_hash: str) -> bool:
        """检查缓存"""
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                return cache_data.get("code_hash") == code_hash
        except Exception:
            return False

    def _load_cache(self, output_format: str, output_file: Optional[str]):
        """加载缓存"""
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                results = cache_data.get("results", {})

            # 根据输出格式处理结果
            if output_format == "text":
                self._print_text_results(results)
            elif output_format == "markdown":
                self._print_markdown_results(results)
            elif output_format == "json":
                self._print_json_results(results, output_file)

        except Exception as e:
            self.error(f"加载缓存失败: {str(e)}")
            raise

    def _save_cache(self, code_hash: str):
        """保存缓存"""
        try:
            # 确保缓存目录存在
            self.create_directory(str(self.cache_dir))

            # 收集分析结果
            results = self._collect_results()

            # 保存缓存
            cache_data = {"code_hash": code_hash, "results": results}

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.error(f"保存缓存失败: {str(e)}")
            raise

    def _collect_results(self) -> Dict:
        """收集分析结果"""
        results = {}

        # 收集文件统计
        results["files"] = self._collect_file_stats()

        # 收集代码统计
        results["code"] = self._collect_code_stats()

        # 收集依赖统计
        results["dependencies"] = self._collect_dependency_stats()

        return results

    def _collect_file_stats(self) -> Dict:
        """收集文件统计"""
        stats = {"total": 0, "python": 0, "other": 0}

        for root, _, files in os.walk(self.project_root):
            if any(skip in root for skip in [".git", ".venv", "__pycache__", ".cache"]):
                continue

            for file in files:
                stats["total"] += 1
                if file.endswith(".py"):
                    stats["python"] += 1
                else:
                    stats["other"] += 1

        return stats

    def _collect_code_stats(self) -> Dict:
        """收集代码统计"""
        stats = {"lines": 0, "comments": 0, "functions": 0, "classes": 0}

        for root, _, files in os.walk(self.project_root):
            if any(skip in root for skip in [".git", ".venv", "__pycache__", ".cache"]):
                continue

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            stats["lines"] += len(content.splitlines())
                            stats["comments"] += content.count("#")
                            stats["functions"] += content.count("def ")
                            stats["classes"] += content.count("class ")
                    except Exception:
                        continue

        return stats

    def _collect_dependency_stats(self) -> Dict:
        """收集依赖统计"""
        stats = {"total": 0, "direct": 0, "indirect": 0}

        try:
            import pkg_resources

            # 获取所有已安装的包
            installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

            # 获取项目依赖
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, "r", encoding="utf-8") as f:
                    requirements = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]

                stats["direct"] = len(requirements)
                stats["total"] = len(installed)
                stats["indirect"] = stats["total"] - stats["direct"]

        except Exception:
            pass

        return stats

    def _print_text_results(self, results: Dict):
        """打印文本格式结果"""
        print("\n代码分析结果:")
        print(f"文件统计:")
        print(f"  总文件数: {results['files']['total']}")
        print(f"  Python文件: {results['files']['python']}")
        print(f"  其他文件: {results['files']['other']}")

        print(f"\n代码统计:")
        print(f"  总行数: {results['code']['lines']}")
        print(f"  注释行数: {results['code']['comments']}")
        print(f"  函数数量: {results['code']['functions']}")
        print(f"  类数量: {results['code']['classes']}")

        print(f"\n依赖统计:")
        print(f"  总依赖数: {results['dependencies']['total']}")
        print(f"  直接依赖: {results['dependencies']['direct']}")
        print(f"  间接依赖: {results['dependencies']['indirect']}")

    def _print_markdown_results(self, results: Dict):
        """打印Markdown格式结果"""
        print("\n# 代码分析结果")

        print("\n## 文件统计")
        print(f"- 总文件数: {results['files']['total']}")
        print(f"- Python文件: {results['files']['python']}")
        print(f"- 其他文件: {results['files']['other']}")

        print("\n## 代码统计")
        print(f"- 总行数: {results['code']['lines']}")
        print(f"- 注释行数: {results['code']['comments']}")
        print(f"- 函数数量: {results['code']['functions']}")
        print(f"- 类数量: {results['code']['classes']}")

        print("\n## 依赖统计")
        print(f"- 总依赖数: {results['dependencies']['total']}")
        print(f"- 直接依赖: {results['dependencies']['direct']}")
        print(f"- 间接依赖: {results['dependencies']['indirect']}")

    def _print_json_results(self, results: Dict, output_file: Optional[str]):
        """打印JSON格式结果"""
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
