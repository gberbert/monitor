@echo off
cd /d "%~dp0"
title Instalador Antigravity

echo ========================================================
echo   INSTALADOR MANUAL DO AGENDAMENTO
echo ========================================================
echo   IMPORTANTE:
echo   Voce deve clicar com BOTAO DIREITO neste arquivo
echo   e escolher: "EXECUTAR COMO ADMINISTRADOR"
echo ========================================================
echo.
pause

echo.
echo Executando script de instalacao...
powershell -NoProfile -ExecutionPolicy Bypass -File "instalar_auto_start.ps1"

echo.
echo ========================================================
echo   VERIFICACAO FINAL
echo ========================================================
powershell -Command "Get-ScheduledTask -TaskName 'Antigravity_VMS_Monitor' | Select-Object TaskName,State"
echo.
echo Se apareceu "Antigravity_VMS_Monitor ... Ready" acima, DEU CERTO.
echo Se apareceu erro vermelho, me mande print.
echo.
pause
