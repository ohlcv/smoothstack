#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目管理命令模块

提供项目管理相关的命令，包括：
- 项目创建和初始化
- 项目列表和状态管理
- 项目配置管理
- 项目依赖管理
"""

import os
import sys
import yaml
import click
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProjectCommand(BaseCommand):
    """项目管理命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.templates_dir = self.project_root / "templates"
        self.config_dir = self.project_root / "config"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, template: Optional[str] = None):
        """创建项目"""
        try:
            self.info(f"创建项目: {name}")

            # 检查项目名称
            if not name or not name.isalnum():
                raise ValueError("项目名称必须为字母数字组合")

            # 检查项目目录
            project_dir = self.projects_dir / name
            if project_dir.exists():
                raise RuntimeError(f"项目已存在: {name}")

            # 选择模板目录
            if template:
                template_dir = self.templates_dir / template
                if not template_dir.exists():
                    raise RuntimeError(f"模板不存在: {template}")
            else:
                template_dir = self.templates_dir / "default"
                if not template_dir.exists():
                    self._create_default_template()

            # 验证模板
            self._validate_template(template_dir)

            # 创建项目目录
            project_dir.mkdir(parents=True, exist_ok=True)

            # 复制模板文件
            self._copy_template(template_dir, project_dir)

            # 替换项目名称
            self._replace_project_name(project_dir, name)

            # 创建项目配置
            self._create_project_config(name)

            self.success(f"项目创建成功: {name}")

        except Exception as e:
            self.error(f"创建项目失败: {e}")
            raise

    def list(self, status: Optional[str] = None):
        """列出项目"""
        try:
            self.info("列出所有项目...")

            projects = []
            for project_dir in self.projects_dir.iterdir():
                if project_dir.is_dir():
                    project_status = self.get_project_status(project_dir.name)
                    if not status or project_status == status:
                        projects.append((project_dir.name, project_status))

            if not projects:
                self.info("未找到项目")
                return

            self.info("\n项目列表:")
            for name, status in projects:
                self.info(f"  {name} - {status}")

        except Exception as e:
            self.error(f"列出项目失败: {e}")
            raise

    def delete(self, name: str, force: bool = False):
        """删除项目"""
        try:
            self.info(f"删除项目: {name}")

            # 检查项目目录
            project_dir = self.projects_dir / name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {name}")

            # 检查项目状态
            status = self.get_project_status(name)
            if status == "运行中" and not force:
                raise RuntimeError("无法删除运行中的项目，请先停止项目或使用 --force")

            # 停止项目
            if status == "运行中":
                self.stop(name)

            # 删除项目目录
            import shutil

            shutil.rmtree(project_dir)

            # 删除项目配置
            config_file = self.config_dir / f"{name}.yml"
            if config_file.exists():
                config_file.unlink()

            self.success(f"项目删除成功: {name}")

        except Exception as e:
            self.error(f"删除项目失败: {e}")
            raise

    def start(self, name: str):
        """启动项目"""
        try:
            self.info(f"启动项目: {name}")

            # 检查项目目录
            project_dir = self.projects_dir / name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {name}")

            # 检查项目配置
            config_file = self.config_dir / f"{name}.yml"
            if not config_file.exists():
                raise RuntimeError(f"项目配置不存在: {name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 启动服务
            if os.system("docker-compose up -d") != 0:
                raise RuntimeError("启动项目失败")

            self.success(f"项目启动成功: {name}")

        except Exception as e:
            self.error(f"启动项目失败: {e}")
            raise

    def stop(self, name: str):
        """停止项目"""
        try:
            self.info(f"停止项目: {name}")

            # 检查项目目录
            project_dir = self.projects_dir / name
            if not project_dir.exists():
                raise RuntimeError(f"项目不存在: {name}")

            # 切换到项目目录
            os.chdir(str(project_dir))

            # 停止服务
            if os.system("docker-compose down") != 0:
                raise RuntimeError("停止项目失败")

            self.success(f"项目停止成功: {name}")

        except Exception as e:
            self.error(f"停止项目失败: {e}")
            raise

    def config(self, name: str, **kwargs):
        """配置项目"""
        try:
            self.info(f"配置项目: {name}")

            # 检查项目配置
            config_file = self.config_dir / f"{name}.yml"
            if not config_file.exists():
                raise RuntimeError(f"项目配置不存在: {name}")

            # 加载现有配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新配置
            config.update(kwargs)

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            self.success(f"项目配置已更新: {name}")

        except Exception as e:
            self.error(f"配置项目失败: {e}")
            raise

    def show(self, name: str):
        """显示项目信息"""
        try:
            self.info(f"显示项目信息: {name}")

            # 检查项目配置
            config_file = self.config_dir / f"{name}.yml"
            if not config_file.exists():
                raise RuntimeError(f"项目配置不存在: {name}")

            # 加载配置
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 获取项目状态
            status = self.get_project_status(name)

            # 显示项目信息
            self.info("\n项目信息:")
            self.info(f"名称: {name}")
            self.info(f"状态: {status}")
            for key, value in config.items():
                if key != "name":
                    self.info(f"{key}: {value}")

        except Exception as e:
            self.error(f"显示项目信息失败: {e}")
            raise

    def _create_default_template(self):
        """创建默认项目模板"""
        try:
            template_dir = self.templates_dir / "default"
            template_dir.mkdir(parents=True, exist_ok=True)

            # 创建docker-compose.yml
            compose_file = template_dir / "docker-compose.yml"
            compose_data = {
                "version": "3.8",
                "services": {
                    "app": {
                        "build": ".",
                        "ports": ["8000:8000"],
                        "environment": {
                            "DEBUG": "true",
                            "DATABASE_URL": "postgresql://postgres:postgres@db:5432/project_name",
                        },
                        "depends_on": ["db"],
                    },
                    "db": {
                        "image": "postgres:13",
                        "ports": ["5432:5432"],
                        "environment": {
                            "POSTGRES_DB": "project_name",
                            "POSTGRES_USER": "postgres",
                            "POSTGRES_PASSWORD": "postgres",
                        },
                        "volumes": ["postgres_data:/var/lib/postgresql/data"],
                    },
                },
                "volumes": {"postgres_data": {}},
            }
            with open(compose_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(compose_data, f, default_flow_style=False)

            # 创建requirements.txt
            requirements_file = template_dir / "requirements.txt"
            requirements_file.write_text(
                "fastapi==0.68.0\nuvicorn==0.15.0\nsqlalchemy==1.4.23\npsycopg2-binary==2.9.1\n"
            )

            # 创建README.md
            readme_file = template_dir / "README.md"
            readme_file.write_text(
                f"""# project_name

这是一个使用FastAPI和PostgreSQL的项目模板。

## 开发环境设置

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 启动服务:
   ```bash
   docker-compose up -d
   ```

3. 访问API文档:
   http://localhost:8000/docs

## 项目结构

```
project_name/
├── app/                # 应用代码
├── tests/             # 测试代码
├── docker-compose.yml # Docker配置
└── requirements.txt   # 项目依赖
```
"""
            )

        except Exception as e:
            self.error(f"创建默认模板失败: {e}")
            raise

    def _validate_template(self, template_dir: Path):
        """验证项目模板"""
        try:
            self.info("验证项目模板...")

            # 检查必要文件
            required_files = ["docker-compose.yml", "requirements.txt", "README.md"]
            for file in required_files:
                file_path = template_dir / file
                if not file_path.exists():
                    raise RuntimeError(f"模板缺少必要文件: {file}")

            # 检查docker-compose.yml
            compose_file = template_dir / "docker-compose.yml"
            with open(compose_file, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            # 检查必要服务
            required_services = ["app", "db"]
            for service in required_services:
                if service not in compose_data.get("services", {}):
                    raise RuntimeError(f"模板缺少必要服务: {service}")

        except Exception as e:
            self.error(f"模板验证失败: {e}")
            raise

    def _copy_template(self, template_dir: Path, project_dir: Path):
        """复制模板文件"""
        try:
            self.info("复制模板文件...")

            # 复制所有文件
            for item in template_dir.iterdir():
                if item.is_file():
                    self.copy_file(item, project_dir / item.name)
                elif item.is_dir():
                    self.copy_directory(item, project_dir / item.name)

        except Exception as e:
            self.error(f"复制模板文件失败: {e}")
            raise

    def _replace_project_name(self, project_dir: Path, name: str):
        """替换项目名称"""
        try:
            self.info("替换项目名称...")

            # 替换docker-compose.yml
            compose_file = project_dir / "docker-compose.yml"
            if compose_file.exists():
                self.replace_text(compose_file, "project_name", name)

            # 替换README.md
            readme_file = project_dir / "README.md"
            if readme_file.exists():
                self.replace_text(readme_file, "project_name", name)

        except Exception as e:
            self.error(f"替换项目名称失败: {e}")
            raise

    def _create_project_config(self, name: str):
        """创建项目配置"""
        try:
            self.info("创建项目配置...")

            # 创建配置数据
            config_data = {
                "name": name,
                "version": "1.0.0",
                "description": f"项目 {name} 的配置文件",
                "created_at": str(datetime.now()),
                "services": {
                    "app": {"port": 8000, "environment": {"DEBUG": "true"}},
                    "db": {
                        "port": 5432,
                        "environment": {
                            "POSTGRES_DB": name,
                            "POSTGRES_USER": "postgres",
                            "POSTGRES_PASSWORD": "postgres",
                        },
                    },
                },
            }

            # 写入配置文件
            config_file = self.config_dir / f"{name}.yml"
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config_data, f, default_flow_style=False)

        except Exception as e:
            self.error(f"创建项目配置失败: {e}")
            raise

    def get_project_status(self, name: str) -> str:
        """获取项目状态"""
        try:
            # 检查项目目录
            project_dir = self.projects_dir / name
            if not project_dir.exists():
                return "不存在"

            # 检查docker-compose.yml
            compose_file = project_dir / "docker-compose.yml"
            if not compose_file.exists():
                return "未配置"

            # 检查容器状态
            os.chdir(str(project_dir))
            if os.system("docker-compose ps | grep -q Up") == 0:
                return "运行中"
            else:
                return "已停止"

        except Exception as e:
            self.error(f"获取项目状态失败: {e}")
            return "未知"


# CLI命令
@click.group()
def project():
    """项目管理命令"""
    pass


@project.command()
@click.argument("name")
@click.option("--template", "-t", help="项目模板")
def create(name: str, template: Optional[str]):
    """创建新项目"""
    cmd = ProjectCommand()
    cmd.create(name, template)


@project.command()
@click.option("--status", "-s", help="按状态筛选")
def list(status: Optional[str]):
    """列出所有项目"""
    cmd = ProjectCommand()
    cmd.list(status)


@project.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="强制删除")
def delete(name: str, force: bool):
    """删除项目"""
    cmd = ProjectCommand()
    cmd.delete(name, force)


@project.command()
@click.argument("name")
def start(name: str):
    """启动项目"""
    cmd = ProjectCommand()
    cmd.start(name)


@project.command()
@click.argument("name")
def stop(name: str):
    """停止项目"""
    cmd = ProjectCommand()
    cmd.stop(name)


@project.command()
@click.argument("name")
@click.option("--version", "-v", help="项目版本")
@click.option("--description", "-d", help="项目描述")
def config(name: str, **kwargs):
    """配置项目"""
    cmd = ProjectCommand()
    cmd.config(name, **kwargs)


@project.command()
@click.argument("name")
def show(name: str):
    """显示项目信息"""
    cmd = ProjectCommand()
    cmd.show(name)
