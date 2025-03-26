"""
Docker管理命令
"""

import os
import sys
import time
import yaml
import docker
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from .base import BaseCommand


class DockerCommand(BaseCommand):
    """Docker管理命令类"""

    def __init__(self):
        super().__init__()
        self.client = docker.from_env()
        self.compose_file = "docker-compose.yml"
        self.env_file = ".env"
        self._compose_data = self._load_compose_data()

    def _load_compose_data(self) -> Dict:
        """加载 docker-compose 配置数据"""
        try:
            if not os.path.exists(self.compose_file):
                self.warning(f"未找到 docker-compose 配置文件: {self.compose_file}")
                return {"services": {}}

            with open(self.compose_file) as f:
                return yaml.safe_load(f) or {"services": {}}
        except Exception as e:
            self.error(f"加载 docker-compose 配置失败: {str(e)}")
            return {"services": {}}

    def _get_service_config(self, service: str) -> Dict:
        """获取服务配置"""
        return self._compose_data.get("services", {}).get(service, {})

    def _get_service_ports(self, service: str) -> List[int]:
        """获取服务端口列表"""
        service_config = self._get_service_config(service)
        ports = service_config.get("ports", [])
        return [int(port.split(":")[0]) for port in ports]

    def _get_service_dependencies(self, service: str) -> List[str]:
        """获取服务依赖列表"""
        service_config = self._get_service_config(service)
        return service_config.get("depends_on", [])

    def _check_environment(self):
        """检查Docker环境"""
        try:
            version = self.client.version()
            print(f"Docker版本: {version['Version']}")
            print(f"API版本: {version['ApiVersion']}")

            # 检查必要的网络
            networks = self.client.networks.list()
            network_names = [net.name for net in networks]
            if "dev-network" not in network_names:
                self.client.networks.create("dev-network", driver="bridge")
                print("创建开发网络: dev-network")

            # 检查必要的卷
            volumes = self.client.volumes.list()
            volume_names = [vol.name for vol in volumes]
            required_volumes = ["data-volume", "logs-volume"]
            for vol_name in required_volumes:
                if vol_name not in volume_names:
                    self.client.volumes.create(vol_name)
                    print(f"创建数据卷: {vol_name}")

        except docker.errors.DockerException as e:
            raise RuntimeError(f"Docker环境检查失败: {str(e)}")

    def setup(self):
        """设置Docker环境"""
        print("正在设置Docker环境...")
        self._check_environment()

        # 创建环境配置文件
        if not os.path.exists(self.env_file):
            with open(self.env_file, "w") as f:
                f.write("# Docker环境配置\n")
                f.write("COMPOSE_PROJECT_NAME=dev\n")
                f.write("POSTGRES_USER=postgres\n")
                f.write("POSTGRES_PASSWORD=postgres\n")
                f.write("POSTGRES_DB=dev\n")
                f.write("REDIS_PASSWORD=redis\n")
            print(f"创建环境配置文件: {self.env_file}")

        print("Docker环境设置完成")

    def up(self, service: Optional[str] = None, build: bool = False):
        """启动服务

        Args:
            service: 服务名称
            build: 是否构建镜像
        """
        self._check_environment()

        cmd = ["docker-compose", "up", "-d"]
        if build:
            cmd.append("--build")
        if service:
            cmd.append(service)

        try:
            subprocess.run(cmd, check=True)
            print(f"服务启动成功: {service if service else 'all'}")

            # 等待服务就绪
            self._wait_for_services(service)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"服务启动失败: {str(e)}")

    def _wait_for_services(self, service: Optional[str] = None):
        """等待服务就绪"""
        config = self._load_compose_data()
        services = [service] if service else config["services"].keys()

        for svc in services:
            if svc not in config["services"]:
                continue

            container_name = f"{os.path.basename(os.getcwd())}_{svc}_1"
            retries = 30
            while retries > 0:
                try:
                    container = self.client.containers.get(container_name)
                    if container.status == "running":
                        # 检查健康检查状态
                        if "Health" in container.attrs["State"]:
                            if (
                                container.attrs["State"]["Health"]["Status"]
                                == "healthy"
                            ):
                                print(f"服务就绪: {svc}")
                                break
                        else:
                            print(f"服务运行中: {svc}")
                            break
                except:
                    pass

                print(f"等待服务就绪: {svc}")
                time.sleep(2)
                retries -= 1

            if retries == 0:
                print(f"警告: 服务可能未完全就绪: {svc}")

    def down(self, service: Optional[str] = None, volumes: bool = False):
        """停止服务

        Args:
            service: 服务名称
            volumes: 是否删除数据卷
        """
        cmd = ["docker-compose", "down"]
        if volumes:
            cmd.append("-v")
        if service:
            cmd.append(service)

        try:
            subprocess.run(cmd, check=True)
            print(f"服务停止成功: {service if service else 'all'}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"服务停止失败: {str(e)}")

    def restart(self, service: Optional[str] = None):
        """重启服务

        Args:
            service: 服务名称
        """
        try:
            if service:
                subprocess.run(["docker-compose", "restart", service], check=True)
                print(f"服务重启成功: {service}")
                self._wait_for_services(service)
            else:
                subprocess.run(["docker-compose", "restart"], check=True)
                print("所有服务重启成功")
                self._wait_for_services()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"服务重启失败: {str(e)}")

    def logs(self, service: Optional[str] = None, tail: int = 100):
        """查看日志

        Args:
            service: 服务名称
            tail: 显示最后几行
        """
        cmd = ["docker-compose", "logs", "--tail", str(tail)]
        if service:
            cmd.append(service)

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"获取日志失败: {str(e)}")

    def status(self):
        """查看服务状态"""
        try:
            if not os.path.exists(self.compose_file):
                self.warning(f"未找到docker-compose配置文件: {self.compose_file}")
                print("没有正在运行的Docker服务")
                return

            print("获取Docker服务状态...")
            subprocess.run(["docker-compose", "ps"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"获取状态失败: {str(e)}")
        except Exception as e:
            self.error(f"获取状态失败: {str(e)}")

            # 直接使用docker命令查询
            try:
                print("\n尝试直接使用docker命令获取容器状态:")
                subprocess.run(["docker", "ps"], check=True)
            except Exception:
                print("无法获取Docker容器状态")

    def clean(self, all: bool = False):
        """清理Docker资源

        Args:
            all: 是否清理所有资源（包括未使用的镜像和数据卷）
        """
        try:
            # 停止并删除所有容器
            subprocess.run(["docker-compose", "down", "-v"], check=True)

            if all:
                # 删除所有未使用的镜像
                self.client.images.prune()
                # 删除所有未使用的卷
                self.client.volumes.prune()
                # 删除所有未使用的网络
                self.client.networks.prune()
                print("已清理所有未使用的Docker资源")

            print("Docker环境清理完成")
        except Exception as e:
            raise RuntimeError(f"清理失败: {str(e)}")

    def build(self, service: Optional[str] = None, no_cache: bool = False):
        """构建镜像

        Args:
            service: 服务名称
            no_cache: 是否不使用缓存
        """
        cmd = ["docker-compose", "build"]
        if no_cache:
            cmd.append("--no-cache")
        if service:
            cmd.append(service)

        try:
            subprocess.run(cmd, check=True)
            print(f"服务构建成功: {service if service else 'all'}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"服务构建失败: {str(e)}")

    def pull(self, service: Optional[str] = None):
        """拉取镜像

        Args:
            service: 服务名称
        """
        cmd = ["docker-compose", "pull"]
        if service:
            cmd.append(service)

        try:
            subprocess.run(cmd, check=True)
            print(f"镜像拉取成功: {service if service else 'all'}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"镜像拉取失败: {str(e)}")

    def push(self, service: Optional[str] = None):
        """推送镜像

        Args:
            service: 服务名称
        """
        cmd = ["docker-compose", "push"]
        if service:
            cmd.append(service)

        try:
            subprocess.run(cmd, check=True)
            print(f"镜像推送成功: {service if service else 'all'}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"镜像推送失败: {str(e)}")

    def exec(self, service: str, command: str):
        """在容器中执行命令

        Args:
            service: 服务名称
            command: 要执行的命令
        """
        try:
            subprocess.run(
                ["docker-compose", "exec", service] + command.split(), check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"命令执行失败: {str(e)}")

    def copy(self, service: str, src: str, dest: str, to_container: bool = True):
        """复制文件

        Args:
            service: 服务名称
            src: 源路径
            dest: 目标路径
            to_container: 是否复制到容器中
        """
        try:
            container_name = f"{os.path.basename(os.getcwd())}_{service}_1"
            if to_container:
                subprocess.run(
                    ["docker", "cp", src, f"{container_name}:{dest}"], check=True
                )
                print(f"文件已复制到容器: {dest}")
            else:
                subprocess.run(
                    ["docker", "cp", f"{container_name}:{src}", dest], check=True
                )
                print(f"文件已从容器复制: {dest}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"文件复制失败: {str(e)}")

    def init_template(self, template: str = "default"):
        """初始化Docker模板"""
        template_dir = os.path.join(
            os.path.dirname(__file__), "..", "templates", "docker", template
        )
        if not os.path.exists(template_dir):
            raise RuntimeError(f"模板不存在: {template}")

        # 复制模板文件
        for filename in os.listdir(template_dir):
            src = os.path.join(template_dir, filename)
            dest = os.path.join(os.getcwd(), filename)
            if os.path.exists(dest):
                continue
            with open(src, "r") as f_src, open(dest, "w") as f_dest:
                f_dest.write(f_src.read())
                print(f"创建文件: {filename}")

        print(f"Docker模板初始化完成: {template}")

    def check_service_health(self, service: str) -> bool:
        """检查服务健康状态"""
        import subprocess

        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(self.compose_file), "ps", service],
                capture_output=True,
                text=True,
            )
            return "healthy" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def check_service_dependencies(self, service: str) -> bool:
        """检查服务依赖是否满足"""
        depends_on = self._get_service_dependencies(service)
        for dep in depends_on:
            if not self.check_service_health(dep):
                return False
        return True

    def validate_service_config(self, service: str) -> bool:
        """验证服务配置"""
        service_config = self._get_service_config(service)

        # 检查必要的配置项
        required_fields = ["image", "ports"]
        return all(field in service_config for field in required_fields)
