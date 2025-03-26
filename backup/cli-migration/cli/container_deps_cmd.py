"""
容器依赖管理命令模块
"""

import os
import sys
import click
from typing import Optional

# 确保能导入core模块
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from ..core.services.container_deps import ContainerDepsManager


@click.group(name="container-deps")
def container_deps_group():
    """容器依赖管理命令组"""
    pass


# ===== 前端依赖管理 =====


@container_deps_group.group(name="frontend")
def frontend_deps():
    """前端容器依赖管理"""
    pass


@frontend_deps.command("add")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--dev", is_flag=True, help="添加为开发依赖")
@click.option("--version", help="指定版本号")
def frontend_add(packages, env, dev, version):
    """添加前端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    success_count = 0

    for package in packages:
        click.echo(f"正在添加前端{'开发' if dev else ''}依赖: {package} (环境: {env})")
        if manager.add_frontend_dep(package, version, env, dev):
            click.echo(f"  添加成功: {package}")
            success_count += 1
        else:
            click.echo(f"  添加失败: {package}")

    if len(packages) > 1:
        click.echo(f"总结: {success_count}/{len(packages)} 个依赖添加成功")


@frontend_deps.command("remove")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--dev", is_flag=True, help="移除开发依赖")
def frontend_remove(packages, env, dev):
    """移除前端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    success_count = 0

    for package in packages:
        click.echo(f"正在移除前端依赖: {package} (环境: {env})")
        dev_flag = True if dev else None  # None表示两种类型都检查
        if manager.remove_frontend_dep(package, env, dev_flag):
            click.echo(f"  移除成功: {package}")
            success_count += 1
        else:
            click.echo(f"  移除失败: {package}")

    if len(packages) > 1:
        click.echo(f"总结: {success_count}/{len(packages)} 个依赖移除成功")


@frontend_deps.command("update")
@click.argument("packages", nargs=-1, required=False)
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--container", help="容器ID或名称")
def frontend_update(packages, env, container):
    """更新前端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    packages_list = list(packages) if packages else None

    click.echo(
        f"正在更新前端依赖{' ' + ', '.join(packages_list) if packages_list else ''}..."
    )
    success, output = manager.update_frontend_deps(packages_list, env, container)

    if success:
        click.echo("依赖更新成功")
        click.echo(output)
    else:
        click.echo(f"依赖更新失败: {output}")


@frontend_deps.command("install")
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--container", help="容器ID或名称")
def frontend_install(env, container):
    """安装前端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()

    click.echo("正在安装前端依赖...")
    success, output = manager.install_frontend_deps(env, container)

    if success:
        click.echo("依赖安装成功")
        click.echo(output)
    else:
        click.echo(f"依赖安装失败: {output}")


@frontend_deps.command("list")
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--dev", is_flag=True, help="仅显示开发依赖")
@click.option("--prod", is_flag=True, help="仅显示生产依赖")
def frontend_list(env, dev, prod):
    """列出前端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    deps = manager.get_frontend_deps(env)

    # 处理过滤选项
    if dev and not prod:
        dep_types = ["devDependencies"]
    elif prod and not dev:
        dep_types = ["dependencies"]
    else:
        dep_types = ["dependencies", "devDependencies"]

    # 按依赖类型显示
    for dep_type in dep_types:
        if dep_type in deps and deps[dep_type]:
            human_readable = "开发依赖" if dep_type == "devDependencies" else "生产依赖"
            click.echo(f"\n{human_readable}:")

            # 对依赖包按名称排序
            sorted_deps = sorted(deps[dep_type].items())

            # 计算最长包名以便对齐
            max_pkg_len = (
                max([len(pkg) for pkg, _ in sorted_deps]) if sorted_deps else 0
            )

            # 显示依赖
            for pkg, ver in sorted_deps:
                click.echo(f"  {pkg:{max_pkg_len}} : {ver}")
        else:
            human_readable = "开发依赖" if dep_type == "devDependencies" else "生产依赖"
            click.echo(f"\n{human_readable}: 无")


@frontend_deps.command("outdated")
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--container", help="容器ID或名称")
def frontend_outdated(env, container):
    """检查过时的前端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()

    click.echo("正在检查过时的前端依赖...")
    success, output = manager.get_outdated_frontend_deps(env, container)

    if success:
        if not output:
            click.echo("所有依赖都是最新的")
        else:
            click.echo("发现过时的依赖:")

            # 显示过时依赖
            # 不同的包管理器输出格式不同，这里做一个简单的适配
            if isinstance(output, dict):
                # npm格式
                for pkg, info in output.items():
                    current = info.get("current", "未知")
                    latest = info.get("latest", "未知")
                    wanted = info.get("wanted", latest)
                    click.echo(
                        f"  {pkg}: 当前 {current} -> 可更新到 {wanted} (最新 {latest})"
                    )
            elif isinstance(output, list):
                # yarn格式
                for item in output:
                    pkg = item.get("name", "未知")
                    current = item.get("current", "未知")
                    latest = item.get("latest", "未知")
                    click.echo(f"  {pkg}: 当前 {current} -> 最新 {latest}")
    else:
        click.echo("检查过时依赖失败")


@frontend_deps.command("run")
@click.argument("script")
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--container", help="容器ID或名称")
def frontend_run(script, env, container):
    """执行前端容器中的脚本"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()

    click.echo(f"正在执行脚本: {script}...")
    success, output = manager.run_frontend_script(script, env, container)

    if success:
        click.echo(f"脚本 {script} 执行成功")
        click.echo(output)
    else:
        click.echo(f"脚本 {script} 执行失败: {output}")


# ----- 前端容器模板管理 -----


@frontend_deps.group("template")
def frontend_template():
    """前端容器模板管理"""
    pass


@frontend_template.command("list")
def frontend_template_list():
    """列出可用的前端容器模板"""
    manager = ContainerDepsManager()
    templates = manager.list_frontend_templates()

    if not templates:
        click.echo("没有可用的前端容器模板")
        return

    click.echo("可用的前端容器模板:")
    for template in templates:
        click.echo(f"  {template['name']}")


@frontend_template.command("view")
@click.argument("name")
def frontend_template_view(name):
    """查看指定的前端容器模板内容"""
    manager = ContainerDepsManager()
    templates = manager.list_frontend_templates()

    # 检查模板是否存在
    template_exists = any(t["name"] == name for t in templates)
    if not template_exists:
        click.echo(f"错误: 模板 {name} 不存在")
        return

    # 查找模板路径
    template_path = next(t["path"] for t in templates if t["name"] == name)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        click.echo(f"模板 {name} 的内容:")
        click.echo("\n" + content)
    except Exception as e:
        click.echo(f"读取模板内容失败: {e}")


@frontend_template.command("create")
@click.argument("name")
@click.option("--file", help="从文件读取模板内容")
def frontend_template_create(name, file):
    """创建新的前端容器模板"""
    manager = ContainerDepsManager()

    # 检查模板名称
    if not name or "/" in name or "\\" in name:
        click.echo(f"错误: 模板名称不合法, 不能包含斜杠")
        return

    # 从文件读取或者交互式输入
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            click.echo(f"读取文件失败: {e}")
            return
    else:
        click.echo("请输入模板内容 (按Ctrl+D结束输入):")
        content_lines = []
        try:
            while True:
                line = input()
                content_lines.append(line)
        except EOFError:
            pass
        content = "\n".join(content_lines)

    # 创建模板
    if manager.create_frontend_template(name, content):
        click.echo(f"成功创建模板: {name}")
    else:
        click.echo(f"创建模板失败")


@frontend_template.command("delete")
@click.argument("name")
@click.option("--force", is_flag=True, help="强制删除，不提示确认")
def frontend_template_delete(name, force):
    """删除前端容器模板"""
    manager = ContainerDepsManager()

    # 默认模板不能删除
    if name in ["dev", "prod"]:
        click.echo(f"错误: 不能删除默认模板 {name}")
        return

    # 确认删除
    if not force and not click.confirm(f"确定要删除模板 {name} 吗?"):
        click.echo("操作已取消")
        return

    # 删除模板
    if manager.delete_frontend_template(name):
        click.echo(f"成功删除模板: {name}")
    else:
        click.echo(f"删除模板失败，可能模板不存在")


@frontend_deps.command("create-container")
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--name", help="容器名称")
def frontend_create_container(env, name):
    """创建前端容器"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()

    click.echo(f"正在创建{env}环境的前端容器...")
    success, result = manager.create_frontend_container(env, name)

    if success:
        click.echo(f"容器创建成功: {result}")
    else:
        click.echo(f"容器创建失败: {result}")


# ===== 后端依赖管理 =====


@container_deps_group.group("backend")
def backend_deps():
    """后端容器依赖管理"""
    pass


@backend_deps.command("add-python")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--version", help="指定版本号")
def backend_add_python(packages, env, version):
    """添加后端容器Python依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    success_count = 0

    for package in packages:
        click.echo(f"正在添加后端Python依赖: {package} (环境: {env})")
        if manager.add_backend_python_dep(package, version, env):
            click.echo(f"  添加成功: {package}")
            success_count += 1
        else:
            click.echo(f"  添加失败: {package}")

    if len(packages) > 1:
        click.echo(f"总结: {success_count}/{len(packages)} 个依赖添加成功")


@backend_deps.command("add-system")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境: dev或prod")
def backend_add_system(packages, env):
    """添加后端容器系统依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    success_count = 0

    for package in packages:
        click.echo(f"正在添加后端系统依赖: {package} (环境: {env})")
        if manager.add_backend_system_dep(package, env):
            click.echo(f"  添加成功: {package}")
            success_count += 1
        else:
            click.echo(f"  添加失败: {package}")

    if len(packages) > 1:
        click.echo(f"总结: {success_count}/{len(packages)} 个依赖添加成功")


@backend_deps.command("remove-python")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境: dev或prod")
def backend_remove_python(packages, env):
    """移除后端容器Python依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    success_count = 0

    for package in packages:
        click.echo(f"正在移除后端Python依赖: {package} (环境: {env})")
        if manager.remove_backend_python_dep(package, env):
            click.echo(f"  移除成功: {package}")
            success_count += 1
        else:
            click.echo(f"  移除失败: {package}")

    if len(packages) > 1:
        click.echo(f"总结: {success_count}/{len(packages)} 个依赖移除成功")


@backend_deps.command("remove-system")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境: dev或prod")
def backend_remove_system(packages, env):
    """移除后端容器系统依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    success_count = 0

    for package in packages:
        click.echo(f"正在移除后端系统依赖: {package} (环境: {env})")
        if manager.remove_backend_system_dep(package, env):
            click.echo(f"  移除成功: {package}")
            success_count += 1
        else:
            click.echo(f"  移除失败: {package}")

    if len(packages) > 1:
        click.echo(f"总结: {success_count}/{len(packages)} 个依赖移除成功")


@backend_deps.command("list")
@click.option("--env", default="dev", help="环境: dev或prod")
def backend_list(env):
    """列出后端容器依赖"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()
    deps = manager.get_backend_deps(env)

    click.echo(f"后端容器依赖 (环境: {env}):")

    if deps["python_packages"]:
        click.echo("\nPython依赖:")
        for pkg, version in deps["python_packages"].items():
            version_str = f": {version}" if version else ""
            click.echo(f"  {pkg}{version_str}")
    else:
        click.echo("\nPython依赖: 无")

    if deps["system_packages"]:
        click.echo("\n系统依赖:")
        for pkg in deps["system_packages"]:
            click.echo(f"  {pkg}")
    else:
        click.echo("\n系统依赖: 无")


# ===== Dockerfile管理 =====


@container_deps_group.group("dockerfile")
def dockerfile_cmd():
    """Dockerfile管理"""
    pass


@dockerfile_cmd.command("generate")
@click.argument("type", type=click.Choice(["frontend", "backend"]))
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--output", help="输出文件路径")
def dockerfile_generate(type, env, output):
    """生成Dockerfile"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()

    if type == "frontend":
        dockerfile = manager.generate_frontend_dockerfile(env, output)
    else:
        dockerfile = manager.generate_backend_dockerfile(env, output)

    if output:
        click.echo(f"Dockerfile已生成: {output}")
    else:
        click.echo("生成的Dockerfile:")
        click.echo("\n" + dockerfile)


@dockerfile_cmd.command("build")
@click.argument("type", type=click.Choice(["frontend", "backend"]))
@click.option("--env", default="dev", help="环境: dev或prod")
@click.option("--tag", help="镜像标签")
@click.option("--dockerfile", help="Dockerfile路径")
@click.option("--context", help="构建上下文路径")
def dockerfile_build(type, env, tag, dockerfile, context):
    """构建Docker镜像"""
    if env not in ["dev", "prod"]:
        click.echo(f"错误: 环境必须是dev或prod，当前值: {env}")
        return

    manager = ContainerDepsManager()

    if not tag:
        tag = f"smoothstack-{type}-{env}:latest"

    click.echo(f"开始构建 {type} {env} 镜像: {tag}")
    success = manager.build_image(type, env, tag, dockerfile, context)

    if success:
        click.echo(f"镜像构建成功: {tag}")
    else:
        click.echo(f"镜像构建失败: {tag}")


# ===== 依赖版本管理 =====


@container_deps_group.group("version")
def version_cmd():
    """依赖版本管理"""
    pass


@version_cmd.command("export")
@click.argument("output_file")
def version_export(output_file):
    """导出依赖配置"""
    manager = ContainerDepsManager()
    data = manager.export_deps(output_file)

    if not output_file:
        import json

        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"依赖配置已导出至: {output_file}")


@version_cmd.command("import")
@click.argument("input_file")
def version_import(input_file):
    """导入依赖配置"""
    if not os.path.exists(input_file):
        click.echo(f"错误: 文件不存在: {input_file}")
        return

    manager = ContainerDepsManager()
    success = manager.import_deps(input_file)

    if success:
        click.echo(f"依赖配置已导入: {input_file}")
    else:
        click.echo(f"依赖配置导入失败: {input_file}")


if __name__ == "__main__":
    container_deps_group()
