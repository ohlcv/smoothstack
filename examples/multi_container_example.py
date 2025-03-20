#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多容器服务组示例

演示如何使用Smoothstack的服务编排功能
"""

import os
import sys
import time
import logging
from pathlib import Path

# 将项目根目录添加到Python路径，以便导入backend模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.container_manager.service_orchestrator import ServiceOrchestrator
from backend.container_manager.models.service_group import (
    ServiceGroup,
    Service,
    ServiceNetwork,
    ServiceDependency,
    ServiceStatus,
    NetworkMode,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("multi_container_example")


def create_web_app_service_group() -> ServiceGroup:
    """
    创建一个包含Web应用、数据库和Redis的服务组
    """
    # 创建服务组
    service_group = ServiceGroup(
        name="web_app",
        description="Web应用示例服务组",
        version="1.0",
    )

    # 添加自定义网络
    service_group.networks["app_network"] = ServiceNetwork(
        name="app_network",
        driver="bridge",
        subnet="172.28.0.0/16",
        gateway="172.28.0.1",
    )

    # 添加PostgreSQL服务
    service_group.services["postgres"] = Service(
        name="postgres",
        image="postgres:13",
        environment={
            "POSTGRES_USER": "app_user",
            "POSTGRES_PASSWORD": "app_password",
            "POSTGRES_DB": "app_db",
        },
        ports={"5432": "5432"},
        volumes={
            "./data/postgres": "/var/lib/postgresql/data",
        },
        networks=["app_network"],
        restart="unless-stopped",
        healthcheck={
            "test": ["CMD", "pg_isready", "-U", "app_user"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
        },
    )

    # 添加Redis服务
    service_group.services["redis"] = Service(
        name="redis",
        image="redis:alpine",
        ports={"6379": "6379"},
        volumes={
            "./data/redis": "/data",
        },
        networks=["app_network"],
        restart="unless-stopped",
        healthcheck={
            "test": ["CMD", "redis-cli", "ping"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
        },
    )

    # 添加Web应用服务，依赖PostgreSQL和Redis
    service_group.services["web"] = Service(
        name="web",
        image="python:3.9-slim",
        command="bash -c 'pip install flask psycopg2-binary redis && python /app/app.py'",
        environment={
            "DATABASE_URL": "postgresql://app_user:app_password@postgres:5432/app_db",
            "REDIS_URL": "redis://redis:6379/0",
            "PORT": "5000",
        },
        ports={"5000": "80"},
        volumes={
            "./app": "/app",
        },
        networks=["app_network"],
        working_dir="/app",
        depends_on=[
            ServiceDependency(service_name="postgres", condition="service_healthy"),
            ServiceDependency(service_name="redis", condition="service_healthy"),
        ],
        restart="unless-stopped",
    )

    return service_group


def setup_example_app():
    """
    设置示例应用文件
    """
    # 创建目录
    app_dir = Path("./app")
    app_dir.mkdir(exist_ok=True)

    # 创建示例Flask应用
    app_py = app_dir / "app.py"
    app_py.write_text(
        """
import os
import time
import flask
import psycopg2
import redis

app = flask.Flask(__name__)

# 连接数据库
def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

# 连接Redis
redis_client = redis.from_url(os.environ['REDIS_URL'])

# 初始化数据库表
def init_db():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute('CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY, timestamp TIMESTAMP)')
    conn.close()

# 初始化数据库
init_db()

@app.route('/')
def index():
    # 记录访问次数
    visit_count = redis_client.incr('visit_count')
    
    # 记录访问时间到数据库
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO visits (timestamp) VALUES (NOW())')
        cur.execute('SELECT COUNT(*) FROM visits')
        db_count = cur.fetchone()[0]
    conn.close()
    
    return flask.render_template('index.html', visit_count=visit_count, db_count=db_count)

# 创建模板目录
if not os.path.exists('templates'):
    os.mkdir('templates')
    
# 创建模板文件
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Smoothstack 多容器示例</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin-top: 20px; }
        h1 { color: #333; }
        .counter { font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <h1>Smoothstack 多容器服务示例</h1>
    <div class="container">
        <p>这是一个使用 Flask + PostgreSQL + Redis 的多容器示例应用。</p>
        <p>Redis 计数器: <span class="counter">{{ visit_count }}</span></p>
        <p>数据库记录数: <span class="counter">{{ db_count }}</span></p>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
"""
    )

    logger.info(f"示例应用文件已创建在 {app_dir}")


def main():
    """
    主函数，演示服务编排功能
    """
    # 初始化服务编排器
    orchestrator = ServiceOrchestrator()

    # 准备示例应用文件
    setup_example_app()

    # 创建服务组
    service_group = create_web_app_service_group()

    # 打印服务组信息
    logger.info(f"服务组: {service_group.name}")
    logger.info(f"描述: {service_group.description}")
    logger.info(f"服务数量: {len(service_group.services)}")
    logger.info(f"网络数量: {len(service_group.networks)}")

    # 保存服务组配置
    if orchestrator.save_service_group(service_group):
        logger.info(f"服务组配置已保存")
    else:
        logger.error(f"服务组配置保存失败")
        return

    # 部署服务组
    logger.info(f"开始部署服务组...")
    success, messages = orchestrator.deploy_service_group(service_group)
    for message in messages:
        logger.info(f"  - {message}")

    if not success:
        logger.error(f"服务组部署失败")
        return

    logger.info(f"服务组部署成功")

    # 启动服务组
    logger.info(f"开始启动服务组...")
    success, messages = orchestrator.start_service_group(service_group.name)
    for message in messages:
        logger.info(f"  - {message}")

    if not success:
        logger.error(f"服务组启动部分失败")
        return

    logger.info(f"服务组启动成功")
    logger.info(f"可以通过 http://localhost:80 访问示例Web应用")

    # 等待用户输入，保持容器运行
    try:
        logger.info("按 Ctrl+C 停止服务组...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到终止信号，开始停止服务组...")

    # 停止服务组
    success, messages = orchestrator.stop_service_group(service_group.name)
    for message in messages:
        logger.info(f"  - {message}")

    logger.info(f"服务组已停止")


if __name__ == "__main__":
    main()
