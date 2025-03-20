:FIX_ALL
echo.
echo Setting system-wide UTF-8 encoding...

:: 设置非Unicode程序的区域设置为UTF-8（而不是GBK 936）
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v ACP /t REG_SZ /d 65001 /f
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage" /v OEMCP /t REG_SZ /d 65001 /f

:: 应用CMD和Python的修复
call :FIX_CMD
call :FIX_PYTHON

echo.
echo System-wide encoding settings updated.
echo You need to RESTART YOUR COMPUTER for these changes to take effect.
echo.
pause
goto MENU