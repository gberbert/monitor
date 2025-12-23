import sqlite3
import os

DB_PATH = r"c:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\desktop_app\cameras.db"

def list_cams():
    if not os.path.exists(DB_PATH):
        print("DB not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT ip, name, username, password, stream_url FROM cameras")
        rows = c.fetchall()
        print(f"Found {len(rows)} cameras:")
        for r in rows:
            print(f"IP: {r[0]} | Name: {r[1]} | URL: {r[4]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_cams()
