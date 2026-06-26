@echo off
chcp 65001 >nul
REM ============================================
REM WeChat Daily - Windows Scheduled Task Setup
REM Right-click -> Run as Administrator
REM ============================================

echo.
echo =============================================
echo   WeChat Daily - Install Scheduled Task
echo =============================================
echo.

set "PROJECT_DIR=%~dp0"

REM Use venv Python if available, otherwise fall back to system Python
set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" set "VENV_PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    set "PYTHON_PATH=%VENV_PYTHON%"
    echo Python: venv ^(%VENV_PYTHON%^)
) else (
    set "PYTHON_PATH=python"
    echo Python: system python
)

"%PYTHON_PATH%" --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found.
    echo Please install Python or run setup_win11.bat from the repository root.
    pause
    exit /b 1
)

echo Project dir: %PROJECT_DIR%
echo.

set "CONFIG_PATH=%PROJECT_DIR%config.yaml"
if exist "%PROJECT_DIR%config.local.yaml" set "CONFIG_PATH=%PROJECT_DIR%config.local.yaml"
echo Config: %CONFIG_PATH%
echo.

if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

echo Creating run script...
(
echo @echo off
echo chcp 65001 ^>nul
echo set PYTHONUTF8=1
echo set PYTHONIOENCODING=utf-8
echo cd /d "%PROJECT_DIR%"
echo echo [%%date%% %%time%%] Start WeChat Daily ^>^> logs\scheduler.log
echo "%PYTHON_PATH%" "%PROJECT_DIR%run_group_daily_pipeline.py" --config "%CONFIG_PATH%" ^>^> logs\scheduler.log 2^>^&1
echo echo [%%date%% %%time%%] Done ^>^> logs\scheduler.log
) > "%PROJECT_DIR%run_daily.bat"

echo Run script created: %PROJECT_DIR%run_daily.bat
echo.

echo Creating scheduled task...
echo Task name: WeChatDaily
echo Run time: Daily 23:00
echo.

schtasks /create /tn "WeChatDaily" /tr "\"%PROJECT_DIR%run_daily.bat\"" /sc daily /st 23:00 /f

if errorlevel 1 (
    echo.
    echo [Error] Failed to create scheduled task.
    echo Please run this script as Administrator.
    pause
    exit /b 1
)

echo.
echo =============================================
echo   Done!
echo =============================================
echo.
echo Scheduled task created. Runs daily at 23:00.
echo.
echo Management commands:
echo   View:   schtasks /query /tn "WeChatDaily"
echo   Run:    schtasks /run /tn "WeChatDaily"
echo   Delete: schtasks /delete /tn "WeChatDaily" /f
echo   Change: schtasks /change /tn "WeChatDaily" /st 22:00
echo.
echo Log file: %PROJECT_DIR%logs\scheduler.log
echo.

pause
