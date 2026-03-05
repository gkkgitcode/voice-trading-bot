# Write-Host "All trading processes stopped."
Write-Host "Stopping MT5 Trading Servers..."

$processes = Get-CimInstance Win32_Process |
Where-Object { $_.CommandLine -like "*trade_api.py*" -or $_.CommandLine -like "*text_bot.py*" }

foreach ($p in $processes) {
    Write-Host "Stopping process ID:" $p.ProcessId
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Closing MT5 terminals..."
taskkill /F /IM terminal64.exe

Write-Host "All trading processes stopped."