$project = $PSScriptRoot
$pythonw = "C:\venvs\audio-visualizer\Scripts\pythonw.exe"

if (-not (Test-Path $pythonw)) {
    Write-Error "Venv not found at $pythonw. Build it first."
    exit 1
}

$startup = [Environment]::GetFolderPath("Startup")
$shortcut = Join-Path $startup "Audio Visualizer.lnk"

$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcut)
$link.TargetPath = $pythonw
$link.Arguments = "`"$project\main.py`""
$link.WorkingDirectory = $project
$link.Save()

Write-Host "Startup shortcut created: $shortcut"