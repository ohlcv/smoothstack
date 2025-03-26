"""
后端工具命令类
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from .base import BaseCommand


class BackendToolsCommand(BaseCommand):
    """后端工具命令类，提供通用的后端开发工具"""

    def __init__(self):
        super().__init__()
        self.backend_dir = self.project_root / "backend"
        self.tools_dir = self.backend_dir / "tools"

    def run_api(self, port: int = 5000, host: str = "0.0.0.0"):
        """运行API服务"""
        self.info(f"启动API服务 {host}:{port}")
        try:
            from backend.main import app
            import uvicorn

            uvicorn.run(app, host=host, port=port, reload=True)
        except Exception as e:
            self.error(f"启动API服务失败: {str(e)}")
            raise

    def manage_logs(self, action: str, service: Optional[str] = None):
        """管理日志"""
        self.info(f"执行日志操作: {action}")
        try:
            from backend.tools.log_manager import LogManager

            manager = LogManager()

            if action == "view":
                manager.view_logs(service)
            elif action == "clean":
                manager.clean_logs(service)
            elif action == "analyze":
                manager.analyze_logs(service)
            else:
                raise ValueError(f"未知的日志操作: {action}")

        except Exception as e:
            self.error(f"日志操作失败: {str(e)}")
            raise

    def manage_containers(self, action: str, service: Optional[str] = None):
        """管理容器"""
        self.info(f"执行容器操作: {action}")
        try:
            from backend.tools.docker_manager import DockerManager

            manager = DockerManager()

            if action == "start":
                manager.start_containers(service)
            elif action == "stop":
                manager.stop_containers(service)
            elif action == "restart":
                manager.restart_containers(service)
            elif action == "status":
                manager.show_status(service)
            elif action == "logs":
                manager.show_logs(service)
            elif action == "clean":
                manager.clean_resources()
            else:
                raise ValueError(f"未知的容器操作: {action}")

        except Exception as e:
            self.error(f"容器操作失败: {str(e)}")
            raise

    def manage_dependencies(self, action: str, packages: Optional[List[str]] = None):
        """管理依赖"""
        self.info(f"执行依赖操作: {action}")
        try:
            from backend.tools.deps_manager import DependencyManager

            manager = DependencyManager()

            if action == "install":
                manager.install_packages(packages)
            elif action == "update":
                manager.update_packages(packages)
            elif action == "remove":
                manager.remove_packages(packages)
            elif action == "list":
                manager.list_packages()
            elif action == "check":
                manager.check_dependencies()
            else:
                raise ValueError(f"未知的依赖操作: {action}")

        except Exception as e:
            self.error(f"依赖操作失败: {str(e)}")
            raise

    def manage_images(self, action: str, image: Optional[str] = None):
        """管理Docker镜像"""
        self.info(f"执行镜像操作: {action}")
        try:
            from backend.tools.image_manager import ImageManager

            manager = ImageManager()

            if action == "build":
                manager.build_image(image)
            elif action == "pull":
                manager.pull_image(image)
            elif action == "push":
                manager.push_image(image)
            elif action == "list":
                manager.list_images()
            elif action == "clean":
                manager.clean_images()
            else:
                raise ValueError(f"未知的镜像操作: {action}")

        except Exception as e:
            self.error(f"镜像操作失败: {str(e)}")
            raise

    def analyze_logs(self, service: Optional[str] = None):
        """分析日志"""
        self.info("开始分析日志")
        try:
            from backend.tools.log_statistics import LogAnalyzer

            analyzer = LogAnalyzer()

            if service:
                analyzer.analyze_service_logs(service)
            else:
                analyzer.analyze_all_logs()

        except Exception as e:
            self.error(f"日志分析失败: {str(e)}")
            raise

    def manage_container_deps(
        self, action: str, packages: Optional[List[str]] = None, env: str = "dev"
    ):
        """管理容器依赖"""
        self.info(f"执行容器依赖操作: {action}")
        try:
            from backend.tools.container_deps_manager import ContainerDepsManager

            manager = ContainerDepsManager()

            if action == "add":
                manager.add_dependencies(packages, env)
            elif action == "remove":
                manager.remove_dependencies(packages, env)
            elif action == "update":
                manager.update_dependencies(packages, env)
            elif action == "list":
                manager.list_dependencies(env)
            elif action == "check":
                manager.check_dependencies(env)
            else:
                raise ValueError(f"未知的容器依赖操作: {action}")

        except Exception as e:
            self.error(f"容器依赖操作失败: {str(e)}")
            raise

    def create_app(self, name: str, template: str = "fastapi"):
        """创建新的后端应用

        Args:
            name: 应用名称
            template: 模板类型 (fastapi/django/flask)
        """
        self.info(f"创建{template}应用: {name}")
        try:
            # 检查模板
            template_dir = self.project_root / "templates" / "backend" / template
            if not template_dir.exists():
                raise ValueError(f"模板不存在: {template}")

            # 创建应用目录
            app_dir = self.backend_dir / name
            if app_dir.exists():
                raise ValueError(f"应用已存在: {name}")

            # 复制模板
            self.copy_item(str(template_dir), str(app_dir))

            # 替换模板变量
            self._replace_template_vars(
                app_dir, {"APP_NAME": name, "PROJECT_NAME": self.project_root.name}
            )

            self.success(f"应用创建成功: {name}")
        except Exception as e:
            self.error(f"创建应用失败: {str(e)}")
            raise

    def add_model(self, app: str, name: str):
        """添加数据模型

        Args:
            app: 应用名称
            name: 模型名称
        """
        self.info(f"添加模型: {app}.{name}")
        try:
            # 检查应用
            app_dir = self.backend_dir / app
            if not app_dir.exists():
                raise ValueError(f"应用不存在: {app}")

            # 创建模型文件
            models_dir = app_dir / "models"
            models_dir.mkdir(exist_ok=True)

            model_file = models_dir / f"{name.lower()}.py"
            if model_file.exists():
                raise ValueError(f"模型已存在: {name}")

            # 生成模型代码
            model_template = self._get_model_template(name)
            with open(model_file, "w", encoding="utf-8") as f:
                f.write(model_template)

            # 更新 __init__.py
            init_file = models_dir / "__init__.py"
            with open(init_file, "a", encoding="utf-8") as f:
                f.write(f"\nfrom .{name.lower()} import {name}")

            self.success(f"模型添加成功: {name}")
        except Exception as e:
            self.error(f"添加模型失败: {str(e)}")
            raise

    def add_api(self, app: str, name: str, crud: bool = True):
        """添加API端点

        Args:
            app: 应用名称
            name: API名称
            crud: 是否生成CRUD端点
        """
        self.info(f"添加API: {app}.{name}")
        try:
            # 检查应用
            app_dir = self.backend_dir / app
            if not app_dir.exists():
                raise ValueError(f"应用不存在: {app}")

            # 创建API目录
            api_dir = app_dir / "api"
            api_dir.mkdir(exist_ok=True)

            # 生成API文件
            api_file = api_dir / f"{name.lower()}.py"
            if api_file.exists():
                raise ValueError(f"API已存在: {name}")

            # 生成API代码
            api_template = self._get_api_template(name, crud)
            with open(api_file, "w", encoding="utf-8") as f:
                f.write(api_template)

            # 更新路由
            self._update_api_routes(app_dir, name)

            self.success(f"API添加成功: {name}")
        except Exception as e:
            self.error(f"添加API失败: {str(e)}")
            raise

    def add_service(self, app: str, name: str):
        """添加服务层

        Args:
            app: 应用名称
            name: 服务名称
        """
        self.info(f"添加服务: {app}.{name}")
        try:
            # 检查应用
            app_dir = self.backend_dir / app
            if not app_dir.exists():
                raise ValueError(f"应用不存在: {app}")

            # 创建服务目录
            services_dir = app_dir / "services"
            services_dir.mkdir(exist_ok=True)

            # 生成服务文件
            service_file = services_dir / f"{name.lower()}.py"
            if service_file.exists():
                raise ValueError(f"服务已存在: {name}")

            # 生成服务代码
            service_template = self._get_service_template(name)
            with open(service_file, "w", encoding="utf-8") as f:
                f.write(service_template)

            # 更新 __init__.py
            init_file = services_dir / "__init__.py"
            with open(init_file, "a", encoding="utf-8") as f:
                f.write(f"\nfrom .{name.lower()} import {name}Service")

            self.success(f"服务添加成功: {name}")
        except Exception as e:
            self.error(f"添加服务失败: {str(e)}")
            raise

    def generate_crud(self, app: str, model: str):
        """生成CRUD操作

        Args:
            app: 应用名称
            model: 模型名称
        """
        self.info(f"生成CRUD: {app}.{model}")
        try:
            # 检查应用和模型
            app_dir = self.backend_dir / app
            if not app_dir.exists():
                raise ValueError(f"应用不存在: {app}")

            model_file = app_dir / "models" / f"{model.lower()}.py"
            if not model_file.exists():
                raise ValueError(f"模型不存在: {model}")

            # 生成 Schema
            self._generate_schema(app_dir, model)

            # 生成 API
            self._generate_api(app_dir, model)

            # 生成 Service
            self._generate_service(app_dir, model)

            self.success(f"CRUD生成成功: {model}")
        except Exception as e:
            self.error(f"生成CRUD失败: {str(e)}")
            raise

    def run_dev(self, app: str, port: int = 8000):
        """运行开发服务器

        Args:
            app: 应用名称
            port: 端口号
        """
        self.info(f"启动开发服务器: {app}")
        try:
            # 检查应用
            app_dir = self.backend_dir / app
            if not app_dir.exists():
                raise ValueError(f"应用不存在: {app}")

            # 激活虚拟环境
            self.activate_venv()

            # 运行服务器
            os.chdir(str(app_dir))
            if os.path.exists("manage.py"):
                # Django
                os.system(f"python manage.py runserver {port}")
            else:
                # FastAPI/Flask
                os.system(f"uvicorn main:app --reload --port {port}")

        except Exception as e:
            self.error(f"启动开发服务器失败: {str(e)}")
            raise

    def _replace_template_vars(self, directory: Path, vars: dict):
        """替换模板变量"""
        for file in directory.rglob("*"):
            if file.is_file():
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()

                for key, value in vars.items():
                    content = content.replace(f"${{{key}}}", value)

                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)

    def _get_model_template(self, name: str) -> str:
        """获取模型模板"""
        return f'''"""
{name} Model
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class {name}(Base):
    """
    {name} Model
    """
    __tablename__ = "{name.lower()}s"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
'''

    def _get_api_template(self, name: str, crud: bool = True) -> str:
        """获取API模板"""
        if not crud:
            return f'''"""
{name} API
"""

from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/{name.lower()}s/", tags=["{name}"])
def get_{name.lower()}s(db: Session = Depends(get_db)):
    """Get all {name}s"""
    pass
'''
        else:
            return f'''"""
{name} API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from ..models.{name.lower()} import {name}
from ..schemas.{name.lower()} import {name}Create, {name}Update, {name}Response

router = APIRouter()


@router.post("/{name.lower()}s/", response_model={name}Response, tags=["{name}"])
def create_{name.lower()}(item: {name}Create, db: Session = Depends(get_db)):
    """Create {name}"""
    pass


@router.get("/{name.lower()}s/", response_model=List[{name}Response], tags=["{name}"])
def get_{name.lower()}s(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all {name}s"""
    pass


@router.get("/{name.lower()}s/{{item_id}}", response_model={name}Response, tags=["{name}"])
def get_{name.lower()}_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get {name} by ID"""
    pass


@router.put("/{name.lower()}s/{{item_id}}", response_model={name}Response, tags=["{name}"])
def update_{name.lower()}_by_id(item_id: int, item: {name}Update, db: Session = Depends(get_db)):
    """Update {name}"""
    pass


@router.delete("/{name.lower()}s/{{item_id}}", tags=["{name}"])
def delete_{name.lower()}_by_id(item_id: int, db: Session = Depends(get_db)):
    """Delete {name}"""
    pass
'''

    def _get_service_template(self, name: str) -> str:
        """获取服务模板"""
        return f'''"""
{name} Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.{name.lower()} import {name}
from ..schemas.{name.lower()} import {name}Create, {name}Update


class {name}Service:
    """
    {name} Service
    """
    
    @staticmethod
    def create(db: Session, item: {name}Create) -> {name}:
        """Create {name}"""
        pass
        
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[{name}]:
        """Get all {name}s"""
        pass
        
    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[{name}]:
        """Get {name} by ID"""
        pass
        
    @staticmethod
    def update(db: Session, item_id: int, item: {name}Update) -> Optional[{name}]:
        """Update {name}"""
        pass
        
    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        """Delete {name}"""
        pass
'''

    def _update_api_routes(self, app_dir: Path, name: str):
        """更新API路由"""
        api_init = app_dir / "api" / "__init__.py"
        if not api_init.exists():
            with open(api_init, "w", encoding="utf-8") as f:
                f.write(
                    '''"""
API Routes
"""

from fastapi import APIRouter

api_router = APIRouter()
'''
                )

        with open(api_init, "a", encoding="utf-8") as f:
            f.write(f"\nfrom .{name.lower()} import router as {name.lower()}_router")
            f.write(f"\napi_router.include_router({name.lower()}_router)")

    def _generate_schema(self, app_dir: Path, model: str):
        """生成Schema"""
        schemas_dir = app_dir / "schemas"
        schemas_dir.mkdir(exist_ok=True)

        schema_file = schemas_dir / f"{model.lower()}.py"
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write(
                f'''"""
{model} Schema
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class {model}Base(BaseModel):
    """Base schema for {model}"""
    pass


class {model}Create({model}Base):
    """Schema for creating {model}"""
    pass


class {model}Update({model}Base):
    """Schema for updating {model}"""
    pass


class {model}Response({model}Base):
    """Schema for {model} response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
'''
            )

    def _generate_api(self, app_dir: Path, model: str):
        """生成API"""
        self.add_api(app_dir.name, model, crud=True)

    def _generate_service(self, app_dir: Path, model: str):
        """生成Service"""
        self.add_service(app_dir.name, model)
