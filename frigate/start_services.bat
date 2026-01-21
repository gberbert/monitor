@echo off
echo =================================
echo INICIANDO SISTEMA HIBRIDO NVR
echo =================================
echo.

echo 1. Iniciando Go2RTC (Ponte Windows -> Cameras)...
cd "%~dp0\..\go2rtc_bin"
:: Adicionar pasta atual (ffmpeg) ao PATH para o comando 'exec:ffmpeg' funcionar
set "PATH=%PATH%;%CD%"
start "Go2RTC Bridge" go2rtc.exe -config go2rtc.yaml

echo.
echo 2. Iniciando Frigate (Docker)...
cd "%~dp0"
call run_frigate.bat
