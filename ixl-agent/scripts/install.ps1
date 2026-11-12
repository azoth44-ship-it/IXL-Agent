param([Parameter(Mandatory=$true)][string]$Workspace,[string]$Python='python')
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
$venv=Join-Path $Workspace '.venv'
if (-not(Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))) {
 & $Python -m venv $venv
 if ($LASTEXITCODE) {throw 'Use a full Python 3.11+ interpreter.'}
}
& (Join-Path $venv 'Scripts\python.exe') -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE) {throw 'Dependency installation failed'}
Write-Host 'Installed. Use session.py with installed Chrome or --channel msedge. No account login or submission was performed.'
