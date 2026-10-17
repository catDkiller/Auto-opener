$ws = New-Object -ComObject WScript.Shell

# Find a Python interpreter (prefer pythonw.exe = no console window)
$candidates = @()
if (Get-Command pythonw -ErrorAction SilentlyContinue) { $candidates += (Get-Command pythonw).Source }
if (Get-Command python   -ErrorAction SilentlyContinue) { $candidates += (Get-Command python).Source }
$candidates += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Recurse -Filter pythonw.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName

$appDir    = $PSScriptRoot
$scriptPy  = Join-Path $appDir 'launcher.pyw'
$iconFile  = Join-Path $appDir 'launcher.ico'
$appsFile  = Join-Path $appDir 'apps.txt'

if (-not (Test-Path $appsFile)) {
    # starter list so the very first click does something friendly
    @(
        '# TaskBar Launcher apps list',
        '[My Apps]',
        'https://www.google.com'
    ) | Set-Content -Path $appsFile -Encoding UTF8
}

if (-not (Test-Path $iconFile)) {
    # generate the built-in icon using the launcher code itself
    if ($candidates.Count -gt 0) {
        & $candidates[0] -c "import base64,io; p=r'$iconFile'; open(p,'wb').write(base64.b64decode(open(r'$scriptPy',encoding='utf-8').read().split('LAUNCHER_ICON_B64 = (')[1].split(')')[0].replace('\n','').replace('\"','')))" 2>$null
    }
}

foreach ($folder in @([Environment]::GetFolderPath('Desktop'),
                      (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))) {
    if (-not (Test-Path $folder)) { continue }
    $sc = $ws.CreateShortcut((Join-Path $folder 'TaskBar Launcher.lnk'))
    if ($candidates.Count -gt 0) {
        $sc.TargetPath      = $candidates[0]
        $sc.Arguments       = "`"$scriptPy`""
    } else {
        # No Python found -> fall back to the batch file launcher
        $sc.TargetPath      = Join-Path $appDir 'My Launcher.bat'
        $sc.Arguments       = ''
    }
    $sc.WorkingDirectory = $appDir
    if (Test-Path $iconFile) { $sc.IconLocation = $iconFile }
    $sc.Description = 'Opens all my favorite apps in one click'
    $sc.Save()
    Write-Host "Created: $(Join-Path $folder 'TaskBar Launcher.lnk')"
}

Write-Host ''
Write-Host '  Done! A shortcut called "TaskBar Launcher" is now on your Desktop.'
Write-Host ''
Write-Host '  To put it on the taskbar:'
Write-Host '    1. Right-click the TaskBar Launcher icon on your Desktop'
Write-Host '    2. Choose  Show more options  ->  Pin to taskbar'
Write-Host ''
Write-Host '  From now on, ONE click on that button opens all your apps.'
Write-Host '  Want to change them? Double-click  Edit My Apps.bat'
Write-Host ''

try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    explorer.exe "/select,$desktop\TaskBar Launcher.lnk"
} catch {}

Read-Host 'Press Enter to close'
