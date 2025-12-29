import sqlite3
import os

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
print("--- CAMERAS TABLE INFO ---")
c.execute("PRAGMA table_info(cameras)")
cols = c.fetchall()
for col in cols:
    print(col)
conn.close()
