#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
容器内依赖管理工具

该工具用于管理Docker容器内的依赖包，包括前端和后端依赖。
主要功能包括：
1. 管理前端容器内的npm/yarn依赖，支持package.json的管理
2. 管理后端容器内的pip依赖，支持requirements.txt的管理
3. 支持多环境（开发/测试/生产）配置
4. 提供Dockerfile模板管理
5. 支持依赖版本锁定和导出
"""

import os
import sys
import json
import click
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import tempfile
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime


# 项目路径和配置
PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
TEMPLATES_DIR = PROJECT_ROOT / "docker" / "templates"
FRONTEND_DOCKERFILE = PROJECT_ROOT / "docker" / "frontend" / "Dockerfile"
BACKEND_DOCKERFILE = PROJECT_ROOT / "docker" / "backend" / "Dockerfile"
FRONTEND_PACKAGE_JSON = FRONTEND_DIR / "package.json"
BACKEND_REQUIREMENTS = BACKEND_DIR / "requirements.txt"
FRONTEND_DEP_LOCK = FRONTEND_DIR / "docker-dep-lock.json"
BACKEND_DEP_LOCK = BACKEND_DIR / "docker-dep-lock.json"

# 确保目录存在
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)
os.makedirs(BACKEND_DIR, exist_ok=True)
os.makedirs(PROJECT_ROOT / "docker" / "frontend", exist_ok=True)
os.makedirs(PROJECT_ROOT / "docker" / "backend", exist_ok=True)

# 初始化Rich控制台
console = Console()


def log_info(message: str) -> None:
    """打印信息日志"""
    console.print(f"[blue]INFO:[/blue] {message}")


def log_success(message: str) -> None:
    """打印成功日志"""
    console.print(f"[green]SUCCESS:[/green] {message}")


def log_warning(message: str) -> None:
    """打印警告日志"""
    console.print(f"[yellow]WARNING:[/yellow] {message}")


def log_error(message: str) -> None:
    """打印错误日志"""
    console.print(f"[red]ERROR:[/red] {message}")


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """运行命令并获取输出"""
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return 1, "", str(e)


def check_dependency_conflicts(component: str) -> bool:
    """检查依赖冲突

    Args:
        component (str): 组件类型 (frontend 或 backend)

    Returns:
        bool: 操作是否成功
    """
    log_info(f"检查{component}依赖冲突...")

    if component == "frontend":
        # 检查前端依赖冲突
        if not os.path.exists(FRONTEND_PACKAGE_JSON):
            log_error("前端package.json不存在")
            return False

        try:
            with open(FRONTEND_PACKAGE_JSON, "r", encoding="utf-8") as f:
                package_data = json.load(f)

            # 创建临时目录检查依赖冲突
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_package_json = os.path.join(tmp_dir, "package.json")
                with open(tmp_package_json, "w", encoding="utf-8") as f:
                    json.dump(package_data, f)

                # 使用npm检查
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "node:16-alpine",
                    "sh",
                    "-c",
                    "cd /app && npm install --package-lock-only --dry-run",
                ]

                code, stdout, stderr = run_command(cmd)

                if code != 0:
                    log_error("检测到依赖冲突")
                    console.print(
                        Panel(stderr, title="依赖冲突详情", border_style="red")
                    )

                    # 提取冲突信息
                    conflicts = []
                    for line in stderr.splitlines():
                        if "ERESOLVE unable to resolve dependency tree" in line:
                            conflicts.append(line)

                    # 显示冲突表格
                    if conflicts:
                        table = Table(title="检测到的依赖冲突")
                        table.add_column("冲突描述", style="red")
                        for conflict in conflicts:
                            table.add_row(conflict)
                        console.print(table)

                    return False

                log_success("未检测到依赖冲突")
                return True
        except Exception as e:
            log_error(f"检查前端依赖冲突时出错: {e}")
            return False

    elif component == "backend":
        # 检查后端依赖冲突
        if not os.path.exists(BACKEND_REQUIREMENTS):
            log_error("后端requirements.txt不存在")
            return False

        try:
            # 创建临时目录检查依赖冲突
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_requirements = os.path.join(tmp_dir, "requirements.txt")
                shutil.copy(BACKEND_REQUIREMENTS, tmp_requirements)

                # 使用pip检查
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "python:3.9-slim",
                    "pip",
                    "check",
                    "-r",
                    "/app/requirements.txt",
                ]

                code, stdout, stderr = run_command(cmd)

                if code != 0 or "has requirement" in stdout:
                    log_error("检测到依赖冲突")
                    conflicts = []

                    # 解析冲突信息
                    for line in stdout.splitlines():
                        if "has requirement" in line or "is incompatible" in line:
                            conflicts.append(line)

                    # 显示冲突表格
                    table = Table(title="检测到的依赖冲突")
                    table.add_column("冲突描述", style="red")

                    if conflicts:
                        for conflict in conflicts:
                            table.add_row(conflict)
                        console.print(table)
                    else:
                        console.print(
                            Panel(stdout, title="依赖冲突详情", border_style="red")
                        )

                    return False

                log_success("未检测到依赖冲突")
                return True
        except Exception as e:
            log_error(f"检查后端依赖冲突时出错: {e}")
            return False

    else:
        log_error(f"不支持的组件类型: {component}")
        return False


def optimize_docker_layers(component: str, output_file: Optional[str] = None) -> bool:
    """优化Docker镜像层

    Args:
        component (str): 组件类型 (frontend 或 backend)
        output_file (Optional[str], optional): 输出的Dockerfile路径. Defaults to None.

    Returns:
        bool: 操作是否成功
    """
    log_info(f"优化{component} Docker镜像层...")

    if component == "frontend":
        dockerfile_path = FRONTEND_DOCKERFILE
        template_path = (
            PROJECT_ROOT / "docker" / "templates" / "frontend" / "vue-prod.dockerfile"
        )

        if not template_path.exists():
            log_error(f"模板文件不存在: {template_path}")
            return False
    elif component == "backend":
        dockerfile_path = BACKEND_DOCKERFILE
        template_path = (
            PROJECT_ROOT
            / "docker"
            / "templates"
            / "backend"
            / "fastapi-prod.dockerfile"
        )

        if not template_path.exists():
            log_error(f"模板文件不存在: {template_path}")
            return False
    else:
        log_error(f"不支持的组件类型: {component}")
        return False

    # 如果指定了输出文件，使用指定的路径
    if output_file:
        target_path = Path(output_file)
    else:
        target_path = dockerfile_path

    try:
        # 读取模板文件
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # 优化Docker层
        optimized_content = optimize_dockerfile_content(template_content, component)

        # 保存到目标路径
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(optimized_content)

        log_success(f"已优化并保存Dockerfile到 {target_path}")
        return True
    except Exception as e:
        log_error(f"优化Docker镜像层失败: {e}")
        return False


def optimize_dockerfile_content(content: str, component: str) -> str:
    """优化Dockerfile内容

    Args:
        content (str): 原始Dockerfile内容
        component (str): 组件类型 (frontend 或 backend)

    Returns:
        str: 优化后的Dockerfile内容
    """
    # 1. 合并RUN命令减少层数
    lines = content.splitlines()
    optimized_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 处理连续的RUN命令
        if line.startswith("RUN"):
            run_commands = [line[4:].strip()]
            j = i + 1

            # 查找连续的RUN命令
            while j < len(lines) and lines[j].strip().startswith("RUN"):
                run_commands.append(lines[j].strip()[4:].strip())
                j += 1

            # 如果有多个连续的RUN，合并它们
            if len(run_commands) > 1:
                merged_run = "RUN " + " && \\\n    ".join(run_commands)
                optimized_lines.append(merged_run)
                i = j
            else:
                optimized_lines.append(line)
                i += 1
        else:
            optimized_lines.append(line)
            i += 1

    # 2. 添加.dockerignore建议
    dockerignore_suggestion = """
# 推荐的.dockerignore配置:
# .git
# node_modules
# npm-debug.log
# Dockerfile
# .dockerignore
# .env
# .env.*
# *.md
# .vscode
# .idea
"""

    # 3. 针对不同组件添加特定优化
    if component == "frontend":
        # 前端特定优化
        optimized_content = "\n".join(optimized_lines)
        # 确保使用缓存优化
        if "npm ci" in optimized_content and "--cache-folder" not in optimized_content:
            optimized_content = optimized_content.replace(
                "npm ci", "npm ci --cache /npm-cache"
            )
        # 添加缓存清理
        if (
            "npm ci" in optimized_content
            and "rm -rf /root/.npm" not in optimized_content
        ):
            optimized_content = optimized_content.replace(
                "npm ci", "npm ci && rm -rf /root/.npm"
            )
    else:
        # 后端特定优化
        optimized_content = "\n".join(optimized_lines)
        # 添加pip缓存清理
        if (
            "pip install" in optimized_content
            and "rm -rf /root/.cache/pip" not in optimized_content
        ):
            optimized_content = optimized_content.replace(
                "pip install", "pip install --no-cache-dir"
            )
        # 确保使用最小基础镜像
        if "python:3.9" in optimized_content and "slim" not in optimized_content:
            optimized_content = optimized_content.replace(
                "python:3.9", "python:3.9-slim"
            )

    # 添加注释说明优化内容
    header_comment = """# 优化的Dockerfile
# 已应用以下优化:
# 1. 合并RUN命令减少层数
# 2. 优化缓存使用
# 3. 清理构建缓存
# 4. 使用最小基础镜像
"""

    return header_comment + optimized_content + dockerignore_suggestion


def ensure_docker_running() -> bool:
    """确保Docker正在运行"""
    code, _, _ = run_command(["docker", "info"])
    if code != 0:
        log_error("Docker 未运行或未正确安装。请确保 Docker 正在运行。")
        return False
    return True


def check_security_vulnerabilities(component: str) -> bool:
    """检查依赖安全漏洞

    Args:
        component (str): 组件类型 (frontend 或 backend)

    Returns:
        bool: 操作是否成功
    """
    log_info(f"检查{component}依赖安全漏洞...")

    if component == "frontend":
        # 检查前端依赖安全漏洞
        if not os.path.exists(FRONTEND_PACKAGE_JSON):
            log_error("前端package.json不存在")
            return False

        try:
            # 创建临时目录检查安全漏洞
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_package_json = os.path.join(tmp_dir, "package.json")
                shutil.copy(FRONTEND_PACKAGE_JSON, tmp_package_json)

                # 使用npm audit检查
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "node:16-alpine",
                    "sh",
                    "-c",
                    "cd /app && npm audit --json",
                ]

                code, stdout, stderr = run_command(cmd)

                if stdout.strip():
                    try:
                        audit_result = json.loads(stdout)

                        # 提取漏洞信息
                        vulnerabilities = audit_result.get("vulnerabilities", {})
                        metadata = audit_result.get("metadata", {})

                        total_count = metadata.get("vulnerabilities", {}).get(
                            "total", 0
                        )

                        if total_count > 0:
                            log_warning(f"检测到 {total_count} 个安全漏洞")

                            # 创建漏洞表格
                            table = Table(title="前端依赖安全漏洞")
                            table.add_column("依赖包", style="cyan")
                            table.add_column("漏洞级别", style="red")
                            table.add_column("漏洞数量", style="yellow")
                            table.add_column("修复建议", style="green")

                            for pkg_name, pkg_info in vulnerabilities.items():
                                severity = pkg_info.get("severity", "unknown")
                                count = 1  # 默认为1个漏洞

                                # 提取修复建议
                                via = pkg_info.get("via", [])
                                if isinstance(via, list) and len(via) > 0:
                                    count = len(via)

                                fix = pkg_info.get("fixAvailable", False)
                                if fix is True:
                                    fix_str = "可用更新修复"
                                elif isinstance(fix, dict):
                                    fix_str = f"更新到 {fix.get('name')}@{fix.get('version', '最新版')}"
                                else:
                                    fix_str = "无可用修复"

                                table.add_row(pkg_name, severity, str(count), fix_str)

                            console.print(table)

                            # 显示漏洞概要
                            summary = metadata.get("vulnerabilities", {})
                            summary_table = Table(title="漏洞级别统计")
                            summary_table.add_column("级别", style="cyan")
                            summary_table.add_column("数量", style="yellow")

                            for level, count in summary.items():
                                if level != "total" and count > 0:
                                    summary_table.add_row(level, str(count))

                            console.print(summary_table)

                            # 提供修复建议
                            if (
                                audit_result.get("audit", {}).get(
                                    "auditReportVersion", 0
                                )
                                > 0
                            ):
                                log_info("修复建议：")
                                console.print(
                                    "[green]运行 npm audit fix 可修复部分漏洞[/]"
                                )
                                console.print(
                                    "[green]运行 npm audit fix --force 可修复大部分漏洞（可能会破坏兼容性）[/]"
                                )

                            return True
                        else:
                            log_success("未检测到安全漏洞")
                            return True
                    except json.JSONDecodeError:
                        if "found 0 vulnerabilities" in stdout:
                            log_success("未检测到安全漏洞")
                            return True
                        else:
                            log_error(f"解析npm audit结果失败")
                            console.print(
                                Panel(stdout, title="npm audit输出", border_style="red")
                            )
                            return False
                else:
                    log_success("未检测到安全漏洞")
                    return True
        except Exception as e:
            log_error(f"检查前端依赖安全漏洞时出错: {e}")
            return False

    elif component == "backend":
        # 检查后端依赖安全漏洞
        if not os.path.exists(BACKEND_REQUIREMENTS):
            log_error("后端requirements.txt不存在")
            return False

        try:
            # 创建临时目录检查安全漏洞
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_requirements = os.path.join(tmp_dir, "requirements.txt")
                shutil.copy(BACKEND_REQUIREMENTS, tmp_requirements)

                # 使用safety检查
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "python:3.9-slim",
                    "sh",
                    "-c",
                    "pip install safety && safety check -r /app/requirements.txt --json",
                ]

                code, stdout, stderr = run_command(cmd)

                if stdout.strip():
                    try:
                        # safety输出的JSON
                        safety_result = json.loads(stdout)

                        vulnerabilities = safety_result.get("vulnerabilities", [])
                        if vulnerabilities:
                            log_warning(f"检测到 {len(vulnerabilities)} 个安全漏洞")

                            # 创建漏洞表格
                            table = Table(title="后端依赖安全漏洞")
                            table.add_column("依赖包", style="cyan")
                            table.add_column("已安装版本", style="yellow")
                            table.add_column("漏洞ID", style="red")
                            table.add_column("修复版本", style="green")

                            for vuln in vulnerabilities:
                                pkg_name = vuln.get("package_name", "unknown")
                                installed_version = vuln.get(
                                    "installed_version", "unknown"
                                )
                                vulnerability_id = vuln.get(
                                    "vulnerability_id", "unknown"
                                )

                                # 提取修复建议
                                fixed_versions = vuln.get("fixed_versions", [])
                                fix_str = (
                                    ", ".join(fixed_versions)
                                    if fixed_versions
                                    else "无可用修复"
                                )

                                table.add_row(
                                    pkg_name,
                                    installed_version,
                                    vulnerability_id,
                                    fix_str,
                                )

                            console.print(table)

                            # 提供修复建议
                            log_info("修复建议：")
                            console.print(
                                "[green]更新受影响的包到最新版本，或指定安全版本[/]"
                            )
                            console.print(
                                "[green]运行 pip install --upgrade <package> 更新特定包[/]"
                            )

                            return True
                        else:
                            log_success("未检测到安全漏洞")
                            return True
                    except json.JSONDecodeError:
                        log_error(f"解析safety检查结果失败")
                        console.print(
                            Panel(stdout, title="safety输出", border_style="red")
                        )
                        return False
                else:
                    log_success("未检测到安全漏洞")
                    return True
        except Exception as e:
            log_error(f"检查后端依赖安全漏洞时出错: {e}")
            return False

    else:
        log_error(f"不支持的组件类型: {component}")
        return False


class ContainerDependencyManager:
    """容器内依赖管理类"""

    def __init__(self):
        """初始化容器依赖管理器"""
        self.project_root = self._get_project_root()
        self.frontend_root = os.path.join(self.project_root, "frontend")
        self.backend_root = os.path.join(self.project_root, "backend")
        self.docker_dir = os.path.join(self.project_root, "docker")
        self.templates_dir = os.path.join(self.docker_dir, "templates")
        self.logs_dir = os.path.join(self.project_root, "logs")

        # 确保目录存在
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def _get_project_root(self) -> str:
        """获取项目根目录"""
        # 尝试查找包含start.sh的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir != os.path.dirname(current_dir):  # 不是根目录
            if os.path.exists(os.path.join(current_dir, "start.sh")):
                return current_dir
            current_dir = os.path.dirname(current_dir)

        # 如果找不到，就使用当前工作目录
        return os.getcwd()

    def run_docker_command(
        self, cmd: List[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """运行Docker命令"""
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=check,
            )
            return result
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Docker命令执行失败: {e}[/]")
            console.print(f"[red]错误输出: {e.stderr}[/]")
            raise

    def get_container_id(self, name: str) -> Optional[str]:
        """获取容器ID"""
        result = self.run_docker_command(
            ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.ID}}"],
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None

    def container_is_running(self, name: str) -> bool:
        """检查容器是否运行中"""
        result = self.run_docker_command(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.ID}}"],
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())

    def ensure_container_running(self, name: str) -> bool:
        """确保容器在运行状态"""
        if self.container_is_running(name):
            return True

        # 尝试启动容器
        container_id = self.get_container_id(name)
        if container_id:
            console.print(f"[yellow]容器 {name} 未运行，尝试启动...[/]")
            result = self.run_docker_command(
                ["docker", "start", container_id], check=False
            )
            if result.returncode == 0:
                console.print(f"[green]容器 {name} 已启动[/]")
                return True
            else:
                console.print(f"[red]启动容器 {name} 失败: {result.stderr}[/]")
                return False
        else:
            console.print(f"[red]容器 {name} 不存在，无法启动[/]")
            return False

    def exec_in_container(
        self, container_name: str, cmd: List[str]
    ) -> subprocess.CompletedProcess:
        """在容器内执行命令"""
        if not self.ensure_container_running(container_name):
            raise RuntimeError(f"容器 {container_name} 不在运行状态")

        docker_cmd = ["docker", "exec", container_name] + cmd
        return self.run_docker_command(docker_cmd)

    def copy_to_container(self, container_name: str, src: str, dest: str) -> bool:
        """拷贝文件到容器"""
        if not os.path.exists(src):
            console.print(f"[red]源文件不存在: {src}[/]")
            return False

        cmd = ["docker", "cp", src, f"{container_name}:{dest}"]
        result = self.run_docker_command(cmd, check=False)
        return result.returncode == 0

    def copy_from_container(self, container_name: str, src: str, dest: str) -> bool:
        """从容器拷贝文件"""
        cmd = ["docker", "cp", f"{container_name}:{src}", dest]
        result = self.run_docker_command(cmd, check=False)
        return result.returncode == 0


# === 前端依赖管理 ===
class FrontendDependencyManager(ContainerDependencyManager):
    """前端容器依赖管理"""

    def __init__(self):
        """初始化前端依赖管理器"""
        super().__init__()
        self.frontend_container = "smoothstack_frontend"
        self.package_json_path = os.path.join(self.frontend_root, "package.json")
        self.package_lock_path = os.path.join(self.frontend_root, "package-lock.json")
        self.yarn_lock_path = os.path.join(self.frontend_root, "yarn.lock")

    def get_package_json(self) -> Dict:
        """获取package.json内容"""
        if not os.path.exists(self.package_json_path):
            return {
                "name": "smoothstack-frontend",
                "version": "1.0.0",
                "dependencies": {},
                "devDependencies": {},
            }

        with open(self.package_json_path, "r") as f:
            return json.load(f)

    def save_package_json(self, data: Dict) -> bool:
        """保存package.json"""
        try:
            with open(self.package_json_path, "w") as f:
                json.dump(data, indent=2, sort_keys=True, ensure_ascii=False, fp=f)
            return True
        except Exception as e:
            console.print(f"[red]保存package.json失败: {e}[/]")
            return False

    def add_dependency(
        self,
        package_name: str,
        version: Optional[str] = None,
        dev: bool = False,
        env: str = "dev",
    ) -> bool:
        """添加前端依赖"""
        console.print(
            f"[bold blue]添加{'开发' if dev else ''}依赖: {package_name} {version or ''}[/]"
        )

        # 确保前端容器在运行中
        if not self.ensure_container_running(self.frontend_container):
            console.print("[red]前端容器未运行，无法添加依赖[/]")
            return False

        # 构建npm/yarn命令
        package_spec = package_name
        if version:
            package_spec = f"{package_name}@{version}"

        cmd_type = "add" if self._using_yarn() else "install"
        cmd = ["yarn", cmd_type] if self._using_yarn() else ["npm", cmd_type]

        if dev:
            cmd.append("--dev")

        cmd.append(package_spec)

        # 在容器内执行
        try:
            result = self.exec_in_container(self.frontend_container, cmd)
            console.print(f"[green]成功添加依赖 {package_spec}[/]")

            # 更新本地package.json和lock文件
            self._sync_package_files_from_container()
            return True
        except Exception as e:
            console.print(f"[red]添加依赖失败: {e}[/]")
            return False

    def remove_dependency(self, package_name: str, dev: bool = False) -> bool:
        """移除前端依赖"""
        console.print(f"[bold blue]移除{'开发' if dev else ''}依赖: {package_name}[/]")

        # 确保前端容器在运行中
        if not self.ensure_container_running(self.frontend_container):
            console.print("[red]前端容器未运行，无法移除依赖[/]")
            return False

        # 构建npm/yarn命令
        cmd_type = "remove" if self._using_yarn() else "uninstall"
        cmd = ["yarn", cmd_type] if self._using_yarn() else ["npm", cmd_type]
        cmd.append(package_name)

        # 在容器内执行
        try:
            result = self.exec_in_container(self.frontend_container, cmd)
            console.print(f"[green]成功移除依赖 {package_name}[/]")

            # 更新本地package.json和lock文件
            self._sync_package_files_from_container()
            return True
        except Exception as e:
            console.print(f"[red]移除依赖失败: {e}[/]")
            return False

    def list_dependencies(self, dev: bool = False) -> bool:
        """列出前端依赖"""
        package_data = self.get_package_json()

        deps_key = "devDependencies" if dev else "dependencies"
        deps = package_data.get(deps_key, {})

        if not deps:
            console.print(f"[yellow]没有找到{'开发' if dev else ''}依赖[/]")
            return True

        # 使用Rich创建表格
        table = Table(title=f"{'开发' if dev else ''}依赖列表")
        table.add_column("包名", style="cyan")
        table.add_column("版本", style="green")

        for pkg, version in sorted(deps.items()):
            table.add_row(pkg, version)

        console.print(table)
        return True

    def update_dependencies(self, package_name: Optional[str] = None) -> bool:
        """更新前端依赖"""
        console.print(f"[bold blue]更新依赖: {package_name or '所有'}[/]")

        # 确保前端容器在运行中
        if not self.ensure_container_running(self.frontend_container):
            console.print("[red]前端容器未运行，无法更新依赖[/]")
            return False

        # 构建npm/yarn命令
        if self._using_yarn():
            cmd = ["yarn", "upgrade"]
            if package_name:
                cmd.append(package_name)
        else:
            cmd = ["npm", "update"]
            if package_name:
                cmd.append(package_name)

        # 在容器内执行
        try:
            result = self.exec_in_container(self.frontend_container, cmd)
            console.print(f"[green]成功更新依赖 {package_name or '所有'}[/]")

            # 更新本地package.json和lock文件
            self._sync_package_files_from_container()
            return True
        except Exception as e:
            console.print(f"[red]更新依赖失败: {e}[/]")
            return False

    def _using_yarn(self) -> bool:
        """检查是否使用yarn"""
        return os.path.exists(self.yarn_lock_path)

    def _sync_package_files_from_container(self) -> bool:
        """从容器同步package文件到本地"""
        # 同步package.json
        tmp_dir = tempfile.mkdtemp()
        try:
            # 从容器复制文件
            files_to_copy = [("/app/package.json", self.package_json_path)]

            # 根据使用的包管理器添加lock文件
            if self._using_yarn():
                files_to_copy.append(("/app/yarn.lock", self.yarn_lock_path))
            else:
                files_to_copy.append(("/app/package-lock.json", self.package_lock_path))

            for container_path, local_path in files_to_copy:
                tmp_path = os.path.join(tmp_dir, os.path.basename(container_path))
                if self.copy_from_container(
                    self.frontend_container, container_path, tmp_path
                ):
                    shutil.copy2(tmp_path, local_path)
                    console.print(f"[green]已同步 {os.path.basename(local_path)}[/]")
                else:
                    console.print(
                        f"[yellow]无法从容器同步 {os.path.basename(local_path)}[/]"
                    )

            return True
        finally:
            shutil.rmtree(tmp_dir)


# === 后端依赖管理 ===
class BackendDependencyManager(ContainerDependencyManager):
    """后端容器依赖管理"""

    def __init__(self):
        """初始化后端依赖管理器"""
        super().__init__()
        self.backend_container = "smoothstack_backend"
        self.requirements_path = os.path.join(self.backend_root, "requirements.txt")
        self.pip_conf_path = os.path.join(self.backend_root, "pip.conf")

    def get_requirements(self) -> List[str]:
        """获取requirements.txt内容"""
        if not os.path.exists(self.requirements_path):
            return []

        with open(self.requirements_path, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

    def save_requirements(self, requirements: List[str]) -> bool:
        """保存requirements.txt"""
        try:
            with open(self.requirements_path, "w") as f:
                for req in requirements:
                    f.write(f"{req}\n")
            return True
        except Exception as e:
            console.print(f"[red]保存requirements.txt失败: {e}[/]")
            return False

    def add_dependency(
        self, package_name: str, version: Optional[str] = None, env: str = "dev"
    ) -> bool:
        """添加后端依赖"""
        console.print(f"[bold blue]添加依赖: {package_name} {version or ''}[/]")

        # 确保后端容器在运行中
        if not self.ensure_container_running(self.backend_container):
            console.print("[red]后端容器未运行，无法添加依赖[/]")
            return False

        # 构建pip命令
        package_spec = package_name
        if version:
            package_spec = f"{package_name}=={version}"

        cmd = ["pip", "install", package_spec]

        # 在容器内执行
        try:
            result = self.exec_in_container(self.backend_container, cmd)
            console.print(f"[green]成功添加依赖 {package_spec}[/]")

            # 更新requirements.txt
            self._generate_requirements_from_container()
            return True
        except Exception as e:
            console.print(f"[red]添加依赖失败: {e}[/]")
            return False

    def remove_dependency(self, package_name: str) -> bool:
        """移除后端依赖"""
        console.print(f"[bold blue]移除依赖: {package_name}[/]")

        # 确保后端容器在运行中
        if not self.ensure_container_running(self.backend_container):
            console.print("[red]后端容器未运行，无法移除依赖[/]")
            return False

        # 构建pip命令
        cmd = ["pip", "uninstall", "-y", package_name]

        # 在容器内执行
        try:
            result = self.exec_in_container(self.backend_container, cmd)
            console.print(f"[green]成功移除依赖 {package_name}[/]")

            # 更新requirements.txt
            self._generate_requirements_from_container()
            return True
        except Exception as e:
            console.print(f"[red]移除依赖失败: {e}[/]")
            return False

    def list_dependencies(self) -> bool:
        """列出后端依赖"""
        # 确保后端容器在运行中
        if not self.ensure_container_running(self.backend_container):
            console.print("[red]后端容器未运行，无法列出依赖[/]")
            return False

        # 构建pip list命令
        cmd = ["pip", "list", "--format=json"]

        # 在容器内执行
        try:
            result = self.exec_in_container(self.backend_container, cmd)
            packages = json.loads(result.stdout)

            # 使用Rich创建表格
            table = Table(title="后端依赖列表")
            table.add_column("包名", style="cyan")
            table.add_column("版本", style="green")

            for pkg in sorted(packages, key=lambda x: x["name"].lower()):
                table.add_row(pkg["name"], pkg["version"])

            console.print(table)
            return True
        except Exception as e:
            console.print(f"[red]列出依赖失败: {e}[/]")
            return False

    def update_dependencies(self, package_name: Optional[str] = None) -> bool:
        """更新后端依赖"""
        console.print(f"[bold blue]更新依赖: {package_name or '所有'}[/]")

        # 确保后端容器在运行中
        if not self.ensure_container_running(self.backend_container):
            console.print("[red]后端容器未运行，无法更新依赖[/]")
            return False

        # 构建pip命令
        cmd = ["pip", "install", "--upgrade"]
        if package_name:
            cmd.append(package_name)
        else:
            # 如果更新所有，需要使用requirements.txt
            self._sync_requirements_to_container()
            cmd.extend(["-r", "/app/requirements.txt"])

        # 在容器内执行
        try:
            result = self.exec_in_container(self.backend_container, cmd)
            console.print(f"[green]成功更新依赖 {package_name or '所有'}[/]")

            # 更新requirements.txt
            self._generate_requirements_from_container()
            return True
        except Exception as e:
            console.print(f"[red]更新依赖失败: {e}[/]")
            return False

    def _generate_requirements_from_container(self) -> bool:
        """从容器生成requirements.txt"""
        # 确保后端容器在运行中
        if not self.ensure_container_running(self.backend_container):
            console.print("[red]后端容器未运行，无法生成requirements.txt[/]")
            return False

        # 在容器内运行pip freeze
        try:
            result = self.exec_in_container(self.backend_container, ["pip", "freeze"])

            # 保存到本地requirements.txt
            with open(self.requirements_path, "w") as f:
                f.write(result.stdout)

            console.print(f"[green]成功更新 requirements.txt[/]")
            return True
        except Exception as e:
            console.print(f"[red]生成requirements.txt失败: {e}[/]")
            return False

    def _sync_requirements_to_container(self) -> bool:
        """同步requirements.txt到容器"""
        if not os.path.exists(self.requirements_path):
            console.print("[yellow]requirements.txt不存在，无法同步到容器[/]")
            return False

        # 确保后端容器在运行中
        if not self.ensure_container_running(self.backend_container):
            console.print("[red]后端容器未运行，无法同步requirements.txt[/]")
            return False

        # 复制到容器
        return self.copy_to_container(
            self.backend_container, self.requirements_path, "/app/requirements.txt"
        )


# === Dockerfile模板管理 ===
class DockerfileTemplateManager(ContainerDependencyManager):
    """Dockerfile模板管理类"""

    def __init__(self):
        """初始化Dockerfile模板管理器"""
        super().__init__()
        self.templates_frontend_dir = os.path.join(self.templates_dir, "frontend")
        self.templates_backend_dir = os.path.join(self.templates_dir, "backend")

        # 确保目录存在
        os.makedirs(self.templates_frontend_dir, exist_ok=True)
        os.makedirs(self.templates_backend_dir, exist_ok=True)

        # 初始化默认模板
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        # 前端开发模板
        frontend_dev_path = os.path.join(self.templates_frontend_dir, "dev.Dockerfile")
        if not os.path.exists(frontend_dev_path):
            with open(frontend_dev_path, "w") as f:
                f.write(
                    """FROM node:18-alpine

WORKDIR /app

# 安装依赖
COPY package.json package-lock.json* yarn.lock* ./
RUN npm install || yarn install

# 复制源码
COPY . .

# 启动开发服务器
CMD ["npm", "run", "dev"]
"""
                )

        # 前端生产模板
        frontend_prod_path = os.path.join(
            self.templates_frontend_dir, "prod.Dockerfile"
        )
        if not os.path.exists(frontend_prod_path):
            with open(frontend_prod_path, "w") as f:
                f.write(
                    """FROM node:18-alpine as build

WORKDIR /app

# 安装依赖
COPY package.json package-lock.json* yarn.lock* ./
RUN npm ci || yarn install --frozen-lockfile

# 复制源码
COPY . .

# 构建应用
RUN npm run build

# 生产环境
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
                )

        # 后端开发模板
        backend_dev_path = os.path.join(self.templates_backend_dir, "dev.Dockerfile")
        if not os.path.exists(backend_dev_path):
            with open(backend_dev_path, "w") as f:
                f.write(
                    """FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制源码
COPY . .

# 启动开发服务器
CMD ["python", "main.py"]
"""
                )

        # 后端生产模板
        backend_prod_path = os.path.join(self.templates_backend_dir, "prod.Dockerfile")
        if not os.path.exists(backend_prod_path):
            with open(backend_prod_path, "w") as f:
                f.write(
                    """FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

# 启动生产服务器
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
"""
                )

    def list_templates(self, component: str) -> bool:
        """列出可用的模板"""
        if component not in ["frontend", "backend"]:
            console.print("[red]组件类型必须是 'frontend' 或 'backend'[/]")
            return False

        templates_dir = (
            self.templates_frontend_dir
            if component == "frontend"
            else self.templates_backend_dir
        )
        template_files = [
            f for f in os.listdir(templates_dir) if f.endswith(".Dockerfile")
        ]

        if not template_files:
            console.print(f"[yellow]没有找到 {component} 模板[/]")
            return True

        console.print(f"[bold blue]{component} Dockerfile模板:[/]")
        for template in sorted(template_files):
            template_name = template.replace(".Dockerfile", "")
            console.print(f"  [cyan]{template_name}[/]")

        return True

    def view_template(self, component: str, template_name: str) -> bool:
        """查看模板内容"""
        if component not in ["frontend", "backend"]:
            console.print("[red]组件类型必须是 'frontend' 或 'backend'[/]")
            return False

        templates_dir = (
            self.templates_frontend_dir
            if component == "frontend"
            else self.templates_backend_dir
        )
        template_path = os.path.join(templates_dir, f"{template_name}.Dockerfile")

        if not os.path.exists(template_path):
            console.print(f"[red]模板 {template_name} 不存在[/]")
            return False

        with open(template_path, "r") as f:
            content = f.read()

        console.print(f"[bold blue]{component}/{template_name}.Dockerfile:[/]")
        console.print(Panel(content, title=f"{component}/{template_name}.Dockerfile"))
        return True

    def create_template(
        self, component: str, template_name: str, content: Optional[str] = None
    ) -> bool:
        """创建新模板"""
        if component not in ["frontend", "backend"]:
            console.print("[red]组件类型必须是 'frontend' 或 'backend'[/]")
            return False

        templates_dir = (
            self.templates_frontend_dir
            if component == "frontend"
            else self.templates_backend_dir
        )
        template_path = os.path.join(templates_dir, f"{template_name}.Dockerfile")

        if os.path.exists(template_path) and not click.confirm(
            f"模板 {template_name} 已存在，是否覆盖?"
        ):
            return False

        if content is None:
            # 交互式编辑内容
            if os.path.exists(template_path):
                with open(template_path, "r") as f:
                    default_content = f.read()
            else:
                # 使用基础模板作为默认内容
                base_template = "dev" if "dev" in template_name.lower() else "prod"
                base_path = os.path.join(templates_dir, f"{base_template}.Dockerfile")
                if os.path.exists(base_path):
                    with open(base_path, "r") as f:
                        default_content = f.read()
                else:
                    default_content = f"""FROM {'node:18-alpine' if component == 'frontend' else 'python:3.9-slim'}

WORKDIR /app

# 这是一个自定义模板
# 请根据需要修改

"""

            # 使用默认编辑器打开临时文件进行编辑
            with tempfile.NamedTemporaryFile(
                suffix=".Dockerfile", mode="w+", delete=False
            ) as tmp:
                tmp.write(default_content)
                tmp_path = tmp.name

            try:
                # 打开编辑器
                editor = os.environ.get(
                    "EDITOR", "vim" if not os.name == "nt" else "notepad"
                )
                subprocess.run([editor, tmp_path], check=False)

                # 读取编辑后的内容
                with open(tmp_path, "r") as f:
                    content = f.read()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # 保存模板
        with open(template_path, "w") as f:
            f.write(content)

        console.print(f"[green]模板 {component}/{template_name}.Dockerfile 已保存[/]")
        return True


# === CLI命令 ===
@click.group()
def cli():
    """容器内依赖管理工具"""
    pass


# 前端依赖命令组
@cli.group("frontend")
def frontend_group():
    """管理前端容器内依赖"""
    pass


@frontend_group.command("add")
@click.argument("package_name", required=True)
@click.option("--version", "-v", help="依赖版本")
@click.option("--dev", "-d", is_flag=True, help="作为开发依赖安装")
@click.option("--env", "-e", default="dev", help="目标环境 (dev/prod)")
def frontend_add(package_name, version, dev, env):
    """添加前端依赖包"""
    manager = FrontendDependencyManager()
    manager.add_dependency(package_name, version, dev, env)


@frontend_group.command("remove")
@click.argument("package_name", required=True)
@click.option("--dev", "-d", is_flag=True, help="从开发依赖移除")
def frontend_remove(package_name, dev):
    """移除前端依赖包"""
    manager = FrontendDependencyManager()
    manager.remove_dependency(package_name, dev)


@frontend_group.command("list")
@click.option("--dev", "-d", is_flag=True, help="列出开发依赖")
def frontend_list(dev):
    """列出前端依赖包"""
    manager = FrontendDependencyManager()
    manager.list_dependencies(dev)


@frontend_group.command("update")
@click.argument("package_name", required=False)
def frontend_update(package_name):
    """更新前端依赖包"""
    manager = FrontendDependencyManager()
    manager.update_dependencies(package_name)


# 后端依赖命令组
@cli.group("backend")
def backend_group():
    """管理后端容器内依赖"""
    pass


@backend_group.command("add")
@click.argument("package_name", required=True)
@click.option("--version", "-v", help="依赖版本")
@click.option("--env", "-e", default="dev", help="目标环境 (dev/prod)")
def backend_add(package_name, version, env):
    """添加后端依赖包"""
    manager = BackendDependencyManager()
    manager.add_dependency(package_name, version, env)


@backend_group.command("remove")
@click.argument("package_name", required=True)
def backend_remove(package_name):
    """移除后端依赖包"""
    manager = BackendDependencyManager()
    manager.remove_dependency(package_name)


@backend_group.command("list")
def backend_list():
    """列出后端依赖包"""
    manager = BackendDependencyManager()
    manager.list_dependencies()


@backend_group.command("update")
@click.argument("package_name", required=False)
def backend_update(package_name):
    """更新后端依赖包"""
    manager = BackendDependencyManager()
    manager.update_dependencies(package_name)


# Dockerfile模板命令组
@cli.group("template")
def template_group():
    """管理Dockerfile模板"""
    pass


@template_group.command("list")
@click.argument(
    "type", type=click.Choice(["frontend", "backend", "all"]), default="all"
)
def template_list(type):
    """列出可用的Dockerfile模板"""
    templates = []

    # 使用之前定义的模板目录
    frontend_dir = Path(TEMPLATES_DIR) / "frontend"
    backend_dir = Path(TEMPLATES_DIR) / "backend"
    os.makedirs(frontend_dir, exist_ok=True)
    os.makedirs(backend_dir, exist_ok=True)

    if type in ["frontend", "all"]:
        for file in frontend_dir.glob("*.dockerfile"):
            templates.append(("frontend", file.name))

    if type in ["backend", "all"]:
        for file in backend_dir.glob("*.dockerfile"):
            templates.append(("backend", file.name))

    table = Table(title="Dockerfile模板列表")
    table.add_column("类型", style="cyan")
    table.add_column("模板名称", style="green")

    for template_type, template_name in templates:
        table.add_row(template_type, template_name)

    if not templates:
        log_warning(f"没有找到{type}类型的模板")
    else:
        console.print(table)


@template_group.command("view")
@click.argument("component", type=click.Choice(["frontend", "backend"]), required=True)
@click.argument("template_name", required=True)
def template_view(component, template_name):
    """查看Dockerfile模板内容"""
    manager = DockerfileTemplateManager()
    manager.view_template(component, template_name)


@template_group.command("create")
@click.argument("component", type=click.Choice(["frontend", "backend"]), required=True)
@click.argument("template_name", required=True)
def template_create(component, template_name):
    """创建新的Dockerfile模板"""
    manager = DockerfileTemplateManager()
    manager.create_template(component, template_name)


@cli.group()
def conflicts():
    """依赖冲突检测"""
    pass


@conflicts.command("check")
@click.argument("component", type=click.Choice(["frontend", "backend"]))
def conflicts_check(component):
    """检查组件依赖冲突"""
    check_dependency_conflicts(component)


@cli.group()
def optimize():
    """镜像层优化"""
    pass


@optimize.command("dockerfile")
@click.argument("component", type=click.Choice(["frontend", "backend"]))
@click.option("--output", "-o", help="输出的Dockerfile路径")
def optimize_dockerfile(component, output):
    """优化Dockerfile减少层数"""
    optimize_docker_layers(component, output)


@cli.group()
def security():
    """依赖安全漏洞检测"""
    pass


@security.command("check")
@click.argument("component", type=click.Choice(["frontend", "backend", "all"]))
def check_deps_security(component: str):
    """检查依赖的安全漏洞"""
    if not ensure_docker_running():
        return

    if component == "all":
        # 检查前端和后端
        frontend_result = check_security_vulnerabilities("frontend")
        backend_result = check_security_vulnerabilities("backend")

        if frontend_result and backend_result:
            log_success("依赖安全检查完成")
        else:
            log_error("依赖安全检查未完全成功")
    else:
        # 检查特定组件
        if check_security_vulnerabilities(component):
            log_success(f"{component}依赖安全检查完成")
        else:
            log_error(f"{component}依赖安全检查失败")


@cli.command("visualize")
@click.argument("component", type=click.Choice(["frontend", "backend"]))
@click.option("--output", "-o", default="dependency_graph.png", help="输出图表文件路径")
def visualize_deps(component: str, output: str):
    """可视化依赖关系图"""
    if not ensure_docker_running():
        return

    log_info(f"生成{component}依赖关系图...")

    try:
        if component == "frontend":
            # 检查package.json是否存在
            if not os.path.exists(FRONTEND_PACKAGE_JSON):
                log_error("前端package.json不存在")
                return

            # 创建临时目录生成依赖图
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_package_json = os.path.join(tmp_dir, "package.json")
                shutil.copy(FRONTEND_PACKAGE_JSON, tmp_package_json)

                # 如果存在package-lock.json，也复制它
                if os.path.exists(
                    os.path.join(
                        os.path.dirname(FRONTEND_PACKAGE_JSON), "package-lock.json"
                    )
                ):
                    shutil.copy(
                        os.path.join(
                            os.path.dirname(FRONTEND_PACKAGE_JSON), "package-lock.json"
                        ),
                        os.path.join(tmp_dir, "package-lock.json"),
                    )

                # 使用dependency-cruiser生成依赖图
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "node:16-alpine",
                    "sh",
                    "-c",
                    "cd /app && npm install dependency-cruiser --no-save && npx depcruise --include-only '^dependencies$' --output-type dot package.json | dot -Tpng -o /app/deps-graph.png",
                ]

                code, stdout, stderr = run_command(cmd)

                if code == 0:
                    # 将生成的图表复制到输出路径
                    graph_file = os.path.join(tmp_dir, "deps-graph.png")
                    if os.path.exists(graph_file):
                        shutil.copy(graph_file, output)
                        log_success(f"依赖关系图已生成: {output}")

                        # 尝试打开图像文件
                        try:
                            if os.name == "nt":  # Windows
                                os.startfile(output)
                            elif os.name == "posix":  # Linux/Mac
                                subprocess.call(("xdg-open", output))
                        except Exception as e:
                            log_warning(f"无法自动打开图像文件: {e}")
                    else:
                        log_error("无法生成依赖关系图")
                else:
                    log_error("生成依赖关系图失败")
                    if stderr:
                        console.print(
                            Panel(stderr, title="错误信息", border_style="red")
                        )

        elif component == "backend":
            # 检查requirements.txt是否存在
            if not os.path.exists(BACKEND_REQUIREMENTS):
                log_error("后端requirements.txt不存在")
                return

            # 创建临时目录生成依赖图
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_requirements = os.path.join(tmp_dir, "requirements.txt")
                shutil.copy(BACKEND_REQUIREMENTS, tmp_requirements)

                # 使用pipdeptree生成依赖图
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "python:3.9-slim",
                    "sh",
                    "-c",
                    "pip install -r /app/requirements.txt pipdeptree graphviz && "
                    + "pipdeptree --graph-output dot > /app/deps.dot && "
                    + "dot -Tpng -o /app/deps-graph.png /app/deps.dot",
                ]

                code, stdout, stderr = run_command(cmd)

                if code == 0:
                    # 将生成的图表复制到输出路径
                    graph_file = os.path.join(tmp_dir, "deps-graph.png")
                    if os.path.exists(graph_file):
                        shutil.copy(graph_file, output)
                        log_success(f"依赖关系图已生成: {output}")

                        # 尝试打开图像文件
                        try:
                            if os.name == "nt":  # Windows
                                os.startfile(output)
                            elif os.name == "posix":  # Linux/Mac
                                subprocess.call(("xdg-open", output))
                        except Exception as e:
                            log_warning(f"无法自动打开图像文件: {e}")
                    else:
                        log_error("无法生成依赖关系图")
                else:
                    log_error("生成依赖关系图失败")
                    if stderr:
                        console.print(
                            Panel(stderr, title="错误信息", border_style="red")
                        )

    except Exception as e:
        log_error(f"可视化依赖关系图时出错: {e}")


@cli.command("tree")
@click.argument("component", type=click.Choice(["frontend", "backend"]))
def show_deps_tree(component: str):
    """显示依赖树结构"""
    if not ensure_docker_running():
        return

    log_info(f"显示{component}依赖树...")

    try:
        if component == "frontend":
            # 检查package.json是否存在
            if not os.path.exists(FRONTEND_PACKAGE_JSON):
                log_error("前端package.json不存在")
                return

            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_package_json = os.path.join(tmp_dir, "package.json")
                shutil.copy(FRONTEND_PACKAGE_JSON, tmp_package_json)

                # 如果存在package-lock.json，也复制它
                if os.path.exists(
                    os.path.join(
                        os.path.dirname(FRONTEND_PACKAGE_JSON), "package-lock.json"
                    )
                ):
                    shutil.copy(
                        os.path.join(
                            os.path.dirname(FRONTEND_PACKAGE_JSON), "package-lock.json"
                        ),
                        os.path.join(tmp_dir, "package-lock.json"),
                    )

                # 使用npm list查看依赖树
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "node:16-alpine",
                    "sh",
                    "-c",
                    "cd /app && npm list --all",
                ]

                code, stdout, stderr = run_command(cmd)

                if stdout:
                    console.print(
                        Panel(stdout, title="前端依赖树", border_style="green")
                    )
                else:
                    log_error("获取前端依赖树失败")
                    if stderr:
                        console.print(
                            Panel(stderr, title="错误信息", border_style="red")
                        )

        elif component == "backend":
            # 检查requirements.txt是否存在
            if not os.path.exists(BACKEND_REQUIREMENTS):
                log_error("后端requirements.txt不存在")
                return

            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_requirements = os.path.join(tmp_dir, "requirements.txt")
                shutil.copy(BACKEND_REQUIREMENTS, tmp_requirements)

                # 使用pipdeptree查看依赖树
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_dir}:/app",
                    "python:3.9-slim",
                    "sh",
                    "-c",
                    "pip install -r /app/requirements.txt pipdeptree && pipdeptree",
                ]

                code, stdout, stderr = run_command(cmd)

                if stdout:
                    console.print(
                        Panel(stdout, title="后端依赖树", border_style="green")
                    )
                else:
                    log_error("获取后端依赖树失败")
                    if stderr:
                        console.print(
                            Panel(stderr, title="错误信息", border_style="red")
                        )

    except Exception as e:
        log_error(f"显示依赖树时出错: {e}")


if __name__ == "__main__":
    cli()
