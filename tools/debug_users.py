
import sqlite3
import os

DB_FILE = os.path.join("desktop_app", "cameras.db")
if not os.path.exists(DB_FILE):
    print("DB not found at", DB_FILE)
    exit()

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
try:
    c.execute("SELECT username, password, approved FROM users")
    print(f"{'USERNAME':<15} | {'PASSWORD':<15} | {'APPROVED'}")
    print("-" * 45)
    for row in c.fetchall():
        print(f"{row[0]:<15} | {row[1]:<15} | {row[2]}")
except Exception as e:
    print("Error:", e)
conn.close()
