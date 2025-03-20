# PowerShell completion script for Smoothstack CLI
# To use this script, add the following line to your PowerShell profile:
# Import-Module path/to/smoothstack-completion.ps1

using namespace System.Management.Automation
using namespace System.Management.Automation.Language

Register-ArgumentCompleter -Native -CommandName smoothstack -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    # Get the command line up to the cursor position
    $commandLine = $commandAst.ToString()
    $commandParts = $commandLine.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
    $currentWord = $wordToComplete

    # Define commands and their descriptions
    $commands = @{
        'help'    = '显示帮助信息'
        'init'    = '初始化新项目'
        'config'  = '管理配置'
        'service' = '管理服务'
        'test'    = '运行测试'
        'lint'    = '代码检查'
        'build'   = '构建项目'
        'dev'     = '启动开发服务器'
    }

    # Define options for each command
    $commandOptions = @{
        'init'    = @(
            '--template', '-t'
            '--python-version'
            '--node-version'
            '--docker'
            '--no-docker'
            '--git'
            '--no-git'
            '--force', '-f'
        )
        'config'  = @(
            '--list', '-l'
            '--unset', '-u'
        )
        'service' = @(
            '--name', '-n'
            '--detach', '-d'
        )
        'test'    = @(
            '--watch', '-w'
            '--coverage', '-c'
        )
        'lint'    = @(
            '--fix', '-f'
        )
        'build'   = @(
            '--mode'
            '--output', '-o'
        )
        'dev'     = @(
            '--port', '-p'
            '--host', '-h'
        )
    }

    # Define option values
    $optionValues = @{
        '--template'       = @('basic', 'fullstack', 'minimal')
        '--python-version' = @('3.8', '3.9', '3.10', '3.11')
        '--node-version'   = @('14', '16', '18', '20')
        '--mode'          = @('development', 'production')
        'type'            = @('frontend', 'backend', 'all')
    }

    # If no command is specified yet, complete with commands
    if ($commandParts.Count -eq 1) {
        return $commands.Keys | Where-Object {
            $_ -like "$currentWord*"
        } | ForEach-Object {
            [CompletionResult]::new($_, $_, [CompletionResultType]::ParameterValue, $commands[$_])
        }
    }

    # Get the current command
    $command = $commandParts[1]

    # If completing a command's options
    if ($command -in $commandOptions.Keys) {
        # If the current word starts with '-', complete with options
        if ($currentWord -like '-*') {
            return $commandOptions[$command] | Where-Object {
                $_ -like "$currentWord*"
            } | ForEach-Object {
                [CompletionResult]::new($_, $_, [CompletionResultType]::ParameterValue, $_)
            }
        }

        # If the previous word is an option that has specific values
        $prevWord = $commandParts[-2]
        if ($prevWord -in $optionValues.Keys) {
            return $optionValues[$prevWord] | Where-Object {
                $_ -like "$currentWord*"
            } | ForEach-Object {
                [CompletionResult]::new($_, $_, [CompletionResultType]::ParameterValue, $_)
            }
        }

        # For commands that require a type parameter
        if ($command -in @('test', 'lint', 'build', 'dev') -and $commandParts.Count -eq 2) {
            return $optionValues['type'] | Where-Object {
                $_ -like "$currentWord*"
            } | ForEach-Object {
                [CompletionResult]::new($_, $_, [CompletionResultType]::ParameterValue, $_)
            }
        }

        # Special handling for service command
        if ($command -eq 'service' -and $commandParts.Count -eq 2) {
            $serviceCommands = @('start', 'stop', 'restart', 'status')
            return $serviceCommands | Where-Object {
                $_ -like "$currentWord*"
            } | ForEach-Object {
                [CompletionResult]::new($_, $_, [CompletionResultType]::ParameterValue, $_)
            }
        }
    }

    # If completing help command topics
    if ($command -eq 'help' -and $commandParts.Count -eq 2) {
        return $commands.Keys | Where-Object {
            $_ -like "$currentWord*"
        } | ForEach-Object {
            [CompletionResult]::new($_, $_, [CompletionResultType]::ParameterValue, $commands[$_])
        }
    }
} 