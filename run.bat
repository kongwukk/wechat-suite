@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

call "%SCRIPT_DIR%wechat-daily\run_group_daily.bat" %*
exit /b %ERRORLEVEL%
