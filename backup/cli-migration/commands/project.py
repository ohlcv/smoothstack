"""
项目管理命令
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from .base import BaseCommand


class ProjectCommand(BaseCommand):
    """项目管理命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.templates_dir = self.project_root / "templates"
        self.config_dir = self.project_root / "config"

    def create(self, name: str):
        """创建项目"""
        self.info(f"创建项目: {name}")

        # 检查项目名称
        if not name or not name.isalnum():
            raise ValueError("项目名称必须为字母数字组合")

        # 检查项目目录
        project_dir = self.projects_dir / name
        if self.check_directory(str(project_dir)):
            raise RuntimeError(f"项目已存在: {name}")

        # 检查模板目录
        template_dir = self.templates_dir / "project"
        if not self.check_directory(str(template_dir)):
            raise RuntimeError("项目模板不存在")

        # 验证模板
        self._validate_template(template_dir)

        # 创建项目目录
        self.create_directory(str(project_dir))

        # 复制模板文件
        self._copy_template(template_dir, project_dir)

        # 替换项目名称
        self._replace_project_name(project_dir, name)

        # 创建项目配置
        self._create_project_config(name)

        self.success(f"项目创建成功: {name}")

    def list(self):
        """列出项目"""
        self.info("列出所有项目...")

        if not self.check_directory(str(self.projects_dir)):
            self.warning("项目目录不存在")
            return

        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                status = self.get_project_status(project_dir.name)
                projects.append((project_dir.name, status))

        if not projects:
            self.info("未找到项目")
            return

        self.info("\n项目列表:")
        for name, status in projects:
            self.info(f"  {name} - {status}")

    def delete(self, name: str):
        """删除项目"""
        self.info(f"删除项目: {name}")

        # 检查项目目录
        project_dir = self.projects_dir / name
        if not self.check_directory(str(project_dir)):
            raise RuntimeError(f"项目不存在: {name}")

        # 停止项目
        self.stop(name)

        # 删除项目目录
        import shutil

        shutil.rmtree(str(project_dir))

        # 删除项目配置
        config_file = self.config_dir / f"{name}.yml"
        if self.check_file(str(config_file)):
            config_file.unlink()

        self.success(f"项目删除成功: {name}")

    def start(self, name: str):
        """启动项目"""
        self.info(f"启动项目: {name}")

        # 检查项目目录
        project_dir = self.projects_dir / name
        if not self.check_directory(str(project_dir)):
            raise RuntimeError(f"项目不存在: {name}")

        # 检查项目配置
        config_file = self.config_dir / f"{name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {name}")

        # 切换到项目目录
        os.chdir(str(project_dir))

        # 启动服务
        if os.system("docker-compose up -d") != 0:
            raise RuntimeError("启动项目失败")

        self.success(f"项目启动成功: {name}")

    def stop(self, name: str):
        """停止项目"""
        self.info(f"停止项目: {name}")

        # 检查项目目录
        project_dir = self.projects_dir / name
        if not self.check_directory(str(project_dir)):
            raise RuntimeError(f"项目不存在: {name}")

        # 切换到项目目录
        os.chdir(str(project_dir))

        # 停止服务
        if os.system("docker-compose down") != 0:
            raise RuntimeError("停止项目失败")

        self.success(f"项目停止成功: {name}")

    def _validate_template(self, template_dir: Path):
        """验证项目模板"""
        self.info("验证项目模板...")

        # 检查必要文件
        required_files = ["docker-compose.yml", "requirements.txt", "README.md"]

        for file in required_files:
            file_path = template_dir / file
            if not self.check_file(str(file_path)):
                raise RuntimeError(f"模板缺少必要文件: {file}")

        # 检查docker-compose.yml
        compose_file = template_dir / "docker-compose.yml"
        try:
            with open(compose_file, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            # 检查必要服务
            required_services = ["app", "db"]
            for service in required_services:
                if service not in compose_data.get("services", {}):
                    raise RuntimeError(f"模板缺少必要服务: {service}")
        except Exception as e:
            raise RuntimeError(f"模板验证失败: {str(e)}")

    def _copy_template(self, template_dir: Path, project_dir: Path):
        """复制模板文件"""
        self.info("复制模板文件...")

        # 复制所有文件
        for item in template_dir.iterdir():
            if item.is_file():
                self.copy_item(str(item), str(project_dir / item.name))
            elif item.is_dir():
                self.copy_item(str(item), str(project_dir / item.name))

    def _replace_project_name(self, project_dir: Path, name: str):
        """替换项目名称"""
        self.info("替换项目名称...")

        # 替换docker-compose.yml
        compose_file = project_dir / "docker-compose.yml"
        if self.check_file(str(compose_file)):
            self.replace_text(str(compose_file), "project_name", name)

        # 替换README.md
        readme_file = project_dir / "README.md"
        if self.check_file(str(readme_file)):
            self.replace_text(str(readme_file), "project_name", name)

    def _create_project_config(self, name: str):
        """创建项目配置"""
        self.info("创建项目配置...")

        # 确保配置目录存在
        self.create_directory(str(self.config_dir))

        # 创建配置数据
        config_data = {
            "name": name,
            "version": "1.0.0",
            "description": f"项目 {name} 的配置文件",
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
            yaml.dump(config_data, f, allow_unicode=True)

    def get_project_status(self, name: str) -> str:
        """获取项目状态"""
        # 检查项目目录
        project_dir = self.projects_dir / name
        if not self.check_directory(str(project_dir)):
            return "不存在"

        # 检查docker-compose.yml
        compose_file = project_dir / "docker-compose.yml"
        if not self.check_file(str(compose_file)):
            return "未配置"

        # 检查容器状态
        os.chdir(str(project_dir))
        if os.system("docker-compose ps | grep -q Up") == 0:
            return "运行中"
        else:
            return "已停止"
