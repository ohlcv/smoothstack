#!/bin/bash

# 加载工具函数
source "$(dirname "$0")/utils.sh"

# 启动Docker服务
start_docker() {
    log_info "启动Docker服务..."
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        return 1
    fi
    
    # 检查Docker Compose
    if ! check_command "docker-compose"; then
        return 1
    fi
    
    log_info "Docker服务已启动"
    return 0
}

# 停止Docker服务
stop_docker() {
    log_info "停止Docker服务..."
    
    # 停止所有容器
    docker-compose down
    
    log_info "Docker服务已停止"
    return 0
}

# 重启Docker服务
restart_docker() {
    stop_docker
    start_docker
}

# Docker服务管理函数
docker_manage() {
    local action=$1
    local project_name=$2
    
    case $action in
        "up")
            start_docker
            ;;
        "down")
            stop_docker
            ;;
        "restart")
            restart_docker
            ;;
        "logs")
            if [ -n "$project_name" ]; then
                docker-compose logs -f "$project_name"
            else
                docker-compose logs -f
            fi
            ;;
        "status")
            docker-compose ps
            ;;
        "build")
            docker-compose build
            ;;
        "clean")
            docker-compose down -v
            ;;
        *)
            log_error "未知的Docker操作: $action"
            return 1
            ;;
    esac
} 