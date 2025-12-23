@echo off
title Antigravity Setup Wizard
color 0f
echo ========================================================
echo   ANTIGRAVITY VMS - SETUP NOVA MAQUINA
echo ========================================================
echo.

:: 1. Verificando Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python em https://www.python.org/
    echo E marque a opcao "ADD TO PATH" no instalador.
    echo.
    pause
    exit
)
echo [OK] Python detectado.

:: 2. Instalando Dependencias
echo.
echo [1/2] Instalando bibliotecas necessarias...
pip install flask requests
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao rodar pip. Verifique sua internet.
)

:: 3. Registrando Auto-Start
echo.
echo [2/2] Criando Agendamento no Windows...
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dp0instalar_auto_start.ps1'"

echo.
echo ========================================================
echo   INSTALACAO CONCLUIDA!
echo   O sistema vai iniciar automaticamente no proximo boot.
echo ========================================================
pause
