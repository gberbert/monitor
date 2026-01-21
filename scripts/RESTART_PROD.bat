@echo off
echo [RESTART PROD] Encerrando processos antigos...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM go2rtc.exe /T >nul 2>&1
taskkill /F /IM ffmpeg.exe /T >nul 2>&1
taskkill /F /IM cloudflared.exe /T >nul 2>&1

echo [RESTART PROD] Aguardando limpeza de portas...
timeout /t 3 /nobreak >nul

echo [RESTART PROD] Iniciando Servicos...
call iniciar_servidor_web.bat

echo [RESTART PROD] Concluido. Janelas minimizadas devem ter aberto.
pause
