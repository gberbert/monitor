@echo off
title NVR MASTER CONTROL
color 0A
echo ==================================================
echo       ANTIGRAVITY NVR - AUTOMATED TEST SUITE
echo ==================================================

echo [1/6] Limpando a casa (Matando processos antigos)...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM go2rtc.exe >nul 2>&1
taskkill /F /IM ffmpeg.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/6] Deletando videos e DB antigos...
if exist nvr_index.db del /F /Q nvr_index.db
if exist recordings\piscina\*.mp4 del /F /Q recordings\piscina\*.mp4
echo    -> Limpeza concluída.

echo [3/6] Iniciando AMBIENTE DE TESTE (Nova Janela)...
:: Sobe 1 nivel (test_lab_hd)
if exist ..\start_test_env.bat (
    start "TEST_ENV_SERVER" cmd /k "cd .. & start_test_env.bat"
) else (
    echo [ERRO] start_test_env.bat nao encontrado em ..\
    echo Tentando raiz...
    start "TEST_ENV_SERVER" cmd /k "cd ..\.. & start_test_env.bat"
)

echo    -> Aguardando 15 segundos para o servidor Go2RTC iniciar...
timeout /t 15

echo [4/6] GRAVANDO VIDEO DE TESTE (H.264)...
echo    -> Gravando por 60 segundos. Aguarde...
python test_nvr_recording.py

echo [5/6] Iniciando API NVR (Nova Janela)...
timeout /t 1 /nobreak >nul
start "NVR_API_SERVER" cmd /k "python nvr_api.py"

echo [6/6] Abrindo Navegador...
timeout /t 2 /nobreak >nul
start http://localhost:5002/timeline

echo ==================================================
echo                  TESTE FINALIZADO
echo ==================================================
echo O navegador deve estar aberto com o video tocando.
echo Pressione qualquer tecla para fechar este controlador.
pause
