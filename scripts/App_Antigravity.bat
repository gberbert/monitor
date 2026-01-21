@echo off
title Antigravity VMS (Proxy Mode)
color 0B

echo ========================================================
echo   INICIANDO SERVIDOR WEB VMS (MODO PROXY)
echo ========================================================
echo.

:: 1. Garantir Dependencias
echo [0/3] Verificando dependencias Python...
pip install flask requests >nul 2>&1

:: 2. Iniciar Go2RTC (Backend de Video :1984)
echo [1/3] Iniciando Go2RTC (Video)...
:: Usamos modo config limpo
cd /d "%~dp0go2rtc_bin"
set PATH=%PATH%;%~dp0go2rtc_bin
start /MIN "Go2RTC Backend" go2rtc.exe -config go2rtc.yaml

:: Aguardar Go2RTC
timeout /t 3 /nobreak >nul

:: 2.1 Iniciar NVR (Gravador + Indexador + API :5002)
echo [1.5/3] Iniciando Servicos NVR...
cd /d "%~dp0"
start "NVR Indexer" /MIN python indexer.py
start "NVR API" /MIN python nvr_api_new.py
start "NVR Recorder" /D "go2rtc_bin" /MIN python recorder.py

:: 3. Iniciar Proxy (Front+Back Unificados :5000)
echo [2/3] Iniciando Proxy VMS (Site+Video)...
cd /d "%~dp0"
start /MIN "VMS Proxy" python vms_proxy.py

:: Aguardar Proxy
timeout /t 2 /nobreak >nul

:: 4. Iniciar Tunnel (LINK FIXO: cams.osberberts.com)
echo [3/3] Conectando ao Mundo (Cloudflare Tunnel Fixo)...
start /MIN "Cloudflare Tunnel" cloudflared.exe tunnel --config config.yml run

echo.
echo ========================================================
echo   SISTEMA ONLINE!
echo   O Proxy esta unindo o Site (go2rtc_bin\www)
echo   com o Video (Go2RTC :1984) numa coisa so (:5000).
echo.
echo   ACESSE EM QUALQUER LUGAR:
echo   ^>^> https://cams.osberberts.com
echo ========================================================
timeout /t 5
