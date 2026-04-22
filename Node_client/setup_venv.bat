@echo off
setlocal

set "ROOT=%~dp0"
set "VENV_NAME=.venv"
set "VENV_PATH=%ROOT%%VENV_NAME%"

echo Creating node client virtual environment at %VENV_PATH%
python -m venv "%VENV_PATH%"
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
