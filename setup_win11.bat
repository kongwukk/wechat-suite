@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT_DIR=%~dp0"

echo ========================================
echo   WeChat Suite - Windows 11 Setup
echo ========================================
echo.

call :find_python
if errorlevel 1 exit /b 1

call :setup_project "%ROOT_DIR%wechat-decrypt"
if errorlevel 1 exit /b 1

call :setup_project "%ROOT_DIR%wechat-daily"
if errorlevel 1 exit /b 1

echo.
echo ========================================
echo   Setup complete
echo ========================================
echo.
echo Next steps:
echo   1. Copy wechat-decrypt\config.example.json to wechat-decrypt\config.json if needed.
echo   2. Copy wechat-daily\config.yaml.example to wechat-daily\config.local.yaml.
echo   3. Fill in API keys and group_daily.chat_name.
echo   4. Run run.bat from this directory.
echo.
pause
exit /b 0

:find_python
where py >nul 2>&1
if not errorlevel 1 (
    py -3.12 --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3.12"
        call :print_python_version
        exit /b 0
    )
    set "PYTHON_CMD=py -3"
    call :check_python_version
    if not errorlevel 1 (
        call :print_python_version
        exit /b 0
    )
)

:find_python_exe
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    call :check_python_version
    if not errorlevel 1 (
        call :print_python_version
        exit /b 0
    )
)

echo [Error] Python 3.12 or newer was not found.
echo Please install Python 3.12 or newer, then run this script again.
exit /b 1

:check_python_version
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
exit /b %ERRORLEVEL%

:print_python_version
%PYTHON_CMD% --version
exit /b 0

:setup_project
set "PROJECT_DIR=%~1"
set "VENV_PY=%PROJECT_DIR%\.venv\Scripts\python.exe"

echo.
echo [setup] %PROJECT_DIR%

if not exist "%VENV_PY%" (
    echo [setup] Creating .venv...
    pushd "%PROJECT_DIR%" >nul
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        popd >nul
        echo [Error] Failed to create virtual environment.
        exit /b 1
    )
    popd >nul
)

"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%VENV_PY%" -m pip install -r "%PROJECT_DIR%\requirements.txt"
if errorlevel 1 exit /b 1

exit /b 0
