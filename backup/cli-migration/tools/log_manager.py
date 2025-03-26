#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
开发日志管理工具

这个模块提供了命令行界面，用于创建、更新和管理项目开发日志。
主要功能包括：
1. 创建新的开发日志文件，基于标准模板
2. 更新开发日志索引和统计报告
3. 根据日期、标签或内容搜索开发日志
4. 查看日志及其统计信息

使用方法:
    python log_manager.py create --tags "前端,依赖管理"
    python log_manager.py update-index
    python log_manager.py search --tag Docker --since 2024-04-01
"""

import os
import re
import sys
import argparse
import datetime
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any

# 导入日志统计模块
try:
    from log_statistics import LogParser, StatisticsAnalyzer, ReportGenerator
except ImportError:
    from backend.tools.log_statistics import (
        LogParser,
        StatisticsAnalyzer,
        ReportGenerator,
    )


class LogManager:
    """开发日志管理器类"""

    def __init__(self, log_dir: str):
        """
        初始化日志管理器

        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = log_dir
        self.template_path = os.path.join(log_dir, "开发日志写作指南.md")
        self.index_path = os.path.join(log_dir, "日志索引.md")
        self.stats_path = os.path.join(log_dir, "日志统计报告.md")

        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)

    def create_log(
        self, tags: List[str] = None, date: Optional[datetime.date] = None
    ) -> str:
        """
        创建新的开发日志文件

        Args:
            tags: 日志标签列表
            date: 日志日期，默认为今天

        Returns:
            创建的日志文件路径
        """
        if date is None:
            date = datetime.date.today()

        # 构建文件名和路径
        file_name = f"{date.strftime('%Y-%m-%d')}.md"
        file_path = os.path.join(self.log_dir, file_name)

        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f"警告: 日志文件 {file_name} 已存在，将覆盖现有内容。")

        # 创建日志内容
        content = self._generate_log_template(date, tags)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"成功创建日志文件: {file_path}")
        return file_path

    def update_index(self) -> None:
        """更新日志索引文件"""
        print("正在更新日志索引...")

        # 解析所有日志
        parser = LogParser(self.log_dir)
        entries = parser.parse_all_logs()

        if not entries:
            print("未找到有效的日志条目")
            return

        # 按年月分组
        entries_by_month = {}
        for entry in entries:
            year_month = f"{entry.date.year}年{entry.date.month}月"
            if year_month not in entries_by_month:
                entries_by_month[year_month] = []
            entries_by_month[year_month].append(entry)

        # 生成索引文件内容
        content = [
            "# Smoothstack 开发日志索引",
            "",
            f"*最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## 日志按日期索引",
            "",
        ]

        # 按时间倒序添加月份
        for year_month in sorted(entries_by_month.keys(), reverse=True):
            content.append(f"### {year_month}")
            content.append("")

            # 按日期倒序添加日志条目
            month_entries = sorted(
                entries_by_month[year_month], key=lambda x: x.date, reverse=True
            )
            for entry in month_entries:
                date_str = entry.date.strftime("%Y-%m-%d")
                file_name = os.path.basename(entry.file_path)

                # 从概览中提取简短描述
                description = (
                    entry.overview.split("\n")[0][:50] + "..."
                    if entry.overview
                    else "无概览"
                )

                # 提取完成的任务数量
                completed_tasks = len([t for t in entry.tasks if t.completed])
                total_tasks = len(entry.tasks)

                # 格式化标签
                tags_str = ", ".join(entry.tags) if entry.tags else ""

                content.append(f"- [{date_str}]({file_name}) - {description}")
                content.append(f"  - 任务: {completed_tasks}/{total_tasks} 已完成")
                if tags_str:
                    content.append(f"  - 标签: {tags_str}")
                content.append("")

        # 添加标签索引
        content.extend(["## 标签索引", ""])

        # 收集标签和对应的日志
        tags_map = {}
        for entry in entries:
            for tag in entry.tags:
                if tag not in tags_map:
                    tags_map[tag] = []
                tags_map[tag].append(entry)

        # 按分类组织标签
        tech_tags = []
        module_tags = []
        phase_tags = []
        other_tags = []

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
            "脚本开发",
        }
        phase_categories = {"规划", "实现", "重构", "测试", "部署", "项目管理", "文档"}

        # 分类标签
        for tag in sorted(tags_map.keys()):
            if tag in tech_categories:
                tech_tags.append(tag)
            elif tag in module_categories:
                module_tags.append(tag)
            elif tag in phase_categories:
                phase_tags.append(tag)
            else:
                other_tags.append(tag)

        # 添加技术类别标签
        if tech_tags:
            content.append("### 技术类别")
            content.append("")
            for tag in tech_tags:
                content.append(f"- {tag}")
                for entry in tags_map[tag]:
                    date_str = entry.date.strftime("%Y-%m-%d")
                    file_name = os.path.basename(entry.file_path)
                    content.append(f"  - [{date_str}]({file_name})")
                content.append("")

        # 添加功能模块标签
        if module_tags:
            content.append("### 功能模块")
            content.append("")
            for tag in module_tags:
                content.append(f"- {tag}")
                for entry in tags_map[tag]:
                    date_str = entry.date.strftime("%Y-%m-%d")
                    file_name = os.path.basename(entry.file_path)
                    content.append(f"  - [{date_str}]({file_name})")
                content.append("")

        # 添加开发阶段标签
        if phase_tags:
            content.append("### 开发阶段")
            content.append("")
            for tag in phase_tags:
                content.append(f"- {tag}")
                for entry in tags_map[tag]:
                    date_str = entry.date.strftime("%Y-%m-%d")
                    file_name = os.path.basename(entry.file_path)
                    content.append(f"  - [{date_str}]({file_name})")
                content.append("")

        # 添加其他标签
        if other_tags:
            content.append("### 其他")
            content.append("")
            for tag in other_tags:
                content.append(f"- {tag}")
                for entry in tags_map[tag]:
                    date_str = entry.date.strftime("%Y-%m-%d")
                    file_name = os.path.basename(entry.file_path)
                    content.append(f"  - [{date_str}]({file_name})")
                content.append("")

        # 写入索引文件
        with open(self.index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"日志索引已更新: {self.index_path}")

    def update_statistics(self) -> None:
        """更新日志统计报告"""
        print("正在更新日志统计报告...")

        # 解析所有日志
        parser = LogParser(self.log_dir)
        entries = parser.parse_all_logs()

        if not entries:
            print("未找到有效的日志条目")
            return

        # 创建分析器
        analyzer = StatisticsAnalyzer(entries)

        # 创建报表生成器
        report_generator = ReportGenerator(analyzer)

        # 生成详细报表
        report = report_generator.generate_detailed_report()

        # 写入统计报告文件
        with open(self.stats_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"日志统计报告已更新: {self.stats_path}")

    def search_logs(
        self,
        keyword: str = None,
        tag: str = None,
        since: datetime.date = None,
        until: datetime.date = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索日志

        Args:
            keyword: 关键词
            tag: 标签
            since: 起始日期
            until: 截止日期

        Returns:
            匹配的日志条目列表
        """
        print("正在搜索日志...")

        # 解析所有日志
        parser = LogParser(self.log_dir)
        entries = parser.parse_all_logs()

        if not entries:
            print("未找到有效的日志条目")
            return []

        # 过滤结果
        results = []
        for entry in entries:
            # 过滤日期
            if since and entry.date < since:
                continue
            if until and entry.date > until:
                continue

            # 过滤标签
            if tag and tag not in entry.tags:
                continue

            # 过滤关键词
            if keyword:
                keyword_lower = keyword.lower()
                overview_match = keyword_lower in entry.overview.lower()
                title_match = keyword_lower in entry.title.lower()
                tasks_match = any(
                    keyword_lower in task.description.lower() for task in entry.tasks
                )
                problems_match = any(
                    keyword_lower in problem.title.lower()
                    or keyword_lower in problem.description.lower()
                    for problem in entry.problems
                )

                if not (overview_match or title_match or tasks_match or problems_match):
                    continue

            # 添加到结果
            results.append(
                {
                    "date": entry.date,
                    "file_path": entry.file_path,
                    "title": entry.title,
                    "overview": (
                        entry.overview[:100] + "..."
                        if len(entry.overview) > 100
                        else entry.overview
                    ),
                    "completed_tasks": len([t for t in entry.tasks if t.completed]),
                    "total_tasks": len(entry.tasks),
                    "tags": entry.tags,
                }
            )

        # 按日期排序结果
        results.sort(key=lambda x: x["date"], reverse=True)

        # 打印结果
        if results:
            print(f"找到 {len(results)} 条匹配的日志:")
            for i, result in enumerate(results):
                date_str = result["date"].strftime("%Y-%m-%d")
                print(f"{i+1}. [{date_str}] {result['title']}")
                print(f"   概览: {result['overview']}")
                print(
                    f"   任务: {result['completed_tasks']}/{result['total_tasks']} 已完成"
                )
                if result["tags"]:
                    print(f"   标签: {', '.join(result['tags'])}")
                print()
        else:
            print("未找到匹配的日志")

        return results

    def view_log(self, date_str: str = None) -> str:
        """
        查看指定日期的日志

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            日志内容
        """
        # 如果未指定日期，使用今天的日期
        if not date_str:
            date = datetime.date.today()
            date_str = date.strftime("%Y-%m-%d")

        # 构建文件路径
        file_path = os.path.join(self.log_dir, f"{date_str}.md")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 日志文件 {date_str}.md 不存在")
            return ""

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 打印内容
        print(f"日志 {date_str}:")
        print("-" * 40)
        print(content)

        return content

    def _generate_log_template(
        self, date: datetime.date, tags: List[str] = None
    ) -> str:
        """
        生成日志模板内容

        Args:
            date: 日志日期
            tags: 日志标签列表

        Returns:
            生成的模板内容
        """
        date_str = date.strftime("%Y-%m-%d")
        tags_str = ", ".join(tags) if tags else ""

        # 基础模板
        template = f"""# 开发日志：{date_str}

标签: {tags_str}

## 今日概览
今日主要工作内容和成果概述...

## 完成的任务
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3

## 遇到的问题
### 问题1：问题标题
- 描述：问题的详细描述
- 解决方案：解决方案的详细说明
- 状态：未解决 / 已解决 / 部分解决

## 明日计划
- [ ] 计划任务1
- [ ] 计划任务2
- [ ] 计划任务3

## 备注
其他需要说明的事项...
"""
        return template


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Development Log Management Tool")

    # 设置全局选项
    parser.add_argument(
        "--log-dir", type=str, default="docs/开发日志", help="日志目录路径"
    )

    # 设置子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 创建日志命令
    create_parser = subparsers.add_parser("create", help="创建新的日志")
    create_parser.add_argument("--tags", type=str, help="日志标签，多个标签用逗号分隔")
    create_parser.add_argument(
        "--date", type=str, help="日志日期 (YYYY-MM-DD)，默认为今天"
    )

    # 更新索引命令
    subparsers.add_parser("update-index", help="更新日志索引")

    # 更新统计报告命令
    subparsers.add_parser("update-stats", help="更新日志统计报告")

    # 搜索日志命令
    search_parser = subparsers.add_parser("search", help="搜索日志")
    search_parser.add_argument("--keyword", type=str, help="搜索关键词")
    search_parser.add_argument("--tag", type=str, help="搜索标签")
    search_parser.add_argument("--since", type=str, help="起始日期 (YYYY-MM-DD)")
    search_parser.add_argument("--until", type=str, help="截止日期 (YYYY-MM-DD)")

    # 查看日志命令
    view_parser = subparsers.add_parser("view", help="查看日志")
    view_parser.add_argument(
        "--date", type=str, help="日志日期 (YYYY-MM-DD)，默认为今天"
    )

    # 更新所有命令
    subparsers.add_parser("update-all", help="更新索引和统计报告")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 创建日志管理器
    log_manager = LogManager(args.log_dir)

    # 处理命令
    if args.command == "create":
        # 解析标签
        tags = args.tags.split(",") if args.tags else []

        # 解析日期
        date = None
        if args.date:
            try:
                date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
            except ValueError:
                print(f"错误: 无效的日期格式 {args.date}，请使用 YYYY-MM-DD 格式")
                return 1

        # 创建日志
        log_manager.create_log(tags=tags, date=date)

    elif args.command == "update-index":
        log_manager.update_index()

    elif args.command == "update-stats":
        log_manager.update_statistics()

    elif args.command == "search":
        # 解析日期
        since = None
        if args.since:
            try:
                since = datetime.datetime.strptime(args.since, "%Y-%m-%d").date()
            except ValueError:
                print(f"错误: 无效的起始日期格式 {args.since}，请使用 YYYY-MM-DD 格式")
                return 1

        until = None
        if args.until:
            try:
                until = datetime.datetime.strptime(args.until, "%Y-%m-%d").date()
            except ValueError:
                print(f"错误: 无效的截止日期格式 {args.until}，请使用 YYYY-MM-DD 格式")
                return 1

        # 搜索日志
        log_manager.search_logs(
            keyword=args.keyword, tag=args.tag, since=since, until=until
        )

    elif args.command == "view":
        log_manager.view_log(args.date)

    elif args.command == "update-all":
        log_manager.update_index()
        log_manager.update_statistics()

    else:
        print("错误: 请指定有效的命令")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
