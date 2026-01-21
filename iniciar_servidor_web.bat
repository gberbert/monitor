@echo off
:: ==========================================
:: STARTUP SCRIPT (SYSTEM/SERVICE MODE)
:: ==========================================

:: 1. Navigate to the script folder (absolute path)
cd /d "%~dp0"

:: 2. Ensure Dependencies (Quiet Mode)
pip install flask requests waitress

:: 2.1 Sync Cameras from DB to Config
echo [AUTO] Sincronizando cameras do Banco de Dados...
python sync_cameras_to_web.py

:: 3. Start Go2RTC (Video Backend)
cd /d "%~dp0go2rtc_bin"
:: FIX: Add bin folder to PATH so Go2RTC can find ffmpeg.exe easily
set "PATH=%PATH%;%~dp0go2rtc_bin"
start "" /MIN go2rtc.exe -config go2rtc.yaml

:: Wait a moment for Go2RTC
timeout /t 5 /nobreak >nul

:: 4. Start VMS Proxy (Web Server)
cd /d "%~dp0"
start "" /MIN python vms_proxy.py

:: 4.1 Start NVR Backend (Timeline API - Port 5002)
start "" /MIN python nvr_api_new.py

:: 4.2 Start NVR Services (Recorder + Indexer)
start "NVR Indexer" /MIN python indexer.py
start "NVR Recorder" /D "go2rtc_bin" /MIN python recorder.py

:: Wait a moment for Proxy
timeout /t 3 /nobreak >nul

:: 5. Start Cloudflare Tunnel
:: Using the existing config.yml in the root folder
start "" /MIN cloudflared.exe tunnel --config config.yml run

:: End of script (Processes remain running in background)
exit
