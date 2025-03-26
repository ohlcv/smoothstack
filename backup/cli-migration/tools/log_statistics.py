#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
开发日志统计工具

这个脚本用于分析项目的开发日志，生成统计数据和报表，帮助项目管理和进度跟踪。
主要功能包括：
1. 解析开发日志文件，提取任务、问题和进度数据
2. 统计完成任务数、未完成任务数、问题解决情况
3. 按日期、标签、内容类型进行数据分组和分析
4. 生成统计报表，包括文本报表和可视化图表
5. 与Git提交历史关联，提供更完整的开发活动视图

使用方法:
    python log_statistics.py --dir ../docs/开发日志 --report summary
    python log_statistics.py --file ../docs/开发日志/2024-04-25.md --report detailed
"""

import os
import re
import sys
import argparse
import datetime
import subprocess
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional, Any, Union
from pathlib import Path


@dataclass
class Task:
    """表示开发日志中的一个任务项"""

    description: str
    completed: bool
    date: datetime.date
    log_file: str
    time_spent: float = 0.0  # 任务耗时（小时）
    completion_percentage: float = 0.0  # 完成百分比（0-100）
    tags: List[str] = None


@dataclass
class Problem:
    """表示开发日志中的一个问题项"""

    title: str
    description: str
    solution: str
    status: str  # "已解决", "未解决", "部分解决"
    date: datetime.date
    log_file: str
    tags: List[str] = None


@dataclass
class LogEntry:
    """表示一个开发日志文件的解析结果"""

    date: datetime.date
    file_path: str
    title: str
    overview: str
    tasks: List[Task]
    problems: List[Problem]
    tags: List[str]
    plans: List[str]
    notes: str


class LogParser:
    """开发日志解析器"""

    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        # 日期格式为：YYYY-MM-DD
        self.date_pattern = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
        # 任务格式为：- [x] 或 - [ ]
        self.task_pattern = re.compile(r"- \[([ x])\] (.*)")
        # 时间花费格式为：(1.5h) 或 (2h)
        self.time_spent_pattern = re.compile(r"\((\d+\.?\d*)h\)")
        # 完成度格式为：完成度50% 或 完成度：50%
        self.completion_pattern = re.compile(r"完成度[：:]?(\d+)%")
        # 标签格式为：标签: tag1, tag2
        self.tags_pattern = re.compile(r"标签[:：] *(.*)")

    def parse_all_logs(self) -> List[LogEntry]:
        """解析日志目录中的所有日志文件"""
        log_entries = []
        log_files = self._get_log_files()

        for log_file in log_files:
            try:
                entry = self.parse_log_file(log_file)
                if entry:
                    log_entries.append(entry)
            except Exception as e:
                print(f"Error parsing {log_file}: {e}")

        return sorted(log_entries, key=lambda x: x.date)

    def parse_log_file(self, file_path: str) -> Optional[LogEntry]:
        """解析单个日志文件"""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析日期
        date_match = self.date_pattern.search(os.path.basename(file_path))
        if not date_match:
            print(f"Cannot parse date from filename: {file_path}")
            return None

        year, month, day = map(int, date_match.groups())
        date = datetime.date(year, month, day)

        # 解析标题
        title = self._extract_section(content, r"# (.*)", "")

        # 解析标签
        tags = []
        tags_match = self.tags_pattern.search(content)
        if tags_match:
            tags = [tag.strip() for tag in tags_match.group(1).split(",")]

        # 解析各个部分
        overview = self._extract_section(
            content, r"## 今日概览\s+(.*?)(?=##|\Z)", "", multiline=True
        )
        tasks_section = self._extract_section(
            content, r"## 完成的任务\s+(.*?)(?=##|\Z)", "", multiline=True
        )
        problems_section = self._extract_section(
            content, r"## 遇到的问题\s+(.*?)(?=##|\Z)", "", multiline=True
        )
        plans_section = self._extract_section(
            content, r"## 明日计划\s+(.*?)(?=##|\Z)", "", multiline=True
        )
        notes = self._extract_section(
            content, r"## 备注\s+(.*?)(?=##|\Z)", "", multiline=True
        )

        # 解析任务
        tasks = self._parse_tasks(tasks_section, date, file_path)

        # 解析问题
        problems = self._parse_problems(problems_section, date, file_path)

        # 解析计划
        plans = self._parse_plans(plans_section)

        return LogEntry(
            date=date,
            file_path=file_path,
            title=title,
            overview=overview,
            tasks=tasks,
            problems=problems,
            tags=tags,
            plans=plans,
            notes=notes,
        )

    def _get_log_files(self) -> List[str]:
        """获取日志目录中所有的日志文件"""
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.endswith(".md") and self.date_pattern.search(file):
                log_files.append(os.path.join(self.log_dir, file))
        return log_files

    def _extract_section(
        self, content: str, pattern: str, default: str, multiline: bool = False
    ) -> str:
        """从内容中提取特定部分"""
        if multiline:
            matches = re.search(pattern, content, re.DOTALL)
        else:
            matches = re.search(pattern, content)

        if matches:
            return matches.group(1).strip()
        return default

    def _parse_tasks(
        self, tasks_section: str, date: datetime.date, file_path: str
    ) -> List[Task]:
        """解析任务部分"""
        tasks = []
        if not tasks_section:
            return tasks

        for line in tasks_section.split("\n"):
            task_match = self.task_pattern.match(line.strip())
            if task_match:
                completed = task_match.group(1) == "x"
                description = task_match.group(2)

                # 解析任务花费时间
                time_spent = 0.0
                time_match = self.time_spent_pattern.search(description)
                if time_match:
                    time_spent = float(time_match.group(1))

                # 解析完成百分比
                completion_percentage = 100.0 if completed else 0.0
                completion_match = self.completion_pattern.search(description)
                if completion_match:
                    completion_percentage = float(completion_match.group(1))

                task = Task(
                    description=description,
                    completed=completed,
                    date=date,
                    log_file=file_path,
                    time_spent=time_spent,
                    completion_percentage=completion_percentage,
                )
                tasks.append(task)

        return tasks

    def _parse_problems(
        self, problems_section: str, date: datetime.date, file_path: str
    ) -> List[Problem]:
        """解析问题部分"""
        problems = []
        if not problems_section:
            return problems

        # 分割各个问题
        problem_blocks = re.split(r"###\s+", problems_section)
        # 跳过第一个（可能是空的）
        problem_blocks = problem_blocks[1:] if len(problem_blocks) > 1 else []

        for block in problem_blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue

            title = lines[0].strip()
            description = ""
            solution = ""
            status = "未定义"

            for line in lines[1:]:
                line = line.strip()
                if line.startswith("- 描述："):
                    description = line[5:].strip()
                elif line.startswith("- 解决方案："):
                    solution = line[7:].strip()
                elif line.startswith("- 状态："):
                    status = line[5:].strip()

            problem = Problem(
                title=title,
                description=description,
                solution=solution,
                status=status,
                date=date,
                log_file=file_path,
            )
            problems.append(problem)

        return problems

    def _parse_plans(self, plans_section: str) -> List[str]:
        """解析计划部分"""
        plans = []
        if not plans_section:
            return plans

        for line in plans_section.split("\n"):
            plan_match = self.task_pattern.match(line.strip())
            if plan_match:
                plans.append(plan_match.group(2))

        return plans


class StatisticsAnalyzer:
    """统计分析器"""

    def __init__(self, log_entries: List[LogEntry]):
        self.log_entries = log_entries

    def get_total_statistics(self) -> Dict[str, Any]:
        """获取总体统计数据"""
        total_logs = len(self.log_entries)
        completed_tasks = sum(
            len([t for t in entry.tasks if t.completed]) for entry in self.log_entries
        )
        pending_tasks = sum(
            len([t for t in entry.tasks if not t.completed])
            for entry in self.log_entries
        )

        problem_statuses = Counter()
        for entry in self.log_entries:
            for problem in entry.problems:
                problem_statuses[problem.status] += 1

        # 统计每月的任务情况
        monthly_stats = defaultdict(lambda: {"planned": 0, "completed": 0})
        for entry in self.log_entries:
            month_key = f"{entry.date.year}年{entry.date.month}月"
            monthly_stats[month_key]["planned"] += len(entry.tasks) + len(entry.plans)
            monthly_stats[month_key]["completed"] += len(
                [t for t in entry.tasks if t.completed]
            )

        # 计算完成率
        for stats in monthly_stats.values():
            if stats["planned"] > 0:
                stats["completion_rate"] = round(
                    stats["completed"] / stats["planned"] * 100, 1
                )
            else:
                stats["completion_rate"] = 0

        # 标签统计
        all_tags = []
        for entry in self.log_entries:
            all_tags.extend(entry.tags)
        tag_counts = Counter(all_tags)

        return {
            "total_logs": total_logs,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "problem_statuses": dict(problem_statuses),
            "monthly_stats": dict(monthly_stats),
            "tag_counts": dict(tag_counts),
        }

    def get_task_completion_trend(self) -> Dict[str, List[int]]:
        """获取任务完成趋势"""
        dates = []
        completed = []
        pending = []

        # 按日期排序
        sorted_entries = sorted(self.log_entries, key=lambda x: x.date)

        for entry in sorted_entries:
            dates.append(entry.date.strftime("%Y-%m-%d"))
            completed.append(len([t for t in entry.tasks if t.completed]))
            pending.append(len([t for t in entry.tasks if not t.completed]))

        return {"dates": dates, "completed": completed, "pending": pending}

    def get_tag_statistics(self) -> Dict[str, Dict[str, int]]:
        """获取标签统计"""
        # 按类别分组标签
        tech_tags = defaultdict(int)  # 技术类别
        module_tags = defaultdict(int)  # 功能模块
        phase_tags = defaultdict(int)  # 开发阶段

        # 预定义的标签分类
        tech_categories = {
            "前端",
            "后端",
            "数据库",
            "Docker",
            "CLI",
            "TypeScript",
            "Python",
            "Node.js",
        }
        module_categories = {
            "依赖管理",
            "容器管理",
            "跨平台",
            "环境管理",
            "文件同步",
            "认证",
            "日志系统",
            "配置",
        }
        phase_categories = {"规划", "实现", "重构", "测试", "部署", "项目管理", "文档"}

        for entry in self.log_entries:
            for tag in entry.tags:
                tag = tag.strip()
                if tag in tech_categories:
                    tech_tags[tag] += 1
                elif tag in module_categories:
                    module_tags[tag] += 1
                elif tag in phase_categories:
                    phase_tags[tag] += 1

        return {
            "tech_tags": dict(tech_tags),
            "module_tags": dict(module_tags),
            "phase_tags": dict(phase_tags),
        }

    def get_time_spent_statistics(self) -> Dict[str, float]:
        """获取时间花费统计"""
        total_time = 0
        time_by_tag = defaultdict(float)

        for entry in self.log_entries:
            for task in entry.tasks:
                if task.time_spent > 0:
                    total_time += task.time_spent
                    for tag in entry.tags:
                        time_by_tag[tag] += task.time_spent / len(entry.tags)

        return {"total_time": total_time, "time_by_tag": dict(time_by_tag)}


class ReportGenerator:
    """报表生成器"""

    def __init__(self, analyzer: StatisticsAnalyzer):
        self.analyzer = analyzer

    def generate_summary_report(self) -> str:
        """生成摘要报表"""
        stats = self.analyzer.get_total_statistics()
        tag_stats = self.analyzer.get_tag_statistics()
        time_stats = self.analyzer.get_time_spent_statistics()

        report = [
            "# 开发日志统计摘要报表",
            "",
            f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 总体统计",
            "",
            f"- 总日志数: {stats['total_logs']}",
            f"- 完成任务数: {stats['completed_tasks']}",
            f"- 未完成任务数: {stats['pending_tasks']}",
            f"- 总记录工时: {time_stats['total_time']:.1f}小时",
            "",
            "## 问题状态统计",
            "",
        ]

        for status, count in stats["problem_statuses"].items():
            report.append(f"- {status}: {count}")

        report.extend(
            [
                "",
                "## 月度任务完成情况",
                "",
                "| 月份 | 计划任务 | 完成任务 | 完成率 |",
                "| ---- | -------- | -------- | ------ |",
            ]
        )

        for month, month_stats in sorted(stats["monthly_stats"].items()):
            report.append(
                f"| {month} | {month_stats['planned']} | {month_stats['completed']} | "
                f"{month_stats['completion_rate']}% |"
            )

        report.extend(["", "## 标签统计", "", "### 技术类别", ""])

        for tag, count in sorted(tag_stats["tech_tags"].items(), key=lambda x: -x[1]):
            report.append(f"- {tag}: {count}")

        report.extend(["", "### 功能模块", ""])

        for tag, count in sorted(tag_stats["module_tags"].items(), key=lambda x: -x[1]):
            report.append(f"- {tag}: {count}")

        report.extend(["", "### 开发阶段", ""])

        for tag, count in sorted(tag_stats["phase_tags"].items(), key=lambda x: -x[1]):
            report.append(f"- {tag}: {count}")

        return "\n".join(report)

    def generate_detailed_report(self) -> str:
        """生成详细报表"""
        stats = self.analyzer.get_total_statistics()
        tag_stats = self.analyzer.get_tag_statistics()
        time_stats = self.analyzer.get_time_spent_statistics()
        trend_data = self.analyzer.get_task_completion_trend()

        # 基础摘要部分
        report = self.generate_summary_report().split("\n")

        # 增加详细统计部分
        report.extend(
            [
                "",
                "## 时间花费统计",
                "",
                f"总记录工时: {time_stats['total_time']:.1f}小时",
                "",
                "### 按标签统计工时",
                "",
                "| 标签 | 工时 | 占比 |",
                "| ---- | ---- | ---- |",
            ]
        )

        for tag, hours in sorted(
            time_stats["time_by_tag"].items(), key=lambda x: -x[1]
        ):
            percentage = (
                hours / time_stats["total_time"] * 100
                if time_stats["total_time"] > 0
                else 0
            )
            report.append(f"| {tag} | {hours:.1f}小时 | {percentage:.1f}% |")

        report.extend(
            [
                "",
                "## 任务完成趋势",
                "",
                "| 日期 | 完成任务 | 未完成任务 |",
                "| ---- | -------- | ---------- |",
            ]
        )

        for i in range(len(trend_data["dates"])):
            report.append(
                f"| {trend_data['dates'][i]} | {trend_data['completed'][i]} | "
                f"{trend_data['pending'][i]} |"
            )

        return "\n".join(report)

    def save_report(self, report: str, output_file: str):
        """保存报表到文件"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {output_file}")


class GitIntegrator:
    """Git集成器，用于与Git提交历史关联"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_commits_for_date(self, date: datetime.date) -> List[Dict[str, str]]:
        """获取指定日期的Git提交"""
        date_str = date.strftime("%Y-%m-%d")
        next_date = (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--after",
                    f"{date_str} 00:00:00",
                    "--before",
                    f"{next_date} 00:00:00",
                    "--pretty=format:%h|%s|%an",
                ],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                print(f"Error getting commits: {result.stderr}")
                return []

            commits = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    parts = line.split("|", 2)
                    if len(parts) == 3:
                        hash_id, message, author = parts
                        commits.append(
                            {"hash": hash_id, "message": message, "author": author}
                        )

            return commits

        except Exception as e:
            print(f"Error accessing git repository: {e}")
            return []


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Development Log Statistics Tool")
    parser.add_argument("--dir", type=str, help="Directory containing log files")
    parser.add_argument("--file", type=str, help="Single log file to analyze")
    parser.add_argument(
        "--report",
        choices=["summary", "detailed"],
        default="summary",
        help="Type of report to generate",
    )
    parser.add_argument("--output", type=str, help="Output file for the report")
    parser.add_argument(
        "--git-repo", type=str, help="Path to git repository for commit integration"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    if not args.dir and not args.file:
        print("Error: Either --dir or --file must be specified")
        return 1

    # 确定日志目录
    log_dir = args.dir or os.path.dirname(args.file)

    # 创建解析器
    parser = LogParser(log_dir)

    # 解析日志
    if args.file:
        entries = [parser.parse_log_file(args.file)]
        # 过滤掉None
        entries = [e for e in entries if e]
    else:
        entries = parser.parse_all_logs()

    if not entries:
        print("No valid log entries found")
        return 1

    print(f"Found {len(entries)} log entries")

    # 创建分析器
    analyzer = StatisticsAnalyzer(entries)

    # 创建报表生成器
    report_generator = ReportGenerator(analyzer)

    # 生成报表
    if args.report == "summary":
        report = report_generator.generate_summary_report()
    else:
        report = report_generator.generate_detailed_report()

    # 如果指定了输出文件，则保存报表
    if args.output:
        report_generator.save_report(report, args.output)
    else:
        print(report)

    # 如果指定了Git仓库，尝试集成Git提交信息
    if args.git_repo:
        git_integrator = GitIntegrator(args.git_repo)
        for entry in entries:
            commits = git_integrator.get_commits_for_date(entry.date)
            if commits:
                print(f"\nGit commits for {entry.date}:")
                for commit in commits:
                    print(
                        f"  {commit['hash']} - {commit['message']} ({commit['author']})"
                    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
