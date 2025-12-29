import sqlite3
import os
import time
import subprocess
import threading
from datetime import datetime

# Config
DB_PATH = "nvr_index.db"
STORAGE_ROOT = "recordings"

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Tabela principal de indexação de vídeo
        c.execute('''CREATE TABLE IF NOT EXISTS recordings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        camera_id TEXT,
                        file_path TEXT,
                        start_time INTEGER, -- Unix Timestamp
                        end_time INTEGER,
                        size_bytes INTEGER
                    )''')
        # Índices para busca rápida na timeline
        c.execute('CREATE INDEX IF NOT EXISTS idx_cam_time ON recordings (camera_id, start_time)')
        
        # Tabela de Eventos (Metadados para colorir a timeline)
        c.execute('''CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        camera_id TEXT,
                        event_type TEXT, -- 'motion', 'ai_human'
                        timestamp INTEGER
                    )''')
        self.conn.commit()

    def index_segment(self, camera_id, path, start, duration):
        """ Registra um novo bloco de vídeo no banco """
        end = start + duration
        size = os.path.getsize(path) if os.path.exists(path) else 0
        c = self.conn.cursor()
        c.execute("INSERT INTO recordings (camera_id, file_path, start_time, end_time, size_bytes) VALUES (?, ?, ?, ?, ?)",
                  (camera_id, path, start, end, size))
        self.conn.commit()
        print(f"[DB] Indexado: {camera_id} | {path} ({duration}s)")

    def get_timeline_segments(self, camera_id, start_ts, end_ts):
        """ Retorna blocos para o frontend desenhar """
        c = self.conn.cursor()
        c.execute("""SELECT start_time, end_time, file_path FROM recordings 
                     WHERE camera_id = ? AND end_time > ? AND start_time < ? 
                     ORDER BY start_time ASC""", (camera_id, start_ts, end_ts))
        return c.fetchall()

class IndexerThread(threading.Thread):
    def __init__(self, camera_id, save_dir, db_manager):
        super().__init__()
        self.camera_id = camera_id
        self.save_dir = save_dir
        self.db = db_manager
        self.running = False

    def run(self):
        self.running = True
        print(f"[NVR-Indexer] Iniciando monitoramento para: {self.camera_id}")
        known_files = set()
        
        while self.running:
            try:
                if os.path.exists(self.save_dir):
                    files = sorted([f for f in os.listdir(self.save_dir) if f.endswith(".mp4")])
                    for f in files:
                        if f in known_files: continue
                        
                        filepath = os.path.join(self.save_dir, f)
                        # Check size implies finished? ffmpeg segment writes to temp then renames? 
                        # FFmpeg segment muxer writes directly. We usually enable index when file is "old enough" or check modification time.
                        # For simplicity: Index if created > 5s ago.
                        
                        # Parse Filename: YYYYMMDD_HHMMSS.mp4
                        try:
                            # New strategy: Read REAL metadata
                            real_start, real_dur = self.get_video_metadata(filepath)
                            
                            start_ts = 0
                            duration = 0
                            
                            if real_start:
                                start_ts = real_start
                                duration = real_dur
                            else:
                                # Fallback to Filename (YYYYMMDD_HHMMSS)
                                try:
                                    # Ex: 20251226_230015.mp4
                                    basename = os.path.basename(filepath)
                                    ts_part = basename.split('_')[1].split('.')[0]
                                    date_part = basename.split('_')[0]
                                    dt = datetime.strptime(f"{date_part}{ts_part}", "%Y%m%d%H%M%S")
                                    start_ts = dt.timestamp()
                                    
                                    # Try to get duration at least?
                                    if real_dur:
                                        duration = real_dur
                                    else:
                                        duration = 10.0 # Blind guess
                                    
                                    print(f"[Indexer] Metadata missing for {f}. Falling back to filename.")
                                except Exception as idx_e:
                                    print(f"[Indexer] Falha total parsing {f}: {idx_e}")
                                    continue
                            
                            if duration > 0 and start_ts > 0:
                                self.db.index_segment(self.camera_id, filepath, start_ts, duration)
                                known_files.add(f)
                        except Exception as e:
                            print(f"[Indexer] ERRO CRÍTICO indexando {f}: {e}")
                            # pass
            except Exception as e:
                print(f"[Indexer] Loop Error: {e}")
                
            time.sleep(5) # Scan every 5s

    def get_video_metadata(self, filepath):
        """
        Extrai Metadata Absoluta (Wall-Clock) do arquivo vídeo.
        Retorna: (start_ts, duration) ou (None, None) se falhar.
        """
        try:
            # Caminho absoluto para FFmpeg (Hardcoded para robustez no test lab)
            ffmpeg_path = r"C:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\go2rtc_bin\ffmpeg.exe"
            
            cmd = [ffmpeg_path, '-hide_banner', '-i', filepath]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
            output = result.stderr

            # 1. Parse Duration
            duration = 10.0 # Fallback
            import re
            dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
            if dur_match:
                h, m, s = int(dur_match.group(1)), int(dur_match.group(2)), float(dur_match.group(3))
                duration = h * 3600 + m * 60 + s

            # 2. Parse Creation Time (Wall-Clock Precision)
            # Ex: creation_time   : 2025-12-26T22:00:00.000000Z
            start_ts = None
            ctime_match = re.search(r"creation_time\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.?\d*Z?)", output)
            
            if ctime_match:
                ctime_str = ctime_match.group(1)
                # Parse ISO8601 to Unix Timestamp
                from datetime import datetime, timezone
                try:
                    # Tenta formato com Z
                    dt = datetime.strptime(ctime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    try:
                        dt = datetime.strptime(ctime_str, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        dt = None # Unknown format
                
                if dt:
                    # FFmpeg grava creation_time em UTC. 
                    # Convertemos para Timestamp (que é UTC por definição)
                    start_ts = dt.replace(tzinfo=timezone.utc).timestamp()
            
            # Check for invalid file ("moov atom not found")
            if "moov atom not found" in output:
                return None, None # Arquivo ainda sendo gravado ou corrompido

            return start_ts, duration

        except Exception as e:
            print(f"[Indexer] Erro lendo metadata {filepath}: {e}")
            return None, None

class StreamIngestor(threading.Thread):
    def __init__(self, camera_id, rtsp_url, db_manager):
        super().__init__()
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.db = db_manager
        self.running = False
        self.save_dir = os.path.join(STORAGE_ROOT, camera_id)
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Start Indexer Sidecar
        self.indexer = IndexerThread(camera_id, self.save_dir, db_manager)

    def run(self):
        self.running = True
        self.indexer.start() # Start watcher
        
        print(f"[NVR] Iniciando gravação: {self.camera_id}")
        
        # Segmentação automática pelo FFmpeg (Chunks de 1 min)
        # -reset_timestamps 1 eh vital
        
        # FFmpeg Path Resolution
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        monitor_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ffmpeg_bin = os.path.join(monitor_root, "go2rtc_bin", "ffmpeg.exe")
        
        cmd = [
            ffmpeg_bin,
            "-hide_banner", "-loglevel", "error",
            "-rtsp_transport", "tcp",
            "-use_wallclock_as_timestamps", "1", # TRUST PC CLOCK, NOT CAMERA
            "-fflags", "+genpts", # Fix missing timestamp headers
            "-i", self.rtsp_url,
            "-c:v", "libx264", 
            "-preset", "ultrafast", 
            "-pix_fmt", "yuv420p", 
            "-force_key_frames", "expr:gte(t,n_forced*2)", 
            "-c:a", "aac", 
            "-f", "segment",
            "-segment_time", "10",
            "-segment_format", "mp4",
            "-reset_timestamps", "1",
            "-strftime", "1", 
            os.path.join(self.save_dir, "%Y%m%d_%H%M%S.mp4")
        ]
        
        self.process = subprocess.Popen(cmd)
        self.process.wait()

class NVREngine:
    def __init__(self):
        self.db = DatabaseManager()
        self.recorders = []

    def start_recording(self, camera_map):
        """ camera_map = {'cam1': 'rtsp://...'} """
        for cam_id, url in camera_map.items():
            ingestor = StreamIngestor(cam_id, url, self.db)
            ingestor.start()
            self.recorders.append(ingestor)

    def stop_recording(self):
        print("[NVR] Parando gravações...")
        for rec in self.recorders:
            rec.running = False
            rec.indexer.running = False
            if hasattr(rec, 'process') and rec.process:
                rec.process.terminate()
        print("[NVR] Gravações encerradas.")


if __name__ == "__main__":
    # Teste de Arquitetura
    print("--- INICIANDO NVR ENTERPRISE CORE (TEST) ---")
    nvr = NVREngine()
    # Simulação de start
    # nvr.start_recording({'teste_cam': 'rtsp://127.0.0.1:8554/piscina'})
    # while True: time.sleep(1)
