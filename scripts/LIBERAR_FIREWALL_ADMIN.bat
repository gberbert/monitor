@echo off
echo ========================================================
echo   LIBERAR ACESSO REMOTO (FIREWALL DO WINDOWS)
echo   Este script precisa ser executado como ADMINISTRADOR.
echo ========================================================
echo.

net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Privilegios de Administrador detectados.
) else (
    echo [ERRO] Voce NAO esta rodando como Administrador.
    echo Clique com botao direito neste arquivo e escolha "Executar como administrador".
    echo.
    pause
    exit
)

echo.
echo Adicionando regras de entrada para o sistema de cameras...
echo.

echo 1. Liberando Porta WEB (5000)...
netsh advfirewall firewall delete rule name="ANTIGRAVITY WEB 5000" >nul 2>&1
netsh advfirewall firewall add rule name="ANTIGRAVITY WEB 5000" dir=in action=allow protocol=TCP localport=5000 profile=any
if %errorLevel% == 0 ( echo [SUCESSO] Porta 5000 liberada. ) else ( echo [FALHA] Erro ao liberar porta 5000. )

echo 2. Liberando Porta RTSP (8554)...
netsh advfirewall firewall delete rule name="ANTIGRAVITY RTSP 8554" >nul 2>&1
netsh advfirewall firewall add rule name="ANTIGRAVITY RTSP 8554" dir=in action=allow protocol=TCP localport=8554 profile=any

echo 3. Liberando Porta API Go2RTC (1984)...
netsh advfirewall firewall delete rule name="ANTIGRAVITY API 1984" >nul 2>&1
netsh advfirewall firewall add rule name="ANTIGRAVITY API 1984" dir=in action=allow protocol=TCP localport=1984 profile=any

echo 4. Liberando Porta WebRTC (8555)...
netsh advfirewall firewall delete rule name="ANTIGRAVITY WebRTC 8555" >nul 2>&1
netsh advfirewall firewall add rule name="ANTIGRAVITY WebRTC 8555" dir=in action=allow protocol=TCP localport=8555 profile=any

echo.
echo ========================================================
echo   CONFIGURACAO CONCLUIDA!
echo   Tente acessar agora pelo celular/tablet:
echo   http://192.168.3.65:5000/dashboard.html
echo ========================================================
echo.
pause
