#!/bin/bash
# Smoothstack 入口脚本 - 代理到 Python CLI 模块

set -e

# 获取当前脚本目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 检查 Python 环境
check_python() {
  if ! command -v python3 &> /dev/null; then
    echo "错误: 需要安装 Python 3.8 或以上版本"
    exit 1
  fi
  
  # 检查 Python 版本
  local py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  local py_ver_major=$(echo $py_ver | cut -d. -f1)
  local py_ver_minor=$(echo $py_ver | cut -d. -f2)
  
  if [ "$py_ver_major" -lt 3 ] || ([ "$py_ver_major" -eq 3 ] && [ "$py_ver_minor" -lt 8 ]); then
    echo "错误: 需要 Python 3.8 或以上版本 (当前版本: $py_ver)"
    exit 1
  fi
}

# 检查虚拟环境
check_venv() {
  local venv_dir="${SCRIPT_DIR}/.venv"
  
  if [ ! -d "$venv_dir" ]; then
    echo "正在创建 Python 虚拟环境..."
    python3 -m venv "$venv_dir"
    
    # 安装必要的依赖
    "${venv_dir}/bin/pip" install -r "${SCRIPT_DIR}/backend/requirements.txt"
  fi
  
  # 激活虚拟环境
  source "${venv_dir}/bin/activate"
}

# 输出帮助信息
show_help() {
  echo "Smoothstack - 现代化全栈应用开发框架"
  echo ""
  echo "使用方法: ./start.sh <命令> [选项]"
  echo ""
  echo "可用命令:"
  echo "  setup               初始化开发环境"
  echo "  run                 运行开发服务器"
  echo "  stop                停止服务"
  echo "  status              查看服务状态"
  echo "  logs                查看日志"
  echo "  restart             重启服务"
  echo "  deps                依赖管理"
  echo "  sources             源管理"
  echo "  help                显示帮助信息"
  echo ""
  echo "选项:"
  echo "  --cn                使用中国镜像源"
  echo "  --verbose           显示详细输出"
  echo ""
  echo "示例:"
  echo "  ./start.sh setup                    # 初始化开发环境"
  echo "  ./start.sh setup --cn               # 使用中国镜像源初始化"
  echo "  ./start.sh run                      # 启动开发服务器"
  echo "  ./start.sh deps install django      # 安装 Django 依赖"
  echo ""
}

# 主函数
main() {
  if [ $# -eq 0 ] || [ "$1" = "help" ]; then
    show_help
    exit 0
  fi
  
  check_python
  check_venv
  
  # 暂时的命令处理逻辑，未来将替换为 Python CLI 调用
  case $1 in
    setup)
      echo "正在初始化开发环境..."
      # TODO: 实现完整的环境设置
      ;;
    run)
      echo "正在启动开发服务器..."
      docker-compose up -d
      echo "服务已启动，前端访问: http://localhost:3000, API访问: http://localhost:5000"
      ;;
    stop)
      echo "正在停止服务..."
      docker-compose down
      echo "服务已停止"
      ;;
    status)
      echo "服务状态:"
      docker-compose ps
      ;;
    logs)
      echo "查看服务日志:"
      docker-compose logs -f
      ;;
    restart)
      echo "正在重启服务..."
      docker-compose restart
      echo "服务已重启"
      ;;
    deps)
      echo "依赖管理功能尚未实现，敬请期待!"
      # TODO: 实现依赖管理功能
      ;;
    sources)
      echo "源管理功能尚未实现，敬请期待!"
      # TODO: 实现源管理功能
      ;;
    *)
      echo "未知命令: $1"
      echo "运行 './start.sh help' 获取帮助"
      exit 1
      ;;
  esac
}

# 执行主函数
main "$@"