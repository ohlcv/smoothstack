#!/bin/bash
# Smoothstack 入口脚本 - 代理到 Python CLI 模块

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本号
VERSION="0.2.0"

# 获取当前脚本目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 环境检查函数
check_environment() {
    # 检查 Docker
    check_docker
    # 检查 Python
    check_python
    # 检查虚拟环境
    check_venv
}

# 检查并启动 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: 需要安装 Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: 需要安装 docker-compose${NC}"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${YELLOW}警告: Docker 未运行，尝试启动 Docker...${NC}"
        start_docker
    fi
}

# 启动 Docker
start_docker() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        local docker_paths=(
            "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"
            "C:\\Program Files (x86)\\Docker\\Docker\\Docker Desktop.exe"
            "$LOCALAPPDATA\\Docker\\Docker Desktop.exe"
            "$PROGRAMFILES\\Docker\\Docker\\Docker Desktop.exe"
            "$PROGRAMFILES(X86)\\Docker\\Docker\\Docker Desktop.exe"
        )
        
        local docker_started=false
        for path in "${docker_paths[@]}"; do
            if [ -f "$path" ]; then
                echo "找到 Docker Desktop 安装路径: $path"
                powershell.exe -Command "Start-Process '$path'" &> /dev/null
                docker_started=true
                break
            fi
        done
        
        if [ "$docker_started" = false ]; then
            echo -e "${RED}错误: 未找到 Docker Desktop 安装路径${NC}"
            echo "请确保已安装 Docker Desktop，或手动启动 Docker Desktop"
            exit 1
        fi
        
        wait_for_docker
    else
        echo -e "${RED}错误: 请手动启动 Docker 服务${NC}"
        exit 1
    fi
}

# 等待 Docker 启动
wait_for_docker() {
    echo "正在等待 Docker 启动..."
    for i in {1..30}; do
        if docker info &> /dev/null; then
            echo "Docker 已成功启动"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${RED}错误: Docker 启动超时${NC}"
    echo "请检查 Docker Desktop 是否正常启动"
    exit 1
}

# 检查 Python 环境
check_python() {
    local python_cmd="python"
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        python_cmd="python3"
    fi

    if ! command -v $python_cmd &> /dev/null; then
        echo -e "${RED}错误: 需要安装 Python 3.8 或以上版本${NC}"
        exit 1
    fi
    
    local py_ver=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [ -z "$py_ver" ]; then
        echo -e "${RED}错误: 无法获取 Python 版本信息${NC}"
        exit 1
    fi
    
    local py_ver_major=$(echo "$py_ver" | cut -d. -f1)
    local py_ver_minor=$(echo "$py_ver" | cut -d. -f2)
    
    if ! [[ "$py_ver_major" =~ ^[0-9]+$ ]] || ! [[ "$py_ver_minor" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}错误: Python 版本格式不正确${NC}"
        exit 1
    fi
    
    if [ "$py_ver_major" -lt 3 ] || ([ "$py_ver_major" -eq 3 ] && [ "$py_ver_minor" -lt 8 ]); then
        echo -e "${RED}错误: 需要 Python 3.8 或以上版本 (当前版本: $py_ver)${NC}"
        exit 1
    fi
}

# 检查虚拟环境
check_venv() {
    local venv_dir="${SCRIPT_DIR}/.venv"
    local python_cmd="python"
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        python_cmd="python3"
    fi
    
    if [ ! -d "$venv_dir" ]; then
        echo -e "${YELLOW}正在创建 Python 虚拟环境...${NC}"
        $python_cmd -m venv "$venv_dir"
        
        if [ -f "${SCRIPT_DIR}/backend/requirements.txt" ]; then
            echo "正在安装后端依赖..."
            "${venv_dir}/Scripts/pip" install -r "${SCRIPT_DIR}/backend/requirements.txt"
        else
            echo "警告: requirements.txt 文件不存在"
        fi
    fi
    
    if [ -f "${venv_dir}/Scripts/activate" ]; then
        source "${venv_dir}/Scripts/activate"
    else
        echo -e "${RED}错误: 虚拟环境激活脚本不存在${NC}"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "使用方式: ./start.sh <命令组> <命令> [选项]"
    echo ""
    echo "可用命令组:"
    echo "  project                             - 项目管理命令"
    echo "  frontend                             - 前端开发命令"
    echo "  backend                              - 后端开发命令"
    echo "  dev                                  - 开发环境管理"
    echo "  system                              - 系统管理命令"
    echo "  docker                              - Docker管理命令"
    echo ""
    echo "常用命令示例:"
    echo "  ./start.sh project create my-project  - 创建新项目"
    echo "  ./start.sh project run my-project     - 运行指定项目"
    echo "  ./start.sh frontend run              - 启动前端开发服务器"
    echo "  ./start.sh backend run               - 启动后端开发服务器"
    echo "  ./start.sh dev start                 - 启动开发环境"
    echo "  ./start.sh system status             - 查看系统状态"
    echo "  ./start.sh docker --help             - 显示Docker命令帮助"
    echo ""
    echo "使用 --help 查看各命令组的详细帮助信息"
}

# 显示项目命令帮助
show_project_help() {
    echo -e "${BLUE}Smoothstack 项目管理命令${NC}"
    echo
    echo "使用方式: ./start.sh project <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  create <name>                         - 创建新项目"
    echo "  run <name>                           - 运行指定项目"
    echo "  build <name>                         - 构建指定项目"
    echo "  test <name>                          - 测试指定项目"
    echo "  deploy <name>                        - 部署指定项目"
    echo "  list                                 - 列出所有项目"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh project create my-project   # 创建新项目"
    echo "  ./start.sh project run my-project      # 运行项目"
    echo "  ./start.sh project build my-project    # 构建项目"
    echo
    echo -e "${GREEN}选项:${NC}"
    echo "  --template <name>                     - 使用指定模板创建项目"
    echo "  --port <number>                       - 指定运行端口"
    echo "  --mode <dev|prod>                     - 指定运行模式"
}

# 显示前端命令帮助
show_frontend_help() {
    echo -e "${BLUE}Smoothstack 前端命令${NC}"
    echo
    echo "使用方式: ./start.sh frontend <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  setup                                 - 设置前端开发环境"
    echo "  run                                   - 启动前端开发服务器"
    echo "  build                                 - 构建前端应用"
    echo "  test                                  - 运行前端测试"
    echo "  stop                                  - 停止前端服务"
    echo "  status                                - 检查前端服务状态"
    echo "  logs                                  - 查看前端日志"
    echo "  deps                                  - 管理前端依赖包"
    echo "  container-deps                        - 管理容器内前端依赖包"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh frontend setup              # 设置前端开发环境"
    echo "  ./start.sh frontend run --port 3000    # 在指定端口运行前端服务"
    echo "  ./start.sh frontend build --mode prod  # 以生产模式构建前端"
    echo "  ./start.sh frontend deps install react # 安装前端依赖"
}

# 显示后端命令帮助
show_backend_help() {
    echo -e "${BLUE}Smoothstack 后端命令${NC}"
    echo
    echo "使用方式: ./start.sh backend <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  setup                                 - 设置后端开发环境"
    echo "  run                                   - 启动后端API服务器"
    echo "  test                                  - 运行后端测试"
    echo "  stop                                  - 停止后端服务"
    echo "  status                                - 检查后端服务状态"
    echo "  logs                                  - 查看后端日志"
    echo "  migrate                               - 运行数据库迁移"
    echo "  deps                                  - 管理后端依赖包"
    echo "  container-deps                        - 管理容器内后端依赖包"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh backend setup              # 设置后端开发环境"
    echo "  ./start.sh backend run --port 5000    # 在指定端口运行后端服务"
    echo "  ./start.sh backend migrate            # 运行数据库迁移"
    echo "  ./start.sh backend deps install       # 安装后端依赖"
}

# 显示系统命令帮助
show_system_help() {
    echo -e "${BLUE}Smoothstack 系统命令${NC}"
    echo
    echo "使用方式: ./start.sh system <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  status                                - 检查所有服务状态"
    echo "  run                                   - 启动所有服务"
    echo "  stop                                  - 停止所有服务"
    echo "  restart                               - 重启服务"
    echo "  update                                - 更新系统"
    echo "  logs                                  - 查看系统日志"
    echo "  clean                                 - 清理系统文件"
    echo "  docker                                - Docker容器和镜像管理"
    echo "  log                                   - 开发日志管理"
    echo "  deps                                  - 依赖管理工具"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh system status              # 检查所有服务状态"
    echo "  ./start.sh system run                 # 启动所有服务"
    echo "  ./start.sh system clean               # 清理系统文件"
    echo "  ./start.sh system log create          # 创建新的开发日志"
}

# 显示Docker命令帮助
show_docker_help() {
    echo "Docker 管理命令:"
    echo "  container  - 容器管理"
    echo "    list     - 列出容器"
    echo "    start    - 启动容器"
    echo "    stop     - 停止容器"
    echo "    restart  - 重启容器"
    echo "    logs     - 查看容器日志"
    echo "    stats    - 查看容器统计信息"
    echo "    info     - 查看容器详情"
    echo "    check    - 检查Docker服务状态"
    echo "    remove   - 删除容器"
    echo "  image     - 镜像管理"
    echo "    list     - 列出镜像"
    echo "    build    - 构建镜像"
    echo "    remove   - 删除镜像"
    echo "  network   - 网络管理"
    echo "    list     - 列出网络"
    echo "    create   - 创建网络"
    echo "    remove   - 删除网络"
    echo "  volume    - 卷管理"
    echo "    list     - 列出卷"
    echo "    create   - 创建卷"
    echo "    remove   - 删除卷"
    echo ""
    echo "示例:"
    echo "  ./start.sh docker container list    # 列出容器"
    echo "  ./start.sh docker container logs    # 查看容器日志"
    echo "  ./start.sh docker image list        # 列出镜像"
    echo "  ./start.sh docker network list      # 列出网络"
    echo "  ./start.sh docker volume list       # 列出卷"
}

# 显示容器命令帮助
show_container_help() {
    echo -e "${BLUE}Smoothstack 容器命令${NC}"
    echo
    echo "使用方式: ./start.sh container <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  list                                  - 列出所有容器"
    echo "  start                                 - 启动容器"
    echo "  stop                                  - 停止容器"
    echo "  rm                                    - 删除容器"
    echo "  logs                                  - 查看容器日志"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh container list              # 列出所有容器"
    echo "  ./start.sh container start my_container # 启动容器"
    echo "  ./start.sh container stop my_container  # 停止容器"
    echo "  ./start.sh container rm my_container     # 删除容器"
}

# 显示依赖管理命令帮助
show_deps_help() {
    echo -e "${BLUE}Smoothstack 依赖管理命令${NC}"
    echo
    echo "使用方式: ./start.sh deps <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  install                               - 安装依赖"
    echo "  update                                - 更新依赖"
    echo "  remove                                - 移除依赖"
    echo "  list                                  - 列出依赖"
    echo "  check                                 - 检查依赖"
    echo "  container-deps                        - 容器内依赖管理"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh deps install               # 安装所有依赖"
    echo "  ./start.sh deps update                # 更新所有依赖"
    echo "  ./start.sh deps list                  # 列出所有依赖"
    echo "  ./start.sh deps container-deps add    # 在容器内添加依赖"
}

# 显示开发环境命令帮助
show_dev_help() {
    echo -e "${BLUE}Smoothstack 开发环境命令${NC}"
    echo
    echo "使用方式: ./start.sh dev <命令> [选项]"
    echo
    echo -e "${GREEN}可用命令:${NC}"
    echo "  setup                                 - 设置开发环境"
    echo "  start                                 - 启动开发环境"
    echo "  stop                                  - 停止开发环境"
    echo "  restart                               - 重启开发环境"
    echo "  status                                - 检查开发环境状态"
    echo "  logs                                  - 查看开发环境日志"
    echo "  shell                                 - 进入开发环境容器"
    echo "  deps                                  - 管理开发环境依赖"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo "  ./start.sh dev setup                  # 设置开发环境"
    echo "  ./start.sh dev start                  # 启动开发环境"
    echo "  ./start.sh dev stop                   # 停止开发环境"
    echo "  ./start.sh dev shell                  # 进入开发环境容器"
    echo "  ./start.sh dev deps install           # 安装开发环境依赖"
}

# 开发环境命令处理
handle_dev_command() {
    local command=$1
    shift

    case $command in
        setup)
            setup_dev_environment
            ;;
        start)
            start_dev_environment
            ;;
        stop)
            stop_dev_environment
            ;;
        restart)
            restart_dev_environment
            ;;
        status)
            check_dev_status
            ;;
        logs)
            show_dev_logs "$@"
            ;;
        shell)
            enter_dev_shell
            ;;
        deps)
            handle_dev_deps "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的开发环境命令: $command${NC}"
            show_dev_help
            exit 1
            ;;
    esac
}

# 设置开发环境
setup_dev_environment() {
    echo -e "${BLUE}正在设置开发环境...${NC}"
    
    # 检查必要的文件
    if [ ! -f "${SCRIPT_DIR}/docker-compose.dev.yml" ]; then
        echo -e "${RED}错误: docker-compose.dev.yml 文件不存在${NC}"
        exit 1
    fi
    
    if [ ! -f "${SCRIPT_DIR}/docker/backend/Dockerfile.dev" ]; then
        echo -e "${RED}错误: Dockerfile.dev 文件不存在${NC}"
        exit 1
    fi
    
    # 构建开发环境镜像
    echo "构建开发环境镜像..."
    docker-compose -f docker-compose.dev.yml build
    
    echo -e "${GREEN}开发环境设置完成${NC}"
}

# 启动开发环境
start_dev_environment() {
    echo -e "${BLUE}正在启动开发环境...${NC}"
    docker-compose -f docker-compose.dev.yml up -d
    echo -e "${GREEN}开发环境已启动${NC}"
}

# 停止开发环境
stop_dev_environment() {
    echo -e "${BLUE}正在停止开发环境...${NC}"
    docker-compose -f docker-compose.dev.yml down
    echo -e "${GREEN}开发环境已停止${NC}"
}

# 重启开发环境
restart_dev_environment() {
    stop_dev_environment
    start_dev_environment
}

# 检查开发环境状态
check_dev_status() {
    echo -e "${BLUE}开发环境状态:${NC}"
    docker-compose -f docker-compose.dev.yml ps
}

# 显示开发环境日志
show_dev_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose -f docker-compose.dev.yml logs --tail=100
    else
        docker-compose -f docker-compose.dev.yml logs --tail=100 "$service"
    fi
}

# 进入开发环境容器
enter_dev_shell() {
    local service=$1
    if [ -z "$service" ]; then
        service="backend"
    fi
    docker-compose -f docker-compose.dev.yml exec "$service" sh
}

# 处理开发环境依赖命令
handle_dev_deps() {
    local command=$1
    shift

    case $command in
        install)
            install_dev_deps "$@"
            ;;
        update)
            update_dev_deps "$@"
            ;;
        list)
            list_dev_deps
            ;;
        *)
            echo -e "${RED}错误: 未知的依赖命令: $command${NC}"
            echo "可用命令: install, update, list"
            exit 1
            ;;
    esac
}

# 安装开发环境依赖
install_dev_deps() {
    local service=$1
    if [ -z "$service" ]; then
        service="backend"
    fi
    docker-compose -f docker-compose.dev.yml exec "$service" pip install "$@"
}

# 更新开发环境依赖
update_dev_deps() {
    local service=$1
    if [ -z "$service" ]; then
        service="backend"
    fi
    docker-compose -f docker-compose.dev.yml exec "$service" pip install --upgrade "$@"
}

# 列出开发环境依赖
list_dev_deps() {
    local service=$1
    if [ -z "$service" ]; then
        service="backend"
    fi
    docker-compose -f docker-compose.dev.yml exec "$service" pip list
}

# 前端命令处理
handle_frontend_command() {
    local command=$1
    shift

    case $command in
        --help|-h)
            show_frontend_help
            ;;
        setup)
            setup_frontend
            ;;
        run)
            run_frontend "$@"
            ;;
        build)
            build_frontend "$@"
            ;;
        test)
            test_frontend
            ;;
        stop)
            stop_frontend
            ;;
        status)
            check_frontend_status
            ;;
        logs)
            show_frontend_logs
            ;;
        deps)
            handle_frontend_deps "$@"
            ;;
        container-deps)
            handle_frontend_container_deps "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的前端命令: $command${NC}"
            show_frontend_help
            exit 1
            ;;
    esac
}

# 后端命令处理
handle_backend_command() {
    local command=$1
    shift

    case $command in
        --help|-h)
            show_backend_help
            ;;
        setup)
            setup_backend
            ;;
        run)
            run_backend "$@"
            ;;
        test)
            test_backend
            ;;
        stop)
            stop_backend
            ;;
        status)
            check_backend_status
            ;;
        logs)
            show_backend_logs
            ;;
        migrate)
            run_migrations
            ;;
        deps)
            handle_backend_deps "$@"
            ;;
        container-deps)
            handle_backend_container_deps "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的后端命令: $command${NC}"
            show_backend_help
            exit 1
            ;;
    esac
}

# 系统命令处理
handle_system_command() {
    local command=$1
    shift

    case $command in
        --help|-h)
            show_system_help
            ;;
        status)
            check_system_status
            ;;
        run)
            run_system
            ;;
        stop)
            stop_system
            ;;
        restart)
            restart_system
            ;;
        update)
            update_system
            ;;
        logs)
            show_system_logs "$@"
            ;;
        clean)
            clean_system
            ;;
        docker)
            handle_docker_command "$@"
            ;;
        log)
            handle_log_command "$@"
            ;;
        deps)
            handle_deps_command "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的系统命令: $command${NC}"
            show_system_help
            exit 1
            ;;
    esac
}

# Docker命令处理
handle_docker_command() {
    local subcommand=$1
    shift

    case $subcommand in
        help|--help|-h)
            show_docker_help
            ;;
        container)
            handle_docker_container "$@"
            ;;
        image)
            handle_docker_image "$@"
            ;;
        network)
            handle_docker_network "$@"
            ;;
        volume)
            handle_docker_volume "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的Docker命令: $subcommand${NC}"
            show_docker_help
            exit 1
            ;;
    esac
}

# 容器命令处理
handle_docker_container() {
    local command=$1
    shift

    # 检查 Python 环境
    if command -v python &> /dev/null && [ -f "${SCRIPT_DIR}/backend/container_manager/commands/container_cmd.py" ]; then
        # 激活虚拟环境
        source "${SCRIPT_DIR}/.venv/Scripts/activate"
        
        # 进入项目目录
        cd "${SCRIPT_DIR}"
        
        case $command in
            list)
                python -m backend.cli.main docker container list "$@"
                ;;
            start)
                python -m backend.cli.main docker container start "$@"
                ;;
            stop)
                python -m backend.cli.main docker container stop "$@"
                ;;
            restart)
                python -m backend.cli.main docker container restart "$@"
                ;;
            remove)
                python -m backend.cli.main docker container remove "$@"
                ;;
            logs)
                python -m backend.cli.main docker container logs "$@"
                ;;
            stats)
                python -m backend.cli.main docker container stats "$@"
                ;;
            info)
                python -m backend.cli.main docker container info "$@"
                ;;
            check)
                python -m backend.cli.main docker container check "$@"
                ;;
            *)
                echo -e "${RED}错误: 未知的容器命令: $command${NC}"
                echo "可用命令: list, start, stop, restart, remove, logs, stats, info, check"
                exit 1
                ;;
        esac
    else
        # 如果 Python 环境不可用，使用原生 Docker 命令
        case $command in
            list)
                docker ps -a "$@"
                ;;
            start)
                docker start "$@"
                ;;
            stop)
                docker stop "$@"
                ;;
            restart)
                docker restart "$@"
                ;;
            remove)
                docker rm "$@"
                ;;
            logs)
                docker logs "$@"
                ;;
            stats)
                docker stats "$@"
                ;;
            info)
                docker inspect "$@"
                ;;
            check)
                docker info "$@"
                ;;
            *)
                echo -e "${RED}错误: 未知的容器命令: $command${NC}"
                echo "可用命令: list, start, stop, restart, remove, logs, stats, info, check"
                exit 1
                ;;
        esac
    fi
}

# 镜像命令处理
handle_docker_image() {
    local command=$1
    shift

    case $command in
        list)
            docker images "$@"
            ;;
        build)
            docker build "$@"
            ;;
        rm)
            docker rmi "$@"
            ;;
        pull)
            docker pull "$@"
            ;;
        push)
            docker push "$@"
            ;;
        tag)
            docker tag "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的镜像命令: $command${NC}"
            echo "可用命令: list, build, rm, pull, push, tag"
            exit 1
            ;;
    esac
}

# 网络命令处理
handle_docker_network() {
    local command=$1
    shift

    case $command in
        list)
            docker network ls "$@"
            ;;
        create)
            docker network create "$@"
            ;;
        rm)
            docker network rm "$@"
            ;;
        connect)
            docker network connect "$@"
            ;;
        disconnect)
            docker network disconnect "$@"
            ;;
        inspect)
            docker network inspect "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的网络命令: $command${NC}"
            echo "可用命令: list, create, rm, connect, disconnect, inspect"
            exit 1
            ;;
    esac
}

# 卷命令处理
handle_docker_volume() {
    local command=$1
    shift

    case $command in
        list)
            docker volume ls "$@"
            ;;
        create)
            docker volume create "$@"
            ;;
        rm)
            docker volume rm "$@"
            ;;
        inspect)
            docker volume inspect "$@"
            ;;
        prune)
            docker volume prune "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的卷命令: $command${NC}"
            echo "可用命令: list, create, rm, inspect, prune"
            exit 1
            ;;
    esac
}

# Docker服务命令处理
handle_docker_service() {
    local command=$1
    shift

    case $command in
        status)
            if command -v python &> /dev/null; then
                python -m backend.cli.main container check
            else
                docker info
            fi
            ;;
        start)
            start_docker
            ;;
        stop)
            if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
                powershell.exe -Command "Stop-Process -Name 'Docker Desktop'"
            else
                sudo systemctl stop docker
            fi
            ;;
        restart)
            handle_docker_service stop
            sleep 2
            handle_docker_service start
            ;;
        *)
            echo -e "${RED}错误: 未知的服务命令: $command${NC}"
            echo "可用命令: status, start, stop, restart"
            exit 1
            ;;
    esac
}

# 依赖命令处理
handle_deps_command() {
    local command=$1
    shift

    case $command in
        install)
            install_deps "$@"
            ;;
        update)
            update_deps "$@"
            ;;
        remove)
            remove_deps "$@"
            ;;
        list)
            list_deps
            ;;
        check)
            check_deps
            ;;
        container-deps)
            handle_container_deps "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的依赖命令: $command${NC}"
            show_deps_help
            exit 1
            ;;
    esac
}

# 前端相关函数
setup_frontend() {
    echo -e "${BLUE}正在设置前端环境...${NC}"
    cd frontend && npm install
    cd ..
    echo -e "${GREEN}前端环境设置完成${NC}"
}

run_frontend() {
    echo -e "${BLUE}正在启动前端服务...${NC}"
    cd frontend && npm run dev "$@"
    cd ..
}

build_frontend() {
    echo -e "${BLUE}正在构建前端应用...${NC}"
    cd frontend && npm run build "$@"
    cd ..
}

test_frontend() {
    echo -e "${BLUE}正在运行前端测试...${NC}"
    cd frontend && npm test
    cd ..
}

stop_frontend() {
    echo -e "${BLUE}正在停止前端服务...${NC}"
    docker-compose -f docker-compose.dev.yml stop frontend
}

check_frontend_status() {
    echo -e "${BLUE}前端服务状态:${NC}"
    docker-compose -f docker-compose.dev.yml ps frontend
}

show_frontend_logs() {
    echo -e "${BLUE}前端服务日志:${NC}"
    docker-compose -f docker-compose.dev.yml logs frontend
}

# 后端相关函数
setup_backend() {
    echo -e "${BLUE}正在设置后端环境...${NC}"
    cd backend && pip install -r requirements.txt
    cd ..
    echo -e "${GREEN}后端环境设置完成${NC}"
}

run_backend() {
    echo -e "${BLUE}正在启动后端服务...${NC}"
    cd backend && uvicorn main:app --reload "$@"
    cd ..
}

test_backend() {
    echo -e "${BLUE}正在运行后端测试...${NC}"
    cd backend && python -m pytest
    cd ..
}

stop_backend() {
    echo -e "${BLUE}正在停止后端服务...${NC}"
    docker-compose -f docker-compose.dev.yml stop backend
}

check_backend_status() {
    echo -e "${BLUE}后端服务状态:${NC}"
    docker-compose -f docker-compose.dev.yml ps backend
}

show_backend_logs() {
    echo -e "${BLUE}后端服务日志:${NC}"
    docker-compose -f docker-compose.dev.yml logs backend
}

run_migrations() {
    echo -e "${BLUE}正在运行数据库迁移...${NC}"
    cd backend && alembic upgrade head
    cd ..
}

# 系统相关函数
check_system_status() {
    echo -e "${BLUE}系统状态:${NC}"
    docker-compose -f docker-compose.dev.yml ps
}

run_system() {
    echo -e "${BLUE}正在启动所有服务...${NC}"
    docker-compose -f docker-compose.dev.yml up -d
}

stop_system() {
    echo -e "${BLUE}正在停止所有服务...${NC}"
    docker-compose -f docker-compose.dev.yml down
}

restart_system() {
    stop_system
    run_system
}

update_system() {
    echo -e "${BLUE}正在更新系统...${NC}"
    git pull
    docker-compose -f docker-compose.dev.yml pull
    docker-compose -f docker-compose.dev.yml up -d --build
}

show_system_logs() {
    echo -e "${BLUE}系统日志:${NC}"
    docker-compose -f docker-compose.dev.yml logs "$@"
}

clean_system() {
    echo -e "${BLUE}正在清理系统...${NC}"
    docker-compose -f docker-compose.dev.yml down -v
    docker system prune -f
}

# 日志相关函数
handle_log_command() {
    local command=$1
    shift

    case $command in
        create)
            create_dev_log "$@"
            ;;
        list)
            list_dev_logs
            ;;
        show)
            show_dev_log "$@"
            ;;
        *)
            echo -e "${RED}错误: 未知的日志命令: $command${NC}"
            echo "可用命令: create, list, show"
            exit 1
            ;;
    esac
}

create_dev_log() {
    local date=$(date +%Y-%m-%d)
    local log_file="docs/开发日志/${date}.md"
    mkdir -p "docs/开发日志"
    touch "$log_file"
    echo "# 开发日志 ${date}" > "$log_file"
    echo -e "${GREEN}已创建开发日志: $log_file${NC}"
}

list_dev_logs() {
    echo -e "${BLUE}开发日志列表:${NC}"
    ls -l docs/开发日志/
}

show_dev_log() {
    local date=$1
    if [ -z "$date" ]; then
        date=$(date +%Y-%m-%d)
    fi
    local log_file="docs/开发日志/${date}.md"
    if [ -f "$log_file" ]; then
        cat "$log_file"
    else
        echo -e "${RED}错误: 日志文件不存在: $log_file${NC}"
    fi
}

# 容器管理命令
handle_container_cmd() {
    # 确保虚拟环境已激活
    ensure_venv

    # 执行容器命令
    python -m backend.cli.main container "$@"
}

# 项目管理命令
handle_project_command() {
    local command=$1
    shift

    case $command in
        create)
            create_project "$@"
            ;;
        run)
            run_project "$@"
            ;;
        build)
            build_project "$@"
            ;;
        test)
            test_project "$@"
            ;;
        deploy)
            deploy_project "$@"
            ;;
        list)
            list_projects
            ;;
        help|--help|-h)
            show_project_help
            ;;
        *)
            echo -e "${RED}错误: 未知的项目命令 '$command'${NC}"
            show_project_help
            exit 1
            ;;
    esac
}

# 创建新项目
create_project() {
    local project_name=$1
    local template="basic"
    shift

    # 解析选项
    while [[ $# -gt 0 ]]; do
        case $1 in
            --template)
                template="$2"
                shift 2
                ;;
            *)
                echo -e "${RED}错误: 未知的选项 '$1'${NC}"
                show_project_help
                exit 1
                ;;
        esac
    done

    if [ -z "$project_name" ]; then
        echo -e "${RED}错误: 请指定项目名称${NC}"
        show_project_help
        exit 1
    fi

    local project_dir="projects/$project_name"
    if [ -d "$project_dir" ]; then
        echo -e "${RED}错误: 项目 '$project_name' 已存在${NC}"
        exit 1
    fi

    echo -e "${BLUE}创建项目 '$project_name' (使用模板: $template)...${NC}"

    # 复制模板
    case $template in
        basic)
            cp -r "examples/basic-template" "$project_dir"
            ;;
        dashboard)
            cp -r "examples/dashboard-template" "$project_dir"
            ;;
        *)
            echo -e "${RED}错误: 未知的模板 '$template'${NC}"
            exit 1
            ;;
    esac

    # 更新项目配置
    sed -i "s/basic-template/$project_name/g" "$project_dir/frontend/package.json"
    echo -e "${GREEN}项目 '$project_name' 创建成功${NC}"
}

# 运行项目
run_project() {
    local project_name=$1
    if [ -z "$project_name" ]; then
        echo -e "${RED}错误: 请指定项目名称${NC}"
        show_project_help
        exit 1
    fi

    local project_dir="projects/$project_name"
    if [ ! -d "$project_dir" ]; then
        echo -e "${RED}错误: 项目 '$project_name' 不存在${NC}"
        exit 1
    fi

    echo -e "${BLUE}运行项目 '$project_name'...${NC}"
    docker-compose -f "$project_dir/docker-compose.yml" up
}

# 构建项目
build_project() {
    local project_name=$1
    if [ -z "$project_name" ]; then
        echo -e "${RED}错误: 请指定项目名称${NC}"
        show_project_help
        exit 1
    fi

    local project_dir="projects/$project_name"
    if [ ! -d "$project_dir" ]; then
        echo -e "${RED}错误: 项目 '$project_name' 不存在${NC}"
        exit 1
    fi

    echo -e "${BLUE}构建项目 '$project_name'...${NC}"
    docker-compose -f "$project_dir/docker-compose.yml" build
}

# 测试项目
test_project() {
    local project_name=$1
    if [ -z "$project_name" ]; then
        echo -e "${RED}错误: 请指定项目名称${NC}"
        show_project_help
        exit 1
    fi

    local project_dir="projects/$project_name"
    if [ ! -d "$project_dir" ]; then
        echo -e "${RED}错误: 项目 '$project_name' 不存在${NC}"
        exit 1
    fi

    echo -e "${BLUE}测试项目 '$project_name'...${NC}"
    # 运行前端测试
    docker-compose -f "$project_dir/docker-compose.yml" run frontend npm test
    # 运行后端测试
    docker-compose -f "$project_dir/docker-compose.yml" run backend pytest
}

# 部署项目
deploy_project() {
    local project_name=$1
    if [ -z "$project_name" ]; then
        echo -e "${RED}错误: 请指定项目名称${NC}"
        show_project_help
        exit 1
    fi

    local project_dir="projects/$project_name"
    if [ ! -d "$project_dir" ]; then
        echo -e "${RED}错误: 项目 '$project_name' 不存在${NC}"
        exit 1
    fi

    echo -e "${BLUE}部署项目 '$project_name'...${NC}"
    docker-compose -f "$project_dir/docker-compose.yml" -f "$project_dir/docker-compose.prod.yml" up -d
}

# 列出所有项目
list_projects() {
    echo -e "${BLUE}项目列表:${NC}"
    if [ -d "projects" ]; then
        for project in projects/*/; do
            if [ -d "$project" ]; then
                project=${project%/}
                project=${project#projects/}
                echo "  - $project"
            fi
        done
    else
        echo "  没有找到任何项目"
    fi
}

# 主函数
main() {
    # 检查环境
    check_environment

    # 如果没有参数，显示帮助信息
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    # 获取命令
    local command_group="$1"
    shift

    # 处理命令
    case $command_group in
        project)
            handle_project_command "$@"
            ;;
        frontend)
            handle_frontend_command "$@"
            ;;
        backend)
            handle_backend_command "$@"
            ;;
        dev)
            handle_dev_command "$@"
            ;;
        system)
            handle_system_command "$@"
            ;;
        docker)
            handle_docker_command "$@"
            ;;
        --help|-h|help)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知的命令组: $command_group${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"