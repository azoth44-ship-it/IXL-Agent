param([Parameter(Mandatory=$true)][string]$Workspace,[string]$Python)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
$Workspace=(Resolve-Path -LiteralPath $Workspace).Path
$venv=Join-Path $Workspace '.venv'
$venvPython=Join-Path $venv 'Scripts\python.exe'
$probe='import sys, venv; raise SystemExit(sys.version_info < (3, 11))'
function Test-Python([string]$Candidate,[string[]]$Arguments) {
 try {
  if (-not (Get-Command $Candidate -ErrorAction SilentlyContinue)) {return $false}
  & $Candidate @Arguments -c $probe 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
 } catch {return $false}
}
if (-not (Test-Python $venvPython @())) {
 $argsForPython=@()
 if ($Python) {
  if (-not (Test-Python $Python @())) {throw 'The supplied Python is not usable. Provide Python 3.11 or newer.'}
 } elseif (Test-Python 'py' @('-3')) {
  $Python='py'
  $argsForPython=@('-3')
 } else {
  $bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (Test-Python $bundled @()) {$Python=$bundled}
  elseif (Test-Python 'python' @()) {$Python='python'}
  else {throw 'No usable Python 3.11 or newer was found.'}
 }
 # A stale venv can contain binaries for another Python version. Leave it
 # intact and repair into a clean sibling instead.
 if (Test-Path -LiteralPath $venv) {
  $venv=Join-Path $Workspace ('.venv-' + (Get-Date -Format 'yyyyMMddHHmmssfff'))
  $venvPython=Join-Path $venv 'Scripts\python.exe'
 }
 & $Python @argsForPython -m venv $venv
 if ($LASTEXITCODE) {throw 'Could not create the workspace Python environment.'}
}
& $venvPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE) {throw 'Dependency installation failed'}
Write-Output $venvPython
