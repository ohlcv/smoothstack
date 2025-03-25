"""
前端容器环境管理

负责前端容器环境的配置和管理
"""

import os
import json
import logging
import tempfile
from typing import Dict, List, Optional, Union, Any, Tuple
import shutil

logger = logging.getLogger(__name__)


class ContainerEnvironment:
    """前端容器环境管理类"""

    def __init__(self, docker_api: Any, project_root: str):
        """初始化容器环境管理器

        Args:
            docker_api: Docker API对象
            project_root: 项目根目录
        """
        self.docker_api = docker_api
        self.project_root = project_root
        self.frontend_dir = os.path.join(self.project_root, "frontend")

        # Dockerfile模板目录
        self.template_dir = os.path.join(
            self.project_root, "config", "container_deps", "templates", "frontend"
        )
        os.makedirs(self.template_dir, exist_ok=True)

        # 默认的开发和生产环境Dockerfile模板
        self._ensure_default_templates()

    def _ensure_default_templates(self) -> None:
        """确保默认的Dockerfile模板存在"""
        # 开发环境模板
        dev_template_path = os.path.join(self.template_dir, "Dockerfile.dev")
        if not os.path.exists(dev_template_path):
            self._create_dev_template(dev_template_path)

        # 生产环境模板
        prod_template_path = os.path.join(self.template_dir, "Dockerfile.prod")
        if not os.path.exists(prod_template_path):
            self._create_prod_template(prod_template_path)

    def _create_dev_template(self, template_path: str) -> None:
        """创建开发环境Dockerfile模板

        Args:
            template_path: 模板文件路径
        """
        template_content = """# 前端开发环境Dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制package.json和package-lock.json（如果存在）
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 设置环境变量
ENV NODE_ENV=development

# 暴露端口
EXPOSE 5173

# 启动开发服务器
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
"""
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

    def _create_prod_template(self, template_path: str) -> None:
        """创建生产环境Dockerfile模板

        Args:
            template_path: 模板文件路径
        """
        template_content = """# 前端生产环境Dockerfile（多阶段构建）
# 构建阶段
FROM node:18-alpine as build

WORKDIR /app

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物到Nginx目录
COPY --from=build /app/dist /usr/share/nginx/html

# 配置Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
"""
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

    def generate_dockerfile(
        self, env: str = "dev", output_path: Optional[str] = None
    ) -> str:
        """生成Dockerfile

        Args:
            env: 环境类型，dev或prod
            output_path: 输出文件路径，不指定则返回内容

        Returns:
            Dockerfile内容或生成的文件路径
        """
        # 确认环境类型
        if env not in ["dev", "prod"]:
            raise ValueError(f"不支持的环境类型: {env}, 必须是dev或prod")

        # 确定模板路径
        template_path = os.path.join(self.template_dir, f"Dockerfile.{env}")
        if not os.path.exists(template_path):
            logger.error(f"模板文件不存在: {template_path}")
            return ""

        # 读取模板内容
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            # TODO: 增加变量替换功能

            # 如果指定了输出路径，保存文件
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return output_path

            # 否则返回内容
            return content
        except Exception as e:
            logger.error(f"生成Dockerfile失败: {e}")
            return ""

    def create_container(
        self, env: str = "dev", name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """创建前端容器

        Args:
            env: 环境类型，dev或prod
            name: 容器名称，不指定则自动生成

        Returns:
            (是否成功, 容器ID或错误信息)
        """
        # 生成临时Dockerfile
        with tempfile.NamedTemporaryFile(suffix=".dockerfile", delete=False) as temp:
            dockerfile_path = temp.name

        try:
            # 生成Dockerfile到临时文件
            content = self.generate_dockerfile(env, dockerfile_path)
            if not content:
                return False, f"生成{env}环境Dockerfile失败"

            # 构建镜像名称
            image_name = f"frontend-{env}:latest"
            if not name:
                name = f"frontend-{env}"

            # 构建镜像
            success = self.docker_api.build_image(
                context_path=self.frontend_dir,
                dockerfile_path=dockerfile_path,
                tag=image_name,
            )

            if not success:
                return False, f"构建{env}环境前端镜像失败"

            # TODO: 实现容器创建逻辑
            # 这里需要调用Docker API创建并启动容器

            return True, name
        except Exception as e:
            logger.error(f"创建前端容器失败: {e}")
            return False, str(e)
        finally:
            # 删除临时Dockerfile
            if os.path.exists(dockerfile_path):
                os.unlink(dockerfile_path)

    def get_container_templates(self) -> List[Dict[str, str]]:
        """获取可用的容器模板列表

        Returns:
            模板列表，每个模板包含name和path
        """
        templates = []

        try:
            for filename in os.listdir(self.template_dir):
                if filename.startswith("Dockerfile."):
                    # 提取环境类型
                    env_type = filename.replace("Dockerfile.", "")
                    template_path = os.path.join(self.template_dir, filename)

                    templates.append({"name": env_type, "path": template_path})
        except Exception as e:
            logger.error(f"获取容器模板列表失败: {e}")

        return templates

    def create_template(self, name: str, content: str) -> bool:
        """创建新的容器模板

        Args:
            name: 模板名称
            content: 模板内容

        Returns:
            是否创建成功
        """
        # 确保模板名称合法
        if not name or "/" in name or "\\" in name:
            logger.error(f"模板名称不合法: {name}")
            return False

        # 构建模板文件路径
        template_path = os.path.join(self.template_dir, f"Dockerfile.{name}")

        try:
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"创建容器模板失败: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """删除容器模板

        Args:
            name: 模板名称

        Returns:
            是否删除成功
        """
        # 检查是否是默认模板
        if name in ["dev", "prod"]:
            logger.error(f"不能删除默认模板: {name}")
            return False

        # 构建模板文件路径
        template_path = os.path.join(self.template_dir, f"Dockerfile.{name}")

        try:
            if os.path.exists(template_path):
                os.unlink(template_path)
                return True
            else:
                logger.error(f"模板不存在: {name}")
                return False
        except Exception as e:
            logger.error(f"删除容器模板失败: {e}")
            return False
