@echo off
echo ==========================================
echo   GIT UNLOCKER - FORCANDO LIBERACAO
echo ==========================================
echo.

echo 1. Matando processos git.exe pendentes...
taskkill /F /IM git.exe /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Processos Git encerrados.
) else (
    echo [INFO] Nenhum processo Git estava rodando.
)

echo.
echo 2. Removendo arquivos de Lock (.git/index.lock)...
if exist ".git\index.lock" (
    del /F /Q ".git\index.lock"
    echo [FIXED] Arquivo index.lock removido.
) else (
    echo [OK] Nenhum index.lock encontrado.
)

if exist ".git\HEAD.lock" (
    del /F /Q ".git\HEAD.lock"
    echo [FIXED] Arquivo HEAD.lock removido.
)

if exist ".git\config.lock" (
    del /F /Q ".git\config.lock"
    echo [FIXED] Arquivo config.lock removido.
)

echo.
echo ==========================================
echo   GIT LIBERADO! TENTE SEU COMMIT NOVAMENTE.
echo ==========================================
pause
