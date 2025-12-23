
import sqlite3
import os

DB_PATH = "desktop_app/cameras.db"
TARGET_IP = "192.168.3.27"
NEW_URL = "rtsp://127.0.0.1:8554/camera_27"

def update_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT mac, stream_url FROM cameras")
    rows = cursor.fetchall()
    
    found = False
    for row in rows:
        mac, url = row
        if TARGET_IP in url:
            print(f"Updating MAC {mac} to use Go2RTC Bridge...")
            cursor.execute("UPDATE cameras SET stream_url = ? WHERE mac = ?", (NEW_URL, mac))
            found = True
    
    if found:
        conn.commit()
        print("Update Complete.")
    else:
        print("Target IP not found.")
            
    conn.close()

if __name__ == "__main__":
    update_db()
