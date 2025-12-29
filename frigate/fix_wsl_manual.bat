@echo off
echo Ativando recursos do Windows para WSL...
:: Requer Admin
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

echo.
echo ========================================================
echo Agora REINICIE o computador.
echo Apos reiniciar, baixe e instale o pacote de atualizacao do Kernel WSL2 aqui:
echo https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
echo ========================================================
pause
