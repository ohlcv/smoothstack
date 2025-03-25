"""
Smoothstack CLI 工具主入口
"""

import sys
import os
from typing import List, Optional

# 将项目根目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, project_root)

import click
from rich.console import Console
from rich.table import Table

# 使用注释掉相对导入，使用其他方式处理这些模块
# from .help import HelpManager
# from .help_cmd import help_command
# from .completion_cmd import completion
# from .log_cmd import log
# from .interactive_cmd import interactive
# from .version_cmd import version
# from .config_cmd import config
# from .utils.logger import init_logging, get_logger
# from .utils.errors import cli_error_handler, ConfigError, UserError
# from .utils.version import check_for_updates

# 导入依赖管理器和源管理器
from backend.dependency_manager import DependencyManager


# 创建主CLI组
@click.group()
def cli():
    """Smoothstack CLI 工具 - 简化全栈开发流程"""
    pass


# 依赖管理命令组
@cli.group(name="deps")
def deps_group():
    """依赖管理命令"""
    pass


# Docker命令组
@cli.group(name="docker")
def docker_group():
    """Docker管理命令"""
    pass


# 导入容器依赖管理命令
try:
    from .container_deps_cmd import container_deps_group

    print("成功导入容器依赖管理命令组")

    # 注册容器依赖管理命令组到主命令组
    cli.add_command(container_deps_group)
    print("已注册容器依赖管理命令组")
    print("可用命令:")
    print("  container-deps - 容器依赖管理")
except ImportError as e:
    print(f"无法导入容器依赖管理命令组: {e}")
    container_deps_group = None
except Exception as e:
    print(f"注册容器依赖管理命令组时出错: {e}")
    container_deps_group = None


# 导入容器管理命令
try:
    from backend.container_manager.commands.container_cmd import container_group

    print("成功导入容器管理命令组")
    docker_group.add_command(container_group)
    print("已注册容器管理命令组")
    print("可用命令:")
    for cmd in container_group.commands.values():
        print(f"  {cmd.name} - {cmd.help}")
except ImportError as e:
    print(f"无法导入容器管理命令组: {e}")
    container_group = None
except Exception as e:
    print(f"注册容器管理命令组时出错: {e}")
    container_group = None


# 初始化日志
# init_logging()

# 创建日志记录器
# logger = get_logger("cli")

# 创建Rich控制台实例
console = Console()

# 自动检查更新的间隔（天）
AUTO_CHECK_INTERVAL = 7


# 前端命令组
@cli.group("frontend")
def frontend_group():
    """前端相关命令"""
    pass


# 后端命令组
@cli.group("backend")
def backend_group():
    """后端相关命令"""
    pass


# 系统命令组
@cli.group("system")
def system_group():
    """系统级命令"""
    pass


# ===== 前端命令 =====


# 前端构建命令
@frontend_group.command("build")
@click.option("--mode", default="development", help="构建模式：development或production")
def frontend_build(mode):
    """构建前端应用"""
    click.echo(f"正在以{mode}模式构建前端应用...")
    # TODO: 实现前端构建逻辑


# 前端运行命令
@frontend_group.command("run")
@click.option("--port", default=3000, help="开发服务器端口")
def frontend_run(port):
    """启动前端开发服务器"""
    click.echo(f"正在启动前端开发服务器，端口：{port}...")
    # TODO: 实现前端运行逻辑


# 前端测试命令
@frontend_group.command("test")
@click.option("--watch", is_flag=True, help="监听文件变化")
def frontend_test(watch):
    """运行前端测试"""
    click.echo(f"正在运行前端测试，监听模式：{watch}...")
    # TODO: 实现前端测试逻辑


# 前端停止命令
@frontend_group.command("stop")
def frontend_stop():
    """停止前端服务"""
    click.echo("正在停止前端服务...")
    # TODO: 实现前端服务停止逻辑


# 前端状态命令
@frontend_group.command("status")
def frontend_status():
    """查看前端服务状态"""
    click.echo("前端服务状态：")
    # TODO: 实现前端状态检查逻辑


# 前端日志命令
@frontend_group.command("logs")
@click.option("--follow", "-f", is_flag=True, help="持续跟踪日志")
@click.option("--lines", "-n", default=100, help="显示的日志行数")
def frontend_logs(follow, lines):
    """查看前端日志"""
    click.echo(f"显示前端日志（行数：{lines}，跟踪模式：{follow}）...")
    # TODO: 实现前端日志查看逻辑


# 前端设置命令
@frontend_group.command("setup")
@click.option("--cn", is_flag=True, help="使用中国镜像源")
def frontend_setup(cn):
    """初始化前端开发环境"""
    click.echo(f"正在初始化前端开发环境，使用中国源：{cn}...")
    # TODO: 实现前端环境初始化逻辑


# ===== 前端依赖管理 =====
@frontend_group.group("deps")
def frontend_deps():
    """前端依赖管理"""
    pass


@frontend_deps.command("install")
@click.argument("packages", nargs=-1, required=True)
@click.option("--source", help="指定源名称")
@click.pass_context
def frontend_deps_install(ctx, packages, source):
    """安装前端依赖包"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()
    installer = "npm"  # 前端固定使用npm

    # 如果指定了源，先切换到该源
    if source:
        success = dm.source_manager.switch_active_source(source, installer)
        if not success:
            click.echo(f"错误: 切换到源 '{source}' 失败")
            ctx.exit(1)
        click.echo(f"已切换到源 '{source}'")

    for package in packages:
        click.echo(f"正在安装前端依赖包: {package}")
        success = dm.install(package, installer_type=installer)
        if success:
            click.echo(f"前端依赖包 {package} 安装成功")
        else:
            click.echo(f"前端依赖包 {package} 安装失败")
            ctx.exit(1)


@frontend_deps.command("update")
@click.argument("packages", nargs=-1, required=False)
@click.option("--source", help="指定源名称")
@click.pass_context
def frontend_deps_update(ctx, packages, source):
    """更新前端依赖包"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()
    installer = "npm"  # 前端固定使用npm

    # 如果指定了源，先切换到该源
    if source:
        success = dm.source_manager.switch_active_source(source, installer)
        if not success:
            click.echo(f"错误: 切换到源 '{source}' 失败")
            ctx.exit(1)
        click.echo(f"已切换到源 '{source}'")

    if packages:
        for package in packages:
            click.echo(f"正在更新前端依赖包: {package}")
            success = dm.update(package, installer_type=installer)
            if success:
                click.echo(f"前端依赖包 {package} 更新成功")
            else:
                click.echo(f"前端依赖包 {package} 更新失败")
                ctx.exit(1)
    else:
        click.echo("正在检查可更新的前端依赖包")
        updates = dm.check_updates(installer_type=installer)

        if not updates:
            click.echo("所有前端依赖包均为最新版本")
            return

        click.echo(f"发现 {len(updates)} 个可更新的前端依赖包:")
        for pkg in updates:
            pkg_name = pkg.get("name", "")
            current = pkg.get("current", "")
            latest = pkg.get("latest", "")
            click.echo(f"  {pkg_name}: {current} -> {latest}")

        if not click.confirm("是否更新所有前端依赖包?"):
            return

        success_count = 0
        fail_count = 0

        for pkg in updates:
            pkg_name = pkg.get("name", "")
            click.echo(f"正在更新 {pkg_name}")
            if dm.update(pkg_name, installer_type=installer):
                click.echo(f"  {pkg_name} 更新成功")
                success_count += 1
            else:
                click.echo(f"  {pkg_name} 更新失败")
                fail_count += 1

        click.echo(
            f"\n总结: {success_count} 个依赖更新成功，{fail_count} 个依赖更新失败"
        )


@frontend_deps.command("list")
def frontend_deps_list():
    """列出已安装的前端依赖包"""
    dm = DependencyManager()
    packages = dm.list_packages(installer_type="npm")

    if not packages:
        click.echo("未安装任何前端依赖包")
        return

    click.echo(f"已安装的前端依赖包 ({len(packages)}):")

    for pkg in packages:
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        click.echo(f"  {name}: {version}")


@frontend_deps.group("container")
def frontend_deps_container():
    """容器内前端依赖管理"""
    pass


@frontend_deps_container.command("add")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境：dev或prod")
def frontend_deps_container_add(packages, env):
    """添加容器内前端依赖"""
    for package in packages:
        click.echo(f"正在添加容器内前端依赖 {package} (环境: {env})...")
    # TODO: 实现容器内前端依赖添加逻辑


# ===== 后端命令 =====


# 后端运行命令
@backend_group.command("run")
@click.option("--port", default=5000, help="API服务器端口")
@click.option("--host", default="0.0.0.0", help="API服务器主机")
def backend_run(port, host):
    """启动后端API服务器"""
    click.echo(f"正在启动后端API服务器，地址：{host}:{port}...")
    # TODO: 实现后端服务器启动逻辑


# 后端测试命令
@backend_group.command("test")
@click.option("--coverage", is_flag=True, help="生成测试覆盖率报告")
def backend_test(coverage):
    """运行后端测试"""
    click.echo(f"正在运行后端测试，覆盖率报告：{coverage}...")
    # TODO: 实现后端测试逻辑


# 后端停止命令
@backend_group.command("stop")
def backend_stop():
    """停止后端服务"""
    click.echo("正在停止后端服务...")
    # TODO: 实现后端服务停止逻辑


# 后端状态命令
@backend_group.command("status")
def backend_status():
    """查看后端服务状态"""
    click.echo("后端服务状态：")
    # TODO: 实现后端状态检查逻辑


# 后端日志命令
@backend_group.command("logs")
@click.option("--follow", "-f", is_flag=True, help="持续跟踪日志")
@click.option("--lines", "-n", default=100, help="显示的日志行数")
def backend_logs(follow, lines):
    """查看后端日志"""
    click.echo(f"显示后端日志（行数：{lines}，跟踪模式：{follow}）...")
    # TODO: 实现后端日志查看逻辑


# 后端迁移命令
@backend_group.command("migrate")
@click.option("--fake", is_flag=True, help="假执行迁移")
def backend_migrate(fake):
    """运行数据库迁移"""
    click.echo(f"正在运行数据库迁移，假执行：{fake}...")
    # TODO: 实现数据库迁移逻辑


# 后端设置命令
@backend_group.command("setup")
@click.option("--cn", is_flag=True, help="使用中国镜像源")
def backend_setup(cn):
    """初始化后端开发环境"""
    click.echo(f"正在初始化后端开发环境，使用中国源：{cn}...")
    # TODO: 实现后端环境初始化逻辑


# ===== 后端依赖管理 =====
@backend_group.group("deps")
def backend_deps():
    """后端依赖管理"""
    pass


@backend_deps.command("install")
@click.argument("packages", nargs=-1, required=True)
@click.option("--source", help="指定源名称")
@click.pass_context
def backend_deps_install(ctx, packages, source):
    """安装后端依赖包"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()
    installer = "pip"  # 后端固定使用pip

    # 如果指定了源，先切换到该源
    if source:
        success = dm.source_manager.switch_active_source(source, installer)
        if not success:
            click.echo(f"错误: 切换到源 '{source}' 失败")
            ctx.exit(1)
        click.echo(f"已切换到源 '{source}'")

    for package in packages:
        click.echo(f"正在安装后端依赖包: {package}")
        success = dm.install(package, installer_type=installer)
        if success:
            click.echo(f"后端依赖包 {package} 安装成功")
        else:
            click.echo(f"后端依赖包 {package} 安装失败")
            ctx.exit(1)


@backend_deps.command("update")
@click.argument("packages", nargs=-1, required=False)
@click.option("--source", help="指定源名称")
@click.pass_context
def backend_deps_update(ctx, packages, source):
    """更新后端依赖包"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()
    installer = "pip"  # 后端固定使用pip

    # 如果指定了源，先切换到该源
    if source:
        success = dm.source_manager.switch_active_source(source, installer)
        if not success:
            click.echo(f"错误: 切换到源 '{source}' 失败")
            ctx.exit(1)
        click.echo(f"已切换到源 '{source}'")

    if packages:
        for package in packages:
            click.echo(f"正在更新后端依赖包: {package}")
            success = dm.update(package, installer_type=installer)
            if success:
                click.echo(f"后端依赖包 {package} 更新成功")
            else:
                click.echo(f"后端依赖包 {package} 更新失败")
                ctx.exit(1)
    else:
        click.echo("正在检查可更新的后端依赖包")
        updates = dm.check_updates(installer_type=installer)

        if not updates:
            click.echo("所有后端依赖包均为最新版本")
            return

        click.echo(f"发现 {len(updates)} 个可更新的后端依赖包:")
        for pkg in updates:
            pkg_name = pkg.get("name", "")
            current = pkg.get("current", "")
            latest = pkg.get("latest", "")
            click.echo(f"  {pkg_name}: {current} -> {latest}")

        if not click.confirm("是否更新所有后端依赖包?"):
            return

        success_count = 0
        fail_count = 0

        for pkg in updates:
            pkg_name = pkg.get("name", "")
            click.echo(f"正在更新 {pkg_name}")
            if dm.update(pkg_name, installer_type=installer):
                click.echo(f"  {pkg_name} 更新成功")
                success_count += 1
            else:
                click.echo(f"  {pkg_name} 更新失败")
                fail_count += 1

        click.echo(f"更新完成: {success_count}个成功, {fail_count}个失败")


@backend_deps.command("list")
def backend_deps_list():
    """列出已安装的后端依赖包"""
    dm = DependencyManager()
    packages = dm.list_packages(installer_type="pip")

    if not packages:
        click.echo("未安装任何后端依赖包")
        return

    click.echo(f"已安装的后端依赖包 ({len(packages)}):")

    for pkg in packages:
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        click.echo(f"  {name}: {version}")


@backend_deps.group("container")
def backend_deps_container():
    """容器内后端依赖管理"""
    pass


@backend_deps_container.command("add")
@click.argument("packages", nargs=-1, required=True)
@click.option("--env", default="dev", help="环境：dev或prod")
@click.option("--system", is_flag=True, help="安装系统包而非Python包")
def backend_deps_container_add(packages, env, system):
    """添加容器内后端依赖"""
    pkg_type = "系统" if system else "Python"
    for package in packages:
        click.echo(f"正在添加容器内后端{pkg_type}依赖 {package} (环境: {env})...")
    # TODO: 实现容器内后端依赖添加逻辑


# ===== 系统命令 =====


# 系统状态命令
@system_group.command("status")
def system_status():
    """查看所有服务状态"""
    click.echo("系统状态：")
    # TODO: 实现系统状态检查逻辑


# 系统重启命令
@system_group.command("restart")
@click.option("--frontend", is_flag=True, help="仅重启前端服务")
@click.option("--backend", is_flag=True, help="仅重启后端服务")
def system_restart(frontend, backend):
    """重启系统服务"""
    if frontend and not backend:
        click.echo("正在重启前端服务...")
        # TODO: 实现前端重启逻辑
    elif backend and not frontend:
        click.echo("正在重启后端服务...")
        # TODO: 实现后端重启逻辑
    else:
        click.echo("正在重启所有服务...")
        # TODO: 实现全系统重启逻辑


# 系统停止命令
@system_group.command("stop")
def system_stop():
    """停止所有服务"""
    click.echo("正在停止所有服务...")
    # TODO: 实现系统停止逻辑


# 系统运行命令
@system_group.command("run")
def system_run():
    """启动所有服务"""
    click.echo("正在启动所有服务...")
    # TODO: 实现系统启动逻辑


# 系统更新命令
@system_group.command("update")
def system_update():
    """更新整个系统"""
    click.echo("正在更新系统...")
    # TODO: 实现系统更新逻辑


# 系统清理命令
@system_group.command("clean")
@click.option("--cache", is_flag=True, help="清理缓存")
@click.option("--temp", is_flag=True, help="清理临时文件")
@click.option("--all", is_flag=True, help="清理所有")
def system_clean(cache, temp, all):
    """清理系统文件"""
    if all:
        cache = temp = True

    if cache:
        click.echo("正在清理缓存...")
        # TODO: 实现缓存清理逻辑

    if temp:
        click.echo("正在清理临时文件...")
        # TODO: 实现临时文件清理逻辑


# 系统日志命令
@system_group.command("logs")
@click.option("--follow", "-f", is_flag=True, help="持续跟踪日志")
@click.option("--service", help="指定服务名称")
def system_logs(follow, service):
    """查看系统日志"""
    if service:
        click.echo(f"显示服务 {service} 的日志，跟踪模式：{follow}...")
    else:
        click.echo(f"显示所有服务的日志，跟踪模式：{follow}...")
    # TODO: 实现日志查看逻辑


# ===== 系统源管理 =====
@system_group.group("sources")
def system_sources():
    """源管理"""
    pass


@system_sources.command("list")
@click.option("--installer", default="all", help="安装器类型 (pip, npm, all)")
def system_sources_list(installer):
    """列出可用的源"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()

    installers = ["pip", "npm"] if installer == "all" else [installer]

    for inst in installers:
        sources = dm.source_manager.list_sources(inst)

        if not sources:
            click.echo(f"未配置任何 {inst} 源")
            continue

        active_source = None
        for source in sources:
            if source.get("active", False):
                active_source = source.get("name", "")
                break

        click.echo(f"{inst} 可用源列表:")
        for source in sources:
            name = source.get("name", "")
            url = source.get("url", "")
            is_active = " (当前)" if source.get("active", False) else ""
            click.echo(f"  {name}: {url}{is_active}")


@system_sources.command("switch")
@click.argument("name")
@click.option("--installer", default="all", help="安装器类型 (pip, npm, all)")
@click.pass_context
def system_sources_switch(ctx, name, installer):
    """切换源"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()

    installers = ["pip", "npm"] if installer == "all" else [installer]
    success_all = True

    for inst in installers:
        click.echo(f"正在切换 {inst} 源到 {name}...")
        success = dm.source_manager.switch_active_source(name, inst)
        if success:
            click.echo(f"{inst} 源切换成功")
        else:
            click.echo(f"{inst} 源切换失败")
            success_all = False

    if not success_all:
        ctx.exit(1)


# ===== 兼容旧命令 =====


# 创建依赖管理兼容命令组
@cli.group("deps")
def deps_compat():
    """依赖包管理（兼容旧命令）"""
    click.echo("警告: 此命令将被弃用，请使用 frontend deps 或 backend deps")
    pass


@deps_compat.command("list")
@click.option("--installer", default="pip", help="安装器类型 (pip, npm)")
def deps_list_compat(installer):
    """列出已安装的依赖包"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()
    packages = dm.list_packages(installer_type=installer)

    if not packages:
        click.echo("未安装任何依赖包")
        return

    click.echo(f"已安装的依赖包 ({len(packages)}):")

    for pkg in packages:
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        click.echo(f"  {name}: {version}")


# 创建源管理兼容命令组
@cli.group("sources")
def sources_compat():
    """管理安装源（兼容旧命令）"""
    click.echo("警告: 此命令将被弃用，请使用 system sources")
    pass


@sources_compat.command("list")
@click.option("--installer", default="pip", help="安装器类型 (pip, npm)")
def sources_list_compat(installer):
    """列出可用的源"""
    from backend.dependency_manager import DependencyManager

    dm = DependencyManager()
    sources = dm.source_manager.list_sources(installer)

    if not sources:
        click.echo(f"未配置任何 {installer} 源")
        return

    active_source = None
    for source in sources:
        if source.get("active", False):
            active_source = source.get("name", "")
            break

    click.echo(f"{installer} 可用源列表:")
    for source in sources:
        name = source.get("name", "")
        url = source.get("url", "")
        is_active = " (当前)" if source.get("active", False) else ""
        click.echo(f"  {name}: {url}{is_active}")


# 兼容旧的容器管理命令组
@cli.group("container")
def container_compat():
    """容器管理（兼容旧命令）"""
    click.echo("警告: 此命令将被弃用，请使用 system docker")
    pass


if __name__ == "__main__":
    # 如果直接运行此文件，执行CLI
    cli()
