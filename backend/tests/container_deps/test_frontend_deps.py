"""
前端依赖管理模块测试
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# 确保能导入core模块
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from core.services.container_deps import ContainerDepsManager
from core.services.container_deps.frontend import PackageManager, ContainerEnvironment


class TestPackageManager(unittest.TestCase):
    """前端包管理器测试"""

    def setUp(self):
        """测试前准备工作"""
        # 创建临时目录作为项目根目录
        self.temp_dir = tempfile.mkdtemp()

        # 创建前端目录
        self.frontend_dir = os.path.join(self.temp_dir, "frontend")
        os.makedirs(self.frontend_dir, exist_ok=True)

        # 创建模拟的Docker API
        self.mock_docker_api = MagicMock()

        # 创建包管理器
        self.package_manager = PackageManager(self.temp_dir, self.mock_docker_api)

    def tearDown(self):
        """测试后清理工作"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)

    def test_load_save_package_json(self):
        """测试加载和保存package.json"""
        # 确认package.json已创建
        self.assertTrue(os.path.exists(os.path.join(self.frontend_dir, "package.json")))

        # 加载package.json
        package_json = self.package_manager.load_package_json()

        # 验证基本结构
        self.assertIn("dependencies", package_json)
        self.assertIn("devDependencies", package_json)

        # 修改并保存
        package_json["name"] = "test-frontend"
        result = self.package_manager.save_package_json(package_json)

        # 验证保存成功
        self.assertTrue(result)

        # 重新加载并验证修改生效
        package_json = self.package_manager.load_package_json()
        self.assertEqual(package_json["name"], "test-frontend")

    def test_add_dependency(self):
        """测试添加依赖"""
        # 添加生产依赖
        result = self.package_manager.add_dependency("vue", "^3.2.0", False)
        self.assertTrue(result)

        # 添加开发依赖
        result = self.package_manager.add_dependency("typescript", "^4.5.0", True)
        self.assertTrue(result)

        # 验证依赖已添加
        package_json = self.package_manager.load_package_json()
        self.assertIn("vue", package_json["dependencies"])
        self.assertEqual(package_json["dependencies"]["vue"], "^3.2.0")
        self.assertIn("typescript", package_json["devDependencies"])
        self.assertEqual(package_json["devDependencies"]["typescript"], "^4.5.0")

    def test_remove_dependency(self):
        """测试移除依赖"""
        # 先添加依赖
        self.package_manager.add_dependency("vue", "^3.2.0", False)
        self.package_manager.add_dependency("typescript", "^4.5.0", True)

        # 移除生产依赖
        result = self.package_manager.remove_dependency("vue", "dependencies")
        self.assertTrue(result)

        # 移除开发依赖
        result = self.package_manager.remove_dependency("typescript", "devDependencies")
        self.assertTrue(result)

        # 验证依赖已移除
        package_json = self.package_manager.load_package_json()
        self.assertNotIn("vue", package_json["dependencies"])
        self.assertNotIn("typescript", package_json["devDependencies"])

    def test_list_dependencies(self):
        """测试列出依赖"""
        # 先添加依赖
        self.package_manager.add_dependency("vue", "^3.2.0", False)
        self.package_manager.add_dependency("typescript", "^4.5.0", True)

        # 列出所有依赖
        deps = self.package_manager.list_dependencies()
        self.assertIn("dependencies", deps)
        self.assertIn("devDependencies", deps)
        self.assertIn("vue", deps["dependencies"])
        self.assertIn("typescript", deps["devDependencies"])

        # 只列出生产依赖
        deps = self.package_manager.list_dependencies("dependencies")
        self.assertIn("dependencies", deps)
        self.assertIn("vue", deps["dependencies"])

        # 只列出开发依赖
        deps = self.package_manager.list_dependencies("devDependencies")
        self.assertIn("devDependencies", deps)
        self.assertIn("typescript", deps["devDependencies"])

    @patch("subprocess.run")
    def test_install_dependencies(self, mock_run):
        """测试安装依赖"""
        # 模拟subprocess.run的返回值
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Dependencies installed successfully"
        mock_run.return_value = mock_process

        # 测试本地安装
        success, output = self.package_manager.install_dependencies()
        self.assertTrue(success)
        self.assertEqual(output, "Dependencies installed successfully")

        # 验证subprocess.run被正确调用
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], "npm")  # 默认使用npm
        self.assertEqual(args[0][1], "install")

        # 测试容器内安装
        mock_run.reset_mock()
        success, output = self.package_manager.install_dependencies("container123")
        self.assertTrue(success)

        # 验证subprocess.run被正确调用，使用docker exec
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], "docker")
        self.assertEqual(args[0][1], "exec")
        self.assertEqual(args[0][2], "container123")
        self.assertEqual(args[0][3], "npm")
        self.assertEqual(args[0][4], "install")


class TestContainerEnvironment(unittest.TestCase):
    """前端容器环境测试"""

    def setUp(self):
        """测试前准备工作"""
        # 创建临时目录作为项目根目录
        self.temp_dir = tempfile.mkdtemp()

        # 创建模拟的Docker API
        self.mock_docker_api = MagicMock()

        # 创建容器环境管理器
        self.container_env = ContainerEnvironment(self.mock_docker_api, self.temp_dir)

    def tearDown(self):
        """测试后清理工作"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)

    def test_default_templates(self):
        """测试默认模板"""
        # 检查默认模板是否创建
        template_dir = os.path.join(
            self.temp_dir, "config", "container_deps", "templates", "frontend"
        )
        dev_template_path = os.path.join(template_dir, "Dockerfile.dev")
        prod_template_path = os.path.join(template_dir, "Dockerfile.prod")

        self.assertTrue(os.path.exists(dev_template_path))
        self.assertTrue(os.path.exists(prod_template_path))

        # 验证模板内容
        with open(dev_template_path, "r", encoding="utf-8") as f:
            dev_content = f.read()
        with open(prod_template_path, "r", encoding="utf-8") as f:
            prod_content = f.read()

        self.assertIn("node:18-alpine", dev_content)
        self.assertIn("npm run dev", dev_content)
        self.assertIn("multi-stage", prod_content.lower())
        self.assertIn("nginx:alpine", prod_content)

    def test_template_management(self):
        """测试模板管理"""
        # 创建自定义模板
        template_content = """FROM node:16-alpine
WORKDIR /app
COPY . .
CMD ["npm", "start"]
"""
        result = self.container_env.create_template("custom", template_content)
        self.assertTrue(result)

        # 获取模板列表
        templates = self.container_env.get_container_templates()
        template_names = [t["name"] for t in templates]
        self.assertIn("dev", template_names)
        self.assertIn("prod", template_names)
        self.assertIn("custom", template_names)

        # 删除自定义模板
        result = self.container_env.delete_template("custom")
        self.assertTrue(result)

        # 验证模板已删除
        templates = self.container_env.get_container_templates()
        template_names = [t["name"] for t in templates]
        self.assertNotIn("custom", template_names)

        # 尝试删除默认模板（应该失败）
        result = self.container_env.delete_template("dev")
        self.assertFalse(result)

    def test_generate_dockerfile(self):
        """测试生成Dockerfile"""
        # 生成开发环境Dockerfile
        content = self.container_env.generate_dockerfile("dev")
        self.assertIsInstance(content, str)
        self.assertNotEqual(content, "")
        self.assertIn("node:18-alpine", content)

        # 生成生产环境Dockerfile
        content = self.container_env.generate_dockerfile("prod")
        self.assertIsInstance(content, str)
        self.assertNotEqual(content, "")
        self.assertIn("nginx:alpine", content)

        # 测试输出到文件
        output_path = os.path.join(self.temp_dir, "test.dockerfile")
        result = self.container_env.generate_dockerfile("dev", output_path)
        self.assertEqual(result, output_path)
        self.assertTrue(os.path.exists(output_path))

    def test_create_container(self):
        """测试创建容器"""
        # 模拟Docker API的行为
        self.mock_docker_api.build_image.return_value = True

        # 创建容器
        success, container_id = self.container_env.create_container(
            "dev", "test-container"
        )

        # 验证结果
        self.assertTrue(success)
        self.assertEqual(container_id, "test-container")

        # 验证Docker API调用
        self.mock_docker_api.build_image.assert_called_once()
        args = self.mock_docker_api.build_image.call_args[1]
        self.assertEqual(args["tag"], "frontend-dev:latest")

        # 测试创建失败的情况
        self.mock_docker_api.build_image.return_value = False
        success, error = self.container_env.create_container("dev")
        self.assertFalse(success)
        self.assertIn("失败", error)


class TestContainerDepsManager(unittest.TestCase):
    """容器依赖管理器集成测试"""

    def setUp(self):
        """测试前准备工作"""
        # 创建临时目录作为项目根目录
        self.temp_dir = tempfile.mkdtemp()

        # 打补丁来使用临时目录
        self.patcher = patch(
            "core.services.container_deps.base.ContainerDepsManager.__init__"
        )
        self.mock_init = self.patcher.start()
        self.mock_init.return_value = None

        # 创建管理器
        self.manager = ContainerDepsManager()
        self.manager.project_root = self.temp_dir

        # 创建模拟的Docker API
        self.mock_docker_api = MagicMock()
        self.manager.docker_api = self.mock_docker_api

        # 创建配置目录
        self.config_dir = os.path.join(self.temp_dir, "config", "container_deps")
        os.makedirs(self.config_dir, exist_ok=True)
        self.manager.config_dir = self.config_dir

        # 初始化前端管理器
        self.manager.frontend_package_manager = PackageManager(
            self.temp_dir, self.mock_docker_api
        )
        self.manager.frontend_env_manager = ContainerEnvironment(
            self.mock_docker_api, self.temp_dir
        )

        # 其他初始化
        self.manager._init_config = MagicMock()

    def tearDown(self):
        """测试后清理工作"""
        # 停止补丁
        self.patcher.stop()

        # 删除临时目录
        shutil.rmtree(self.temp_dir)

    def test_frontend_deps_integration(self):
        """测试前端依赖管理集成功能"""
        # 添加依赖
        result = self.manager.add_frontend_dep("vue", "^3.2.0", "dev", False)
        self.assertTrue(result)

        # 获取依赖列表
        deps = self.manager.get_frontend_deps("dev")
        self.assertIn("dependencies", deps)
        self.assertIn("vue", deps["dependencies"])

        # 移除依赖
        result = self.manager.remove_frontend_dep("vue", "dev", False)
        self.assertTrue(result)

        # 验证依赖已移除
        deps = self.manager.get_frontend_deps("dev")
        self.assertNotIn("vue", deps["dependencies"])

    @patch("subprocess.run")
    def test_frontend_deps_commands(self, mock_run):
        """测试前端依赖命令集成"""
        # 模拟subprocess.run的返回值
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Command executed successfully"
        mock_run.return_value = mock_process

        # 测试安装依赖
        success, output = self.manager.install_frontend_deps("dev")
        self.assertTrue(success)

        # 测试更新依赖
        success, output = self.manager.update_frontend_deps(["vue"], "dev")
        self.assertTrue(success)

        # 测试运行脚本
        success, output = self.manager.run_frontend_script("dev", "dev")
        self.assertTrue(success)

    def test_frontend_template_integration(self):
        """测试前端模板管理集成功能"""
        # 获取模板列表
        templates = self.manager.list_frontend_templates()
        template_names = [t["name"] for t in templates]
        self.assertIn("dev", template_names)
        self.assertIn("prod", template_names)

        # 创建自定义模板
        result = self.manager.create_frontend_template("test", "FROM node:16")
        self.assertTrue(result)

        # 验证模板已创建
        templates = self.manager.list_frontend_templates()
        template_names = [t["name"] for t in templates]
        self.assertIn("test", template_names)

        # 删除模板
        result = self.manager.delete_frontend_template("test")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
