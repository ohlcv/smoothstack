title Cursor IDE 缓存清理工具
color 0A

echo ====================================================
echo            Cursor IDE 缓存清理工具
echo ====================================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 此脚本需要管理员权限运行。
    echo 请右键点击脚本并选择"以管理员身份运行"。
    echo.
    pause
    exit /b 1
)

echo 此脚本将清理 Cursor IDE 的缓存文件以提高性能。
echo 请在继续之前关闭 Cursor IDE。
echo.
set /p continue=Cursor IDE 已关闭了吗? (Y/N): 
if /i "%continue%" neq "Y" (
    echo 操作已取消。请关闭 Cursor IDE 然后重试。
    pause
    exit /b 0
)

echo.
echo 正在清理 Cursor 缓存文件...
echo.

:: 定义可能存储 Cursor 缓存的路径
set APPDATA_PATH=%APPDATA%\Cursor
set LOCALAPPDATA_PATH=%LOCALAPPDATA%\Cursor
set CODE_CACHE_PATH=%USERPROFILE%\.vscode-cursor
set EXTENSION_PATH=%USERPROFILE%\.cursor

:: 清理 AppData\Roaming\Cursor
if exist "%APPDATA_PATH%" (
    echo 清理 %APPDATA_PATH%\Cache
    if exist "%APPDATA_PATH%\Cache" (
        rd /s /q "%APPDATA_PATH%\Cache"
        mkdir "%APPDATA_PATH%\Cache"
    )
    
    echo 清理 %APPDATA_PATH%\Code Cache
    if exist "%APPDATA_PATH%\Code Cache" (
        rd /s /q "%APPDATA_PATH%\Code Cache"
        mkdir "%APPDATA_PATH%\Code Cache"
    )
    
    echo 清理 %APPDATA_PATH%\GPUCache
    if exist "%APPDATA_PATH%\GPUCache" (
        rd /s /q "%APPDATA_PATH%\GPUCache"
        mkdir "%APPDATA_PATH%\GPUCache"
    )
)

:: 清理 AppData\Local\Cursor
if exist "%LOCALAPPDATA_PATH%" (
    echo 清理 %LOCALAPPDATA_PATH%\Cache
    if exist "%LOCALAPPDATA_PATH%\Cache" (
        rd /s /q "%LOCALAPPDATA_PATH%\Cache"
        mkdir "%LOCALAPPDATA_PATH%\Cache"
    )
    
    echo 清理 %LOCALAPPDATA_PATH%\Code Cache
    if exist "%LOCALAPPDATA_PATH%\Code Cache" (
        rd /s /q "%LOCALAPPDATA_PATH%\Code Cache"
        mkdir "%LOCALAPPDATA_PATH%\Code Cache"
    )
    
    echo 清理 %LOCALAPPDATA_PATH%\GPUCache
    if exist "%LOCALAPPDATA_PATH%\GPUCache" (
        rd /s /q "%LOCALAPPDATA_PATH%\GPUCache"
        mkdir "%LOCALAPPDATA_PATH%\GPUCache"
    )
)

:: 清理 .vscode-cursor 代码缓存
if exist "%CODE_CACHE_PATH%" (
    echo 清理 %CODE_CACHE_PATH%\Cache
    if exist "%CODE_CACHE_PATH%\Cache" (
        rd /s /q "%CODE_CACHE_PATH%\Cache"
        mkdir "%CODE_CACHE_PATH%\Cache"
    )
    
    echo 清理 %CODE_CACHE_PATH%\CachedData
    if exist "%CODE_CACHE_PATH%\CachedData" (
        rd /s /q "%CODE_CACHE_PATH%\CachedData"
        mkdir "%CODE_CACHE_PATH%\CachedData"
    )
    
    echo 清理 %CODE_CACHE_PATH%\GPUCache
    if exist "%CODE_CACHE_PATH%\GPUCache" (
        rd /s /q "%CODE_CACHE_PATH%\GPUCache"
        mkdir "%CODE_CACHE_PATH%\GPUCache"
    )
    
    echo 清理 %CODE_CACHE_PATH%\logs
    if exist "%CODE_CACHE_PATH%\logs" (
        rd /s /q "%CODE_CACHE_PATH%\logs"
        mkdir "%CODE_CACHE_PATH%\logs"
    )
    
    echo 清理代码存储
    if exist "%CODE_CACHE_PATH%\User\workspaceStorage" (
        rd /s /q "%CODE_CACHE_PATH%\User\workspaceStorage"
        mkdir "%CODE_CACHE_PATH%\User\workspaceStorage"
    )
)

:: 清理扩展临时数据
if exist "%EXTENSION_PATH%" (
    echo 清理 %EXTENSION_PATH%\caches
    if exist "%EXTENSION_PATH%\caches" (
        rd /s /q "%EXTENSION_PATH%\caches"
        mkdir "%EXTENSION_PATH%\caches"
    )
)

:: 清理可能与 Cursor 相关的 Windows 临时文件
echo 清理与 Cursor 相关的 Windows 临时文件...
del /f /s /q "%TEMP%\Cursor*.*" >nul 2>&1

echo.
echo ====================================================
echo               清理完成！
echo ====================================================
echo.
echo 所有 Cursor 缓存文件已成功清理。
echo 现在您可以重新启动 Cursor 以获得更好的性能。
echo.
echo 注意: 清理缓存后，Cursor 首次启动可能需要较长时间
echo       这是因为它需要重建必要的文件，属于正常现象。
echo.

pause
exit /b 0