@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "DEFAULT_CONFIG=%SCRIPT_DIR%config.yaml"
if exist "%SCRIPT_DIR%config.local.yaml" set "DEFAULT_CONFIG=%SCRIPT_DIR%config.local.yaml"

set "CONFIG_PATH=%DEFAULT_CONFIG%"
set "EXTRA_ARGS="

if "%~1"=="" goto run_pipeline

set "FIRST_ARG=%~1"
if "%FIRST_ARG%"=="--config" (
    set "EXTRA_ARGS=%*"
    goto run_pipeline
) else if "%FIRST_ARG%"=="-c" (
    set "EXTRA_ARGS=%*"
    goto run_pipeline
) else if "%FIRST_ARG:~0,2%"=="--" (
    goto collect_extra_args
) else (
    set "CONFIG_PATH=%~1"
    shift /1
)

:collect_extra_args
if "%~1"=="" goto run_pipeline
set "EXTRA_ARGS=!EXTRA_ARGS! "^"%~1^""
shift /1
goto collect_extra_args

:run_pipeline
set "PYTHON_PATH=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_PATH%" set "PYTHON_PATH=%SCRIPT_DIR%venv\Scripts\python.exe"
if not exist "%PYTHON_PATH%" set "PYTHON_PATH=python"

"%PYTHON_PATH%" --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found.
    echo Run setup_win11.bat from the repository root, or install Python 3.12+.
    exit /b 1
)

echo [run_group_daily] using config: %CONFIG_PATH%

pushd "%SCRIPT_DIR%" >nul
"%PYTHON_PATH%" "%SCRIPT_DIR%run_group_daily_pipeline.py" --config "%CONFIG_PATH%" !EXTRA_ARGS!
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul

exit /b %EXIT_CODE%
