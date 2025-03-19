#!/bin/bash

# 配置文档生成脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 进入项目根目录
cd "$PROJECT_ROOT" || { echo "无法进入项目根目录: $PROJECT_ROOT"; exit 1; }

# 创建文档目录（如果不存在）
DOCS_DIR="$PROJECT_ROOT/docs/配置文档"
mkdir -p "$DOCS_DIR"

# 默认选项
FORMAT="markdown"
OUTPUT_FILE="$DOCS_DIR/配置文档.md"
OPEN_DOC=false

# 显示帮助信息
function show_help {
    echo "配置文档生成工具"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --format <format>    指定文档格式 (markdown, html, json, yaml)"
    echo "  -o, --output <file>      指定输出文件路径"
    echo "  -p, --open               生成后打开文档"
    echo "  -h, --help               显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -f html -o docs/配置文档/配置文档.html -p"
    echo "  $0 --format json --output docs/配置文档/config.json"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -p|--open)
            OPEN_DOC=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 根据格式设置默认文件名
if [ -z "$OUTPUT_FILE" ]; then
    case $FORMAT in
        markdown|md)
            OUTPUT_FILE="$DOCS_DIR/配置文档.md"
            ;;
        html|htm)
            OUTPUT_FILE="$DOCS_DIR/配置文档.html"
            ;;
        json)
            OUTPUT_FILE="$DOCS_DIR/config.json"
            ;;
        yaml|yml)
            OUTPUT_FILE="$DOCS_DIR/config.yaml"
            ;;
        *)
            OUTPUT_FILE="$DOCS_DIR/配置文档.$FORMAT"
            ;;
    esac
fi

# 构建命令
CMD="python scripts/generate_config_docs.py --format $FORMAT --output $OUTPUT_FILE"
if [ "$OPEN_DOC" = true ]; then
    CMD="$CMD --open"
fi

# 显示正在执行的操作
echo "生成 $FORMAT 格式的配置文档: $OUTPUT_FILE"

# 执行命令
eval "$CMD"

# 显示结果
if [ $? -eq 0 ]; then
    echo "文档生成成功！"
    echo "文件路径: $OUTPUT_FILE"
else
    echo "文档生成失败！"
fi 