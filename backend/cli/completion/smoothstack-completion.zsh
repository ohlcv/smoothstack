#compdef smoothstack

# Zsh completion script for Smoothstack CLI
# To use this script, add the following line to your .zshrc:
# fpath=(path/to/smoothstack/completion $fpath)
# autoload -Uz compinit && compinit

_smoothstack() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    # Define commands and their descriptions
    local -a commands
    commands=(
        'help:显示帮助信息'
        'init:初始化新项目'
        'config:管理配置'
        'service:管理服务'
        'test:运行测试'
        'lint:代码检查'
        'build:构建项目'
        'dev:启动开发服务器'
    )

    # Define common options
    local -a common_opts
    common_opts=(
        '(-h --help)'{-h,--help}'[显示帮助信息]'
        '(-v --version)'{-v,--version}'[显示版本信息]'
    )

    # Define command-specific options
    local -a init_opts config_opts service_opts test_opts lint_opts build_opts dev_opts
    init_opts=(
        '(-t --template)'{-t,--template}'[项目模板]:template:(basic fullstack minimal)'
        '--python-version[Python版本]:version:(3.8 3.9 3.10 3.11)'
        '--node-version[Node.js版本]:version:(14 16 18 20)'
        '(--docker --no-docker)--docker[添加Docker支持]'
        '(--docker --no-docker)--no-docker[不添加Docker支持]'
        '(--git --no-git)--git[初始化Git仓库]'
        '(--git --no-git)--no-git[不初始化Git仓库]'
        '(-f --force)'{-f,--force}'[强制覆盖已存在的目录]'
    )

    config_opts=(
        '(-l --list)'{-l,--list}'[列出所有配置]'
        '(-u --unset)'{-u,--unset}'[删除配置项]'
    )

    service_opts=(
        '(-n --name)'{-n,--name}'[服务名称]:name:->service_names'
        '(-d --detach)'{-d,--detach}'[后台运行]'
    )

    test_opts=(
        '(-w --watch)'{-w,--watch}'[监视模式]'
        '(-c --coverage)'{-c,--coverage}'[生成覆盖率报告]'
        ':type:(frontend backend all)'
    )

    lint_opts=(
        '(-f --fix)'{-f,--fix}'[自动修复问题]'
        ':type:(frontend backend all)'
    )

    build_opts=(
        '--mode[构建模式]:mode:(development production)'
        '(-o --output)'{-o,--output}'[输出目录]:directory:_files -/'
        ':type:(frontend backend all)'
    )

    dev_opts=(
        '(-p --port)'{-p,--port}'[端口号]:port:'
        '(-h --host)'{-h,--host}'[主机地址]:host:'
        ':type:(frontend backend all)'
    )

    _arguments -C \
        $common_opts \
        ': :->command' \
        '*:: :->option-or-argument'

    case "$state" in
        command)
            _describe -t commands 'command' commands
            ;;
        option-or-argument)
            case "$words[1]" in
                help)
                    _describe -t commands 'command' commands
                    ;;
                init)
                    _arguments $init_opts
                    ;;
                config)
                    _arguments $config_opts \
                        '*:key-value:->config_keys'
                    case "$state" in
                        config_keys)
                            local -a keys
                            keys=( ${(f)"$(smoothstack config --list 2>/dev/null | cut -d= -f1)"} )
                            _describe -t keys 'config key' keys
                            ;;
                    esac
                    ;;
                service)
                    _arguments $service_opts
                    case "$state" in
                        service_names)
                            local -a services
                            services=( ${(f)"$(smoothstack service list 2>/dev/null)"} )
                            _describe -t services 'service' services
                            ;;
                    esac
                    ;;
                test)
                    _arguments $test_opts
                    ;;
                lint)
                    _arguments $lint_opts
                    ;;
                build)
                    _arguments $build_opts
                    ;;
                dev)
                    _arguments $dev_opts
                    ;;
            esac
            ;;
    esac
}

_smoothstack "$@" 