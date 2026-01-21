@echo off
echo PARANDO TODOS OS SERVICOS DO MONITOR...
echo.
taskkill /F /IM python.exe /IM go2rtc.exe /IM ffmpeg.exe /IM cloudflared.exe
echo.
echo Todos os processos foram finalizados.
pause
