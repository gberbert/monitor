@echo off
echo Parando Gravador (recorder.py)...
wmic process where "CommandLine like '%%recorder.py%%'" call terminate
timeout /t 2 /nobreak
echo Iniciando Gravador...
cd /d "%~dp0"
start "Monitor Recorder" /B python go2rtc_bin\recorder.py
echo Gravador reiniciado com sucesso.
