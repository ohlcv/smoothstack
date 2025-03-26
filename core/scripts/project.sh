#!/bin/bash

# 加载工具函数
source "$(dirname "$0")/utils.sh"

# 项目管理函数
project_manage() {
    local action=$1
    local project_name=$2
    
    case $action in
        "create")
            create_project "$project_name"
            ;;
        "list")
            list_projects
            ;;
        "delete")
            delete_project "$project_name"
            ;;
        "start")
            start_project "$project_name"
            ;;
        "stop")
            stop_project "$project_name"
            ;;
        *)
            log_error "未知的项目操作: $action"
            return 1
            ;;
    esac
}

# 创建项目
create_project() {
    local project_name=$1
    
    if [ -z "$project_name" ]; then
        log_error "请指定项目名称"
        return 1
    fi
    
    local project_dir="$PROJECT_ROOT/projects/$project_name"
    
    if [ -d "$project_dir" ]; then
        log_error "项目 $project_name 已存在"
        return 1
    fi
    
    # 创建项目目录
    mkdir -p "$project_dir"
    
    # 复制项目模板
    cp -r "$PROJECT_ROOT/templates/framework-website"/* "$project_dir/"
    
    log_info "项目 $project_name 创建成功"
    return 0
}

# 列出项目
list_projects() {
    local projects_dir="$PROJECT_ROOT/projects"
    
    if [ ! -d "$projects_dir" ]; then
        log_info "暂无项目"
        return 0
    fi
    
    log_info "项目列表:"
    ls -l "$projects_dir" | grep "^d" | awk '{print $9}'
    return 0
}

# 删除项目
delete_project() {
    local project_name=$1
    
    if [ -z "$project_name" ]; then
        log_error "请指定项目名称"
        return 1
    fi
    
    local project_dir="$PROJECT_ROOT/projects/$project_name"
    
    if [ ! -d "$project_dir" ]; then
        log_error "项目 $project_name 不存在"
        return 1
    fi
    
    # 停止项目
    stop_project "$project_name"
    
    # 删除项目目录
    rm -rf "$project_dir"
    
    log_info "项目 $project_name 删除成功"
    return 0
}

# 启动项目
start_project() {
    local project_name=$1
    
    if [ -z "$project_name" ]; then
        log_error "请指定项目名称"
        return 1
    fi
    
    local project_dir="$PROJECT_ROOT/projects/$project_name"
    
    if [ ! -d "$project_dir" ]; then
        log_error "项目 $project_name 不存在"
        return 1
    fi
    
    # 进入项目目录
    cd "$project_dir"
    
    # 启动项目
    docker-compose up -d
    
    log_info "项目 $project_name 启动成功"
    return 0
}

# 停止项目
stop_project() {
    local project_name=$1
    
    if [ -z "$project_name" ]; then
        log_error "请指定项目名称"
        return 1
    fi
    
    local project_dir="$PROJECT_ROOT/projects/$project_name"
    
    if [ ! -d "$project_dir" ]; then
        log_error "项目 $project_name 不存在"
        return 1
    fi
    
    # 进入项目目录
    cd "$project_dir"
    
    # 停止项目
    docker-compose down
    
    log_info "项目 $project_name 停止成功"
    return 0
} 