import subprocess
import time
import os
import sys
import sqlite3
import re
import unicodedata
import hashlib

# ==========================================
# CONFIGURACOES GLOBAIS
# ==========================================
GO2RTC_HOST = "127.0.0.1"
GO2RTC_PORT = "8554"
SEGMENT_TIME = 60
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Project Root
DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")
FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe")

def get_storage_path():
    # PATH ABSOLUTO: monitor/go2rtc_bin/storage
    return os.path.join(BASE_DIR, "go2rtc_bin", "storage")

STORAGE_DIR = get_storage_path()

# ==========================================
# HELPERS
# ==========================================
def safe_name(name):
    # Replica logica do sync para garantir match com nomes de pasta/banco
    try:
        s = name.lower()
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
        s = re.sub(r'[^a-z0-9]', '_', s)
        s = re.sub(r'_+', '_', s)
        return s.strip('_')
    except:
        return "unknown"

def get_target_url(camera_name):
    """
    Resolve a URL RTSP correta. Tenta primeiro calcular o ID (src_MD5) baseada na URL do banco.
    Se falhar, tenta conectar pelo nome.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, stream_url FROM cameras")
        rows = c.fetchall()
        conn.close()
        
        target_url = None
        for r_name, r_url in rows:
            if safe_name(r_name) == camera_name:
                target_url = r_url
                break
        
        if target_url:
            # Hash MD5 da URL Original (Logica do Sync)
            url_hash = hashlib.md5(target_url.strip().encode()).hexdigest()[:8]
            stream_id = f"src_{url_hash}"
            return f"rtsp://{GO2RTC_HOST}:{GO2RTC_PORT}/{stream_id}"
        else:
            # Fallback
            return f"rtsp://{GO2RTC_HOST}:{GO2RTC_PORT}/{camera_name}"
    except Exception as e:
        print(f"[RESOLVER ERROR] {e}")
        return f"rtsp://{GO2RTC_HOST}:{GO2RTC_PORT}/{camera_name}"

def get_enabled_cameras():
    """
    Retorna lista de nomes (safe_name) das cameras que devem ser gravadas.
    Logica Estrita: record_enabled deve ser verdadeiro.
    """
    if not os.path.exists(DB_PATH):
        print(f"[DB ERROR] Banco nao encontrado: {DB_PATH}")
        return []

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, record_enabled FROM cameras")
        rows = c.fetchall()
        conn.close()
        
        enabled = []
        for name, rec in rows:
            try:
                # Trata 'true', '1', 1, 'yes', 'y' como True
                val = str(rec).lower()
                is_on = val in ['true', '1', 'y', 'yes'] or (val.isdigit() and int(val) > 0)
            except: 
                is_on = False
            
            if is_on:
                enabled.append(safe_name(name))
        return list(set(enabled))
    except Exception as e:
        print(f"[DB READ ERROR] {e}")
        return []

def start_recording(camera_name):
    """Inicia processo FFmpeg para uma camera."""
    cam_path = os.path.join(STORAGE_DIR, camera_name)
    if not os.path.exists(cam_path):
        try: os.makedirs(cam_path)
        except: pass
    
    rtsp_url = get_target_url(camera_name)
    output_pattern = os.path.join(cam_path, f"%Y-%m-%d_%H-%M-%S.mp4")
    
    # Flags Otimizadas para Compatibilidade Web (H.264)
    cmd = [
        FFMPEG_PATH, 
        "-hide_banner", "-loglevel", "error",
        "-rtsp_transport", "tcp",
        "-use_wallclock_as_timestamps", "1",
        "-i", rtsp_url,
        # CODEC: H.264 Ultrafast (Baixo CPU)
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        # SEGMENTAÇÃO: 60s
        "-f", "segment", "-segment_time", str(SEGMENT_TIME),
        "-segment_format", "mp4", "-movflags", "+faststart",
        "-reset_timestamps", "1", "-strftime", "1",
        output_pattern
    ]
    
    print(f"[REC START] Iniciando: {camera_name} -> {rtsp_url}")
    
    # CREATE_NEW_PROCESS_GROUP no Windows permite matar arvore de processos se necessario
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    return subprocess.Popen(cmd, creationflags=creation_flags)

# ==========================================
# MAIN LOOP (MANAGER)
# ==========================================
def main():
    print("=== MONITOR NVR GRAVADOR (DYNAMIC MANAGER v3) ===")
    print(f"Database: {DB_PATH}")
    print(f"Storage : {STORAGE_DIR}")
    
    if not os.path.exists(STORAGE_DIR):
        try: os.makedirs(STORAGE_DIR)
        except: pass
    
    # Dicionario de Processos Ativos
    # Key: camera_name (safe), Value: subprocess.Popen object
    active_procs = {}
    
    try:
        while True:
            # 1. State Reconciliation (A cada loop)
            wanted_cameras = get_enabled_cameras()
            
            # A. STOP (Quem esta rodando mas nao devia)
            current_running = list(active_procs.keys())
            for name in current_running:
                if name not in wanted_cameras:
                    print(f"[REC STOP] Configuração mudou. Parando: {name}")
                    proc = active_procs[name]
                    # Tenta terminar gracefully
                    if proc.poll() is None:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            print(f"[REC KILL] Forçando parada: {name}")
                            proc.kill()
                    del active_procs[name]
            
            # B. START / MONITOR (Quem devia rodar)
            for name in wanted_cameras:
                needs_start = False
                
                if name not in active_procs:
                    needs_start = True # Novo
                else:
                    # Ja existe, verifica se morreu
                    ret_code = active_procs[name].poll()
                    if ret_code is not None:
                        print(f"[REC WATCHDOG] Processo {name} morreu (Code {ret_code}). Reiniciando...")
                        needs_start = True
                
                if needs_start:
                    # Rate limiting basico (se morreu muito rapido, o sleep do loop segura)
                    active_procs[name] = start_recording(name)
            
            # C. Tick Rate
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Parando todos os gravadores...")
        for p in active_procs.values():
            if p.poll() is None: p.terminate()
        print("Bye.")

if __name__ == "__main__":
    main()
