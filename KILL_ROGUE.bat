@echo off
echo === FINALIZADOR DE PROCESSOS ROGUE (ADMIN) ===
echo Este script tenta forcar o encerramento de processos Python/FFmpeg orfaos.
echo Necessario executar como ADMINISTRADOR.

taskkill /F /PID 11564 /T
taskkill /F /PID 11384 /T
taskkill /F /PID 11372 /T
taskkill /F /PID 9228 /T

taskkill /F /IM ffmpeg.exe /T

echo.
echo Se houver mensagems "Acesso Negado", voce precisa clicar com botao direito
echo neste arquivo e escolher "Executar como Administrador".
echo.
pause
