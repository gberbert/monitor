@echo off
echo Reiniciando Recorder...
taskkill /F /FI "WINDOWTITLE eq monitor_recorder" /T
taskkill /F /IM python.exe /FI "COMMANDLINE eq *recorder.py*" /T

timeout /t 2 /nobreak >nul

echo Iniciando Recorder...
start "monitor_recorder" /min python go2rtc_bin\recorder.py
echo Feito.
