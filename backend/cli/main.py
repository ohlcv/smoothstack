"""
Smoothstack CLI 工具主入口
"""

import sys
import os
from typing import List, Optional
import click
from rich.console import Console

from .help import HelpManager
from .help_cmd import help_command
from .completion_cmd import completion
from .log_cmd import log
from .interactive_cmd import interactive
from .version_cmd import version
from .config_cmd import config
from .utils.logger import init_logging, get_logger
from .utils.errors import cli_error_handler, ConfigError, UserError
from .utils.version import check_for_updates

# 初始化日志
init_logging()

# 创建日志记录器
logger = get_logger("cli")

# 创建Rich控制台实例
console = Console()

# 自动检查更新的间隔（天）
AUTO_CHECK_INTERVAL = 7


# 全局选项装饰器
def global_options(func):
    """添加全局选项的装饰器"""
    func = click.option(
        "--verbose",
        "-v",
        count=True,
        help="增加详细输出级别 (-v: 信息, -vv: 调试, -vvv: 跟踪)",
    )(func)
    func = click.option(
        "--quiet", "-q", is_flag=True, help="降低输出级别，只显示警告和错误"
    )(func)
    func = click.option("--no-color", is_flag=True, help="禁用彩色输出")(func)
    func = click.option("--log-file", help="指定日志文件路径")(func)
    func = click.option("--interactive", "-i", is_flag=True, help="启动交互式模式")(
        func
    )
    func = click.option("--no-update-check", is_flag=True, help="禁用自动更新检查")(
        func
    )
    return func


@click.group()
@click.version_option(version="1.0.0")
@global_options
@click.pass_context
def cli(ctx, verbose, quiet, no_color, log_file, interactive, no_update_check):
    """Smoothstack CLI 工具 - 简化全栈开发流程"""
    # 存储全局选项供子命令使用
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["no_color"] = no_color
    ctx.obj["log_file"] = log_file
    ctx.obj["interactive"] = interactive
    ctx.obj["no_update_check"] = no_update_check

    # 配置日志级别
    if verbose > 0:
        if verbose == 1:
            init_logging(console_level="info")
            logger.info("启用信息级别日志")
        elif verbose == 2:
            init_logging(console_level="debug")
            logger.info("启用调试级别日志")
        else:  # verbose >= 3
            init_logging(console_level="debug")  # Python logging没有trace级别
            os.environ["SMOOTHSTACK_TRACE"] = "1"  # 设置环境变量表示trace级别
            logger.info("启用跟踪级别日志")
    elif quiet:
        init_logging(console_level="warning")

    # 禁用彩色输出
    if no_color:
        os.environ["NO_COLOR"] = "1"

    logger.debug(
        f"CLI启动，参数：verbose={verbose}, quiet={quiet}, no_color={no_color}, log_file={log_file}, "
        f"interactive={interactive}, no_update_check={no_update_check}"
    )

    # 自动检查更新（非静默模式），除非明确禁用
    if not no_update_check and not quiet:
        _auto_check_update()

    # 如果指定了交互式模式，启动交互式命令界面
    if interactive:
        from .interactive_cmd import InteractiveCommandRunner

        runner = InteractiveCommandRunner(cli)
        runner.run()
        ctx.exit()


def _auto_check_update():
    """自动检查更新（如果距离上次检查超过指定天数）"""
    try:
        from datetime import datetime, timedelta
        import json
        from pathlib import Path

        # 检查更新状态文件
        home_dir = Path.home()
        ss_dir = home_dir / ".smoothstack"
        ss_dir.mkdir(exist_ok=True)
        last_check_file = ss_dir / ".last_update_check"

        # 确定是否需要检查
        need_check = True
        if last_check_file.exists():
            try:
                data = json.loads(last_check_file.read_text(encoding="utf-8"))
                last_check = datetime.fromisoformat(data.get("timestamp", ""))
                if datetime.now() - last_check < timedelta(days=AUTO_CHECK_INTERVAL):
                    need_check = False
            except Exception as e:
                logger.debug(f"读取上次更新检查记录失败: {e}")

        # 执行检查
        if need_check:
            logger.debug("执行自动更新检查")
            has_update, _ = check_for_updates(show_current=False)

            # 更新检查时间
            last_check_file.write_text(
                json.dumps({"timestamp": datetime.now().isoformat()}), encoding="utf-8"
            )

            # 如果有更新，显示提示
            if has_update:
                console.print(
                    "\n[yellow]发现新版本可用！使用 'smoothstack version check' 查看详情。[/yellow]\n"
                )

    except Exception as e:
        # 自动更新检查失败不应影响正常使用
        logger.debug(f"自动更新检查失败: {e}")


@cli.command()
@click.argument("topic", required=False)
@click.pass_context
def help(ctx, topic: Optional[str] = None):
    """显示帮助信息"""
    logger.debug(f"执行帮助命令，主题：{topic}")
    help_command([topic] if topic else [])


@cli.command()
@click.argument("name", required=False)
@click.option("--template", "-t", default="basic", help="项目模板")
@click.option("--python-version", default="3.8", help="Python版本")
@click.option("--node-version", default="16", help="Node.js版本")
@click.option("--docker/--no-docker", default=False, help="是否添加Docker支持")
@click.option("--git/--no-git", default=True, help="是否初始化Git仓库")
@click.option("--force", "-f", is_flag=True, help="强制覆盖已存在的目录")
@click.pass_context
def init(
    ctx,
    name: Optional[str],
    template: str,
    python_version: str,
    node_version: str,
    docker: bool,
    git: bool,
    force: bool,
):
    """初始化新项目"""
    logger.debug(
        f"执行初始化命令，参数：name={name}, template={template}, python_version={python_version}, node_version={node_version}, docker={docker}, git={git}, force={force}"
    )
    # TODO: 实现项目初始化功能
    raise UserError("项目初始化功能尚未实现", "此功能将在后续版本中提供")


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "-l", is_flag=True, help="列出所有配置")
@click.option("--unset", "-u", is_flag=True, help="删除配置项")
@click.pass_context
def config(ctx, key: Optional[str], value: Optional[str], list: bool, unset: bool):
    """管理配置"""
    logger.debug(
        f"执行配置命令，参数：key={key}, value={value}, list={list}, unset={unset}"
    )
    # TODO: 实现配置管理功能
    raise ConfigError("配置管理功能尚未实现", "此功能将在后续版本中提供")


@cli.command()
@click.argument("command", required=True)
@click.option("--name", "-n", help="服务名称")
@click.option("--detach", "-d", is_flag=True, help="后台运行")
@click.pass_context
def service(ctx, command: str, name: Optional[str], detach: bool):
    """管理服务"""
    logger.debug(f"执行服务命令，参数：command={command}, name={name}, detach={detach}")
    # TODO: 实现服务管理功能
    console.print("[red]服务管理功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--watch", "-w", is_flag=True, help="监视模式")
@click.option("--coverage", "-c", is_flag=True, help="生成覆盖率报告")
@click.pass_context
def test(ctx, type: str, watch: bool, coverage: bool):
    """运行测试"""
    logger.debug(f"执行测试命令，参数：type={type}, watch={watch}, coverage={coverage}")
    # TODO: 实现测试功能
    console.print("[red]测试功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--fix", "-f", is_flag=True, help="自动修复问题")
@click.pass_context
def lint(ctx, type: str, fix: bool):
    """代码检查"""
    logger.debug(f"执行代码检查命令，参数：type={type}, fix={fix}")
    # TODO: 实现代码检查功能
    console.print("[red]代码检查功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--mode", default="development", help="构建模式")
@click.option("--output", "-o", help="输出目录")
@click.pass_context
def build(ctx, type: str, mode: str, output: Optional[str]):
    """构建项目"""
    logger.debug(f"执行构建命令，参数：type={type}, mode={mode}, output={output}")
    # TODO: 实现项目构建功能
    console.print("[red]项目构建功能尚未实现[/red]")


@cli.command()
@click.argument("type", type=click.Choice(["frontend", "backend", "all"]))
@click.option("--port", "-p", help="端口号")
@click.option("--host", "-h", help="主机地址")
@click.pass_context
def dev(ctx, type: str, port: Optional[str], host: Optional[str]):
    """启动开发服务器"""
    logger.debug(f"执行开发服务器命令，参数：type={type}, port={port}, host={host}")
    # TODO: 实现开发服务器功能
    console.print("[red]开发服务器功能尚未实现[/red]")


# 添加子命令
cli.add_command(completion)
cli.add_command(log)
cli.add_command(interactive)
cli.add_command(version)
cli.add_command(config)


@cli_error_handler
def main():
    """CLI工具入口函数"""
    logger.debug("CLI工具启动")
    cli()  # 使用装饰器处理异常


if __name__ == "__main__":
    main()
