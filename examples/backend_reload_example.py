#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
后端热重载示例应用

演示如何在FastAPI应用中使用热重载功能
"""

import os
import sys
import time
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend_reload_example")

# 创建FastAPI应用
app = FastAPI(title="后端热重载示例", description="演示FastAPI应用的热重载功能")

# 定义一些基本变量
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 确保目录存在
TEMPLATE_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# 创建模板文件(如果不存在)
index_template = TEMPLATE_DIR / "index.html"
if not index_template.exists():
    with open(index_template, "w", encoding="utf-8") as f:
        f.write(
            """<!DOCTYPE html>
<html>
<head>
    <title>热重载示例</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .info {
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .time {
            font-weight: bold;
            color: #0066cc;
        }
        .counter {
            font-size: 24px;
            font-weight: bold;
            color: #cc0000;
            margin: 20px 0;
        }
        .actions {
            margin-top: 30px;
        }
        button {
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>后端热重载示例</h1>
    
    <div class="info">
        <p>当前服务器时间: <span class="time">{{ server_time }}</span></p>
        <p>服务器启动于: <span class="time">{{ start_time }}</span></p>
        <p>应用版本: <span>{{ version }}</span></p>
    </div>
    
    <div class="counter">
        计数器: {{ counter }}
    </div>
    
    <div class="actions">
        <button onclick="location.reload()">刷新页面</button>
        <button onclick="fetch('/api/increment').then(() => location.reload())">增加计数</button>
        <button onclick="fetch('/api/reset').then(() => location.reload())">重置计数</button>
    </div>
    
    <div class="info" style="margin-top: 30px;">
        <p>热重载说明:</p>
        <ol>
            <li>修改此应用的代码后，服务器会自动重启</li>
            <li>计数器值会在重启后保持，因为它存储在内存中</li>
            <li>尝试修改响应中的一些文本，然后保存文件查看效果</li>
        </ol>
    </div>
</body>
</html>"""
        )

# 设置模板和静态文件
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 内存中的数据
START_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
VERSION = "1.0.0"  # 尝试修改此值，然后保存文件查看热重载效果
COUNTER = 0


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页"""
    global COUNTER
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": START_TIME,
            "version": VERSION,
            "counter": COUNTER,
        },
    )


@app.get("/api/increment")
async def increment_counter():
    """增加计数器"""
    global COUNTER
    COUNTER += 1
    logger.info(f"计数器增加到: {COUNTER}")
    return {"counter": COUNTER}


@app.get("/api/reset")
async def reset_counter():
    """重置计数器"""
    global COUNTER
    COUNTER = 0
    logger.info("计数器已重置")
    return {"counter": COUNTER}


@app.get("/api/time")
async def get_time():
    """获取当前时间"""
    return {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("示例应用已启动")
    logger.info(f"请访问 http://localhost:8000 查看示例")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("示例应用已关闭")


if __name__ == "__main__":
    # 启动应用，开启热重载
    uvicorn.run(
        "backend_reload_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 启用uvicorn的热重载功能
        reload_dirs=[str(BASE_DIR)],  # 指定要监视的目录
    )
