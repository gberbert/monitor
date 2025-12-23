
import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'desktop_app', 'cameras.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# NOTE: The column is 'stream_url', NOT 'url'
cursor.execute("SELECT name, ip, stream_url, username, password FROM cameras WHERE ip = '192.168.3.27'")
row = cursor.fetchone()

if row:
    print(f"Name: {row[0]}")
    print(f"IP: {row[1]}")
    print(f"URL: {row[2]}")
    print(f"User: {row[3]}")
    print(f"Pass: {row[4]}")
else:
    print("Camera 192.168.3.27 not found in DB")

conn.close()
