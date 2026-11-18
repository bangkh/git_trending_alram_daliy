$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (!(Test-Path $python)) { throw 'Run install.ps1 first.' }
$action = New-ScheduledTaskAction -Execute $python -Argument ('"' + (Join-Path $PSScriptRoot 'agent.py') + '" serve') -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'GitHubTrendingPersonalAgent' -Action $action -Trigger $trigger -Settings $settings -Description 'Daily Trending digest and Telegram preference feedback' -Force | Out-Null
Start-ScheduledTask -TaskName 'GitHubTrendingPersonalAgent'
Write-Host 'Registered and started. Do not also run start.bat.'
