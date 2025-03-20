# Bash completion script for Smoothstack CLI
# To use this script, add the following line to your .bashrc:
# source /path/to/smoothstack-completion.bash

_smoothstack_completion() {
    local cur prev words cword
    _init_completion || return

    # List of all commands
    local commands="help init config service test lint build dev"

    # List of options for each command
    local help_opts=""
    local init_opts="--template --python-version --node-version --docker --no-docker --git --no-git --force"
    local config_opts="--list --unset"
    local service_opts="--name --detach"
    local test_opts="--watch --coverage"
    local lint_opts="--fix"
    local build_opts="--mode --output"
    local dev_opts="--port --host"

    # List of values for specific options
    local templates="basic fullstack minimal"
    local types="frontend backend all"

    # Handle command completion
    if [ $cword -eq 1 ]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    # Get the command
    local cmd=${words[1]}

    # Handle option completion for each command
    case "$cmd" in
        help)
            # Complete with command names
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
        init)
            case "$prev" in
                --template|-t)
                    # Complete with template names
                    COMPREPLY=($(compgen -W "$templates" -- "$cur"))
                    ;;
                --python-version)
                    # Complete with Python versions
                    COMPREPLY=($(compgen -W "3.8 3.9 3.10 3.11" -- "$cur"))
                    ;;
                --node-version)
                    # Complete with Node.js versions
                    COMPREPLY=($(compgen -W "14 16 18 20" -- "$cur"))
                    ;;
                *)
                    # Complete with options
                    COMPREPLY=($(compgen -W "$init_opts" -- "$cur"))
                    ;;
            esac
            ;;
        config)
            case "$prev" in
                config)
                    # Complete with config keys
                    local keys=$(smoothstack config --list 2>/dev/null | cut -d= -f1)
                    COMPREPLY=($(compgen -W "$keys" -- "$cur"))
                    ;;
                *)
                    # Complete with options
                    COMPREPLY=($(compgen -W "$config_opts" -- "$cur"))
                    ;;
            esac
            ;;
        service)
            case "$prev" in
                service)
                    # Complete with service commands
                    COMPREPLY=($(compgen -W "start stop restart status" -- "$cur"))
                    ;;
                --name|-n)
                    # Complete with service names
                    local services=$(smoothstack service list 2>/dev/null)
                    COMPREPLY=($(compgen -W "$services" -- "$cur"))
                    ;;
                *)
                    # Complete with options
                    COMPREPLY=($(compgen -W "$service_opts" -- "$cur"))
                    ;;
            esac
            ;;
        test|lint|build|dev)
            case "$prev" in
                "$cmd")
                    # Complete with component types
                    COMPREPLY=($(compgen -W "$types" -- "$cur"))
                    ;;
                *)
                    # Complete with command-specific options
                    local var_name="${cmd}_opts"
                    local opts=${!var_name}
                    COMPREPLY=($(compgen -W "$opts" -- "$cur"))
                    ;;
            esac
            ;;
    esac
}

# Register the completion function
complete -F _smoothstack_completion smoothstack 