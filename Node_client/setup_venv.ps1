param(
    [string]$VenvName = ".venv"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root $VenvName
$pythonExe = "python"

Write-Host "Creating node client virtual environment at $venvPath"
& $pythonExe -m venv $venvPath

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
