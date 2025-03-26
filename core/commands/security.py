#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全命令模块

提供安全相关的命令，包括：
- 用户认证
- 权限管理
- 密钥管理
- 安全审计
"""

import os
import sys
import yaml
import click
import hashlib
import secrets
import jwt
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from .base import BaseCommand
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SecurityCommand(BaseCommand):
    """安全命令类"""

    def __init__(self):
        super().__init__()
        self.projects_dir = self.project_root / "projects"
        self.security_dir = self.project_root / "security"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.security_dir.mkdir(parents=True, exist_ok=True)

    def login(self, username: str, password: str):
        """用户登录"""
        try:
            self.info(f"用户登录: {username}")

            # 检查用户配置
            users_file = self.security_dir / "users.yml"
            if not users_file.exists():
                raise RuntimeError("用户配置不存在")

            # 加载用户配置
            with open(users_file, "r", encoding="utf-8") as f:
                users = yaml.safe_load(f)

            # 验证用户
            if username not in users:
                raise RuntimeError(f"用户不存在: {username}")

            # 验证密码
            if not self._verify_password(password, users[username]["password"]):
                raise RuntimeError("密码错误")

            # 生成令牌
            token = self._generate_token(username)

            # 保存令牌
            self._save_token(token)

            self.success("登录成功")

        except Exception as e:
            self.error(f"登录失败: {e}")
            raise

    def logout(self):
        """用户登出"""
        try:
            self.info("用户登出")

            # 删除令牌
            token_file = self.security_dir / "token"
            if token_file.exists():
                token_file.unlink()

            self.success("登出成功")

        except Exception as e:
            self.error(f"登出失败: {e}")
            raise

    def create_user(self, username: str, password: str, role: str = "user"):
        """创建用户"""
        try:
            self.info(f"创建用户: {username}")

            # 检查用户配置
            users_file = self.security_dir / "users.yml"
            if not users_file.exists():
                users = {}
            else:
                with open(users_file, "r", encoding="utf-8") as f:
                    users = yaml.safe_load(f)

            # 检查用户是否存在
            if username in users:
                raise RuntimeError(f"用户已存在: {username}")

            # 创建用户
            users[username] = {
                "password": self._hash_password(password),
                "role": role,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 保存用户配置
            with open(users_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(users, f, default_flow_style=False)

            self.success(f"创建用户成功: {username}")

        except Exception as e:
            self.error(f"创建用户失败: {e}")
            raise

    def delete_user(self, username: str):
        """删除用户"""
        try:
            self.info(f"删除用户: {username}")

            # 检查用户配置
            users_file = self.security_dir / "users.yml"
            if not users_file.exists():
                raise RuntimeError("用户配置不存在")

            # 加载用户配置
            with open(users_file, "r", encoding="utf-8") as f:
                users = yaml.safe_load(f)

            # 检查用户是否存在
            if username not in users:
                raise RuntimeError(f"用户不存在: {username}")

            # 删除用户
            del users[username]

            # 保存用户配置
            with open(users_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(users, f, default_flow_style=False)

            self.success(f"删除用户成功: {username}")

        except Exception as e:
            self.error(f"删除用户失败: {e}")
            raise

    def change_password(self, username: str, old_password: str, new_password: str):
        """修改密码"""
        try:
            self.info(f"修改密码: {username}")

            # 检查用户配置
            users_file = self.security_dir / "users.yml"
            if not users_file.exists():
                raise RuntimeError("用户配置不存在")

            # 加载用户配置
            with open(users_file, "r", encoding="utf-8") as f:
                users = yaml.safe_load(f)

            # 检查用户是否存在
            if username not in users:
                raise RuntimeError(f"用户不存在: {username}")

            # 验证旧密码
            if not self._verify_password(old_password, users[username]["password"]):
                raise RuntimeError("旧密码错误")

            # 修改密码
            users[username]["password"] = self._hash_password(new_password)

            # 保存用户配置
            with open(users_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(users, f, default_flow_style=False)

            self.success("修改密码成功")

        except Exception as e:
            self.error(f"修改密码失败: {e}")
            raise

    def create_key(self, name: str, type: str = "ssh"):
        """创建密钥"""
        try:
            self.info(f"创建密钥: {name}")

            # 检查密钥配置
            keys_file = self.security_dir / "keys.yml"
            if not keys_file.exists():
                keys = {}
            else:
                with open(keys_file, "r", encoding="utf-8") as f:
                    keys = yaml.safe_load(f)

            # 检查密钥是否存在
            if name in keys:
                raise RuntimeError(f"密钥已存在: {name}")

            # 生成密钥
            if type == "ssh":
                key = self._generate_ssh_key()
            else:
                raise RuntimeError(f"不支持的密钥类型: {type}")

            # 创建密钥
            keys[name] = {
                "type": type,
                "public_key": key["public_key"],
                "private_key": key["private_key"],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 保存密钥配置
            with open(keys_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(keys, f, default_flow_style=False)

            self.success(f"创建密钥成功: {name}")

        except Exception as e:
            self.error(f"创建密钥失败: {e}")
            raise

    def delete_key(self, name: str):
        """删除密钥"""
        try:
            self.info(f"删除密钥: {name}")

            # 检查密钥配置
            keys_file = self.security_dir / "keys.yml"
            if not keys_file.exists():
                raise RuntimeError("密钥配置不存在")

            # 加载密钥配置
            with open(keys_file, "r", encoding="utf-8") as f:
                keys = yaml.safe_load(f)

            # 检查密钥是否存在
            if name not in keys:
                raise RuntimeError(f"密钥不存在: {name}")

            # 删除密钥
            del keys[name]

            # 保存密钥配置
            with open(keys_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(keys, f, default_flow_style=False)

            self.success(f"删除密钥成功: {name}")

        except Exception as e:
            self.error(f"删除密钥失败: {e}")
            raise

    def list_keys(self):
        """列出密钥"""
        try:
            self.info("列出密钥:")

            # 检查密钥配置
            keys_file = self.security_dir / "keys.yml"
            if not keys_file.exists():
                self.info("未找到密钥")
                return

            # 加载密钥配置
            with open(keys_file, "r", encoding="utf-8") as f:
                keys = yaml.safe_load(f)

            # 显示密钥列表
            if not keys:
                self.info("未找到密钥")
                return

            self.info("\n密钥列表:")
            for name, key in keys.items():
                self.info(f"名称: {name}")
                self.info(f"类型: {key['type']}")
                self.info(f"创建时间: {key['created_at']}")
                self.info("")

        except Exception as e:
            self.error(f"列出密钥失败: {e}")
            raise

    def audit(self, action: str, **kwargs):
        """安全审计"""
        try:
            self.info(f"安全审计: {action}")

            # 检查审计配置
            audit_file = self.security_dir / "audit.yml"
            if not audit_file.exists():
                audit = []
            else:
                with open(audit_file, "r", encoding="utf-8") as f:
                    audit = yaml.safe_load(f)

            # 创建审计记录
            record = {
                "action": action,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "details": kwargs,
            }

            # 添加审计记录
            audit.append(record)

            # 保存审计配置
            with open(audit_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(audit, f, default_flow_style=False)

            self.success("审计记录已添加")

        except Exception as e:
            self.error(f"安全审计失败: {e}")
            raise

    def list_audit(self, action: Optional[str] = None):
        """列出审计记录"""
        try:
            self.info("列出审计记录:")

            # 检查审计配置
            audit_file = self.security_dir / "audit.yml"
            if not audit_file.exists():
                self.info("未找到审计记录")
                return

            # 加载审计配置
            with open(audit_file, "r", encoding="utf-8") as f:
                audit = yaml.safe_load(f)

            # 过滤审计记录
            if action:
                audit = [record for record in audit if record["action"] == action]

            # 显示审计记录
            if not audit:
                self.info("未找到审计记录")
                return

            self.info("\n审计记录:")
            for record in audit:
                self.info(f"操作: {record['action']}")
                self.info(f"时间: {record['timestamp']}")
                self.info("详情:")
                for key, value in record["details"].items():
                    self.info(f"  {key}: {value}")
                self.info("")

        except Exception as e:
            self.error(f"列出审计记录失败: {e}")
            raise

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return self._hash_password(password) == hashed_password

        except Exception as e:
            self.error(f"验证密码失败: {e}")
            raise

    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        try:
            salt = secrets.token_hex(16)
            return f"{salt}:{hashlib.sha256((salt + password).encode()).hexdigest()}"

        except Exception as e:
            self.error(f"哈希密码失败: {e}")
            raise

    def _generate_token(self, username: str) -> str:
        """生成令牌"""
        try:
            # 创建令牌
            token = {"username": username, "exp": datetime.utcnow() + timedelta(days=1)}

            # 签名令牌
            return jwt.encode(token, "secret", algorithm="HS256")

        except Exception as e:
            self.error(f"生成令牌失败: {e}")
            raise

    def _save_token(self, token: str):
        """保存令牌"""
        try:
            # 保存令牌
            token_file = self.security_dir / "token"
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(token)

        except Exception as e:
            self.error(f"保存令牌失败: {e}")
            raise

    def _generate_ssh_key(self) -> Dict[str, str]:
        """生成SSH密钥"""
        try:
            # 生成密钥对
            private_key = secrets.token_hex(32)
            public_key = hashlib.sha256(private_key.encode()).hexdigest()

            return {"private_key": private_key, "public_key": public_key}

        except Exception as e:
            self.error(f"生成SSH密钥失败: {e}")
            raise


# CLI命令
@click.group()
def security():
    """安全命令"""
    pass


@security.command()
@click.argument("username")
@click.password_option()
def login(username: str, password: str):
    """用户登录"""
    cmd = SecurityCommand()
    cmd.login(username, password)


@security.command()
def logout():
    """用户登出"""
    cmd = SecurityCommand()
    cmd.logout()


@security.command()
@click.argument("username")
@click.password_option()
@click.option("--role", "-r", default="user", help="用户角色")
def create_user(username: str, password: str, role: str):
    """创建用户"""
    cmd = SecurityCommand()
    cmd.create_user(username, password, role)


@security.command()
@click.argument("username")
def delete_user(username: str):
    """删除用户"""
    cmd = SecurityCommand()
    cmd.delete_user(username)


@security.command()
@click.argument("username")
@click.password_option("old_password", prompt="旧密码")
@click.password_option("new_password", prompt="新密码")
def change_password(username: str, old_password: str, new_password: str):
    """修改密码"""
    cmd = SecurityCommand()
    cmd.change_password(username, old_password, new_password)


@security.command()
@click.argument("name")
@click.option("--type", "-t", default="ssh", help="密钥类型")
def create_key(name: str, type: str):
    """创建密钥"""
    cmd = SecurityCommand()
    cmd.create_key(name, type)


@security.command()
@click.argument("name")
def delete_key(name: str):
    """删除密钥"""
    cmd = SecurityCommand()
    cmd.delete_key(name)


@security.command()
def list_keys():
    """列出密钥"""
    cmd = SecurityCommand()
    cmd.list_keys()


@security.command()
@click.argument("action")
@click.option("--username", "-u", help="用户名")
@click.option("--project", "-p", help="项目名称")
@click.option("--details", "-d", help="详细信息")
def audit(action: str, **kwargs):
    """安全审计"""
    cmd = SecurityCommand()
    cmd.audit(action, **kwargs)


@security.command()
@click.option("--action", "-a", help="操作类型")
def list_audit(action: Optional[str]):
    """列出审计记录"""
    cmd = SecurityCommand()
    cmd.list_audit(action)
