@echo off
setlocal

cd /d "%~dp0"

if not exist dist mkdir dist

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo ERROR: backend\venv\Scripts\python.exe was not found.
  echo Create the virtual environment first or update this script to point to a valid Python.
  exit /b 1
)

"%PYTHON_EXE%" -m ensurepip --upgrade
if errorlevel 1 (
  echo ERROR: Failed to bootstrap pip in the backend virtual environment.
  exit /b 1
)

"%PYTHON_EXE%" -m pip install --upgrade pip pyinstaller
if errorlevel 1 (
  echo ERROR: Failed to install pip or PyInstaller.
  exit /b 1
)

"%PYTHON_EXE%" -m PyInstaller ^
  --onefile ^
  --name EnergyNodeAgent ^
  --add-data "node_config.json;." ^
  node_agent.py
if errorlevel 1 (
  echo ERROR: PyInstaller build failed.
  exit /b 1
)

echo.
echo Build complete. EXE is in backend\dist\EnergyNodeAgent.exe
pause
