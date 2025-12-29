from flask import Flask, jsonify, request, send_from_directory
import os
import sqlite3
import datetime

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminho para storage do Go2RTC
STORAGE_DIR = os.path.join(BASE_DIR, "go2rtc_bin", "storage")
DB_PATH = os.path.join(BASE_DIR, "monitor.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "test_lab_hd", "nvr_module") # timeline_demo.html está aqui

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory(TEMPLATE_DIR, 'timeline_demo.html')

@app.route('/api/nvr/timeline')
def timeline():
    camera_id = request.args.get('camera', 'piscina')
    # Recebe timestamps Unix
    import time
    now = time.time()
    try:
        start_ts = float(request.args.get('start', now - 86400))
        end_ts = float(request.args.get('end', now))
        
        # O banco usa ISO Strings
        start_iso = datetime.datetime.fromtimestamp(start_ts).isoformat()
        end_iso = datetime.datetime.fromtimestamp(end_ts).isoformat()
    except:
        start_iso = datetime.datetime.now().isoformat()
        end_iso = datetime.datetime.now().isoformat()

    conn = get_db_connection()
    c = conn.cursor()
    
    # Query na tabela 'videos' - Schema: start_time, end_time, file_path
    query = """
        SELECT start_time, end_time, file_path 
        FROM videos 
        WHERE camera_name = ? 
        AND end_time >= ? 
        AND start_time <= ?
        ORDER BY start_time ASC
    """
    
    # Smart Lookup Check
    has_videos = False
    try:
        c.execute(query, (camera_id, start_iso, end_iso))
        rows = c.fetchall()
        if len(rows) > 0: has_videos = True
    except: rows = []

    # LOGGER DEBUG
    def log_debug(msg):
        try:
            with open("api_debug.log", "a") as f:
                f.write(f"{datetime.datetime.now()} [DEBUG] {msg}\n")
        except: pass

    resolved_camera = camera_id

    try:
        if not has_videos:
            log_debug(f"--- SMART LOOKUP START for {camera_id} ---")
            try:
                cam_db_path = os.path.join(BASE_DIR, "desktop_app", "cameras.db")
                
                if os.path.exists(cam_db_path):
                    cdb = sqlite3.connect(cam_db_path)
                    cc = cdb.cursor()
                    
                    # Helper Name normalization
                    def safe_name_py(n):
                        import re, unicodedata
                        try:
                            s = n.lower()
                            s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
                            s = re.sub(r'[^a-z0-9]', '_', s)
                            s = re.sub(r'_+', '_', s)
                            return s.strip('_')
                        except: return "unknown"

                    # Get Cameras
                    try:
                        cc.execute("SELECT name, rtsp_url, ip FROM cameras")
                    except:
                        log_debug("Coluna rtsp_url nao existe? Tentando old schema.")
                        cc.execute("SELECT name, '', ip FROM cameras")
                        
                    all_cams = cc.fetchall()
                    cdb.close()

                    my_url = None
                    my_ip = None
                    
                    # Encontrar Self
                    for name, url, ip in all_cams:
                        s_name = safe_name_py(name)
                        if s_name == camera_id:
                            my_url = url
                            my_ip = ip
                            log_debug(f"Self Found: {name}")
                            break
                    
                    if my_ip or my_url:
                        fallback_candidates = []
                        for name, url, ip in all_cams:
                            s_target = safe_name_py(name)
                            if s_target == camera_id: continue
                            
                            match = False
                            if my_ip and ip and ip == my_ip: match = True
                            if my_url and url and url == my_url: match = True
                            
                            if match:
                                log_debug(f"Matches Sibling: {name}")
                                fallback_candidates.append(s_target)

                        # Check Siblings
                        for cand in fallback_candidates:
                            log_debug(f"Checking {cand}...")
                            c.execute(query, (cand, start_iso, end_iso))
                            rows_sibling = c.fetchall()
                            if len(rows_sibling) > 0:
                                log_debug(f"FOUND {len(rows_sibling)} videos in {cand}!")
                                rows = rows_sibling
                                resolved_camera = cand
                                break # Found
                    else:
                        log_debug("Self not found in external DB (Sync issue?)")
                        
            except Exception as e:
                log_debug(f"EXCEPTION INNER: {e}")
        
        conn.close()
        
        segments = []
        for r in rows:
            # DB returns ISO strings
            try:
                s_dt = datetime.datetime.fromisoformat(r[0])
                e_dt = datetime.datetime.fromisoformat(r[1])
                fname = os.path.basename(r[2])
                
                segments.append({
                    "start": s_dt.timestamp(),
                    "end": e_dt.timestamp(),
                    "filename": fname,
                    "camera": camera_id,       # Logical ID
                    "src_camera": resolved_camera # Physical Folder
                })
            except Exception as e: log_debug(f"Row Parse Error: {e}")
            
        return jsonify(segments)

    except Exception as fatal:
        log_debug(f"FATAL ERROR IN TIMELINE: {fatal}")
        import traceback
        log_debug(traceback.format_exc())
        return jsonify({"error": str(fatal)}), 500

@app.route('/video/<camera_id>/<filename>')
def serve_video(camera_id, filename):
    folder = os.path.join(STORAGE_DIR, camera_id)
    return send_from_directory(folder, filename)

if __name__ == '__main__':
    print("--- NVR API v2 (PORT 5002) ---")
    print(f"Lendo videos de: {STORAGE_DIR}")
    app.run(host='0.0.0.0', port=5002, use_reloader=False)
