@echo off
echo [AUTO] Encerrando processos...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM go2rtc.exe /T >nul 2>&1
taskkill /F /IM ffmpeg.exe /T >nul 2>&1
taskkill /F /IM cloudflared.exe /T >nul 2>&1
echo [AUTO] Aguardando...
timeout /t 3 /nobreak >nul
echo [AUTO] Iniciando...
call iniciar_servidor_web.bat
echo [AUTO] Feito.
exit
