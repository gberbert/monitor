@echo off
echo =================================================
echo   ADIANTANDO RELOGIO DO SISTEMA EM 14s
echo =================================================
echo Solicitando Permissao de Administrador...

:: Invoca PowerShell como Admin para alterar a hora
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList 'Set-Date -Date (Get-Date).AddSeconds(14)'"

echo.
echo Comando enviado. Se voce aceitou o UAC, o relogio deve ter pulado 14s.
echo Agora grave um novo video e veja se bate!
echo.
pause
