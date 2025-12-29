import os
import sqlite3
import time
import datetime
import subprocess

# Configuracao
DB_PATH = "monitor.db"
STORAGE_DIR = "go2rtc_bin/storage"

FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "go2rtc_bin", "ffmpeg.exe")

def get_video_duration(file_path):
    """
    Tenta obter a duracao do video usando ffmpeg (parse stderr).
    """
    try:
        # ffmpeg -i file
        result = subprocess.run(
            [FFMPEG_PATH, "-hide_banner", "-i", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Output esta no stderr: "Duration: 00:00:59.98, ..."
        import re
        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = float(duration_match.group(3))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
            
        return 60.0 # Fallback seguro se falhar parse (melhor que ignorar)
    except Exception as e:
        print(f"Erro ffmpeg duration: {e}")
        return 60.0 # Fallback


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_name TEXT,
            start_time TEXT,
            end_time TEXT,
            file_path TEXT,
            duration REAL
        )
    ''')
    conn.commit()
    conn.close()

def scan_and_index():
    print(f"[Indexer] Varrendo {STORAGE_DIR}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Câmeras sao subpastas
    if not os.path.exists(STORAGE_DIR):
        print(f"[Indexer] Pasta {STORAGE_DIR} nao encontrada.")
        return

    cameras = [d for d in os.listdir(STORAGE_DIR) if os.path.isdir(os.path.join(STORAGE_DIR, d))]

    for cam in cameras:
        cam_dir = os.path.join(STORAGE_DIR, cam)
        files = [f for f in os.listdir(cam_dir) if f.endswith(".mp4")]

        for f in files:
            file_path = os.path.join(cam_dir, f)
            
            # Verificar se ja esta no banco
            cursor.execute("SELECT id FROM videos WHERE file_path = ?", (file_path,))
            if cursor.fetchone():
                continue # Ja indexado

            # Parse filename: YYYY-MM-DD_HH-MM-SS.mp4
            try:
                timestamp_str = f.replace(".mp4", "")
                dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                start_time_iso = dt.isoformat()
                
                # Obter duracao real (importante para timeline)
                duration = get_video_duration(file_path)
                if duration is None:
                    continue

                if duration < 5.0:
                    print(f"[Indexer] Ignorando/Removendo Video Curto/Corrompido: {f} ({duration:.2f}s)")
                    print(f"[Indexer] QUARANTINED Short Video: {f} ({duration:.2f}s)")
                    # try:
                    #     os.rename(file_path, file_path + ".quarantine")
                    # except: pass
                    # continue

                end_time_dt = dt + datetime.timedelta(seconds=duration)
                end_time_iso = end_time_dt.isoformat()

                cursor.execute('''
                    INSERT INTO videos (camera_name, start_time, end_time, file_path, duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (cam, start_time_iso, end_time_iso, file_path, duration))
                
                print(f"[Indexer] Novo video indexado: {cam}/{f} ({duration:.2f}s)")
                conn.commit()

            except Exception as e:
                print(f"[Indexer] Erro ao processar {f}: {e}")

    conn.close()

# Configuracao de Retencao (Lê de cameras.db)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMERAS_DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")

def safe_name(name):
    import re
    import unicodedata
    s = name.lower()
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[^a-z0-9]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def get_retention_map():
    retrieval = {}
    if not os.path.exists(CAMERAS_DB_PATH): 
        return retrieval
    
    try:
        conn = sqlite3.connect(CAMERAS_DB_PATH)
        c = conn.cursor()
        try:
            c.execute("SELECT name, retention_days FROM cameras")
            rows = c.fetchall()
            for name, days in rows:
                clean = safe_name(name)
                # Garante minimo 1 dia
                val = int(days) if days else 7
                if val < 1: val = 1
                retrieval[clean] = val
        except: pass
        conn.close()
    except: pass
    return retrieval

def get_global_config():
    # Enforce Absolute Path consistency with Recorder
    abs_storage = os.path.join(os.path.dirname(os.path.abspath(__file__)), "go2rtc_bin", "storage")
    
    conf = {
        "storage_path": abs_storage,
        "quota": 500
    }
    
    if not os.path.exists(CAMERAS_DB_PATH): return conf
    
    try:
        conn = sqlite3.connect(CAMERAS_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT key, value FROM config")
        rows = c.fetchall()
        for k, v in rows:
            # IGNORAR 'storage_path' do banco. Usar Hardcoded Blindado.
            # if k == 'storage_path': ...
            
            if k == 'disk_quota_gb': 
                try:
                    conf["quota"] = int(v)
                except: pass
            
            if k == 'gemini_api_key': conf["gemini_api_key"] = v
            if k == 'gemini_model': conf["gemini_model"] = v
        conn.close()
    except: pass
    return conf

def cleanup_storage():
    """Remove arquivos antigos e garante espaço em disco"""
    config = get_global_config()
    STORAGE_DIR = config["storage_path"] # Override global const
    retention_map = get_retention_map()
    default_retention = 7
    
    now = time.time()
    
    if not os.path.exists(STORAGE_DIR): return

    # 1. Limpeza por Idade (Retention Policy)
    cameras = [d for d in os.listdir(STORAGE_DIR) if os.path.isdir(os.path.join(STORAGE_DIR, d))]
    
    for cam in cameras:
        days = retention_map.get(cam, default_retention)
        cutoff = now - (days * 86400)
        
        cam_dir = os.path.join(STORAGE_DIR, cam)
        try:
            files = [f for f in os.listdir(cam_dir) if f.endswith(".mp4")]
            for f in files:
                filepath = os.path.join(cam_dir, f)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff:
                        print(f"[Cleanup] Removendo antigo: {f} (Limit: {days}d)")
                        os.remove(filepath)
                        # Remove do index tambem
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("DELETE FROM videos WHERE file_path = ?", (filepath,))
                        conn.commit()
                        conn.close()
                except Exception as e:
                    print(f"Erro ao deletar {f}: {e}")
        except: pass

    # 2. Limpeza por Espaço (Quota Global)
    import shutil
    try:
        total, used, free = shutil.disk_usage(STORAGE_DIR)
        min_free_gb = 5 
        quota_bytes = config["quota"] * 1024 * 1024 * 1024
        
        # Se livre < 5GB OU Usado > Quota (aprox) -> Na verdade quota de disco é qto o disco tem.
        # Usuario define "Quota de Disco" como "Maximo que NVR pode usar"? 
        # Geralmente NVR usa o disco todo disponivel ate sobrar X.
        # Vamos respeitar o input: "disk_quota_gb". Se usarmos mais que isso, apaga.
        # Mas calcular 'used' de uma pasta é lento.
        # Melhor abordagem simples: Manter Free Space > 5GB sempre.
        # E se Quota definida < Total Disk? 
        # Vamos manter Free Space > 5GB como fail safe.
        
        min_free = 5 * 1024 * 1024 * 1024 # 5GB
        
        while free < min_free:
            print(f"[Cleanup] Espaço Crítico ({free/1024/1024:.0f}MB). Apagando vídeo mais antigo...")
            # Busca video mais antigo no banco
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT file_path FROM videos ORDER BY start_time ASC LIMIT 1")
            row = c.fetchone()
            conn.close()
            
            if row and row[0] and os.path.exists(row[0]):
                try:
                    os.remove(row[0])
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("DELETE FROM videos WHERE file_path = ?", (row[0],))
                    conn.commit()
                    conn.close()
                    # Recalcula free
                    total, used, free = shutil.disk_usage(STORAGE_DIR)
                except:
                    break 
            else:
                break 
    except: pass

def main():
    print("=== INDEXADOR + CLEANER DE VÍDEOS ===")
    init_db()
    while True:
        scan_and_index()
        cleanup_storage() # Roda limpeza a cada ciclo
        time.sleep(10) # Varre a cada 10 segundos

if __name__ == "__main__":
    main()
