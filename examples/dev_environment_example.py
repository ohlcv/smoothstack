#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境管理器示例

演示如何使用开发环境管理器创建和管理开发环境
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入容器管理器
from backend.container_manager import dev_environment_manager
from backend.container_manager.models.dev_environment import (
    DevEnvironment,
    EnvironmentType,
    PortMapping,
    VolumeMount,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dev_environment_example")


def list_templates_example():
    """列出所有模板"""
    print("\n=== 列出所有开发环境模板 ===")
    templates = dev_environment_manager.list_templates()

    if not templates:
        print("没有找到模板")
        return

    for template in templates:
        print(f"模板: {template.name} ({template.env_type.name})")
        print(f"  镜像: {template.image}")
        print(f"  描述: {template.description or '无'}")

        if template.ports:
            ports_str = ", ".join(str(p) for p in template.ports)
            print(f"  端口映射: {ports_str}")

        if template.volumes:
            print("  卷挂载:")
            for volume in template.volumes:
                print(f"    {volume}")

        print()


def create_custom_template_example():
    """创建自定义模板示例"""
    print("\n=== 创建自定义开发环境模板 ===")

    # 创建一个自定义的Flask开发环境模板
    flask_env = DevEnvironment(
        name="flask-dev",
        env_type=EnvironmentType.PYTHON,
        image="python:3.9-slim",
        description="Flask开发环境",
        working_dir="/app",
        command="flask run --host=0.0.0.0 --port=5000",
        ports=[
            PortMapping(host_port=5000, container_port=5000, description="Flask应用"),
            PortMapping(host_port=5678, container_port=5678, description="调试器"),
        ],
        volumes=[VolumeMount(host_path="${workspaceFolder}", container_path="/app")],
        environment={
            "FLASK_APP": "app.py",
            "FLASK_ENV": "development",
            "PYTHONPATH": "/app",
        },
        vscode_extensions=[
            "ms-python.python",
            "ms-python.vscode-pylance",
            "njpwerner.autodocstring",
        ],
    )

    # 保存模板
    success = dev_environment_manager.create_template(flask_env)

    if success:
        print(f"自定义模板 {flask_env.name} 创建成功")
    else:
        print(f"自定义模板创建失败")


def create_development_environment_example():
    """创建开发环境示例"""
    print("\n=== 创建开发环境 ===")

    # 选择一个模板
    template_name = "flask-dev"
    container_name = "flask-dev-container"

    # 设置项目目录
    project_dir = os.path.join(project_root, "examples", "flask_app")
    os.makedirs(project_dir, exist_ok=True)

    # 创建一个简单的Flask应用
    create_sample_flask_app(project_dir)

    # 创建开发环境
    options = {
        "create_devcontainer": True,
        "start_container": True,
        "pull_image": True,
        "environment": {"DEBUG": "true"},
    }

    success, message = dev_environment_manager.create_environment(
        template_name=template_name,
        container_name=container_name,
        project_dir=project_dir,
        options=options,
    )

    if success:
        print(f"开发环境创建成功: {message}")
        print(f"项目目录: {project_dir}")
        print(
            "现在您可以使用VSCode打开项目目录，然后使用Remote-Containers扩展在容器中打开项目"
        )
    else:
        print(f"开发环境创建失败: {message}")


def create_sample_flask_app(project_dir):
    """创建示例Flask应用"""
    # 创建app.py
    with open(os.path.join(project_dir, "app.py"), "w") as f:
        f.write(
            """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        "message": "Hello from Development Container!",
        "service": "Flask API"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
"""
        )

    # 创建requirements.txt
    with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
        f.write("flask==2.0.1\n")

    # 创建README.md
    with open(os.path.join(project_dir, "README.md"), "w") as f:
        f.write(
            """# Flask开发容器示例

这是一个使用开发容器的Flask应用示例。

## 使用方法

1. 使用VSCode打开此目录
2. 安装Remote-Containers扩展
3. 使用"Remote-Containers: Reopen in Container"命令在容器中打开
4. 容器启动后，应用将在http://localhost:5000运行

## API端点

- `GET /`: 返回问候消息
- `GET /health`: 返回健康状态检查
"""
        )


def export_template_example():
    """导出模板示例"""
    print("\n=== 导出模板 ===")

    template_name = "flask-dev"
    output_file = os.path.join(project_root, "examples", f"{template_name}.yaml")

    # 获取模板
    template = dev_environment_manager.get_template(template_name)

    if not template:
        print(f"模板 {template_name} 不存在")
        return

    # 导出模板
    success = template.save_to_file(output_file)

    if success:
        print(f"模板已导出到: {output_file}")

        # 显示文件内容
        print("\n文件内容预览:")
        with open(output_file, "r") as f:
            content = f.read()
            print("-" * 40)
            print(content[:500] + ("..." if len(content) > 500 else ""))
            print("-" * 40)
    else:
        print("模板导出失败")


def main():
    """主函数"""
    print("=== 开发环境管理器示例 ===")

    # 列出模板
    list_templates_example()

    # 创建自定义模板
    create_custom_template_example()

    # 再次列出模板验证创建成功
    list_templates_example()

    # 导出模板
    export_template_example()

    # 创建开发环境
    user_input = input("\n是否创建开发环境示例? (y/n): ").strip().lower()
    if user_input == "y":
        create_development_environment_example()
    else:
        print("跳过创建开发环境示例")

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
