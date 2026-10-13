param([string]$AppDir = (Join-Path $env:LOCALAPPDATA 'TihiyDen'), [string]$SkinName = 'TihiyDen')
$rmPaths = @('C:\Program Files\Rainmeter\Rainmeter.exe', 'C:\Program Files (x86)\Rainmeter\Rainmeter.exe')
$rm = $rmPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($rm -and (Get-Process Rainmeter -ErrorAction SilentlyContinue)) { & $rm '!DeactivateConfig' $SkinName }
foreach ($t in "$SkinName Refresh", "$SkinName Rainmeter") { Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue }
$ini = Join-Path $env:APPDATA 'Rainmeter\Rainmeter.ini'
$skins = $null
if (Test-Path $ini) { $l = Get-Content $ini | Where-Object { $_ -match '^SkinPath=' } | Select-Object -First 1; if ($l) { $skins = $l.Substring(9).Trim() } }
if (-not $skins) { $skins = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Rainmeter\Skins' }
$sd = Join-Path $skins $SkinName
Add-Type -AssemblyName Microsoft.VisualBasic
foreach ($p in $sd, $AppDir) {
    if (Test-Path $p) { [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($p, 'OnlyErrorDialogs', 'SendToRecycleBin'); Write-Host "Moved to Recycle Bin: $p" }
}
Write-Host 'Uninstalled. Rainmeter itself is left installed.'
