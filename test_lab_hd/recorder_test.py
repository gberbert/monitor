import subprocess
import time
import os
import threading
import sys
import sqlite3
import re
import unicodedata

# Configuracoes TESTE
GO2RTC_HOST = "127.0.0.1"
GO2RTC_PORT = "8556" # Porta do ambiente de teste
STORAGE_DIR = "storage_test" # Folder separado para teste
SEGMENT_TIME = 60

# Base Dir relative (test_lab_hd)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# DB de Prod: ../desktop_app/cameras.db
DB_PATH = os.path.join(BASE_DIR, "..", "desktop_app", "cameras.db")
# FFmpeg: ../go2rtc_bin/ffmpeg.exe
# FFmpeg: Use 'ffmpeg' command (PATH set in start script)
FFMPEG_PATH = "ffmpeg"

def ensure_dirs(cam_list):
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
    for cam in cam_list:
        path = os.path.join(STORAGE_DIR, cam)
        if not os.path.exists(path):
            os.makedirs(path)

# Reuse logic from recorder.py (Simplified)

def safe_name(name):
    s = name.lower()
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[^a-z0-9]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def get_cameras_to_record():
    if not os.path.exists(DB_PATH):
        print(f"[WARN] DB nao encontrado: {DB_PATH}")
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("SELECT name, record_enabled, stream_url, crop_mode FROM cameras")
            rows = c.fetchall()
        except:
            print("[WARN] Schema error. Trying simple query.")
            c.execute("SELECT name, 1, '', 0 FROM cameras")
            rows = c.fetchall()
        conn.close()

        sources = {}
        for name, rec, url, crop in rows:
            clean = safe_name(name)
            is_enabled = (rec == 1 or str(rec)=="1")
            
            if not url: url = "unknown_" + clean
            if url not in sources:
                sources[url] = { "master": None, "any_enabled": False, "candidates": [] }
            
            # Logic: If crop=0, it's master
            try: crop = int(crop) 
            except: crop = 0
            
            if crop == 0:
                sources[url]["master"] = clean
            else:
                sources[url]["candidates"].append(clean)
                
            if is_enabled:
                sources[url]["any_enabled"] = True

        final_list = []
        for url, data in sources.items():
            if data["any_enabled"]:
                # FIXED LOGIC: If NO Master (Crop 0), record ALL Candidates (Crop 1, 2...)
                target = data["master"]
                if target:
                    final_list.append(target)
                    print(f"[REC TEST] Gravando Master: {target}")
                else:
                    if data["candidates"]:
                        for cand in data["candidates"]:
                            final_list.append(cand)
                            print(f"[REC TEST] Gravando Crop: {cand}")

        return list(set(final_list))

    except Exception as e:
        print(f"[ERROR] DB Error: {e}")
        return []

def record_camera(camera_name):
    rtsp_url = f"rtsp://{GO2RTC_HOST}:{GO2RTC_PORT}/{camera_name}"
    output_pattern = os.path.join(STORAGE_DIR, camera_name, f"%Y-%m-%d_%H-%M-%S.mp4")
    
    cmd = [
        FFMPEG_PATH,
        "-hide_banner", "-loglevel", "error",
        "-rtsp_transport", "tcp",
        "-use_wallclock_as_timestamps", "1",
        "-i", rtsp_url,
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac",
        "-f", "segment", "-segment_time", str(SEGMENT_TIME),
        "-segment_format", "mp4",
        "-reset_timestamps", "1",
        "-strftime", "1",
        output_pattern
    ]

    print(f"[{camera_name}] TEST REC STARTED: {rtsp_url}")
    while True:
        try:
            p = subprocess.Popen(cmd)
            p.wait()
            print(f"[{camera_name}] FFmpeg restart delay...")
            time.sleep(5)
        except Exception as e:
            print(f"[{camera_name}] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("=== TEST LAB RECORDER ===")
    cams = get_cameras_to_record()
    ensure_dirs(cams)
    for cam in cams:
        t = threading.Thread(target=record_camera, args=(cam,))
        t.daemon = True
        t.start()
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: pass
