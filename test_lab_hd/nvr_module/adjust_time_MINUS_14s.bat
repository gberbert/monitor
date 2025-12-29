@echo off
echo =================================================
echo   ATRASANDO RELOGIO DO SISTEMA EM 14s
echo =================================================
echo Solicitando Permissao de Administrador...

:: Invoca PowerShell como Admin para alterar a hora ( -14 segundos )
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList 'Set-Date -Date (Get-Date).AddSeconds(-14)'"

echo.
echo Comando enviado. Verifique se o horario voltou ao normal.
echo.
pause
