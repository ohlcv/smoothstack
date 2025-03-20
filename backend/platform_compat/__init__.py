"""
跨平台兼容性模块

提供跨平台的功能支持，处理Windows和Unix系统的差异。
"""

from .command import (
    execute_command,
    execute_command_async,
)

from .env import (
    get_env_path_separator,
    normalize_env_var,
    get_env_dict,
    expand_env_vars,
    set_env_var,
    get_path_var,
    update_path_var,
)

from .fs import (
    ensure_dir_permissions,
    get_file_encoding as get_fs_file_encoding,
    make_file_executable,
    safe_remove,
    safe_copy,
    safe_move,
    get_file_owner,
    set_file_owner,
    get_file_attributes,
)

from .process import (
    is_admin,
    get_process_info,
    list_processes,
    is_process_running,
    kill_process,
    get_process_children,
    set_process_priority,
    get_process_environment,
)

from .encoding import (
    get_system_encoding,
    get_file_encoding,
    convert_to_utf8,
    normalize_newlines,
    get_bom_header,
    write_file_with_encoding,
    read_file_with_encoding,
)

__all__ = [
    # command.py
    "execute_command",
    "execute_command_async",
    # env.py
    "get_env_path_separator",
    "normalize_env_var",
    "get_env_dict",
    "expand_env_vars",
    "set_env_var",
    "get_path_var",
    "update_path_var",
    # fs.py
    "ensure_dir_permissions",
    "get_fs_file_encoding",
    "make_file_executable",
    "safe_remove",
    "safe_copy",
    "safe_move",
    "get_file_owner",
    "set_file_owner",
    "get_file_attributes",
    # process.py
    "is_admin",
    "get_process_info",
    "list_processes",
    "is_process_running",
    "kill_process",
    "get_process_children",
    "set_process_priority",
    "get_process_environment",
    # encoding.py
    "get_system_encoding",
    "get_file_encoding",
    "convert_to_utf8",
    "normalize_newlines",
    "get_bom_header",
    "write_file_with_encoding",
    "read_file_with_encoding",
]
