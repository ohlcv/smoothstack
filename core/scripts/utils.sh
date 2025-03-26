#!/bin/bash

# 日志函数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装"
        return 1
    fi
    return 0
}

# 检查目录是否存在
check_dir() {
    if [ ! -d "$1" ]; then
        log_error "目录 $1 不存在"
        return 1
    fi
    return 0
}

# 复制目录
copy_dir() {
    if [ -d "$2" ]; then
        rm -rf "$2"
    fi
    cp -r "$1" "$2"
    log_info "已复制 $1 到 $2"
} 