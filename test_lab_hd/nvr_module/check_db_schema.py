import sqlite3
import os

db_path = "nvr_index.db"
if not os.path.exists(db_path):
    print("DB nao existe!")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tabelas:", c.fetchall())
    
    # Check videos columns
    try:
        c.execute("PRAGMA table_info(videos)")
        cols = [r[1] for r in c.fetchall()]
        print("Colunas em VIDEOS:", cols)
    except:
        print("Erro lendo videos")
    
    conn.close()
