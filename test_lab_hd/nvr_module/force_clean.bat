@echo off
echo [NVR CLEANER] Buscando processos zumbis...

:: Mata todos os processos python.exe (WARNING: Isso mata TODOS os pythons do usuario)
:: Se isso for muito agressivo, me avise. Mas é a unica forma garantida sem PID.
:: Alternativa: tentar renomear o arquivo db.

echo [1] Tentando matar processos Python (Se houver)...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Administrator: *" >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

echo [2] Aguardando liberacao de handles (2s)...
timeout /t 2 /nobreak >nul

echo [3] Forcando exclusao do DB...
del /F /Q nvr_index.db
if exist nvr_index.db (
    echo [ERRO] Falha ao deletar nvr_index.db. Reinicie o computador ou use o Unlocker.
) else (
    echo [SUCESSO] DB Deletado.
)

echo [4] Forcando exclusao dos videos...
del /F /Q recordings\piscina\*.mp4
echo [SUCESSO] Videos limpos.

echo [CONCLUIDO] Ambiente NVR resetado.
pause
