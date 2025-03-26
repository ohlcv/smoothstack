"""
文档生成命令
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional
from .base import BaseCommand


class DocsCommand(BaseCommand):
    """文档生成命令类"""

    def __init__(self):
        super().__init__()
        self.docs_dir = self.project_root / "docs"
        self.template_dir = self.project_root / "core" / "templates" / "docs"
        self.required_files = [
            "README.md",
            "API.md",
            "DEVELOPMENT.md",
            "DEPLOYMENT.md",
            "CONTRIBUTING.md",
        ]

    def generate(self, output_dir: Optional[str] = None):
        """生成文档"""
        self.info("开始生成文档...")

        # 验证模板
        self._validate_template()

        # 设置输出目录
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.docs_dir

        # 创建输出目录
        self.create_directory(str(output_path))

        try:
            # 复制模板文件
            self._copy_template(output_path)

            # 替换项目信息
            self._replace_project_info(output_path)

            self.success("文档生成完成")
        except Exception as e:
            self.error(f"文档生成失败: {str(e)}")
            raise

    def _validate_template(self):
        """验证文档模板"""
        self.info("验证文档模板...")

        if not self.template_dir.exists():
            raise RuntimeError(f"文档模板目录不存在: {self.template_dir}")

        # 检查必需文件
        for file in self.required_files:
            file_path = self.template_dir / file
            if not file_path.exists():
                raise RuntimeError(f"缺少必需的模板文件: {file}")

        # 检查模板文件格式
        for file in self.required_files:
            file_path = self.template_dir / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查必需变量
                required_vars = ["{{project_name}}", "{{version}}", "{{description}}"]
                for var in required_vars:
                    if var not in content:
                        raise RuntimeError(f"模板文件 {file} 缺少必需变量: {var}")

            except Exception as e:
                raise RuntimeError(f"验证模板文件 {file} 失败: {str(e)}")

    def _copy_template(self, output_path: Path):
        """复制模板文件"""
        self.info("复制模板文件...")

        for file in self.required_files:
            src = self.template_dir / file
            dst = output_path / file

            try:
                shutil.copy2(src, dst)
                self.info(f"已复制: {file}")
            except Exception as e:
                raise RuntimeError(f"复制文件 {file} 失败: {str(e)}")

    def _replace_project_info(self, output_path: Path):
        """替换项目信息"""
        self.info("替换项目信息...")

        # 读取项目配置
        config_file = self.project_root / "config" / "project.yaml"
        if not config_file.exists():
            raise RuntimeError("项目配置文件不存在")

        try:
            import yaml

            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            project_name = config.get("name", "Unknown Project")
            version = config.get("version", "0.1.0")
            description = config.get("description", "No description available")

            # 替换所有文件中的变量
            for file in self.required_files:
                file_path = output_path / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 替换变量
                    content = content.replace("{{project_name}}", project_name)
                    content = content.replace("{{version}}", version)
                    content = content.replace("{{description}}", description)

                    # 写回文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    self.info(f"已更新: {file}")
                except Exception as e:
                    raise RuntimeError(f"更新文件 {file} 失败: {str(e)}")

        except Exception as e:
            raise RuntimeError(f"读取项目配置失败: {str(e)}")

    def serve(self, port: int = 8000):
        """启动文档服务器"""
        self.info("启动文档服务器...")

        try:
            import http.server
            import socketserver

            # 切换到文档目录
            os.chdir(str(self.docs_dir))

            # 创建服务器
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), handler) as httpd:
                self.info(f"文档服务器已启动: http://localhost:{port}")
                httpd.serve_forever()

        except Exception as e:
            self.error(f"启动文档服务器失败: {str(e)}")
            raise
