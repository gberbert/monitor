@echo off
echo STARTING GO2RTC BRIDGE...
cd go2rtc_bin
start /B go2rtc.exe
cd ..

timeout /t 2 >nul

echo STARTING MONITORING APP...
python desktop_app/main_modern.py
