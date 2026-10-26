Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -like "*audio-visualizer*main.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId }