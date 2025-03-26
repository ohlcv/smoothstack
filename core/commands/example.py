import os
import sys
import subprocess
from typing import Optional, List
from .base import BaseCommand


class ExampleCommand(BaseCommand):
    """示例项目管理命令"""

    def __init__(self):
        super().__init__()
        self.examples_dir = os.path.join(self.templates_dir, "framework-website")

    def _check_environment(self) -> bool:
        """检查环境是否满足要求"""
        try:
            # 检查Docker是否安装
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            self.logger.error("Docker未安装或无法访问")
            return False

    def _copy_example(self, name: str) -> bool:
        """复制示例项目到目标目录"""
        try:
            target_dir = os.path.join(os.getcwd(), name)
            if os.path.exists(target_dir):
                self.logger.error(f"目录 {name} 已存在")
                return False

            # 复制示例项目
            self._copy_directory(self.examples_dir, target_dir)
            self.logger.info(f"示例项目已复制到 {target_dir}")
            return True
        except Exception as e:
            self.logger.error(f"复制示例项目失败: {str(e)}")
            return False

    def create(self, name: str) -> bool:
        """创建示例项目"""
        if not self._check_environment():
            return False

        if not self._copy_example(name):
            return False

        try:
            # 进入项目目录
            os.chdir(name)

            # 启动项目
            self.logger.info("正在启动示例项目...")
            subprocess.run(["docker-compose", "up", "--build"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"启动项目失败: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}")
            return False

    def start(self, name: str) -> bool:
        """启动已存在的示例项目"""
        try:
            # 进入项目目录
            os.chdir(name)

            # 启动项目
            self.logger.info("正在启动项目...")
            subprocess.run(["docker-compose", "up"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"启动项目失败: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}")
            return False

    def stop(self, name: str) -> bool:
        """停止示例项目"""
        try:
            # 进入项目目录
            os.chdir(name)

            # 停止项目
            self.logger.info("正在停止项目...")
            subprocess.run(["docker-compose", "down"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"停止项目失败: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}")
            return False

    def list(self) -> List[str]:
        """列出可用的示例项目"""
        examples = []
        for item in os.listdir(self.templates_dir):
            if item.startswith("framework-"):
                examples.append(item.replace("framework-", ""))
        return examples
