"""
命令注册表
"""

from typing import Dict, List, Optional, Type
from .base import BaseCommand
from .env import EnvCommand
from .docker import DockerCommand
from .project import ProjectCommand
from .db import DBCommand
from .clean import CleanCommand
from .api import ApiCommand
from .analyze import AnalyzeCommand
from .docs import DocsCommand
from .backend_tools import BackendToolsCommand


class CommandRegistry:
    """命令注册表类"""

    def __init__(self):
        self.commands: Dict[str, Type[BaseCommand]] = {}
        self.aliases: Dict[str, str] = {}

        # 注册命令
        self.register("env", EnvCommand)
        self.register("docker", DockerCommand)
        self.register("project", ProjectCommand)
        self.register("db", DBCommand)
        self.register("clean", CleanCommand)
        self.register("api", ApiCommand)
        self.register("analyze", AnalyzeCommand)
        self.register("docs", DocsCommand)
        self.register("backend", BackendToolsCommand)

        # 注册别名
        self.register_alias("environment", "env")
        self.register_alias("container", "docker")
        self.register_alias("proj", "project")
        self.register_alias("database", "db")
        self.register_alias("analysis", "analyze")
        self.register_alias("documentation", "docs")
        self.register_alias("be", "backend")

    def register(self, name: str, command_class: Type[BaseCommand]):
        """注册命令"""
        self.commands[name] = command_class

    def register_alias(self, alias: str, command: str):
        """注册命令别名"""
        if command not in self.commands:
            raise ValueError(f"命令不存在: {command}")
        self.aliases[alias] = command

    def get_command(self, name: str) -> Optional[Type[BaseCommand]]:
        """获取命令类"""
        # 检查别名
        if name in self.aliases:
            name = self.aliases[name]

        return self.commands.get(name)

    def list_commands(self) -> List[str]:
        """列出所有命令"""
        commands = []

        # 添加主命令
        for name in self.commands:
            commands.append(name)

        # 添加别名
        for alias in self.aliases:
            commands.append(alias)

        return sorted(commands)

    def get_command_help(self, name: str) -> Optional[str]:
        """获取命令帮助信息"""
        command_class = self.get_command(name)
        if command_class:
            return command_class.__doc__
        return None

    def get_command_aliases(self, name: str) -> List[str]:
        """获取命令的别名列表"""
        aliases = []
        for alias, cmd in self.aliases.items():
            if cmd == name:
                aliases.append(alias)
        return sorted(aliases)

    def get_command_by_alias(self, alias: str) -> Optional[str]:
        """通过别名获取命令名"""
        return self.aliases.get(alias)

    def is_alias(self, name: str) -> bool:
        """检查是否为命令别名"""
        return name in self.aliases

    def get_all_aliases(self) -> Dict[str, str]:
        """获取所有命令别名"""
        return self.aliases.copy()
