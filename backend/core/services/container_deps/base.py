"""
容器依赖管理基础类
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path

from .docker.docker_api import DockerAPI
from .frontend import PackageManager, ContainerEnvironment

logger = logging.getLogger(__name__)


class ContainerDepsManager:
    """容器依赖管理器，负责管理Docker容器内的依赖"""

    def __init__(self, project_root: Optional[str] = None):
        """初始化容器依赖管理器

        Args:
            project_root: 项目根目录路径，如果为None则自动查找
        """
        # 设置项目根目录
        if project_root is None:
            # 自动查找项目根目录（查找包含.git或docker-compose.yml的目录）
            current_dir = Path(os.getcwd())
            root_dir = current_dir
            while root_dir != root_dir.parent:
                if (root_dir / ".git").exists() or (
                    root_dir / "docker-compose.yml"
                ).exists():
                    break
                root_dir = root_dir.parent

            # 如果未找到合适的目录，使用当前目录
            if root_dir == root_dir.parent:
                root_dir = current_dir

            self.project_root = str(root_dir)
        else:
            self.project_root = project_root

        # 初始化Docker API
        self.docker_api = DockerAPI()

        # 配置目录
        self.config_dir = os.path.join(self.project_root, "config", "container_deps")
        os.makedirs(self.config_dir, exist_ok=True)

        # 前端依赖配置文件
        self.frontend_deps_file = os.path.join(self.config_dir, "frontend_deps.json")

        # 后端依赖配置文件
        self.backend_deps_file = os.path.join(self.config_dir, "backend_deps.json")

        # 模板目录
        self.template_dir = os.path.join(
            self.project_root,
            "backend",
            "core",
            "services",
            "container_deps",
            "template",
        )

        # 初始化前端依赖管理器
        self.frontend_package_manager = PackageManager(
            self.project_root, self.docker_api
        )

        # 初始化前端容器环境管理器
        self.frontend_env_manager = ContainerEnvironment(
            self.docker_api, self.project_root
        )

        # 初始化配置
        self._init_config()

    def _init_config(self):
        """初始化配置文件"""
        # 确保前端依赖配置文件存在
        if not os.path.exists(self.frontend_deps_file):
            self._save_json(
                self.frontend_deps_file,
                {
                    "dev": {"dependencies": {}, "devDependencies": {}},
                    "prod": {"dependencies": {}, "devDependencies": {}},
                },
            )

        # 确保后端依赖配置文件存在
        if not os.path.exists(self.backend_deps_file):
            self._save_json(
                self.backend_deps_file,
                {
                    "dev": {"python_packages": {}, "system_packages": []},
                    "prod": {"python_packages": {}, "system_packages": []},
                },
            )

    def _load_json(self, file_path: str) -> Dict:
        """加载JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            JSON内容
        """
        try:
            if not os.path.exists(file_path):
                return {}

            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            return {}

    def _save_json(self, file_path: str, data: Dict) -> bool:
        """保存JSON文件

        Args:
            file_path: JSON文件路径
            data: 要保存的数据

        Returns:
            是否保存成功
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            return False

    # ==== 前端依赖管理 ====

    def get_frontend_deps(self, env: str = "dev") -> Dict:
        """获取前端依赖信息

        Args:
            env: 环境类型，dev或prod

        Returns:
            依赖信息字典
        """
        # 使用前端包管理器获取依赖信息
        deps = self.frontend_package_manager.list_dependencies()
        return deps

    def add_frontend_dep(
        self,
        package_name: str,
        version: Optional[str] = None,
        env: str = "dev",
        dev: bool = False,
    ) -> bool:
        """添加前端依赖

        Args:
            package_name: 包名
            version: 版本号，不指定则使用最新版
            env: 环境类型，dev或prod
            dev: 是否为开发依赖

        Returns:
            是否添加成功
        """
        # 使用前端包管理器添加依赖
        return self.frontend_package_manager.add_dependency(package_name, version, dev)

    def remove_frontend_dep(
        self, package_name: str, env: str = "dev", dev: Optional[bool] = None
    ) -> bool:
        """移除前端依赖

        Args:
            package_name: 包名
            env: 环境类型，dev或prod
            dev: 是否为开发依赖，None表示两者都检查

        Returns:
            是否移除成功
        """
        # 确定依赖类型
        dep_type = None
        if dev is not None:
            dep_type = "devDependencies" if dev else "dependencies"

        # 使用前端包管理器移除依赖
        return self.frontend_package_manager.remove_dependency(package_name, dep_type)

    def update_frontend_deps(
        self,
        packages: List[str] = None,
        env: str = "dev",
        container_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """更新前端依赖

        Args:
            packages: 要更新的包列表，不指定则更新全部
            env: 环境类型，dev或prod
            container_id: 容器ID，不指定则在本地环境更新

        Returns:
            (是否成功, 输出信息)
        """
        # 使用前端包管理器更新依赖
        return self.frontend_package_manager.update_dependencies(packages, container_id)

    def install_frontend_deps(
        self, env: str = "dev", container_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """安装前端依赖

        Args:
            env: 环境类型，dev或prod
            container_id: 容器ID，不指定则在本地环境安装

        Returns:
            (是否成功, 输出信息)
        """
        # 使用前端包管理器安装依赖
        return self.frontend_package_manager.install_dependencies(container_id)

    def get_outdated_frontend_deps(
        self, env: str = "dev", container_id: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """获取过时的前端依赖信息

        Args:
            env: 环境类型，dev或prod
            container_id: 容器ID，不指定则在本地环境检查

        Returns:
            (是否成功, 过时的依赖信息)
        """
        # 使用前端包管理器获取过时的依赖信息
        return self.frontend_package_manager.get_outdated_packages(container_id)

    def run_frontend_script(
        self, script_name: str, env: str = "dev", container_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """执行前端脚本

        Args:
            script_name: 脚本名称
            env: 环境类型，dev或prod
            container_id: 容器ID，不指定则在本地环境执行

        Returns:
            (是否成功, 输出信息)
        """
        # 使用前端包管理器执行脚本
        return self.frontend_package_manager.run_script(script_name, container_id)

    def list_frontend_templates(self) -> List[Dict[str, str]]:
        """获取前端容器模板列表

        Returns:
            模板列表，每个模板包含name和path
        """
        # 使用前端容器环境管理器获取模板列表
        return self.frontend_env_manager.get_container_templates()

    def create_frontend_template(self, name: str, content: str) -> bool:
        """创建前端容器模板

        Args:
            name: 模板名称
            content: 模板内容

        Returns:
            是否创建成功
        """
        # 使用前端容器环境管理器创建模板
        return self.frontend_env_manager.create_template(name, content)

    def delete_frontend_template(self, name: str) -> bool:
        """删除前端容器模板

        Args:
            name: 模板名称

        Returns:
            是否删除成功
        """
        # 使用前端容器环境管理器删除模板
        return self.frontend_env_manager.delete_template(name)

    def create_frontend_container(
        self, env: str = "dev", name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """创建前端容器

        Args:
            env: 环境类型，dev或prod
            name: 容器名称，不指定则自动生成

        Returns:
            (是否成功, 容器ID或错误信息)
        """
        # 使用前端容器环境管理器创建容器
        return self.frontend_env_manager.create_container(env, name)

    # ==== 后端依赖管理 ====

    def get_backend_deps(self, env: str = "dev") -> Dict:
        """获取后端依赖列表

        Args:
            env: 环境，dev或prod

        Returns:
            依赖列表
        """
        data = self._load_json(self.backend_deps_file)
        return data.get(env, {"python_packages": {}, "system_packages": []})

    def add_backend_python_dep(
        self, package_name: str, version: Optional[str] = None, env: str = "dev"
    ) -> bool:
        """添加后端Python依赖

        Args:
            package_name: 包名
            version: 版本号，None表示最新版本
            env: 环境，dev或prod

        Returns:
            是否添加成功
        """
        # 加载当前配置
        data = self._load_json(self.backend_deps_file)

        # 确保环境存在
        if env not in data:
            data[env] = {"python_packages": {}, "system_packages": []}

        # 添加依赖
        if version is None:
            # 不指定版本
            data[env]["python_packages"][package_name] = ""
        else:
            data[env]["python_packages"][package_name] = version

        # 保存配置
        return self._save_json(self.backend_deps_file, data)

    def add_backend_system_dep(self, package_name: str, env: str = "dev") -> bool:
        """添加后端系统依赖

        Args:
            package_name: 包名
            env: 环境，dev或prod

        Returns:
            是否添加成功
        """
        # 加载当前配置
        data = self._load_json(self.backend_deps_file)

        # 确保环境存在
        if env not in data:
            data[env] = {"python_packages": {}, "system_packages": []}

        # 添加依赖(如果不存在)
        if package_name not in data[env]["system_packages"]:
            data[env]["system_packages"].append(package_name)

        # 保存配置
        return self._save_json(self.backend_deps_file, data)

    def remove_backend_python_dep(self, package_name: str, env: str = "dev") -> bool:
        """移除后端Python依赖

        Args:
            package_name: 包名
            env: 环境，dev或prod

        Returns:
            是否移除成功
        """
        # 加载当前配置
        data = self._load_json(self.backend_deps_file)

        # 确保环境存在
        if env not in data:
            return False

        # 移除依赖
        if package_name in data[env]["python_packages"]:
            del data[env]["python_packages"][package_name]
            # 保存配置
            return self._save_json(self.backend_deps_file, data)

        return False

    def remove_backend_system_dep(self, package_name: str, env: str = "dev") -> bool:
        """移除后端系统依赖

        Args:
            package_name: 包名
            env: 环境，dev或prod

        Returns:
            是否移除成功
        """
        # 加载当前配置
        data = self._load_json(self.backend_deps_file)

        # 确保环境存在
        if env not in data:
            return False

        # 移除依赖
        if package_name in data[env]["system_packages"]:
            data[env]["system_packages"].remove(package_name)
            # 保存配置
            return self._save_json(self.backend_deps_file, data)

        return False

    # ==== 构建功能 ====

    def generate_frontend_dockerfile(
        self, env: str = "dev", output_path: Optional[str] = None
    ) -> str:
        """生成前端Dockerfile

        Args:
            env: 环境，dev或prod
            output_path: 输出路径，None表示返回内容而不保存

        Returns:
            Dockerfile内容
        """
        # 加载前端依赖
        frontend_deps = self.get_frontend_deps(env)

        # 加载模板
        template_file = os.path.join(
            self.template_dir, f"frontend_{env}.dockerfile.template"
        )
        if not os.path.exists(template_file):
            # 使用默认模板
            if env == "dev":
                template = """FROM node:16-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

# 安装依赖
RUN npm install

# 安装开发依赖
{dev_dependencies}

# 将所有文件复制到容器中
COPY . .

# 暴露端口
EXPOSE 3000

# 启动开发服务器
CMD ["npm", "run", "dev"]
"""
            else:  # prod
                template = """FROM node:16-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./

# 安装依赖
RUN npm install

# 将所有文件复制到容器中
COPY . .

# 构建应用
RUN npm run build

# 生产环境阶段
FROM nginx:stable-alpine

# 复制构建文件到Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""
        else:
            with open(template_file, "r", encoding="utf-8") as f:
                template = f.read()

        # 处理依赖
        dependencies = ""
        if frontend_deps["dependencies"]:
            deps_list = []
            for pkg, version in frontend_deps["dependencies"].items():
                if version and version != "latest":
                    deps_list.append(f"{pkg}@{version}")
                else:
                    deps_list.append(pkg)
            if deps_list:
                dependencies = f'RUN npm install --save {" ".join(deps_list)}'

        dev_dependencies = ""
        if frontend_deps["devDependencies"]:
            deps_list = []
            for pkg, version in frontend_deps["devDependencies"].items():
                if version and version != "latest":
                    deps_list.append(f"{pkg}@{version}")
                else:
                    deps_list.append(pkg)
            if deps_list:
                dev_dependencies = f'RUN npm install --save-dev {" ".join(deps_list)}'

        # 替换模板中的变量
        dockerfile = template.format(
            dependencies=dependencies, dev_dependencies=dev_dependencies
        )

        # 保存或返回
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(dockerfile)

        return dockerfile

    def generate_backend_dockerfile(
        self, env: str = "dev", output_path: Optional[str] = None
    ) -> str:
        """生成后端Dockerfile

        Args:
            env: 环境，dev或prod
            output_path: 输出路径，None表示返回内容而不保存

        Returns:
            Dockerfile内容
        """
        # 加载后端依赖
        backend_deps = self.get_backend_deps(env)

        # 加载模板
        template_file = os.path.join(
            self.template_dir, f"backend_{env}.dockerfile.template"
        )
        if not os.path.exists(template_file):
            # 使用默认模板
            if env == "dev":
                template = """FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \\
    apt-get install -y --no-install-recommends {system_packages} && \\
    apt-get clean && \\
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装其他Python依赖
{python_packages}

# 复制所有文件
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
"""
            else:  # prod
                template = """FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \\
    apt-get install -y --no-install-recommends {system_packages} && \\
    apt-get clean && \\
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装其他Python依赖
{python_packages}

# 复制所有文件
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
"""
        else:
            with open(template_file, "r", encoding="utf-8") as f:
                template = f.read()

        # 处理系统依赖
        system_packages = (
            " ".join(backend_deps["system_packages"])
            if backend_deps["system_packages"]
            else ""
        )
        if not system_packages:
            system_packages = "gcc"  # 默认至少安装gcc

        # 处理Python依赖
        python_packages = ""
        if backend_deps["python_packages"]:
            install_cmds = []
            for pkg, version in backend_deps["python_packages"].items():
                if version:
                    install_cmds.append(
                        f"RUN pip install --no-cache-dir {pkg}=={version}"
                    )
                else:
                    install_cmds.append(f"RUN pip install --no-cache-dir {pkg}")
            python_packages = "\n".join(install_cmds)

        # 替换模板中的变量
        dockerfile = template.format(
            system_packages=system_packages, python_packages=python_packages
        )

        # 保存或返回
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(dockerfile)

        return dockerfile

    def build_image(
        self,
        image_type: str,
        env: str = "dev",
        tag: Optional[str] = None,
        dockerfile_path: Optional[str] = None,
        context_path: Optional[str] = None,
    ) -> bool:
        """构建镜像

        Args:
            image_type: 镜像类型，frontend或backend
            env: 环境，dev或prod
            tag: 镜像标签，None表示使用默认标签
            dockerfile_path: Dockerfile路径，None表示自动生成
            context_path: 构建上下文路径，None表示使用默认路径

        Returns:
            是否构建成功
        """
        if image_type not in ["frontend", "backend"]:
            logger.error(f"不支持的镜像类型: {image_type}")
            return False

        # 设置默认标签
        if tag is None:
            tag = f"smoothstack-{image_type}-{env}:latest"

        # 设置构建上下文
        if context_path is None:
            if image_type == "frontend":
                context_path = os.path.join(self.project_root, "frontend")
            else:
                context_path = os.path.join(self.project_root, "backend")

        # 确保上下文路径存在
        if not os.path.exists(context_path):
            logger.error(f"构建上下文路径不存在: {context_path}")
            return False

        # 处理Dockerfile
        temp_dockerfile = None
        try:
            if dockerfile_path is None:
                # 生成临时Dockerfile
                temp_dockerfile = os.path.join(context_path, f"Dockerfile.{env}.temp")
                if image_type == "frontend":
                    self.generate_frontend_dockerfile(env, temp_dockerfile)
                else:
                    self.generate_backend_dockerfile(env, temp_dockerfile)
                dockerfile_path = temp_dockerfile

            # 构建镜像
            return self.docker_api.build_image(context_path, dockerfile_path, tag)

        finally:
            # 清理临时文件
            if temp_dockerfile and os.path.exists(temp_dockerfile):
                try:
                    os.remove(temp_dockerfile)
                except Exception as e:
                    logger.warning(f"清理临时Dockerfile失败: {e}")

    def export_deps(self, output_file: Optional[str] = None) -> Dict:
        """导出所有依赖配置

        Args:
            output_file: 输出文件路径，None表示仅返回数据不保存

        Returns:
            依赖配置数据
        """
        # 加载配置
        frontend_deps = self._load_json(self.frontend_deps_file)
        backend_deps = self._load_json(self.backend_deps_file)

        # 合并配置
        data = {"frontend": frontend_deps, "backend": backend_deps}

        # 保存或返回
        if output_file:
            self._save_json(output_file, data)

        return data

    def import_deps(self, input_file: str) -> bool:
        """导入依赖配置

        Args:
            input_file: 输入文件路径

        Returns:
            是否导入成功
        """
        try:
            # 加载配置
            data = self._load_json(input_file)

            # 验证数据格式
            if "frontend" not in data or "backend" not in data:
                logger.error("导入文件格式错误，缺少frontend或backend部分")
                return False

            # 保存配置
            self._save_json(self.frontend_deps_file, data["frontend"])
            self._save_json(self.backend_deps_file, data["backend"])

            return True

        except Exception as e:
            logger.error(f"导入依赖配置失败: {e}")
            return False
