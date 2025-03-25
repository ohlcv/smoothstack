"""
Docker API交互类

提供Docker操作的API接口，包括镜像构建、容器管理等
"""

import os
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple

logger = logging.getLogger(__name__)


class DockerAPI:
    """Docker API交互类"""

    def __init__(self):
        """初始化Docker API"""
        # 检查Docker是否可用
        if not self._check_docker_available():
            logger.warning("Docker不可用，部分功能可能无法正常工作")

    def _check_docker_available(self) -> bool:
        """检查Docker是否可用

        Returns:
            是否可用
        """
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"检查Docker可用性失败: {e}")
            return False

    def _run_docker_command(
        self, cmd: List[str], capture_output: bool = True
    ) -> Tuple[bool, str]:
        """运行Docker命令

        Args:
            cmd: 命令行参数列表
            capture_output: 是否捕获输出

        Returns:
            (成功标志, 输出/错误信息)
        """
        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    return False, result.stderr
                return True, result.stdout
            else:
                # 直接在终端显示输出
                result = subprocess.run(cmd, check=False)
                return result.returncode == 0, ""
        except Exception as e:
            logger.error(f"运行Docker命令失败: {e}")
            return False, str(e)

    def build_image(self, context_path: str, dockerfile_path: str, tag: str) -> bool:
        """构建Docker镜像

        Args:
            context_path: 构建上下文路径
            dockerfile_path: Dockerfile路径
            tag: 镜像标签

        Returns:
            是否构建成功
        """
        try:
            # 检查路径是否存在
            if not os.path.exists(context_path):
                logger.error(f"构建上下文路径不存在: {context_path}")
                return False

            if not os.path.exists(dockerfile_path):
                logger.error(f"Dockerfile路径不存在: {dockerfile_path}")
                return False

            # 构建命令
            cmd = ["docker", "build", "-f", dockerfile_path, "-t", tag, context_path]

            # 执行构建
            logger.info(f"开始构建镜像: {tag}")
            success, output = self._run_docker_command(cmd, capture_output=False)

            if success:
                logger.info(f"镜像构建成功: {tag}")
            else:
                logger.error(f"镜像构建失败: {output}")

            return success

        except Exception as e:
            logger.error(f"构建镜像失败: {e}")
            return False

    def list_images(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出Docker镜像

        Args:
            name_filter: 镜像名称过滤器

        Returns:
            镜像信息列表
        """
        try:
            # 构建命令
            cmd = [
                "docker",
                "image",
                "ls",
                "--format",
                "{{.ID}}|{{.Repository}}|{{.Tag}}|{{.Size}}",
            ]

            if name_filter:
                cmd.extend(["--filter", f"reference={name_filter}"])

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"列出镜像失败: {output}")
                return []

            # 解析输出
            images = []
            for line in output.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) >= 4:
                    images.append(
                        {
                            "id": parts[0],
                            "repository": parts[1],
                            "tag": parts[2],
                            "size": parts[3],
                        }
                    )

            return images

        except Exception as e:
            logger.error(f"列出镜像失败: {e}")
            return []

    def remove_image(self, image: str, force: bool = False) -> bool:
        """删除Docker镜像

        Args:
            image: 镜像ID或标签
            force: 是否强制删除

        Returns:
            是否删除成功
        """
        try:
            # 构建命令
            cmd = ["docker", "image", "rm"]

            if force:
                cmd.append("-f")

            cmd.append(image)

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"删除镜像失败: {output}")

            return success

        except Exception as e:
            logger.error(f"删除镜像失败: {e}")
            return False

    def list_containers(
        self, all_containers: bool = True, name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出Docker容器

        Args:
            all_containers: 是否列出所有容器（包括已停止的）
            name_filter: 容器名称过滤器

        Returns:
            容器信息列表
        """
        try:
            # 构建命令
            cmd = [
                "docker",
                "container",
                "ls",
                "--format",
                "{{.ID}}|{{.Image}}|{{.Command}}|{{.Status}}|{{.Ports}}|{{.Names}}",
            ]

            if all_containers:
                cmd.append("-a")

            if name_filter:
                cmd.extend(["--filter", f"name={name_filter}"])

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"列出容器失败: {output}")
                return []

            # 解析输出
            containers = []
            for line in output.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) >= 6:
                    containers.append(
                        {
                            "id": parts[0],
                            "image": parts[1],
                            "command": parts[2],
                            "status": parts[3],
                            "ports": parts[4],
                            "name": parts[5],
                        }
                    )

            return containers

        except Exception as e:
            logger.error(f"列出容器失败: {e}")
            return []

    def start_container(self, container: str) -> bool:
        """启动Docker容器

        Args:
            container: 容器ID或名称

        Returns:
            是否启动成功
        """
        try:
            # 构建命令
            cmd = ["docker", "container", "start", container]

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"启动容器失败: {output}")

            return success

        except Exception as e:
            logger.error(f"启动容器失败: {e}")
            return False

    def stop_container(self, container: str) -> bool:
        """停止Docker容器

        Args:
            container: 容器ID或名称

        Returns:
            是否停止成功
        """
        try:
            # 构建命令
            cmd = ["docker", "container", "stop", container]

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"停止容器失败: {output}")

            return success

        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            return False

    def remove_container(self, container: str, force: bool = False) -> bool:
        """删除Docker容器

        Args:
            container: 容器ID或名称
            force: 是否强制删除

        Returns:
            是否删除成功
        """
        try:
            # 构建命令
            cmd = ["docker", "container", "rm"]

            if force:
                cmd.append("-f")

            cmd.append(container)

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"删除容器失败: {output}")

            return success

        except Exception as e:
            logger.error(f"删除容器失败: {e}")
            return False

    def container_logs(self, container: str, tail: int = 100) -> str:
        """获取容器日志

        Args:
            container: 容器ID或名称
            tail: 返回的最后行数

        Returns:
            容器日志
        """
        try:
            # 构建命令
            cmd = ["docker", "container", "logs", "--tail", str(tail), container]

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"获取容器日志失败: {output}")
                return ""

            return output

        except Exception as e:
            logger.error(f"获取容器日志失败: {e}")
            return ""

    def prune_images(self) -> bool:
        """清理未使用的镜像

        Returns:
            是否清理成功
        """
        try:
            # 构建命令
            cmd = ["docker", "image", "prune", "-f"]

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"清理镜像失败: {output}")

            return success

        except Exception as e:
            logger.error(f"清理镜像失败: {e}")
            return False

    def prune_containers(self) -> bool:
        """清理停止的容器

        Returns:
            是否清理成功
        """
        try:
            # 构建命令
            cmd = ["docker", "container", "prune", "-f"]

            # 执行命令
            success, output = self._run_docker_command(cmd)

            if not success:
                logger.error(f"清理容器失败: {output}")

            return success

        except Exception as e:
            logger.error(f"清理容器失败: {e}")
            return False
