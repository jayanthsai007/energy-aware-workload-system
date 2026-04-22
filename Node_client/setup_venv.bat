@echo off
setlocal

set "ROOT=%~dp0"
set "VENV_NAME=.venv"
set "VENV_PATH=%ROOT%%VENV_NAME%"
set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo Python 3 was not found. Install Python 3.12+ and make sure either "py" or "python" works in Command Prompt.
    exit /b 1
)

echo Creating node client virtual environment at %VENV_PATH%
%PYTHON_CMD% -m venv "%VENV_PATH%"
if errorlevel 1 exit /b 1

echo Installing node client dependencies
"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%VENV_PATH%\Scripts\python.exe" -m pip install -r "%ROOT%requirements.txt"
if errorlevel 1 exit /b 1

echo.
echo Node client environment is ready.
echo Activate it with:
echo   %VENV_NAME%\Scripts\activate.bat
echo Then run:
echo   python node_ui.py
