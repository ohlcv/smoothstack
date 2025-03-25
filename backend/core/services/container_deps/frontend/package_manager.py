"""
前端容器依赖包管理器

负责管理容器内的package.json文件和执行npm/yarn命令
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class PackageManager:
    """前端包管理器，负责管理package.json和执行npm/yarn命令"""

    def __init__(self, project_root: str, docker_api: Any):
        """初始化包管理器

        Args:
            project_root: 项目根目录
            docker_api: Docker API对象
        """
        self.project_root = project_root
        self.docker_api = docker_api

        # 前端项目目录
        self.frontend_dir = os.path.join(self.project_root, "frontend")

        # 确保前端项目目录存在
        os.makedirs(self.frontend_dir, exist_ok=True)

        # 包管理器类型：npm或yarn
        self.package_manager_type = self._detect_package_manager()

        # 项目package.json文件路径
        self.package_json_path = os.path.join(self.frontend_dir, "package.json")

        # 如果package.json不存在，创建一个基础版本
        if not os.path.exists(self.package_json_path):
            self._create_default_package_json()

    def _detect_package_manager(self) -> str:
        """检测项目使用的包管理器类型（npm或yarn）

        Returns:
            包管理器类型："npm"或"yarn"
        """
        # 检查是否存在yarn.lock文件
        if os.path.exists(os.path.join(self.frontend_dir, "yarn.lock")):
            return "yarn"

        # 默认使用npm
        return "npm"

    def _create_default_package_json(self) -> None:
        """创建默认的package.json文件"""
        default_package = {
            "name": "frontend",
            "version": "0.1.0",
            "private": True,
            "description": "Frontend for the project",
            "scripts": {
                "dev": "vite",
                "build": "vue-tsc && vite build",
                "preview": "vite preview",
            },
            "dependencies": {},
            "devDependencies": {},
        }

        with open(self.package_json_path, "w", encoding="utf-8") as f:
            json.dump(default_package, f, indent=2)

    def load_package_json(self) -> Dict:
        """加载package.json文件内容

        Returns:
            package.json的内容
        """
        try:
            with open(self.package_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载package.json失败: {e}")
            return {"dependencies": {}, "devDependencies": {}}

    def save_package_json(self, content: Dict) -> bool:
        """保存package.json文件

        Args:
            content: 文件内容

        Returns:
            是否保存成功
        """
        try:
            with open(self.package_json_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存package.json失败: {e}")
            return False

    def add_dependency(
        self, package_name: str, version: Optional[str] = None, is_dev: bool = False
    ) -> bool:
        """添加依赖包

        Args:
            package_name: 包名
            version: 版本号，不指定则使用最新版
            is_dev: 是否为开发依赖

        Returns:
            是否添加成功
        """
        package_json = self.load_package_json()

        # 确定依赖类型
        dep_type = "devDependencies" if is_dev else "dependencies"

        # 确保依赖对象存在
        if dep_type not in package_json:
            package_json[dep_type] = {}

        # 添加或更新依赖
        if version:
            package_json[dep_type][package_name] = version
        else:
            # 不指定版本号时，使用latest
            package_json[dep_type][package_name] = "latest"

        # 保存修改后的package.json
        return self.save_package_json(package_json)

    def remove_dependency(
        self, package_name: str, dep_type: Optional[str] = None
    ) -> bool:
        """移除依赖包

        Args:
            package_name: 包名
            dep_type: 依赖类型，可以是"dependencies"、"devDependencies"或None（检查两者）

        Returns:
            是否移除成功
        """
        package_json = self.load_package_json()
        removed = False

        # 如果未指定依赖类型，检查两种类型
        if dep_type is None:
            dep_types = ["dependencies", "devDependencies"]
        else:
            dep_types = [dep_type]

        # 从指定的依赖类型中移除
        for dt in dep_types:
            if dt in package_json and package_name in package_json[dt]:
                del package_json[dt][package_name]
                removed = True

        # 如果移除了依赖，保存修改
        if removed:
            return self.save_package_json(package_json)

        return False

    def list_dependencies(
        self, dep_type: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """列出依赖包

        Args:
            dep_type: 依赖类型，可以是"dependencies"、"devDependencies"或None（返回两者）

        Returns:
            依赖列表，格式为 {依赖类型: {包名: 版本号}}
        """
        package_json = self.load_package_json()
        result = {}

        # 如果未指定依赖类型，返回两种类型
        if dep_type is None:
            dep_types = ["dependencies", "devDependencies"]
        else:
            dep_types = [dep_type]

        # 收集指定类型的依赖
        for dt in dep_types:
            if dt in package_json:
                result[dt] = package_json[dt]
            else:
                result[dt] = {}

        return result

    def install_dependencies(
        self, container_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """在容器内安装依赖包

        Args:
            container_id: 容器ID，不指定则使用当前环境

        Returns:
            (是否成功, 输出信息)
        """
        cmd_prefix = self.package_manager_type  # npm或yarn

        if container_id:
            # 在容器内执行
            full_cmd = ["docker", "exec", container_id, cmd_prefix, "install"]
        else:
            # 在本地执行
            full_cmd = [cmd_prefix, "install"]

        try:
            result = subprocess.run(
                full_cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            success = result.returncode == 0
            output = result.stdout if success else f"{result.stdout}\n{result.stderr}"

            if success:
                logger.info("依赖安装成功")
            else:
                logger.error(f"依赖安装失败: {output}")

            return success, output
        except Exception as e:
            logger.error(f"执行依赖安装命令失败: {e}")
            return False, str(e)

    def update_dependencies(
        self, packages: List[str] = None, container_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """在容器内更新依赖包

        Args:
            packages: 要更新的包列表，不指定则更新全部
            container_id: 容器ID，不指定则使用当前环境

        Returns:
            (是否成功, 输出信息)
        """
        cmd_prefix = self.package_manager_type  # npm或yarn

        # 构建命令
        if self.package_manager_type == "npm":
            cmd = [cmd_prefix, "update"]
        else:  # yarn
            cmd = [cmd_prefix, "upgrade"]

        # 添加包名（如果指定）
        if packages:
            cmd.extend(packages)

        if container_id:
            # 在容器内执行
            full_cmd = ["docker", "exec", container_id] + cmd
        else:
            # 在本地执行
            full_cmd = cmd

        try:
            result = subprocess.run(
                full_cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            success = result.returncode == 0
            output = result.stdout if success else f"{result.stdout}\n{result.stderr}"

            if success:
                logger.info("依赖更新成功")
            else:
                logger.error(f"依赖更新失败: {output}")

            return success, output
        except Exception as e:
            logger.error(f"执行依赖更新命令失败: {e}")
            return False, str(e)

    def get_outdated_packages(
        self, container_id: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """获取过时的依赖包信息

        Args:
            container_id: 容器ID，不指定则使用当前环境

        Returns:
            (是否成功, 过时包信息)
        """
        cmd_prefix = self.package_manager_type  # npm或yarn

        # npm outdated --json 或 yarn outdated --json
        cmd = [cmd_prefix, "outdated", "--json"]

        if container_id:
            # 在容器内执行
            full_cmd = ["docker", "exec", container_id] + cmd
        else:
            # 在本地执行
            full_cmd = cmd

        try:
            result = subprocess.run(
                full_cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            # npm outdated在没有过时包时会返回非零状态码
            if result.returncode != 0 and not result.stdout.strip():
                return False, {}

            try:
                outdated_data = json.loads(result.stdout)
                return True, outdated_data
            except json.JSONDecodeError:
                logger.error(f"解析过时包信息失败: {result.stdout}")
                return False, {}

        except Exception as e:
            logger.error(f"获取过时包信息失败: {e}")
            return False, {}

    def run_script(
        self, script_name: str, container_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """执行package.json中定义的脚本

        Args:
            script_name: 脚本名称
            container_id: 容器ID，不指定则使用当前环境

        Returns:
            (是否成功, 输出信息)
        """
        cmd_prefix = self.package_manager_type  # npm或yarn

        # npm run script_name 或 yarn run script_name
        cmd = [cmd_prefix, "run", script_name]

        if container_id:
            # 在容器内执行
            full_cmd = ["docker", "exec", container_id] + cmd
        else:
            # 在本地执行
            full_cmd = cmd

        try:
            result = subprocess.run(
                full_cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            success = result.returncode == 0
            output = result.stdout if success else f"{result.stdout}\n{result.stderr}"

            if success:
                logger.info(f"脚本 {script_name} 执行成功")
            else:
                logger.error(f"脚本 {script_name} 执行失败: {output}")

            return success, output
        except Exception as e:
            logger.error(f"执行脚本命令失败: {e}")
            return False, str(e)
