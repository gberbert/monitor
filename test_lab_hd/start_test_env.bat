@echo off
:: ==========================================
:: STARTUP SCRIPT (TEST ENV HD)
:: ==========================================

:: 1. Navigate to the script folder (absolute path)
cd /d "%~dp0"

:: 2. Sync Config (Safe Mode)
echo [TEST] Syncing Test Cameras...
python sync_test.py

:: 3. Start Test Go2RTC (Ports 1985/8556)
echo [TEST] Starting Go2RTC...
start "" /MIN ..\go2rtc_bin\go2rtc.exe -config go2rtc_test.yaml

:: Wait a moment for Go2RTC
timeout /t 5 /nobreak >nul

:: 4. Start Test VMS Proxy (Port 5001)
echo [TEST] Starting VMS Proxy...
start "" /MIN python vms_proxy_test.py

echo.
echo ==================================================
echo      TEST ENVIRONMENT STARTED
echo ==================================================
echo   DASHBOARD: http://localhost:5001/dashboard.html
echo   GO2RTC:    http://localhost:1985
echo ==================================================
pause
exit
