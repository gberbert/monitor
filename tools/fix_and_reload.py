import sqlite3
import os
import requests
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")
GO2RTC_API = "http://127.0.0.1:1984/api/streams"

def log(msg):
    print(f"[FIX] {msg}")

def fix_db():
    if not os.path.exists(DB_PATH):
        log("DB not found!")
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Encontrar cameras com senha problematica nao escapada
    c.execute("SELECT mac, stream_url FROM cameras")
    rows = c.fetchall()
    
    dirty = False
    for mac, url in rows:
        if "@" in url:
            # Check for double @ in authority part
            # rtsp://user:pass@word@ip...
            # A correct url has only ONE @ before the host.
            # Heuristic: if we see "vigueraberbert@2025" we fix it.
            if "vigueraberbert@2025" in url:
                log(f"Found broken URL for {mac}")
                new_url = url.replace("vigueraberbert@2025", "vigueraberbert%402025")
                c.execute("UPDATE cameras SET stream_url = ? WHERE mac = ?", (new_url, mac))
                log(f" -> Fixed: {new_url}")
                dirty = True
                
    if dirty:
        conn.commit()
    else:
        log("No DB fixes needed.")
    conn.close()

def apply_hotfix_api():
    # Force update 'src_ee279333' (Porteiro)
    # We construct the Correct URL explicitly
    stream_id = "src_ee279333"
    correct_url = "rtsp://admin:vigueraberbert%402025@192.168.3.125:554/cam/realmonitor?channel=1&subtype=0"
    
    # Go2RTC API: PUT /api/streams?src={id}&url={value}
    params = {
        "src": stream_id,
        "url": correct_url
    }
    
    try:
        log(f"Applying Hotfix to Go2RTC API for {stream_id}...")
        r = requests.put(GO2RTC_API, params=params, timeout=5)
        if r.status_code in [200, 201]:
            log(" -> Success! Stream updated in memory.")
        else:
            log(f" -> Failed: {r.status_code} {r.text}")
    except Exception as e:
        log(f" -> API Error: {e}")

if __name__ == "__main__":
    log("Starting Fixes...")
    fix_db()
    
    # Run Sync to update YAML
    import sync_cameras_to_web
    sync_cameras_to_web.sync_config()
    
    # Apply Hotfix
    apply_hotfix_api()
