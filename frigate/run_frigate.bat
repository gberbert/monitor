@echo off
echo Iniciando Frigate NVR...
echo Certifique-se que o Docker Desktop esta rodando!

:: Adicionar Docker ao PATH (caso nao tenha reiniciado o terminal)
set "PATH=%PATH%;C:\Program Files\Docker\Docker\resources\bin"

:: Criar diretório de storage se nao existir
if not exist "storage" mkdir "storage"

:: Caminho Absoluto Atual
set "PWD=%~dp0"
:: Remover backslash final
set "PWD=%PWD:~0,-1%"

echo Config Path: %PWD%\config.yml
echo Storage Path: %PWD%\storage

:: Parar instancia anterior se houver
docker stop frigate
docker rm frigate

:: Iniciar Docker
:: Nota: Mapeamento de portas 8554 (RTSP) pode conflitar se nosso Go2RTC antigo estiver rodando.
:: O Frigate tem seu proprio Go2RTC interno na porta 8554.
:: Certifique-se de parar o 'test_lab' ou 'nvr_core' antes.

docker run -d ^
  --name frigate ^
  --restart=unless-stopped ^
  --mount type=tmpfs,target=/tmp/cache,tmpfs-size=1000000000 ^
  --shm-size=64m ^
  -v "%PWD%\storage":/media/frigate ^
  -v "%PWD%\config.yml":/config/config.yml:ro ^
  --net=host ^
  ghcr.io/blakeblackshear/frigate:stable

echo.
echo Frigate iniciado! Acesse http://localhost:5000
echo Usuario padrao nao requer senha inicialmente.
pause
