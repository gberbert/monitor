@echo off
title ANTIGRAVITY MONITOR - RESTART
color 0c
echo ==================================================
echo      LIMPANDO PROCESSOS RESIDUAIS
echo ==================================================
:: Mata processos de infraestrutura web antigos para evitar portas presas
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM go2rtc.exe /T >nul 2>&1
taskkill /F /IM cloudflared.exe /T >nul 2>&1
taskkill /F /IM ffmpeg.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo Aguardando 10 segundos para liberação total (Cloudflare)...
ping -n 11 127.0.0.1 >nul

echo.
echo ==================================================
echo      INICIANDO APP_ANTIGRAVITY.BAT
echo ==================================================
echo.

call App_Antigravity.bat
