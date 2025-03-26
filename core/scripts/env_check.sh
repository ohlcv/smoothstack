#!/bin/bash

# 加载工具函数
source "$(dirname "$0")/utils.sh"

# 检查开发环境
check_dev_env() {
    log_info "检查开发环境..."
    
    # 检查Docker
    if ! check_command "docker"; then
        return 1
    fi
    
    # 检查Docker Compose
    if ! check_command "docker-compose"; then
        return 1
    fi
    
    # 检查Node.js
    if ! check_command "node"; then
        return 1
    fi
    
    # 检查Python
    if ! check_command "python"; then
        return 1
    fi
    
    log_info "开发环境检查完成"
    return 0
} 