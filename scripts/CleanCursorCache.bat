setlocal enabledelayedexpansion

echo ======================================================
echo            Cursor缓存清理工具
echo ======================================================
echo.

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 请以管理员权限运行此脚本！
    echo 右键点击此批处理文件，选择"以管理员身份运行"。
    echo.
    pause
    exit /b 1
)

:: 确保Cursor已关闭
tasklist | findstr /i "cursor.exe" >nul
if %errorlevel% equ 0 (
    echo 检测到Cursor正在运行。
    echo 请先关闭Cursor应用程序，然后再继续。
    echo.
    pause
    exit /b 1
)

:: 设置缓存路径
set "APPDATA_PATH=%APPDATA%\Cursor"
set "LOCALAPPDATA_PATH=%LOCALAPPDATA%\Cursor"
set "USER_DATA_PATH=%LOCALAPPDATA%\Cursor\User Data"

echo 正在清理Cursor缓存文件...
echo.

:: 清理AppData目录中的缓存
if exist "%APPDATA_PATH%" (
    echo 清理 %APPDATA_PATH%\Cache ...
    if exist "%APPDATA_PATH%\Cache" rd /s /q "%APPDATA_PATH%\Cache"
    
    echo 清理 %APPDATA_PATH%\Code Cache ...
    if exist "%APPDATA_PATH%\Code Cache" rd /s /q "%APPDATA_PATH%\Code Cache"
    
    echo 清理 %APPDATA_PATH%\GPUCache ...
    if exist "%APPDATA_PATH%\GPUCache" rd /s /q "%APPDATA_PATH%\GPUCache"
)

:: 清理LocalAppData目录中的缓存
if exist "%USER_DATA_PATH%" (
    echo 清理 %USER_DATA_PATH%\Cache ...
    if exist "%USER_DATA_PATH%\Cache" rd /s /q "%USER_DATA_PATH%\Cache"
    
    echo 清理 %USER_DATA_PATH%\Code Cache ...
    if exist "%USER_DATA_PATH%\Code Cache" rd /s /q "%USER_DATA_PATH%\Code Cache"
    
    echo 清理 %USER_DATA_PATH%\GPUCache ...
    if exist "%USER_DATA_PATH%\GPUCache" rd /s /q "%USER_DATA_PATH%\GPUCache"
    
    echo 清理 %USER_DATA_PATH%\Storage ...
    if exist "%USER_DATA_PATH%\Storage" rd /s /q "%USER_DATA_PATH%\Storage"
    
    echo 清理 %USER_DATA_PATH%\blob_storage ...
    if exist "%USER_DATA_PATH%\blob_storage" rd /s /q "%USER_DATA_PATH%\blob_storage"
    
    :: 清理Default目录下的缓存
    if exist "%USER_DATA_PATH%\Default" (
        echo 清理 %USER_DATA_PATH%\Default\Cache ...
        if exist "%USER_DATA_PATH%\Default\Cache" rd /s /q "%USER_DATA_PATH%\Default\Cache"
        
        echo 清理 %USER_DATA_PATH%\Default\Code Cache ...
        if exist "%USER_DATA_PATH%\Default\Code Cache" rd /s /q "%USER_DATA_PATH%\Default\Code Cache"
        
        echo 清理 %USER_DATA_PATH%\Default\GPUCache ...
        if exist "%USER_DATA_PATH%\Default\GPUCache" rd /s /q "%USER_DATA_PATH%\Default\GPUCache"
        
        echo 清理 %USER_DATA_PATH%\Default\IndexedDB ...
        if exist "%USER_DATA_PATH%\Default\IndexedDB" rd /s /q "%USER_DATA_PATH%\Default\IndexedDB"
        
        echo 清理 %USER_DATA_PATH%\Default\Local Storage ...
        if exist "%USER_DATA_PATH%\Default\Local Storage" rd /s /q "%USER_DATA_PATH%\Default\Local Storage"
    )
)

echo.
echo ======================================================
echo            清理完成！
echo ======================================================
echo.
echo Cursor缓存文件已被清理。
echo 现在Cursor应该能够更流畅地运行了。
echo.
pause