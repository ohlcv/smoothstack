#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API服务启动脚本
"""

import uvicorn
from backend.api import create_app, get_settings


def main():
    """启动API服务"""
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


if __name__ == "__main__":
    main()
