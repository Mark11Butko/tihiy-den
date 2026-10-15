param([string]$SkinName = 'TihiyDen')
$ErrorActionPreference = 'Stop'
$rm = @('C:\Program Files\Rainmeter\Rainmeter.exe','C:\Program Files (x86)\Rainmeter\Rainmeter.exe') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $rm) { throw 'Rainmeter is not installed' }
if (-not (Get-Process Rainmeter -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $rm -WorkingDirectory (Split-Path $rm) -WindowStyle Hidden
    Start-Sleep -Seconds 5
}
& $rm '!ActivateConfig' $SkinName "$SkinName.ini"
& $rm '!Show' $SkinName
& $rm '!ZPos' '-2' $SkinName
