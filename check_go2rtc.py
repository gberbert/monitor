import requests
import json

try:
    print("Checking Go2RTC Streams...")
    r = requests.get("http://127.0.0.1:1984/api/streams")
    if r.status_code == 200:
        data = r.json()
        print(f"STREAMS FOUND: {len(data)}")
        for key, value in data.items():
            print(f" - {key}: {value}")
            
        if not any("_mjpeg" in k for k in data.keys()):
            print("\n[ALERT] NO MJPEG STREAMS FOUND! FFmpeg path is likely wrong.")
    else:
        print(f"Error: {r.status_code}")
except Exception as e:
    print(f"Connection Failed: {e}")
