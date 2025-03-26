#!/bin/bash

# 加载工具函数
source "$(dirname "$0")/utils.sh"

# 数据库管理函数
db_manage() {
    local action=$1
    local project_name=$2
    
    case $action in
        "migrate")
            run_migrations "$project_name"
            ;;
        "rollback")
            rollback_migrations "$project_name"
            ;;
        "seed")
            seed_database "$project_name"
            ;;
        "reset")
            reset_database "$project_name"
            ;;
        "backup")
            backup_database "$project_name"
            ;;
        "restore")
            restore_database "$project_name"
            ;;
        *)
            log_error "未知的数据库操作: $action"
            return 1
            ;;
    esac
}

# 运行数据库迁移
run_migrations() {
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
    
    # 运行迁移
    python manage.py migrate
    
    log_info "数据库迁移完成"
    return 0
}

# 回滚数据库迁移
rollback_migrations() {
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
    
    # 回滚迁移
    python manage.py migrate --rollback
    
    log_info "数据库迁移回滚完成"
    return 0
}

# 填充数据库种子数据
seed_database() {
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
    
    # 填充种子数据
    python manage.py seed
    
    log_info "数据库种子数据填充完成"
    return 0
}

# 重置数据库
reset_database() {
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
    
    # 重置数据库
    python manage.py reset_db
    
    log_info "数据库重置完成"
    return 0
}

# 创建数据库备份
backup_database() {
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
    
    # 创建备份
    python manage.py backup
    
    log_info "数据库备份完成"
    return 0
}

# 恢复数据库备份
restore_database() {
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
    
    # 恢复备份
    python manage.py restore
    
    log_info "数据库备份恢复完成"
    return 0
} 