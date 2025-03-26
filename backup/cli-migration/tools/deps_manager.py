#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖管理工具 - 实现依赖包和源管理功能

该模块提供简单的依赖管理CLI接口，支持:
- 依赖包安装、卸载、列表和更新
- 源的列表、检查和切换
"""

import os
import sys
import subprocess
import click


@click.group()
def cli():
    """Smoothstack 依赖管理工具"""
    pass


# ===== 依赖管理命令 =====
@cli.group("deps")
def deps():
    """依赖包管理"""
    pass


@deps.command("install")
@click.argument("package")
@click.option("--source", help="指定源名称")
def deps_install(package, source):
    """安装依赖包"""
    cmd = ["pip", "install", package]

    # 如果指定了源，添加--index-url参数
    if source:
        if source == "pypi-tsinghua":
            cmd.extend(["--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"])
        elif source == "pypi-aliyun":
            cmd.extend(["--index-url", "https://mirrors.aliyun.com/pypi/simple"])
        elif source == "pypi":
            pass  # 使用默认源
        else:
            click.echo(f"警告: 未知源 '{source}'，使用默认源")

    click.echo(f"正在安装依赖包: {package}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        click.echo(f"依赖包 {package} 安装成功")
    else:
        click.echo(f"依赖包 {package} 安装失败")
        click.echo(result.stderr)
        sys.exit(1)


@deps.command("uninstall")
@click.argument("package")
def deps_uninstall(package):
    """卸载依赖包"""
    cmd = ["pip", "uninstall", "-y", package]

    click.echo(f"正在卸载依赖包: {package}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        click.echo(f"依赖包 {package} 卸载成功")
    else:
        click.echo(f"依赖包 {package} 卸载失败")
        click.echo(result.stderr)
        sys.exit(1)


@deps.command("list")
def deps_list():
    """列出已安装的依赖包"""
    cmd = ["pip", "list"]

    click.echo("已安装的依赖包:")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo("获取依赖包列表失败")
        click.echo(result.stderr)
        sys.exit(1)


@deps.command("update")
@click.argument("package", required=False)
@click.option("--source", help="指定源名称")
def deps_update(package, source):
    """更新依赖包"""
    base_cmd = ["pip", "install", "--upgrade"]

    # 如果指定了源，添加--index-url参数
    if source:
        if source == "pypi-tsinghua":
            base_cmd.extend(["--index-url", "https://pypi.tuna.tsinghua.edu.cn/simple"])
        elif source == "pypi-aliyun":
            base_cmd.extend(["--index-url", "https://mirrors.aliyun.com/pypi/simple"])
        elif source == "pypi":
            pass  # 使用默认源
        else:
            click.echo(f"警告: 未知源 '{source}'，使用默认源")

    if package:
        cmd = base_cmd + [package]
        click.echo(f"正在更新依赖包: {package}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            click.echo(f"依赖包 {package} 更新成功")
        else:
            click.echo(f"依赖包 {package} 更新失败")
            click.echo(result.stderr)
            sys.exit(1)
    else:
        # 获取所有过时的包
        check_cmd = ["pip", "list", "--outdated"]
        check_result = subprocess.run(check_cmd, capture_output=True, text=True)

        if check_result.returncode != 0:
            click.echo("检查可更新的依赖包失败")
            click.echo(check_result.stderr)
            sys.exit(1)

        # 解析输出找到需要更新的包
        lines = check_result.stdout.strip().split("\n")
        if len(lines) <= 2:
            click.echo("所有依赖包均为最新版本")
            return

        outdated_packages = []
        for line in lines[2:]:  # 跳过标题行
            parts = line.split()
            if len(parts) >= 1:
                outdated_packages.append(parts[0])

        if not outdated_packages:
            click.echo("所有依赖包均为最新版本")
            return

        click.echo(f"发现 {len(outdated_packages)} 个可更新的依赖包:")
        for pkg in outdated_packages:
            click.echo(f"  {pkg}")

        if click.confirm("是否更新所有依赖包?"):
            success_count = 0
            fail_count = 0

            for pkg in outdated_packages:
                cmd = base_cmd + [pkg]
                click.echo(f"正在更新 {pkg}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    click.echo(f"  {pkg} 更新成功")
                    success_count += 1
                else:
                    click.echo(f"  {pkg} 更新失败")
                    fail_count += 1

            click.echo(f"更新完成: {success_count}个成功, {fail_count}个失败")


# ===== 源管理命令 =====
@cli.group("sources")
def sources():
    """管理安装源"""
    pass


@sources.command("list")
def sources_list():
    """列出可用的源"""
    sources = [
        {"name": "pypi", "url": "https://pypi.org/simple", "description": "PyPI官方源"},
        {
            "name": "pypi-tsinghua",
            "url": "https://pypi.tuna.tsinghua.edu.cn/simple",
            "description": "清华大学开源软件镜像站",
        },
        {
            "name": "pypi-aliyun",
            "url": "https://mirrors.aliyun.com/pypi/simple",
            "description": "阿里云镜像站",
        },
    ]

    click.echo("可用的PyPI镜像源:")
    for source in sources:
        click.echo(f"  {source['name']}: {source['url']} - {source['description']}")


@sources.command("check")
def sources_check():
    """检查源的健康状态"""
    import requests
    from concurrent.futures import ThreadPoolExecutor

    sources = [
        {"name": "pypi", "url": "https://pypi.org/simple"},
        {"name": "pypi-tsinghua", "url": "https://pypi.tuna.tsinghua.edu.cn/simple"},
        {"name": "pypi-aliyun", "url": "https://mirrors.aliyun.com/pypi/simple"},
    ]

    def check_source(source):
        try:
            start_time = __import__("time").time()
            response = requests.get(source["url"], timeout=5)
            end_time = __import__("time").time()
            latency = (end_time - start_time) * 1000  # 转换为毫秒

            return {
                "name": source["name"],
                "url": source["url"],
                "status": "正常" if response.status_code == 200 else "异常",
                "latency": latency,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "name": source["name"],
                "url": source["url"],
                "status": "不可访问",
                "error": str(e),
                "latency": 0,
            }

    click.echo("正在检查源健康状态...")

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        results = list(executor.map(check_source, sources))

    # 按延迟排序
    results.sort(key=lambda x: x.get("latency", float("inf")))

    click.echo("源健康状态:")
    for result in results:
        status = result["status"]
        latency = result.get("latency", 0)
        status_str = f"{status} ({latency:.2f}ms)" if latency > 0 else status
        click.echo(f"  {result['name']}: {status_str}")


@sources.command("switch")
@click.argument("name")
def sources_switch(name):
    """切换当前使用的源"""
    # 在简单实现中，我们只是打印如何手动切换源
    if name == "pypi":
        click.echo("已切换到PyPI官方源")
        click.echo("提示: 在安装包时使用默认源")
    elif name == "pypi-tsinghua":
        click.echo("已切换到清华大学镜像源")
        click.echo(
            "提示: 在安装包时使用 --index-url https://pypi.tuna.tsinghua.edu.cn/simple"
        )
    elif name == "pypi-aliyun":
        click.echo("已切换到阿里云镜像源")
        click.echo(
            "提示: 在安装包时使用 --index-url https://mirrors.aliyun.com/pypi/simple"
        )
    else:
        click.echo(f"错误: 未知源 '{name}'")
        click.echo("可用的源: pypi, pypi-tsinghua, pypi-aliyun")
        sys.exit(1)


if __name__ == "__main__":
    cli()
