#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境管理命令模块

提供环境管理相关的命令，包括：
- 环境创建
- 环境切换
- 环境配置
- 环境清理
"""

import os
import sys
import yaml
import click
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnvCommand(BaseCommand):
    """环境管理命令类"""

    def __init__(self):
        super().__init__()
        self.env_dir = self.project_root / "env"
        self.config_file = self.env_dir / "config.yml"

    def create(self, env_name: str, env_type: str = "dev"):
        """创建新环境"""
        try:
            self.info(f"创建{env_type}环境: {env_name}")

            # 创建环境目录
            env_path = self.env_dir / env_name
            env_path.mkdir(parents=True, exist_ok=True)

            # 创建环境配置
            config = {
                "name": env_name,
                "type": env_type,
                "created_at": str(datetime.now()),
                "status": "active",
            }

            # 保存环境配置
            config_file = env_path / "config.yml"
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            # 创建环境变量文件
            env_file = env_path / ".env"
            env_file.touch()

            # 更新环境列表
            self._update_env_list(env_name)

            self.success(f"环境 {env_name} 创建成功")

        except Exception as e:
            self.error(f"创建环境失败: {e}")
            raise

    def switch(self, env_name: str):
        """切换到指定环境"""
        try:
            self.info(f"切换到环境: {env_name}")

            # 检查环境是否存在
            env_path = self.env_dir / env_name
            if not env_path.exists():
                raise RuntimeError(f"环境 {env_name} 不存在")

            # 加载环境配置
            config_file = env_path / "config.yml"
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新当前环境
            self._update_current_env(env_name)

            # 加载环境变量
            env_file = env_path / ".env"
            if env_file.exists():
                self._load_env_vars(env_file)

            self.success(f"已切换到环境 {env_name}")

        except Exception as e:
            self.error(f"切换环境失败: {e}")
            raise

    def config(self, env_name: Optional[str] = None, **kwargs):
        """配置环境"""
        try:
            # 如果没有指定环境，使用当前环境
            if not env_name:
                env_name = self._get_current_env()

            self.info(f"配置环境: {env_name}")

            # 检查环境是否存在
            env_path = self.env_dir / env_name
            if not env_path.exists():
                raise RuntimeError(f"环境 {env_name} 不存在")

            # 加载现有配置
            config_file = env_path / "config.yml"
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新配置
            config.update(kwargs)

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success(f"环境 {env_name} 配置已更新")

        except Exception as e:
            self.error(f"配置环境失败: {e}")
            raise

    def show(self, env_name: Optional[str] = None):
        """显示环境信息"""
        try:
            # 如果没有指定环境，显示所有环境
            if not env_name:
                self._show_all_envs()
                return

            # 显示指定环境信息
            env_path = self.env_dir / env_name
            if not env_path.exists():
                raise RuntimeError(f"环境 {env_name} 不存在")

            # 加载环境配置
            config_file = env_path / "config.yml"
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 显示环境信息
            self.info(f"环境信息: {env_name}")
            for key, value in config.items():
                self.info(f"{key}: {value}")

        except Exception as e:
            self.error(f"显示环境信息失败: {e}")
            raise

    def clean(self, env_name: Optional[str] = None, force: bool = False):
        """清理环境"""
        try:
            # 如果没有指定环境，清理所有环境
            if not env_name:
                self._clean_all_envs(force)
                return

            # 清理指定环境
            env_path = self.env_dir / env_name
            if not env_path.exists():
                raise RuntimeError(f"环境 {env_name} 不存在")

            # 检查是否是当前环境
            current_env = self._get_current_env()
            if env_name == current_env and not force:
                raise RuntimeError("无法清理当前环境，请先切换到其他环境或使用 --force")

            # 删除环境目录
            import shutil

            shutil.rmtree(env_path)

            # 更新环境列表
            self._update_env_list()

            self.success(f"环境 {env_name} 已清理")

        except Exception as e:
            self.error(f"清理环境失败: {e}")
            raise

    def _update_env_list(self, env_name: Optional[str] = None):
        """更新环境列表"""
        try:
            # 加载现有列表
            env_list = []
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    env_list = yaml.safe_load(f) or []

            # 更新列表
            if env_name:
                if env_name not in env_list:
                    env_list.append(env_name)
            else:
                # 重新扫描环境目录
                env_list = [d.name for d in self.env_dir.iterdir() if d.is_dir()]

            # 保存列表
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(env_list, f, default_flow_style=False)

        except Exception as e:
            self.error(f"更新环境列表失败: {e}")
            raise

    def _update_current_env(self, env_name: str):
        """更新当前环境"""
        try:
            current_env_file = self.env_dir / ".current"
            with open(current_env_file, "w", encoding="utf-8") as f:
                f.write(env_name)
        except Exception as e:
            self.error(f"更新当前环境失败: {e}")
            raise

    def _get_current_env(self) -> str:
        """获取当前环境"""
        try:
            current_env_file = self.env_dir / ".current"
            if not current_env_file.exists():
                return "default"
            with open(current_env_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            self.error(f"获取当前环境失败: {e}")
            return "default"

    def _load_env_vars(self, env_file: Path):
        """加载环境变量"""
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip("\"'")
        except Exception as e:
            self.error(f"加载环境变量失败: {e}")
            raise

    def _show_all_envs(self):
        """显示所有环境"""
        try:
            # 加载环境列表
            if not self.config_file.exists():
                self.info("没有找到任何环境")
                return

            with open(self.config_file, "r", encoding="utf-8") as f:
                env_list = yaml.safe_load(f) or []

            # 获取当前环境
            current_env = self._get_current_env()

            # 显示环境列表
            self.info("环境列表:")
            for env_name in env_list:
                status = "当前" if env_name == current_env else "可用"
                self.info(f"- {env_name} ({status})")

        except Exception as e:
            self.error(f"显示环境列表失败: {e}")
            raise

    def _clean_all_envs(self, force: bool):
        """清理所有环境"""
        try:
            # 获取当前环境
            current_env = self._get_current_env()

            # 加载环境列表
            if not self.config_file.exists():
                self.info("没有找到任何环境")
                return

            with open(self.config_file, "r", encoding="utf-8") as f:
                env_list = yaml.safe_load(f) or []

            # 清理每个环境
            for env_name in env_list:
                if env_name == current_env and not force:
                    self.warning(f"跳过当前环境 {env_name}，使用 --force 强制清理")
                    continue

                env_path = self.env_dir / env_name
                if env_path.exists():
                    import shutil

                    shutil.rmtree(env_path)

            # 更新环境列表
            self._update_env_list()

            self.success("所有环境已清理")

        except Exception as e:
            self.error(f"清理所有环境失败: {e}")
            raise


# CLI命令
@click.group()
def env():
    """环境管理命令"""
    pass


@env.command()
@click.argument("name")
@click.option("--type", "-t", default="dev", help="环境类型：dev/test/prod")
def create(name: str, type: str):
    """创建新环境"""
    cmd = EnvCommand()
    cmd.create(name, type)


@env.command()
@click.argument("name")
def switch(name: str):
    """切换到指定环境"""
    cmd = EnvCommand()
    cmd.switch(name)


@env.command()
@click.argument("name")
@click.option("--type", "-t", help="环境类型")
@click.option("--status", "-s", help="环境状态")
def config(name: str, **kwargs):
    """配置环境"""
    cmd = EnvCommand()
    cmd.config(name, **kwargs)


@env.command()
@click.argument("name", required=False)
def show(name: Optional[str]):
    """显示环境信息"""
    cmd = EnvCommand()
    cmd.show(name)


@env.command()
@click.argument("name", required=False)
@click.option("--force", "-f", is_flag=True, help="强制清理")
def clean(name: Optional[str], force: bool):
    """清理环境"""
    cmd = EnvCommand()
    cmd.clean(name, force)
