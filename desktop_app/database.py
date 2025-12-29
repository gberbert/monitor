import sqlite3
import os
import json
import time
import threading

DB_FILE = os.path.join(os.path.dirname(__file__), 'cameras.db')
JSON_FILE = os.path.join(os.path.dirname(__file__), 'cameras.json')

# Lock Global para Evitar Crash de Concorrência
db_lock = threading.Lock()

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL;") # Melhor Concorrência
        # Tabela Robusta para Câmeras
        c.execute('''
            CREATE TABLE IF NOT EXISTS cameras (
                mac TEXT PRIMARY KEY,
                name TEXT,
                ip TEXT,
                port INTEGER,
                username TEXT,
                password TEXT,
                stream_url TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crop_mode INTEGER DEFAULT 0
            )
        ''')
        
        # Migração Segura: Adiciona coluna se não existir
        try:
            c.execute("ALTER TABLE cameras ADD COLUMN crop_mode INTEGER DEFAULT 0")
        except: 
            pass 

        try:
            c.execute("ALTER TABLE cameras ADD COLUMN display_rank INTEGER DEFAULT 999")
        except:
            pass

        # Migration: timeout para conexao RTSP
        try:
            c.execute("ALTER TABLE cameras ADD COLUMN timeout INTEGER DEFAULT 25")
        except:
            pass

        # Migration: Config NVR
        try:
            c.execute("ALTER TABLE cameras ADD COLUMN record_enabled INTEGER DEFAULT 1")
        except:
            pass
        try:
            c.execute("ALTER TABLE cameras ADD COLUMN retention_days INTEGER DEFAULT 7")
        except:
            pass

        # Tabela de Usuarios
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                approved INTEGER DEFAULT 0
            )
        ''')
        
        # Migration: Adiciona coluna approved se nao existir
        try:
            c.execute("ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 0")
        except:
            pass

        # Garante que Admin e aprovado
        try:
            c.execute("INSERT OR IGNORE INTO users (username, password, approved) VALUES (?, ?, ?)", ('admin', 'admin', 1))
            c.execute("UPDATE users SET approved=1 WHERE username='admin'") # Força aprovacao do admin antigo
        except:
            pass

        # Tabela de Configuracoes Globais
        c.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Defaults
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('storage_path', 'go2rtc_bin/storage')")
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('disk_quota_gb', '500')")

        conn.commit()
        conn.close()

def get_config(key, default=None):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else default

def set_config(key, value):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

def create_user(username, password):
    with db_lock:
        try:
            conn = get_connection()
            c = conn.cursor()
            # Por padrao cria DESAPROVADO (0)
            c.execute("INSERT INTO users (username, password, approved) VALUES (?, ?, 0)", (username, password))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

def verify_user(username, password):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT password, approved FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        
        # Verifica senha E aprovacao
        if result and result[0] == password:
            if result[1] == 1:
                return "ok"
            else:
                return "pending"
        return "invalid"

def get_pending_users():
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE approved = 0")
        users = [row[0] for row in c.fetchall()]
        conn.close()
        return users

def get_all_users():
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT username, approved FROM users")
        rows = c.fetchall()
        conn.close()
        
    return [{"username": r[0], "approved": bool(r[1]), "is_admin": (r[0]=='admin')} for r in rows]

def approve_user(username):
    update_user_status(username, True)

def update_user_status(username, approved):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        val = 1 if approved else 0
        c.execute("UPDATE users SET approved = ? WHERE username = ?", (val, username))
        conn.commit()
        conn.close()


def delete_user(username):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()

def change_password(username, new_pass):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET password = ? WHERE username = ?", (new_pass, username))
        conn.commit()
        conn.close()
        
        # Migração Automática (JSON -> SQL)
        if os.path.exists(JSON_FILE) and not os.path.exists(DB_FILE + ".migrated"):
            pass 
            
    if os.path.exists(JSON_FILE) and not os.path.exists(DB_FILE + ".migrated"):
        migrate_from_json()

def migrate_from_json():
    print("Migrando dados do JSON para SQLite...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for cam in data:
            import re
            user = "admin"
            password = ""
            ip = ""
            url = cam.get('url', '')
            match = re.search(r'//(.*?):(.*?)@', url)
            if match:
                user = match.group(1)
                password = match.group(2)
            ip_match = re.search(r'@(.*?):', url) or re.search(r'//(.*?):', url)
            if ip_match:
                ip = ip_match.group(1).split('@')[-1]

            mac = cam.get('mac')
            if not mac: mac = f"UNKNOWN-{ip}"
            
            upsert_camera(mac, cam.get('name', 'Camera Importada'), ip, user, password, url)
            
        with open(DB_FILE + ".migrated", 'w') as f: f.write("OK")
    except Exception as e:
        print(f"Erro na migracao: {e}")

def upsert_camera(mac, name, ip, user, password, url, crop_mode=0, timeout=25, record_enabled=1, retention_days=7):
    """Insere ou Atualiza uma câmera baseado no MAC"""
    mac = mac.strip().upper() 
    print(f"DEBUG: DB UPSERT | MAC: {mac} | URL: {url} | REC: {record_enabled}")
    
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM cameras WHERE mac = ?", (mac,))
        exists = c.fetchone()
        
        if exists:
            # Update
            c.execute('''
                UPDATE cameras 
                SET ip = ?, username = ?, password = ?, stream_url = ?, crop_mode = ?, timeout = ?, record_enabled = ?, retention_days = ?, last_seen = CURRENT_TIMESTAMP
                WHERE mac = ?
            ''', (ip, user, password, url, crop_mode, timeout, record_enabled, retention_days, mac))
        else:
            # New camera
            c.execute('''
                INSERT INTO cameras (mac, name, ip, username, password, stream_url, crop_mode, timeout, record_enabled, retention_days, display_rank)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 999)
            ''', (mac, name, ip, user, password, url, crop_mode, timeout, record_enabled, retention_days))
            
        conn.commit()
        conn.close()

def update_camera_order(order_list):
    """
    Updates the display rank for a batch of cameras.
    order_list: list of dicts [{'mac': '...', 'rank': 1}, ...]
    """
    print(f"UPDATING ORDER: {len(order_list)} items")
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        try:
            for item in order_list:
                c.execute("UPDATE cameras SET display_rank = ? WHERE mac = ?", (item['rank'], item['mac']))
            conn.commit()
            print("Order updated successfully.")
        except Exception as e:
            print(f"Failed to update order: {e}")
        finally:
            conn.close()

def get_all_cameras():
    with db_lock:
        conn = get_connection()
        conn.row_factory = sqlite3.Row 
        c = conn.cursor()
        # Sort by user rank, then name
        c.execute("SELECT * FROM cameras ORDER BY display_rank ASC, name ASC")
        rows = c.fetchall()
        conn.close()
    
    cameras = []
    for r in rows:
        # Fallback seguro
        crop = 0
        rank = 999
        timeout = 25
        rec = 1
        ret = 7
        try: crop = r['crop_mode']
        except: pass
        try: rank = r['display_rank']
        except: pass
        try: timeout = r['timeout'] if r['timeout'] else 25
        except: pass
        try: rec = r['record_enabled'] if r['record_enabled'] is not None else 1
        except: pass
        try: ret = r['retention_days'] if r['retention_days'] is not None else 7
        except: pass
        
        cameras.append({
            "mac": r["mac"],
            "name": r["name"],
            "ip": r["ip"],
            "username": r["username"],
            "password": r["password"],
            "rtsp_url": r["stream_url"],
            "crop_mode": crop,
            "rank": rank,
            "timeout": timeout,
            "record_enabled": rec,
            "retention_days": ret
        })
    return cameras

def delete_camera(mac):
    with db_lock:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM cameras WHERE mac = ?", (mac,))
        conn.commit()
        conn.close()
