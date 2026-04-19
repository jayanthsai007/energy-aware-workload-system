@echo off
echo Building Node Software Package...

cd /d "%~dp0"

REM Install PyInstaller if not present
..\backend\venv\Scripts\python.exe -m pip install pyinstaller

REM Build the executable using spec file
..\backend\venv\Scripts\pyinstaller NodeSoftware.spec

echo.
echo Build complete! Check dist/ folder for NodeSoftware.exe
echo.
pause