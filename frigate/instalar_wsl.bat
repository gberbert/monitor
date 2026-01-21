@echo off
:: Verificar Privilegios de Admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ==========================================
    echo Instalando WSL (Windows Subsystem for Linux)
    echo ==========================================
    echo Isso pode levar alguns minutos.
    echo Uma janela de console pode aparecer baixando o Ubuntu.
    echo.
    
    wsl --install
    
    echo.
    echo ==========================================
    echo IMPORTANTE:
    echo Se a instalacao concluiu com sucesso, voce DEVE
    echo REINICIAR O COMPUTADOR para finalizar.
    echo ==========================================
    pause
) else (
    echo Solicitando permissao de Administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
)
