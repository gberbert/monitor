@echo off
echo ==========================================
echo      NVR RESET & RECORD TOOL
echo ==========================================

echo [1/4] Matando processos Python antigos...
taskkill /F /IM python.exe /FI "WINDOWTITLE ne NVR RESET*" >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] Limpando arquivos...
if exist nvr_index.db del /F /Q nvr_index.db
if exist recordings\piscina\*.mp4 del /F /Q recordings\piscina\*.mp4
echo    -> Casa Limpa.

echo [3/4] Iniciando Gravacao de Teste (60s)...
echo    -> Aguarde enquanto geramos videos novos H.264 puros...
python test_nvr_recording.py

echo.
echo ==========================================
echo      GRAVACAO CONCLUIDA!
echo ==========================================
echo.
echo Agora, para ver o resultado:
echo 1. Abra um novo terminal DESTA PASTA.
echo 2. Rode: python nvr_api.py
echo 3. Acesse: http://localhost:5002/timeline
echo.
pause
