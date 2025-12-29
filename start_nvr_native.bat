@echo off
echo =================================
echo INICIANDO MONITOR NVR (NATIVO + PYTHON)
echo =================================
echo.

echo 1. Preparando pastas...
if not exist "go2rtc_bin\storage" mkdir "go2rtc_bin\storage"

echo.
echo 2. Iniciando Go2RTC (Core)...
cd "%~dp0\go2rtc_bin"
set "PATH=%PATH%;%CD%"
start "Go2RTC Core" go2rtc.exe -config go2rtc.yaml

echo.
echo 3. Aguardando Go2RTC subir (5s)...
timeout /t 5 >nul

echo.
echo 4. Iniciando Gravador Python...
start "Indexador DB" /min python indexer.py
start "NVR API Web" /min python nvr_api_new.py
python recorder.py

pause
