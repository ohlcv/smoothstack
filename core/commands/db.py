"""
数据库管理命令
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional
from datetime import datetime
from .base import BaseCommand


class DBCommand(BaseCommand):
    """数据库管理命令类"""

    def __init__(self):
        super().__init__()
        self.config_dir = self.project_root / "config"

    def migrate(self, project_name: str):
        """运行迁移"""
        self.info(f"运行数据库迁移: {project_name}")

        # 检查项目配置
        config_file = self.config_dir / f"{project_name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {project_name}")

        # 加载配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查数据库连接
        self._check_db_connection(config)

        # 运行迁移
        project_dir = self.project_root / "projects" / project_name
        os.chdir(str(project_dir))

        if os.system("alembic upgrade head") != 0:
            raise RuntimeError("数据库迁移失败")

        self.success("数据库迁移完成")

    def rollback(self, project_name: str):
        """回滚迁移"""
        self.info(f"回滚数据库迁移: {project_name}")

        # 检查项目配置
        config_file = self.config_dir / f"{project_name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {project_name}")

        # 加载配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查数据库连接
        self._check_db_connection(config)

        # 回滚迁移
        project_dir = self.project_root / "projects" / project_name
        os.chdir(str(project_dir))

        if os.system("alembic downgrade -1") != 0:
            raise RuntimeError("数据库回滚失败")

        self.success("数据库回滚完成")

    def seed(self, project_name: str):
        """填充种子数据"""
        self.info(f"填充数据库种子数据: {project_name}")

        # 检查项目配置
        config_file = self.config_dir / f"{project_name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {project_name}")

        # 加载配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查数据库连接
        self._check_db_connection(config)

        # 运行种子脚本
        project_dir = self.project_root / "projects" / project_name
        seed_script = project_dir / "scripts" / "seed.py"

        if not self.check_file(str(seed_script)):
            raise RuntimeError("种子脚本不存在")

        os.chdir(str(project_dir))
        if os.system(f"python {seed_script}") != 0:
            raise RuntimeError("填充种子数据失败")

        self.success("种子数据填充完成")

    def reset(self, project_name: str):
        """重置数据库"""
        self.info(f"重置数据库: {project_name}")

        # 检查项目配置
        config_file = self.config_dir / f"{project_name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {project_name}")

        # 加载配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查数据库连接
        self._check_db_connection(config)

        # 重置数据库
        project_dir = self.project_root / "projects" / project_name
        os.chdir(str(project_dir))

        # 删除所有表
        if os.system("alembic downgrade base") != 0:
            raise RuntimeError("重置数据库失败")

        # 重新运行迁移
        if os.system("alembic upgrade head") != 0:
            raise RuntimeError("数据库迁移失败")

        self.success("数据库重置完成")

    def backup(self, project_name: str):
        """创建备份"""
        self.info(f"创建数据库备份: {project_name}")

        # 检查项目配置
        config_file = self.config_dir / f"{project_name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {project_name}")

        # 加载配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查数据库连接
        self._check_db_connection(config)

        # 创建备份目录
        backup_dir = self.project_root / "backups"
        self.create_directory(str(backup_dir))

        # 生成备份文件名
        backup_file = (
            backup_dir
            / f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        )

        # 创建备份
        db_config = config["services"]["db"]["environment"]
        backup_cmd = (
            f"docker-compose exec -T db pg_dump "
            f"-U {db_config['POSTGRES_USER']} "
            f"-d {db_config['POSTGRES_DB']} "
            f"> {backup_file}"
        )

        if os.system(backup_cmd) != 0:
            raise RuntimeError("创建数据库备份失败")

        self.success(f"数据库备份创建成功: {backup_file}")

    def restore(self, project_name: str, backup_file: str):
        """恢复备份"""
        self.info(f"恢复数据库备份: {project_name}")

        # 检查项目配置
        config_file = self.config_dir / f"{project_name}.yml"
        if not self.check_file(str(config_file)):
            raise RuntimeError(f"项目配置不存在: {project_name}")

        # 加载配置
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 检查数据库连接
        self._check_db_connection(config)

        # 检查备份文件
        if not self.check_file(backup_file):
            raise RuntimeError(f"备份文件不存在: {backup_file}")

        # 恢复备份
        project_dir = self.project_root / "projects" / project_name
        os.chdir(str(project_dir))

        db_config = config["services"]["db"]["environment"]
        restore_cmd = (
            f"docker-compose exec -T db psql "
            f"-U {db_config['POSTGRES_USER']} "
            f"-d {db_config['POSTGRES_DB']} "
            f"< {backup_file}"
        )

        if os.system(restore_cmd) != 0:
            raise RuntimeError("恢复数据库备份失败")

        self.success("数据库备份恢复完成")

    def _check_db_connection(self, config: dict):
        """检查数据库连接"""
        self.info("检查数据库连接...")

        # 获取数据库配置
        db_config = config["services"]["db"]["environment"]
        db_host = "localhost"
        db_port = config["services"]["db"]["port"]

        # 等待数据库就绪
        try:
            self.wait_for_service(db_host, db_port)
        except TimeoutError:
            raise RuntimeError("数据库连接超时")

        # 测试数据库连接
        import psycopg2

        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_config["POSTGRES_DB"],
                user=db_config["POSTGRES_USER"],
                password=db_config["POSTGRES_PASSWORD"],
            )
            conn.close()
        except Exception as e:
            raise RuntimeError(f"数据库连接失败: {str(e)}")
