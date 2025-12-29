import requests
import os
import datetime
import glob
import json

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

log("=== DIAGNOSTICO NVR V3 (No Deps) ===")

# 2. Checar Go2RTC Streams
log("Checando Go2RTC (:1984)...")
try:
    r = requests.get("http://127.0.0.1:1984/api/streams", timeout=2)
    if r.status_code == 200:
        data = r.json()
        log(f"Go2RTC Online. Streams: {list(data.keys())}")
        for k, v in data.items():
            prod = len(v.get('producers', []))
            cons = len(v.get('consumers', []))
            log(f"  > {k}: {prod} prod, {cons} cons")
    else:
        log(f"Go2RTC Erro HTTP: {r.status_code}")
except Exception as e:
    log(f"Go2RTC Falha Conexão: {e}")

# 3. Checar NVR API
log("Checando NVR API (:5002)...")
try:
    r = requests.get("http://127.0.0.1:5002/", timeout=2)
    log(f"NVR API V2 (:5002) Status: {r.status_code}")
except Exception as e:
    log(f"NVR API V2 Offline: {e}")

# 4. Checar Storage
log("Checando Pasta Storage...")
base_storage = os.path.join("go2rtc_bin", "storage")
if os.path.exists(base_storage):
    cams = os.listdir(base_storage)
    log(f"Pastas encontradas: {cams}")
    for cam in cams:
        cam_dir = os.path.join(base_storage, cam)
        if os.path.isdir(cam_dir):
            files = sorted(glob.glob(os.path.join(cam_dir, "*.mp4")), key=os.path.getmtime, reverse=True)
            if files:
                last_file = files[0]
                size = os.path.getsize(last_file) / 1024
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(last_file))
                log(f"  > {cam}: Último: {os.path.basename(last_file)} ({size:.1f}KB) em {mtime}")
            else:
                log(f"  > {cam}: VAZIO")
else:
    log("Pasta Storage não encontrada!")

# 5. Check logs
if os.path.exists("recorder.err"):
    log("Check Log recorder.err (Errors):")
    try:
        with open("recorder.err", "r") as f:
            lines = f.readlines()[-5:]
            for l in lines: print("    " + l.strip())
    except: pass
