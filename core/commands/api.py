"""
API命令
"""

import os
import sys
import uvicorn
import requests
from pathlib import Path
from typing import Optional
from .base import BaseCommand


class ApiCommand(BaseCommand):
    """API命令类"""

    def __init__(self):
        super().__init__()
        self.health_check_url = "http://localhost:8000/health"

    def run(self):
        """运行API服务"""
        self.info("启动API服务...")

        try:
            # 导入必要的模块
            from backend.api import create_app, get_settings

            # 获取API设置
            settings = get_settings()

            # 创建应用实例
            app = create_app()

            # 启动服务器
            uvicorn.run(
                app,
                host=settings.host,
                port=settings.port,
                reload=settings.debug,
                log_level=settings.log_level.lower(),
            )
        except Exception as e:
            self.error(f"启动API服务失败: {str(e)}")
            raise

    def check_status(self):
        """检查API服务状态"""
        self.info("检查API服务状态...")

        try:
            # 发送健康检查请求
            response = requests.get(self.health_check_url, timeout=5)

            # 检查响应状态
            if response.status_code == 200:
                self.success("API服务正常运行")
                return True
            else:
                self.warning(f"API服务异常 (状态码: {response.status_code})")
                return False

        except requests.exceptions.ConnectionError:
            self.error("API服务未运行")
            return False
        except requests.exceptions.Timeout:
            self.error("API服务响应超时")
            return False
        except Exception as e:
            self.error(f"检查API服务状态失败: {str(e)}")
            return False
