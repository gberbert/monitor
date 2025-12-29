import sqlite3
import os
import time

DB_PATH = "nvr_index.db"

def check_db():
    print(f"--- DIAGNOSTICO NVR DB ---")
    if not os.path.exists(DB_PATH):
        print(f"[ERRO] Arquivo de banco {DB_PATH} nao encontrado!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count rows
        c.execute("SELECT count(*) FROM recordings")
        count = c.fetchone()[0]
        print(f"Total de gravações indexadas: {count}")
        
        if count > 0:
            print("\nÚltimos 5 registros:")
            c.execute("SELECT id, camera_id, start_time, end_time, file_path FROM recordings ORDER BY id DESC LIMIT 5")
            rows = c.fetchall()
            for r in rows:
                print(f"ID: {r[0]} | Cam: {r[1]} | Inicio: {r[2]} | Fim: {r[3]} | Arquivo: {r[4]}")
                # Check file existence
                if os.path.exists(r[4]):
                    print(f"   -> Arquivo Físico OK")
                else:
                    print(f"   -> [ALERTA] Arquivo físico SUMIU!")
                    
        conn.close()
    except Exception as e:
        print(f"[ERRO] Falha ao ler DB: {e}")

if __name__ == "__main__":
    check_db()
