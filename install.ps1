$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
py -3 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ installation required.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed.' }
if (!(Test-Path '.env')) { Copy-Item '.env.example' '.env' }
Write-Host 'Edit .env, then run start.bat. See README.md.'
notepad .env
