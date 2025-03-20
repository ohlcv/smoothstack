"""
Shell completion script management module.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List

from ..utils.platform import is_windows, get_home_dir


def get_completion_dir() -> Path:
    """
    获取补全脚本目录路径。

    Returns:
        Path: 补全脚本目录的路径
    """
    return Path(__file__).parent


def get_shell_type() -> str:
    """
    检测当前使用的shell类型。

    Returns:
        str: shell类型 ('bash', 'zsh', 'powershell')
    """
    if is_windows():
        return "powershell"

    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    return "bash"  # 默认使用bash


def get_shell_config_file() -> Optional[Path]:
    """
    获取shell配置文件路径。

    Returns:
        Optional[Path]: 配置文件路径，如果找不到则返回None
    """
    home = get_home_dir()
    shell_type = get_shell_type()

    if shell_type == "powershell":
        # PowerShell配置文件路径
        profile_paths = [
            home
            / "Documents"
            / "WindowsPowerShell"
            / "Microsoft.PowerShell_profile.ps1",
            home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        ]
        for path in profile_paths:
            if path.exists():
                return path
        # 如果配置文件不存在，使用第一个路径
        return profile_paths[0]

    elif shell_type == "zsh":
        return home / ".zshrc"
    else:  # bash
        return home / ".bashrc"


def install_completion() -> bool:
    """
    安装shell补全脚本。

    Returns:
        bool: 安装是否成功
    """
    shell_type = get_shell_type()
    completion_dir = get_completion_dir()
    config_file = get_shell_config_file()

    if not config_file:
        print("无法找到shell配置文件")
        return False

    if shell_type == "powershell":
        script_path = completion_dir / "smoothstack-completion.ps1"
        if not script_path.exists():
            print(f"找不到PowerShell补全脚本: {script_path}")
            return False

        # 确保配置文件目录存在
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # 添加Import-Module命令到PowerShell配置文件
        import_line = f"Import-Module {script_path}"
        if not config_file.exists() or import_line not in config_file.read_text():
            with config_file.open("a") as f:
                f.write(f"\n{import_line}\n")

    elif shell_type == "zsh":
        script_path = completion_dir / "smoothstack-completion.zsh"
        if not script_path.exists():
            print(f"找不到Zsh补全脚本: {script_path}")
            return False

        # 添加fpath和compinit命令到.zshrc
        fpath_line = f"fpath=({completion_dir} $fpath)"
        compinit_line = "autoload -Uz compinit && compinit"

        content = config_file.read_text() if config_file.exists() else ""
        if fpath_line not in content or compinit_line not in content:
            with config_file.open("a") as f:
                if fpath_line not in content:
                    f.write(f"\n{fpath_line}\n")
                if compinit_line not in content:
                    f.write(f"{compinit_line}\n")

    else:  # bash
        script_path = completion_dir / "smoothstack-completion.bash"
        if not script_path.exists():
            print(f"找不到Bash补全脚本: {script_path}")
            return False

        # 添加source命令到.bashrc
        source_line = f"source {script_path}"
        if not config_file.exists() or source_line not in config_file.read_text():
            with config_file.open("a") as f:
                f.write(f"\n{source_line}\n")

    print(f"补全脚本已安装到 {config_file}")
    print("请重新打开终端或运行以下命令使补全生效：")
    if shell_type == "powershell":
        print(". $PROFILE")
    elif shell_type == "zsh":
        print("source ~/.zshrc")
    else:
        print("source ~/.bashrc")

    return True


def uninstall_completion() -> bool:
    """
    卸载shell补全脚本。

    Returns:
        bool: 卸载是否成功
    """
    shell_type = get_shell_type()
    completion_dir = get_completion_dir()
    config_file = get_shell_config_file()

    if not config_file or not config_file.exists():
        print("找不到shell配置文件")
        return False

    content = config_file.read_text()
    new_content = []
    modified = False

    if shell_type == "powershell":
        script_path = completion_dir / "smoothstack-completion.ps1"
        import_line = f"Import-Module {script_path}"
        for line in content.splitlines():
            if import_line not in line:
                new_content.append(line)
            else:
                modified = True

    elif shell_type == "zsh":
        fpath_line = f"fpath=({completion_dir} $fpath)"
        compinit_line = "autoload -Uz compinit && compinit"
        for line in content.splitlines():
            if fpath_line not in line and compinit_line not in line:
                new_content.append(line)
            else:
                modified = True

    else:  # bash
        script_path = completion_dir / "smoothstack-completion.bash"
        source_line = f"source {script_path}"
        for line in content.splitlines():
            if source_line not in line:
                new_content.append(line)
            else:
                modified = True

    if modified:
        with config_file.open("w") as f:
            f.write("\n".join(new_content))
        print(f"补全脚本已从 {config_file} 中移除")
        print("请重新打开终端使更改生效")
        return True
    else:
        print("未找到补全脚本配置")
        return False


def list_completion_scripts() -> List[str]:
    """
    列出所有可用的补全脚本。

    Returns:
        List[str]: 补全脚本文件名列表
    """
    completion_dir = get_completion_dir()
    return [
        f.name
        for f in completion_dir.glob("smoothstack-completion.*")
        if f.is_file() and f.suffix in (".bash", ".zsh", ".ps1")
    ]
