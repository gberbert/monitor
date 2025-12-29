from flask import Flask, jsonify, request, send_from_directory, abort
import os
import sqlite3

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
DB_PATH = os.path.join(BASE_DIR, "nvr_index.db")

app = Flask(__name__)
# CORS removed for simplicity


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/status')
def status():
    return jsonify({"status": "NVR API Online", "storage_root": RECORDINGS_DIR})

@app.route('/timeline')
def serve_timeline_ui():
    return send_from_directory(BASE_DIR, 'timeline_demo.html')

@app.route('/api/nvr/timeline')
def timeline():
    camera_id = request.args.get('camera', 'piscina')
    # Default: Last 24h
    import time
    now = int(time.time())
    start = int(request.args.get('start', now - 86400))
    end = int(request.args.get('end', now))
    
    conn = get_db_connection()
    c = conn.cursor()
    # Pega segmentos que intersectam o periodo
    c.execute("""SELECT start_time, end_time, file_path 
                 FROM recordings 
                 WHERE camera_id = ? 
                 AND end_time >= ? 
                 AND start_time <= ?
                 ORDER BY start_time ASC""", (camera_id, start, end))
    rows = c.fetchall()
    conn.close()
    
    segments = []
    for r in rows:
        # Convert absolute file path to relative URL
        fname = os.path.basename(r['file_path'])
        segments.append({
            "start": r['start_time'],
            "end": r['end_time'],
            "url": f"/video/{camera_id}/{fname}",
            "type": "continuous"
        })
        
    return jsonify(segments)

@app.route('/video/<camera_id>/<filename>')
def serve_video(camera_id, filename):
    # Security: Prevent traversal
    safe_dir = os.path.join(RECORDINGS_DIR, camera_id)
    return send_from_directory(safe_dir, filename)

if __name__ == '__main__':
    print("--- INICIANDO NVR API (PORT 5002) ---")
    app.run(host='0.0.0.0', port=5002, debug=True)
