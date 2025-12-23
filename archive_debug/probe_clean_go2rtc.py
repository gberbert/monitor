import cv2
import time
import sys
import sqlite3

# Define streams to check
STREAMS = [
    "camera_27",
    "camera_27_default", 
    "camera_27_admin", 
    "camera_27_berbert"
]

DB_PATH = r"c:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\desktop_app\cameras.db"

def update_db(stream_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if we have an entry for this IP/MAC?
        # We'll just update ALL entries with IP 192.168.3.27 to use this URL
        # Or upsert a new one.
        
        url = f"rtsp://127.0.0.1:8554/{stream_name}"
        print(f"Updating DB to use: {url}")
        
        c.execute("UPDATE cameras SET stream_url = ? WHERE ip = '192.168.3.27'", (url,))
        
        if c.rowcount == 0:
            print("No existing camera found in DB with that IP. Inserting new.")
            # Upsert logic manual
            c.execute("INSERT INTO cameras (mac, name, ip, username, password, stream_url, crop_mode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ("UNKNOWN-27", "Camera 27 (Go2RTC)", "192.168.3.27", "admin", "viguera2001", url, 0))
            
        conn.commit()
        conn.close()
        print("Database Updated Successfully.")
    except Exception as e:
        print(f"DB Error: {e}")

def check_stream(name):
    url = f"rtsp://127.0.0.1:8554/{name}"
    print(f"Checking {url} ...")
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            print(f"SUCCESS! Stream '{name}' is working.")
            return True
    return False

def main():
    print("Probing Clean Go2RTC Streams...")
    
    found = False
    for s in STREAMS:
        if check_stream(s):
            print(f"\n>>> FOUND WORKING CONFIG: {s} <<<")
            update_db(s)
            found = True
            break
            
    if not found:
        print("\nALL STREAMS FAILED via Go2RTC.")
        # FORCE UPDATE TO PRIMARY ANYWAY?
        print("Forcing update to primary 'camera_27' so App uses Go2RTC architecture.")
        update_db("camera_27")

if __name__ == "__main__":
    main()
