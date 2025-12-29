@echo off
title ANTIGRAVITY TEST RESTART
color 0b
echo ==================================================
echo      REINICIANDO AMBIENTE DE TESTE (HD)
echo ==================================================
taskkill /F /IM python.exe /T 
taskkill /F /IM go2rtc.exe /T 
taskkill /F /IM ffmpeg.exe /T 

echo Aguardando limpeza de portas...
timeout /t 3 /nobreak >nul

cd /d "%~dp0"
call start_test_env.bat
exit
