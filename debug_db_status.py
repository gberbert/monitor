import sqlite3
import os

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")

print(f"Checking DB at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("DB does not exist!")
    exit()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
print("--- STORAGE PATH CONFIG ---")
try:
    c.execute("SELECT key, value FROM config WHERE key='storage_path'")
    print(c.fetchall())
except Exception as e:
    print(f"Error reading config: {e}")

print("\n--- CAMERAS ENABLED STATUS ---")
try:
    c.execute("SELECT name, record_enabled, stream_url FROM cameras")
    for row in c.fetchall():
        print(row)
except Exception as e:
    print(f"Error reading cameras: {e}")
conn.close()
