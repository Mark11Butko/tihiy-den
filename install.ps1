<#
 Quiet Day / Tihiy Den - installer.
 Usage:  powershell -ExecutionPolicy Bypass -File install.ps1 [-Lang ru|en] [-City Name] [-FxBase RUB|EUR|USD|...]
 Nothing is sent anywhere except public weather/rate APIs. No accounts, no keys.
#>
param(
    [ValidateSet('ru','en','')][string]$Lang = '',
    [string]$City = '',
    [string]$FxBase = '',
    [double]$Scale = 0.9,
    [string]$AppDir = (Join-Path $env:LOCALAPPDATA 'TihiyDen'),
    [string]$SkinName = 'TihiyDen',
    [switch]$NoAutostart,
    [switch]$NoLaunch
)
$ErrorActionPreference = 'Stop'
$src = Join-Path $PSScriptRoot 'src'

function Say($m) { Write-Host "==> $m" -ForegroundColor Cyan }

if (-not $Lang) { $Lang = Read-Host 'Language (ru/en) [ru]'; if (-not $Lang) { $Lang = 'ru' } }
if (-not $City) { $City = Read-Host 'City for weather [Bratislava]'; if (-not $City) { $City = 'Bratislava' } }
if (-not $FxBase) { $FxBase = Read-Host 'Base currency (RUB = Bank of Russia rates; EUR, USD, PLN... = ECB) [EUR]'; if (-not $FxBase) { $FxBase = 'EUR' } }

# 1. Python
Say 'Checking Python'
$py = $null
foreach ($c in 'python', 'py') {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notmatch 'WindowsApps') { $py = $cmd.Source; break }
}
if (-not $py) {
    Say 'Installing Python via winget'
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
    $py = (Get-Command python -ErrorAction Stop).Source
}
& $py -c "import sys; assert sys.version_info >= (3,9)"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.9+ is required' }

# 2. Rainmeter
$rmPaths = @('C:\Program Files\Rainmeter\Rainmeter.exe', 'C:\Program Files (x86)\Rainmeter\Rainmeter.exe')
$rm = $rmPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $rm) {
    Say 'Installing Rainmeter via winget'
    winget install -e --id Rainmeter.Rainmeter --accept-package-agreements --accept-source-agreements
    $rm = $rmPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $rm) { throw 'Rainmeter not found after install' }
    Start-Process $rm; Start-Sleep 6   # first start creates Rainmeter.ini and the Skins folder
}

# 3. Python packages
Say 'Installing Python packages'
& $py -m pip install --user --quiet --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

# 4. Copy program, configure, build
Say "Copying program to $AppDir"
New-Item -ItemType Directory -Force $AppDir | Out-Null
Copy-Item (Join-Path $src '*.py') $AppDir -Force
Push-Location $AppDir
try {
    & $py -X utf8 configure.py --lang $Lang --city $City --base $FxBase --scale $Scale --skin-name $SkinName
    Say 'Building icons and skin'
    & $py -X utf8 build_icons.py
    & $py -X utf8 build_skin.py
    Say 'First data fetch'
    & $py -X utf8 engine.py refresh --force
} finally { Pop-Location }

# 5. Scheduled tasks
if (-not $NoAutostart) {
    Say 'Registering scheduled tasks (refresh every minute, Rainmeter at logon)'
    $pyw = Join-Path (Split-Path $py) 'pythonw.exe'
    if (-not (Test-Path $pyw)) { $pyw = $py }
    $set = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
    $act = New-ScheduledTaskAction -Execute $pyw -Argument ('"{0}" refresh' -f (Join-Path $AppDir 'engine.py')) -WorkingDirectory $AppDir
    $trg = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName "$SkinName Refresh" -Action $act -Trigger $trg -Settings $set -Force | Out-Null
    $act2 = New-ScheduledTaskAction -Execute $rm
    $trg2 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $trg2.Delay = 'PT15S'
    Register-ScheduledTask -TaskName "$SkinName Rainmeter" -Action $act2 -Trigger $trg2 -Settings $set -Force | Out-Null
}

# 6. Activate the skin
if (-not $NoLaunch) {
    Say 'Launching widget'
    if (-not (Get-Process Rainmeter -ErrorAction SilentlyContinue)) { Start-Process $rm; Start-Sleep 5 }
    & $rm '!Refresh' | Out-Null
    Start-Sleep 1
    & $rm '!ActivateConfig' $SkinName "$SkinName.ini"
}
Say 'Done!'
Write-Host ("Config: " + (Join-Path $AppDir 'data\config.json'))
Write-Host ("Google Calendar: put your secret iCal URL into " + (Join-Path $AppDir 'calendars.txt') + " (see README).")
