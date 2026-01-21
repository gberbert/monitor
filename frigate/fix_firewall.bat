@echo off
echo Liberando portas do Go2RTC no Firewall do Windows...

netsh advfirewall firewall add rule name="Go2RTC RTSP" dir=in action=allow protocol=TCP localport=8554
netsh advfirewall firewall add rule name="Go2RTC API" dir=in action=allow protocol=TCP localport=1984
netsh advfirewall firewall add rule name="Go2RTC WebRTC" dir=in action=allow protocol=TCP localport=8555
netsh advfirewall firewall add rule name="Go2RTC WebRTC UDP" dir=in action=allow protocol=UDP localport=8555

echo.
echo Regras adicionadas. Tente reiniciar o Frigate.
pause
