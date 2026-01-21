@echo off
echo =================================
echo INICIANDO SISTEMA COMPLETO (VMS + NVR)
echo =================================
echo.

echo 1. Sincronizando Configuracoes...
python sync_cameras_to_web.py

echo.
echo 2. Preparando pastas NVR...
if not exist "go2rtc_bin\storage" mkdir "go2rtc_bin\storage"

echo.
echo 3. Iniciando Go2RTC (Core)...
cd "%~dp0\go2rtc_bin"
set "PATH=%PATH%;%CD%"
start "Go2RTC Core" go2rtc.exe -config go2rtc.yaml

echo.
echo 4. Aguardando Go2RTC subir (5s)...
timeout /t 5 >nul

echo.
echo 5. Iniciando Backend VMS (Porta 5000)...
cd "%~dp0"
start "VMS Proxy Main" /min python vms_proxy.py

echo.
echo 6. Iniciando NVR Services (Gravador, Indexador, API)...
start "Indexador DB" /min python indexer.py
start "NVR API Web" /min python nvr_api_new.py
:: Recorder roda na janela principal para feedback
echo Inciando Gravador (Python Recorder)...
python go2rtc_bin\recorder.py

pause
