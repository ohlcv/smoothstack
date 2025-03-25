"""
文件系统操作模块

提供跨平台的文件系统操作功能，处理Windows和Unix系统的文件系统差异。
"""

import os
import sys
import stat
import shutil
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

try:
    import chardet

    HAS_CHARDET = True
except ImportError:
    print("请安装chardet: pip install chardet")
    HAS_CHARDET = False


def ensure_dir_permissions(path: Union[str, Path], mode: int = 0o755) -> bool:
    """
    确保目录具有正确的权限，处理跨平台差异

    Args:
        path: 目录路径
        mode: 权限模式（Unix风格）

    Returns:
        是否设置成功
    """
    try:
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True, mode=mode)
        elif path.is_dir():
            if sys.platform != "win32":
                # 在Unix系统上设置权限
                path.chmod(mode)
        return True
    except Exception as e:
        print(f"设置目录权限失败: {e}")
        return False


def get_file_encoding(file_path: Union[str, Path], default: str = "utf-8") -> str:
    """
    检测文件编码，处理跨平台差异

    Args:
        file_path: 文件路径
        default: 默认编码

    Returns:
        文件编码
    """
    try:
        # 读取文件的前4KB来检测编码
        with open(file_path, "rb") as f:
            raw = f.read(4096)
            if not raw:
                return default

            # 使用chardet检测编码
            if HAS_CHARDET:
                result = chardet.detect(raw)
                if result["encoding"] and result["confidence"] > 0.7:
                    return result["encoding"]

            # 如果没有chardet或检测结果不可靠，返回默认编码
            return default
    except Exception as e:
        print(f"检测文件编码失败: {e}")
        return default


def make_file_executable(file_path: Union[str, Path]) -> bool:
    """
    使文件可执行，处理跨平台差异

    Args:
        file_path: 文件路径

    Returns:
        是否设置成功
    """
    try:
        if sys.platform == "win32":
            # Windows不需要设置可执行权限
            return True
        else:
            # Unix系统设置可执行权限
            current = os.stat(file_path)
            os.chmod(file_path, current.st_mode | stat.S_IEXEC)
            return True
    except Exception as e:
        print(f"设置文件可执行权限失败: {e}")
        return False


def safe_remove(path: Union[str, Path]) -> bool:
    """
    安全删除文件或目录，处理跨平台差异

    Args:
        path: 文件或目录路径

    Returns:
        是否删除成功
    """
    try:
        path = Path(path)
        if not path.exists():
            return True

        if path.is_file() or path.is_symlink():
            # 删除文件或符号链接
            path.unlink()
        else:
            # 删除目录及其内容
            shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"删除失败: {e}")
        return False


def safe_copy(
    src: Union[str, Path], dst: Union[str, Path], follow_symlinks: bool = True
) -> bool:
    """
    安全复制文件或目录，处理跨平台差异

    Args:
        src: 源路径
        dst: 目标路径
        follow_symlinks: 是否跟随符号链接

    Returns:
        是否复制成功
    """
    try:
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            print(f"源路径不存在: {src}")
            return False

        if src.is_file():
            # 复制文件
            shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
        else:
            # 复制目录
            shutil.copytree(src, dst, symlinks=not follow_symlinks)
        return True
    except Exception as e:
        print(f"复制失败: {e}")
        return False


def safe_move(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """
    安全移动文件或目录，处理跨平台差异

    Args:
        src: 源路径
        dst: 目标路径

    Returns:
        是否移动成功
    """
    try:
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            print(f"源路径不存在: {src}")
            return False

        # 如果目标是目录，确保它存在
        if dst.is_dir():
            dst.mkdir(parents=True, exist_ok=True)

        # 移动文件或目录
        shutil.move(str(src), str(dst))
        return True
    except Exception as e:
        print(f"移动失败: {e}")
        return False


def get_file_owner(path: Union[str, Path]) -> Optional[str]:
    """
    获取文件所有者，处理跨平台差异

    Args:
        path: 文件路径

    Returns:
        文件所有者名称，如果获取失败则返回None
    """
    try:
        if sys.platform == "win32":
            import win32security
            import win32api

            # 获取文件安全描述符
            sd = win32security.GetFileSecurity(
                str(path), win32security.OWNER_SECURITY_INFORMATION
            )

            # 获取所有者SID
            owner_sid = sd.GetSecurityDescriptorOwner()

            # 将SID转换为账户名
            name, domain, type = win32security.LookupAccountSid("", owner_sid)
            return f"{domain}\\{name}"
        else:
            import pwd

            stat_info = os.stat(path)
            return pwd.getpwuid(stat_info.st_uid).pw_name
    except Exception as e:
        print(f"获取文件所有者失败: {e}")
        return None


def set_file_owner(path: Union[str, Path], owner: str) -> bool:
    """
    设置文件所有者，处理跨平台差异

    Args:
        path: 文件路径
        owner: 所有者名称

    Returns:
        是否设置成功
    """
    try:
        if sys.platform == "win32":
            import win32security
            import win32api

            # 解析域名和用户名
            domain, username = owner.split("\\") if "\\" in owner else ("", owner)

            # 获取用户SID
            sid, _, _ = win32security.LookupAccountName(None, username)

            # 获取文件安全描述符
            sd = win32security.GetFileSecurity(
                str(path), win32security.OWNER_SECURITY_INFORMATION
            )

            # 设置新的所有者
            sd.SetSecurityDescriptorOwner(sid, True)
            win32security.SetFileSecurity(
                str(path), win32security.OWNER_SECURITY_INFORMATION, sd
            )
        else:
            import pwd

            uid = pwd.getpwnam(owner).pw_uid
            os.chown(path, uid, -1)
        return True
    except Exception as e:
        print(f"设置文件所有者失败: {e}")
        return False


def get_file_attributes(path: Union[str, Path]) -> Dict[str, Any]:
    """
    获取文件属性，处理跨平台差异

    Args:
        path: 文件路径

    Returns:
        文件属性字典
    """
    try:
        path = Path(path)
        stat_info = path.stat()

        attributes = {
            "size": stat_info.st_size,
            "created": stat_info.st_ctime,
            "modified": stat_info.st_mtime,
            "accessed": stat_info.st_atime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "is_symlink": path.is_symlink(),
        }

        if sys.platform == "win32":
            import win32api
            import win32con

            # 获取Windows特定的文件属性
            win_attrs = win32api.GetFileAttributes(str(path))
            attributes.update(
                {
                    "hidden": bool(win_attrs & win32con.FILE_ATTRIBUTE_HIDDEN),
                    "system": bool(win_attrs & win32con.FILE_ATTRIBUTE_SYSTEM),
                    "archive": bool(win_attrs & win32con.FILE_ATTRIBUTE_ARCHIVE),
                    "readonly": bool(win_attrs & win32con.FILE_ATTRIBUTE_READONLY),
                }
            )
        else:
            # 获取Unix特定的文件权限
            mode = stat_info.st_mode
            attributes.update(
                {
                    "permissions": oct(mode & 0o777),
                    "readable": bool(mode & stat.S_IRUSR),
                    "writable": bool(mode & stat.S_IWUSR),
                    "executable": bool(mode & stat.S_IXUSR),
                }
            )

        return attributes
    except Exception as e:
        print(f"获取文件属性失败: {e}")
        return {}
