
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ajuste o caminho se necessário, mas baseado no recorder.py:
# recorder está em go2rtc_bin, então sobe um nivel para monitor
ROOT_DIR = os.path.dirname(BASE_DIR) 
# Mas debug_sql será criado em monitor, então desktop_app está em ./desktop_app
DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")

print(f"Testando DB em: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("DB NAO ENCONTRADO!")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print("Conexao OK. Tentando query do recorder...")
    
    query = "SELECT name, record_enabled, stream_url, crop_mode FROM cameras"
    print(f"Query: {query}")
    
    c.execute(query)
    rows = c.fetchall()
    
    print(f"Sucesso! Retornou {len(rows)} linhas.")
    for row in rows:
        print(f" - {row}")
        
    conn.close()

except Exception as e:
    print(f"ERRO FATAL: {e}")
