import requests
import os
import psutil
import datetime
import glob
import json

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

log("=== DIAGNOSTICO NVR V2 ===")

# 1. Checar Processos
expected = ["go2rtc.exe", "python.exe", "ffmpeg.exe", "cloudflared.exe"]
running = {p.name() for p in psutil.process_iter()}
log(f"Processos Rodando: {[p for p in expected if p in running]}")

# 2. Checar Go2RTC Streams
try:
    r = requests.get("http://127.0.0.1:1984/api/streams", timeout=2)
    if r.status_code == 200:
        data = r.json()
        log(f"Go2RTC Online. Streams: {list(data.keys())}")
        # Verificar produtcrs/consumers
        for k, v in data.items():
            log(f"  > {k}: {len(v.get('producers', []))} producers, {len(v.get('consumers', []))} consumers")
    else:
        log(f"Go2RTC Erro HTTP: {r.status_code}")
except Exception as e:
    log(f"Go2RTC Falha Conexão: {e}")

# 3. Checar NVR API
try:
    r = requests.get("http://127.0.0.1:5002/", timeout=2) # Index retorna HTML
    log(f"NVR API V2 (:5002) Status: {r.status_code}")
except Exception as e:
    log(f"NVR API V2 Offline: {e}")

# 4. Checar Storage (Novos Arquivos)
base_storage = os.path.join("go2rtc_bin", "storage")
if os.path.exists(base_storage):
    cams = os.listdir(base_storage)
    log(f"Pastas no Storage: {cams}")
    for cam in cams:
        cam_dir = os.path.join(base_storage, cam)
        if os.path.isdir(cam_dir):
            files = sorted(glob.glob(os.path.join(cam_dir, "*.mp4")), key=os.path.getmtime, reverse=True)
            if files:
                last_file = files[0]
                size = os.path.getsize(last_file) / 1024 # KB
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(last_file))
                log(f"  > {cam}: Último vídeo: {os.path.basename(last_file)} ({size:.1f}KB) em {mtime}")
            else:
                log(f"  > {cam}: Nenhum vídeo encontrado.")
else:
    log("Pasta Storage não encontrada!")

# 5. Check logs
if os.path.exists("recorder.err"):
    log("Ultimas 5 linhas recorder.err:")
    with open("recorder.err", "r") as f:
        lines = f.readlines()[-5:]
        for l in lines: print("    " + l.strip())
