#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境一致性验证命令行接口

提供命令行工具，用于验证和确保容器环境与宿主环境的一致性
"""

import os
import json
import logging
import click
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..consistency_manager import consistency_manager

# 设置日志记录
logger = logging.getLogger(__name__)


@click.group(name="consistency", help="环境一致性验证工具")
def consistency_cmd_group():
    """容器环境一致性验证命令组"""
    pass


@consistency_cmd_group.command(name="check", help="检查容器环境与宿主环境的一致性")
@click.argument("container", required=True, type=str)
@click.option(
    "--dependencies/--no-dependencies", default=True, help="是否检查依赖包一致性"
)
@click.option("--env-vars/--no-env-vars", default=True, help="是否检查环境变量一致性")
@click.option("--ports/--no-ports", default=True, help="是否检查端口映射一致性")
@click.option("--files/--no-files", default=True, help="是否检查文件同步一致性")
@click.option(
    "--path", "-p", multiple=True, help="需要检查文件同步的宿主路径（可多次指定）"
)
@click.option(
    "--env-whitelist", "-e", multiple=True, help="环境变量检查白名单（可多次指定）"
)
@click.option("--report/--no-report", default=True, help="是否生成报告文件")
@click.option("--output", "-o", type=str, help="结果输出文件，不指定则打印到控制台")
@click.option("--json", "json_output", is_flag=True, help="以JSON格式输出结果")
def check_consistency(
    container: str,
    dependencies: bool,
    env_vars: bool,
    ports: bool,
    files: bool,
    path: List[str],
    env_whitelist: List[str],
    report: bool,
    output: Optional[str],
    json_output: bool,
):
    """
    检查容器环境与宿主环境的一致性

    CONTAINER: 容器ID或名称
    """
    try:
        result = consistency_manager.run_consistency_check(
            container_id_or_name=container,
            check_dependencies=dependencies,
            check_env_vars=env_vars,
            check_ports=ports,
            check_files=files,
            host_paths=list(path) if path else None,
            env_var_whitelist=list(env_whitelist) if env_whitelist else None,
            generate_report=report,
        )

        # 格式化输出
        if json_output:
            formatted_output = json.dumps(result, indent=2)
        else:
            formatted_output = format_check_result(result)

        # 输出结果
        if output:
            with open(output, "w") as f:
                f.write(formatted_output)
            click.echo(f"结果已保存到: {output}")
        else:
            click.echo(formatted_output)

    except Exception as e:
        logger.error(f"检查一致性时出错: {e}")
        click.echo(f"错误: {e}", err=True)


@consistency_cmd_group.command(name="fix", help="修复容器环境与宿主环境的一致性问题")
@click.argument("container", required=True, type=str)
@click.option("--report", "-r", type=str, required=True, help="一致性检查报告文件路径")
@click.option("--auto-fix/--no-auto-fix", default=False, help="是否自动修复问题")
@click.option("--output", "-o", type=str, help="结果输出文件，不指定则打印到控制台")
@click.option("--json", "json_output", is_flag=True, help="以JSON格式输出结果")
def fix_consistency_issues(
    container: str,
    report: str,
    auto_fix: bool,
    output: Optional[str],
    json_output: bool,
):
    """
    修复容器环境与宿主环境的一致性问题

    CONTAINER: 容器ID或名称
    """
    try:
        # 读取报告文件
        with open(report, "r") as f:
            report_data = json.load(f)

        # 获取问题列表
        issues = report_data.get("issues", [])

        if not issues:
            click.echo("报告中没有发现问题需要修复。")
            return

        # 修复问题
        result = consistency_manager.fix_consistency_issues(
            container_id_or_name=container, issues=issues, auto_fix=auto_fix
        )

        # 格式化输出
        if json_output:
            formatted_output = json.dumps(result, indent=2)
        else:
            formatted_output = format_fix_result(result)

        # 输出结果
        if output:
            with open(output, "w") as f:
                f.write(formatted_output)
            click.echo(f"结果已保存到: {output}")
        else:
            click.echo(formatted_output)

    except Exception as e:
        logger.error(f"修复一致性问题时出错: {e}")
        click.echo(f"错误: {e}", err=True)


@consistency_cmd_group.command(
    name="save-baseline", help="保存环境基准线，用于后续比较"
)
@click.argument("container", required=True, type=str)
@click.argument("baseline_name", required=True, type=str)
@click.option("--json", "json_output", is_flag=True, help="以JSON格式输出结果")
def save_environment_baseline(container: str, baseline_name: str, json_output: bool):
    """
    保存环境基准线，用于后续比较

    CONTAINER: 容器ID或名称
    BASELINE_NAME: 基准线名称
    """
    try:
        result = consistency_manager.save_baseline(
            container_id_or_name=container, baseline_name=baseline_name
        )

        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"已保存环境基准线 '{baseline_name}'")
            click.echo(f"基准线文件: {result['baseline_file']}")
            click.echo(f"保存时间: {result['timestamp']}")

    except Exception as e:
        logger.error(f"保存环境基准线时出错: {e}")
        click.echo(f"错误: {e}", err=True)


@consistency_cmd_group.command(name="compare", help="将当前环境与基准线比较")
@click.argument("container", required=True, type=str)
@click.argument("baseline_name", required=True, type=str)
@click.option("--output", "-o", type=str, help="结果输出文件，不指定则打印到控制台")
@click.option("--json", "json_output", is_flag=True, help="以JSON格式输出结果")
def compare_with_baseline(
    container: str, baseline_name: str, output: Optional[str], json_output: bool
):
    """
    将当前环境与基准线比较

    CONTAINER: 容器ID或名称
    BASELINE_NAME: 基准线名称
    """
    try:
        result = consistency_manager.compare_with_baseline(
            container_id_or_name=container, baseline_name=baseline_name
        )

        if "error" in result:
            click.echo(f"错误: {result['error']}", err=True)
            return

        # 格式化输出
        if json_output:
            formatted_output = json.dumps(result, indent=2)
        else:
            formatted_output = format_compare_result(result)

        # 输出结果
        if output:
            with open(output, "w") as f:
                f.write(formatted_output)
            click.echo(f"结果已保存到: {output}")
        else:
            click.echo(formatted_output)

    except Exception as e:
        logger.error(f"比较环境基准线时出错: {e}")
        click.echo(f"错误: {e}", err=True)


@consistency_cmd_group.command(name="list-baselines", help="列出所有保存的环境基准线")
@click.option("--json", "json_output", is_flag=True, help="以JSON格式输出结果")
def list_environment_baselines(json_output: bool):
    """列出所有保存的环境基准线"""
    try:
        config_dir = Path.home() / ".smoothstack" / "consistency"

        if not config_dir.exists():
            if json_output:
                click.echo(json.dumps({"baselines": []}))
            else:
                click.echo("没有找到任何环境基准线。")
            return

        baselines = []
        for file in config_dir.glob("baseline_*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)

                baselines.append(
                    {
                        "name": data.get("name", file.stem.replace("baseline_", "")),
                        "timestamp": data.get("timestamp", ""),
                        "container": data.get("container", {}).get("name", ""),
                        "file": str(file),
                    }
                )
            except Exception:
                # 忽略无法解析的文件
                pass

        # 排序基准线（按名称）
        baselines.sort(key=lambda b: b["name"])

        if json_output:
            click.echo(json.dumps({"baselines": baselines}, indent=2))
        else:
            if not baselines:
                click.echo("没有找到任何环境基准线。")
                return

            click.echo("环境基准线列表:")
            for baseline in baselines:
                click.echo(
                    f"  - {baseline['name']} (容器: {baseline['container']}, 时间: {baseline['timestamp']})"
                )

    except Exception as e:
        logger.error(f"列出环境基准线时出错: {e}")
        click.echo(f"错误: {e}", err=True)


def format_check_result(result: Dict[str, Any]) -> str:
    """格式化一致性检查结果为易读的文本"""
    output = []

    # 标题
    output.append("==== 容器环境一致性检查结果 ====")
    output.append("")

    # 容器信息
    container = result.get("container", {})
    output.append(
        f"容器: {container.get('name', '?')} ({container.get('id', '?')[:12]})"
    )
    output.append(f"镜像: {container.get('image', '?')}")
    output.append(f"检查时间: {result.get('timestamp', '?')}")
    output.append("")

    # 执行的检查
    checks = result.get("checks_performed", {})
    output.append("执行的检查:")
    output.append(f"  - 依赖包: {'是' if checks.get('dependencies', False) else '否'}")
    output.append(
        f"  - 环境变量: {'是' if checks.get('environment_variables', False) else '否'}"
    )
    output.append(
        f"  - 端口映射: {'是' if checks.get('port_mappings', False) else '否'}"
    )
    output.append(f"  - 文件同步: {'是' if checks.get('file_sync', False) else '否'}")
    output.append("")

    # 问题汇总
    summary = result.get("issue_summary", {})
    output.append("问题汇总:")
    output.append(f"  - 总数: {summary.get('total', 0)}")
    output.append(f"  - 错误: {summary.get('by_severity', {}).get('error', 0)}")
    output.append(f"  - 警告: {summary.get('by_severity', {}).get('warning', 0)}")
    output.append(f"  - 信息: {summary.get('by_severity', {}).get('info', 0)}")
    output.append("")

    # 问题列表
    issues = result.get("issues", [])
    if issues:
        output.append("问题详情:")
        for i, issue in enumerate(issues, 1):
            severity = issue.get("severity", "unknown")
            severity_symbol = {
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
                "unknown": "❓",
            }.get(severity, "❓")

            issue_type = issue.get("type", "unknown")
            output.append(
                f"{i}. {severity_symbol} [{severity.upper()}] {get_issue_description(issue)}"
            )
    else:
        output.append("恭喜！没有发现一致性问题。")

    # 报告文件
    if "report_file" in result:
        output.append("")
        output.append(f"详细报告已保存至: {result['report_file']}")

    return "\n".join(output)


def format_fix_result(result: Dict[str, Any]) -> str:
    """格式化修复结果为易读的文本"""
    output = []

    # 标题
    output.append("==== 容器环境一致性问题修复结果 ====")
    output.append("")

    # 容器信息
    container = result.get("container", {})
    output.append(
        f"容器: {container.get('name', '?')} ({container.get('id', '?')[:12]})"
    )
    output.append(f"修复时间: {result.get('timestamp', '?')}")
    output.append(f"自动修复: {'是' if result.get('auto_fix', False) else '否'}")
    output.append("")

    # 修复汇总
    summary = result.get("summary", {})
    output.append("修复汇总:")
    output.append(f"  - 总问题数: {summary.get('total_issues', 0)}")
    output.append(f"  - 已修复: {summary.get('fixed', 0)}")
    output.append(f"  - 修复失败: {summary.get('failed', 0)}")
    output.append("")

    # 修复详情
    fix_results = result.get("fix_results", [])
    if fix_results:
        output.append("修复详情:")
        for i, fix in enumerate(fix_results, 1):
            issue = fix.get("issue", {})
            fixed = fix.get("fixed", False)
            status_symbol = "✅" if fixed else "❌"

            output.append(f"{i}. {status_symbol} {get_issue_description(issue)}")

            if fixed:
                output.append(f"   方法: {fix.get('fix_method', '未知')}")
                if "note" in fix:
                    output.append(f"   注意: {fix['note']}")
            else:
                if fix.get("error"):
                    output.append(f"   错误: {fix['error']}")

            output.append("")

    return "\n".join(output)


def format_compare_result(result: Dict[str, Any]) -> str:
    """格式化基准线比较结果为易读的文本"""
    output = []

    # 标题
    output.append("==== 环境基准线比较结果 ====")
    output.append("")

    # 基准线信息
    output.append(f"基准线: {result.get('baseline_name', '?')}")
    output.append(f"基准线时间: {result.get('baseline_timestamp', '?')}")
    output.append(f"当前时间: {result.get('current_timestamp', '?')}")
    output.append("")

    # 容器信息
    container = result.get("container", {})
    output.append(
        f"当前容器: {container.get('name', '?')} ({container.get('id', '?')[:12]})"
    )

    baseline_container = result.get("baseline_container", {})
    output.append(
        f"基准线容器: {baseline_container.get('name', '?')} ({baseline_container.get('id', '?')[:12]})"
    )
    output.append("")

    # 比较汇总
    summary = result.get("summary", {})
    output.append("变更汇总:")
    output.append(f"  - 当前问题数: {result.get('current_issues_count', 0)}")
    output.append(f"  - 基准线问题数: {result.get('baseline_issues_count', 0)}")
    output.append(f"  - 新增问题: {summary.get('new_issues', 0)}")
    output.append(f"  - 已解决问题: {summary.get('resolved_issues', 0)}")
    output.append(f"  - 净变化: {summary.get('net_change', 0)}")
    output.append("")

    # 新增问题
    new_issues = result.get("new_issues", [])
    if new_issues:
        output.append("新增问题:")
        for i, issue in enumerate(new_issues, 1):
            severity = issue.get("severity", "unknown")
            severity_symbol = {
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
                "unknown": "❓",
            }.get(severity, "❓")

            output.append(
                f"{i}. {severity_symbol} [{severity.upper()}] {get_issue_description(issue)}"
            )
        output.append("")

    # 已解决问题
    resolved_issues = result.get("resolved_issues", [])
    if resolved_issues:
        output.append("已解决问题:")
        for i, issue in enumerate(resolved_issues, 1):
            output.append(f"{i}. ✅ {get_issue_description(issue)}")
        output.append("")

    if not new_issues and not resolved_issues:
        output.append("没有发现变化，当前环境与基准线一致。")

    return "\n".join(output)


def get_issue_description(issue: Dict[str, Any]) -> str:
    """根据问题类型生成易读的问题描述"""
    issue_type = issue.get("type", "unknown")

    if issue_type == "python_package_version_mismatch":
        return (
            f"Python包版本不一致: {issue.get('package', '?')} "
            f"(宿主: {issue.get('host_version', '?')}, "
            f"容器: {issue.get('container_version', '?')})"
        )

    elif issue_type == "python_package_missing_in_container":
        return f"容器中缺少Python包: {issue.get('package', '?')} (宿主版本: {issue.get('host_version', '?')})"

    elif issue_type == "python_package_missing_in_host":
        return f"宿主环境中缺少Python包: {issue.get('package', '?')} (容器版本: {issue.get('container_version', '?')})"

    elif issue_type == "node_version_mismatch":
        return (
            f"Node.js版本不一致 "
            f"(宿主: {issue.get('host_version', '?')}, "
            f"容器: {issue.get('container_version', '?')})"
        )

    elif issue_type == "npm_package_version_mismatch":
        return (
            f"NPM包版本不一致: {issue.get('package', '?')} "
            f"(宿主: {issue.get('host_version', '?')}, "
            f"容器: {issue.get('container_version', '?')})"
        )

    elif issue_type == "npm_package_missing_in_container":
        return f"容器中缺少NPM包: {issue.get('package', '?')} (宿主版本: {issue.get('host_version', '?')})"

    elif issue_type == "npm_package_missing_in_host":
        return f"宿主环境中缺少NPM包: {issue.get('package', '?')} (容器版本: {issue.get('container_version', '?')})"

    elif issue_type == "env_var_value_mismatch":
        return (
            f"环境变量值不一致: {issue.get('variable', '?')} "
            f"(宿主: {issue.get('host_value', '?')}, "
            f"容器: {issue.get('container_value', '?')})"
        )

    elif issue_type == "env_var_missing_in_container":
        return f"容器中缺少环境变量: {issue.get('variable', '?')} (宿主值: {issue.get('host_value', '?')})"

    elif issue_type == "env_var_missing_in_host":
        return f"宿主环境中缺少环境变量: {issue.get('variable', '?')} (容器值: {issue.get('container_value', '?')})"

    elif issue_type == "port_mapping_inaccessible":
        return (
            f"端口映射不可访问: 容器端口 {issue.get('container_port', '?')} -> "
            f"宿主 {issue.get('host_ip', '?')}:{issue.get('host_port', '?')}"
        )

    elif issue_type == "host_path_not_exist":
        return f"宿主路径不存在: {issue.get('host_path', '?')}"

    elif issue_type == "host_path_not_mapped":
        return f"宿主路径未映射到容器: {issue.get('host_path', '?')}"

    elif issue_type == "file_not_synced_to_container":
        return (
            f"文件未同步到容器: {issue.get('host_path', '?')} -> "
            f"{issue.get('container_path', '?')}"
        )

    elif issue_type == "file_content_mismatch":
        return (
            f"文件内容不一致: {issue.get('host_path', '?')} (容器: {issue.get('container_path', '?')}, "
            f"宿主大小: {issue.get('host_size', '?')}B, "
            f"容器大小: {issue.get('container_size', '?')}B)"
        )

    return f"未知问题类型: {issue_type}"
