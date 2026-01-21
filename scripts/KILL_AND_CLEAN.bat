@echo off
echo ===================================================
echo   FORCAR PARADA DE TODOS OS PROCESSOS (ADMIN)
echo ===================================================
echo.
echo Tentando finalizar processos Python, FFmpeg e Go2RTC...
echo.

taskkill /F /IM python.exe /T
taskkill /F /IM ffmpeg.exe /T
taskkill /F /IM go2rtc.exe /T
taskkill /F /IM cloudflared.exe /T

echo.
echo Verificando se a pasta "storage" indevida existe...
if exist "%~dp0storage" (
    echo Movendo pasta "storage" errada da raiz para "storage_OLD_DO_NOT_USE"...
    move "%~dp0storage" "%~dp0storage_OLD_DO_NOT_USE"
)

echo.
echo Processo concluido. Se houve erros de "Acesso Negado",
echo CLIQUE COM O BOTAO DIREITO neste arquivo e selecione
echo "EXECUTAR COMO ADMINISTRADOR".
echo.
pause
