@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -like '*streamlit*apk_sampah_suara*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Aplikasi telah dihentikan.
ping -n 3 127.0.0.1 >nul
