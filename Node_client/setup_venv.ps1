param(
    [string]$VenvName = ".venv"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root $VenvName

function Get-PythonLauncher {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3", "-m", "venv")
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python", "-m", "venv")
    }

    throw "Python 3 was not found. Install Python 3.12+ and make sure either 'py' or 'python' works in PowerShell."
}

$pythonCmd = Get-PythonLauncher

Write-Host "Creating node client virtual environment at $venvPath"
& $pythonCmd[0] $pythonCmd[1] $pythonCmd[2] $pythonCmd[3] $venvPath

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment creation failed. Expected python not found at $venvPython"
}

Write-Host "Installing node client dependencies"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")

Write-Host ""
Write-Host "Node client environment is ready."
Write-Host "Activate it with:"
Write-Host "  .\$VenvName\Scripts\Activate.ps1"
Write-Host "Then run:"
Write-Host "  python node_ui.py"
