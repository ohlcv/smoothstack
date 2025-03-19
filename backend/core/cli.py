#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoothstack CLI

命令行接口入口点，用于管理开发环境和依赖
"""

import os
import sys
import click
from typing import Optional
from pathlib import Path

# CLI版本
VERSION = "0.1.0"

# 项目根目录
try:
    # 假设此文件位于 backend/core 目录
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
except Exception:
    # 回退到当前工作目录
    ROOT_DIR = Path.cwd()


@click.group()
@click.version_option(version=VERSION)
@click.pass_context
def cli(ctx):
    """Smoothstack CLI - 现代化全栈应用开发框架命令行工具"""
    # 确保 context object 存在
    ctx.ensure_object(dict)
    # 存储根目录
    ctx.obj["ROOT_DIR"] = ROOT_DIR


@cli.command()
@click.option("--cn", is_flag=True, help="使用中国镜像源")
@click.option("--verbose", is_flag=True, help="显示详细输出")
@click.pass_context
def setup(ctx, cn: bool, verbose: bool):
    """初始化开发环境"""
    click.echo(f"正在初始化开发环境...")
    click.echo(f"使用中国镜像源: {cn}")
    click.echo(f"详细输出: {verbose}")
    click.echo(f"项目根目录: {ctx.obj['ROOT_DIR']}")
    # TODO: 实现完整的环境设置逻辑


@cli.command()
@click.option("--detach", "-d", is_flag=True, help="后台运行")
@click.pass_context
def run(ctx, detach: bool):
    """运行开发服务器"""
    click.echo(f"正在启动开发服务器...")
    click.echo(f"后台运行: {detach}")
    # TODO: 实现服务启动逻辑


@cli.command()
@click.pass_context
def stop(ctx):
    """停止服务"""
    click.echo(f"正在停止服务...")
    # TODO: 实现服务停止逻辑


@cli.command()
@click.pass_context
def status(ctx):
    """查看服务状态"""
    click.echo(f"服务状态:")
    # TODO: 实现状态检查逻辑


@cli.group()
@click.pass_context
def deps(ctx):
    """依赖管理功能组"""
    pass


@deps.command("install")
@click.argument("package", required=True)
@click.option("--env", default="dev", help="环境 (dev, prod, test)")
@click.option("--source", help="指定源")
@click.pass_context
def deps_install(ctx, package: str, env: str, source: Optional[str]):
    """安装依赖包"""
    click.echo(f"正在安装依赖: {package}")
    click.echo(f"环境: {env}")
    click.echo(f"源: {source or '默认'}")
    # TODO: 实现依赖安装逻辑


@deps.command("update")
@click.argument("package", required=False)
@click.option("--env", default="dev", help="环境 (dev, prod, test)")
@click.pass_context
def deps_update(ctx, package: Optional[str], env: str):
    """更新依赖包"""
    if package:
        click.echo(f"正在更新依赖: {package}")
    else:
        click.echo(f"正在更新所有依赖")
    click.echo(f"环境: {env}")
    # TODO: 实现依赖更新逻辑


@cli.group()
@click.pass_context
def sources(ctx):
    """源管理功能组"""
    pass


@sources.command("list")
@click.pass_context
def sources_list(ctx):
    """列出所有可用源"""
    click.echo(f"可用源列表:")
    # TODO: 实现源列表显示逻辑


@sources.command("add")
@click.argument("name", required=True)
@click.argument("url", required=True)
@click.pass_context
def sources_add(ctx, name: str, url: str):
    """添加自定义源"""
    click.echo(f"正在添加源: {name} -> {url}")
    # TODO: 实现源添加逻辑


if __name__ == "__main__":
    cli(obj={})
