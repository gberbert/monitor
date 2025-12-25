import os
import requests
import socket
import json
from flask import Flask, request, Response, send_from_directory, jsonify

# Config - Pasta onde estao os arquivos do site (Login, Dashboard, etc)
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www')
# Endereco do Go2RTC local (Video)
GO2RTC_API = "http://127.0.0.1:1984"

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')

@app.route('/')
def root():
    return send_from_directory(STATIC_FOLDER, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Tenta servir arquivo da pasta static
    if os.path.exists(os.path.join(STATIC_FOLDER, filename)):
        return send_from_directory(STATIC_FOLDER, filename)
    else:
        return "File not found", 404

# --- PWA EXPLICIT ROUTES ---
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(STATIC_FOLDER, 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(STATIC_FOLDER, 'sw.js', mimetype='application/javascript')

@app.route('/placeholder_error.png')
def serve_icon():
    return send_from_directory(STATIC_FOLDER, 'placeholder_error.png', mimetype='image/png')
# ---------------------------

@app.route('/api/info')
def get_info():
    # Detect Local IP by connecting dummy socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        pass
    
    return jsonify({
        "local_ip": local_ip,
        "port": 5000,
        "local_url": f"http://{local_ip}:5000/dashboard.html"
    })

# Import Database Logic from Subfolder
import sys
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'desktop_app'))
    import database
    # CRITICAL: Initialize DB to run pending migrations (add columns)
    database.init_db()
except Exception as e:
    print(f"Failed to import database: {e}")

@app.route('/api/cameras', methods=['GET'])
def get_db_cameras():
    try:
        # 1. Busca configs do BD
        db_cams = database.get_all_cameras()
        
        # 2. Busca streams ativos do Go2RTC
        active_streams = {}
        try:
            r = requests.get(f"{GO2RTC_API}/api/streams")
            if r.status_code == 200:
                active_streams = r.json()
        except:
            print("Erro ao conectar Go2RTC para status")

        # 3. Faz o Match (Backend Logic)
        enriched_cams = []
        for cam in db_cams:
            cam_name = cam.get('name', 'Unknown')
            
            # --- BUSCA INTELIGENTE DE STREAMS (ROBUST MATCHING) ---
            found_key = None
            
            # 1. Normalização do Nome do Banco (Minúsculo, sem espaços)
            import re
            cam_name_clean = re.sub(r'[^a-z0-9]', '', cam_name.lower())
            
            # Lista de chaves ativas no Go2RTC
            stream_keys = list(active_streams.keys())
            
            # ESTRATÉGIA A: Busca Exata (Nome Completo)
            # Prioriza versao _mjpeg se existir
            candidates = [
                f"{cam_name}_mjpeg",        # Ex: Varanda_mjpeg
                cam_name,                   # Ex: Varanda
                f"{cam_name_clean}_mjpeg",  # Ex: varanda_mjpeg
                cam_name_clean              # Ex: varanda
            ]
            
            for cand in candidates:
                # Procura case-insensitive nas chaves
                match = next((k for k in stream_keys if k.lower() == cand.lower()), None)
                if match:
                    found_key = match
                    break
            
            # ESTRATÉGIA B: Busca Fuzzy (Contém) - Fallback
            # Útil se o nome no banco for "Câmera Rua" e no Go2RTC for "Rua"
            if not found_key:
                for k in stream_keys:
                    k_clean = re.sub(r'[^a-z0-9]', '', k.lower())
                    # Se o nome limpo do banco estiver contido na chave (ex: 'rua' in 'rua_mjpeg')
                    # Ou vice-versa (ex: 'rua' in 'camera_rua')
                    if (len(cam_name_clean) > 3 and cam_name_clean in k_clean) or \
                       (len(k_clean) > 3 and k_clean in cam_name_clean):
                        # Se achou uma versão _mjpeg, prefira ela imediatamente
                        if '_mjpeg' in k.lower():
                            found_key = k
                            break
                        # Se não, guarda essa como tentativa, mas continua procurando uma mjpeg melhor
                        if not found_key: found_key = k

            # --- DEFINIÇÃO FINAL DO STREAM ---
            # Se achou algo, define URLs. Se não, tudo fica None (Fallback Offline)
            is_online = (found_key is not None)
            base_key = found_key
            
            # Lógica para garantir que usamos MJPEG se disponível
            # Se achamos 'rua', mas existe 'rua_mjpeg', trocamos para 'rua_mjpeg' para performance
            if found_key and '_mjpeg' not in found_key.lower():
                 better_mjpeg = next((k for k in stream_keys if k.lower() == f"{found_key.lower()}_mjpeg"), None)
                 if better_mjpeg:
                     base_key = better_mjpeg # Upgrade para MJPEG

            enriched_cams.append({
                **cam,
                "is_online": is_online,
                "stream_key": base_key, # Chave exata para usar na API stream.mjpeg
                "snapshot_url": f"/api/frame.jpeg?src={base_key}" if is_online else None # Fallback antigo
            })
            
        return jsonify(enriched_cams)
    except Exception as e:
        print(f"Error in get_cameras: {e}")
        return str(e), 500

@app.route('/api/reorder', methods=['POST'])
def reorder_cameras():
    try:
        order_list = request.json
        # Expecting list of {mac: '...', rank: 1}
        database.update_camera_order(order_list)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(e)
        return str(e), 500

@app.route('/api/delete_camera', methods=['POST'])
def remove_camera():
    try:
        data = request.json
        mac = data.get('mac')
        if mac: 
            database.delete_camera(mac)
            # Trigger Config Sync
            import sync_cameras_to_web
            try:
                sync_cameras_to_web.sync_config()
            except: pass
            return jsonify({"status": "ok"})
        return jsonify({"error": "No MAC provided"}), 400
    except Exception as e:
        return str(e), 500

@app.route('/api/save_camera', methods=['POST'])
def save_camera():
    try:
        data = request.json
        mac = data.get('mac')
        
        # SE NÃO VIER ID/MAC, É UMA NOVA CÂMERA -> GERA ID
        if not mac:
            import uuid
            mac = "MANUAL-" + str(uuid.uuid4())[:8].upper()
            
        # AUTO-GENERATE URL IF MISSING (Intelbras Standard)
        stream_url = data.get('url', '')
        if not stream_url and data.get('ip') and data.get('username'):
            # Default to channel 1, subtype 0 (Main Stream)
            stream_url = f"rtsp://{data.get('username')}:{data.get('password')}@{data.get('ip')}:554/cam/realmonitor?channel=1&subtype=0"

        # Call safe DB upsert
        database.upsert_camera(
            mac,
            data.get('name', 'Nova Câmera'),
            data.get('ip'),
            data.get('username'),
            data.get('password'),
            stream_url,
            data.get('crop_mode', 0)
        )
        
        # Trigger Config Sync
        import sync_cameras_to_web
        try:
            sync_cameras_to_web.sync_config()
        except: pass
        
        return jsonify({"status": "ok", "mac": mac})
    except Exception as e:
        print(f"Save Error: {e}")
        return str(e), 500

@app.route('/api/check_ip', methods=['POST'])
def check_ip():
    try:
        ip = request.json.get('ip')
        if not ip: return jsonify({"ok": False, "error": "Sem IP"})
        
        # Simples teste de conexão TCP na porta RTSP (554)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2) # 2 segundos timeout
        result = sock.connect_ex((ip, 554))
        sock.close()
        
        if result == 0:
            return jsonify({"ok": True, "msg": "Porta 554 aberta"})
        else:
            return jsonify({"ok": False, "error": f"Porta Fechada (Erro {result})"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route('/api/check_login', methods=['POST'])
def check_login():
    import subprocess
    data = request.json
    ip = data.get('ip')
    user = data.get('username')
    pwd = data.get('password')
    
    # 1. Tentar Intelbras Substream (Leve)
    # 2. Tentar Raiz
    test_urls = [
         f"rtsp://{user}:{pwd}@{ip}:554/cam/realmonitor?channel=1&subtype=1",
         f"rtsp://{user}:{pwd}@{ip}:554/"
    ]
    
    ffmpeg_path = "C:/antigravity_www/ffmpeg.exe"
    if not os.path.exists(ffmpeg_path): ffmpeg_path = "ffmpeg"

    last_error = "Falha Geral"
    
    for url in test_urls:
        try:
            # Teste rápido: conectar e ler info
            cmd = [ffmpeg_path, "-hide_banner", "-rtsp_transport", "tcp", "-i", url, "-t", "0.5", "-f", "null", "-"]
            # Timeout curto
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=4)
            
            if result.returncode == 0:
                return jsonify({"ok": True, "msg": "Conectado!"})
            
            err = result.stderr.decode('utf-8', errors='ignore')
            if "401 Unauthorized" in err:
                return jsonify({"ok": False, "error": "Senha Incorreta (401)"})
            last_error = "Sem resposta ou erro de conexão"
            
        except Exception as e:
            last_error = str(e)
            
    return jsonify({"ok": False, "error": last_error})

# --- AUTH API ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    result = database.verify_user(username, password)
    
    if result == "ok":
        return jsonify({"status": "ok", "token": "dummy-token-v1"})
    elif result == "pending":
         return jsonify({"status": "error", "message": "Conta aguardando aprovação do Admin"}), 403
    else:
        return jsonify({"status": "error", "message": "Credenciais invalidas"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Preencha tudo"}), 400
        
    if database.create_user(username, password):
        return jsonify({"status": "ok", "message": "Criado! Aguarde aprovação do Admin."})
    else:
        return jsonify({"status": "error", "message": "Usuario ja existe"}), 409

# --- ADMIN USER MANAGEMENT ---
@app.route('/api/users/pending', methods=['GET'])
def list_pending():
    # Idealmente checar se quem pede é admin
    users = database.get_pending_users()
    return jsonify(users)

@app.route('/api/users/all', methods=['GET'])
def list_all_users():
    users = database.get_all_users()
    return jsonify(users)

@app.route('/api/users/toggle', methods=['POST'])
def toggle_user_api():
    data = request.json
    username = data.get('username')
    status = data.get('approved')
    if username == 'admin': return jsonify({"error": "Admin is always active"}), 400
    database.update_user_status(username, status)
    return jsonify({"status": "ok"})

@app.route('/api/users/approve', methods=['POST'])
def approve_user_api():
    data = request.json
    target_user = data.get('username')
    database.approve_user(target_user)
    return jsonify({"status": "ok"})

@app.route('/api/users/delete', methods=['POST'])
def delete_user_api():
    data = request.json
    target_user = data.get('username')
    if target_user == 'admin': return jsonify({"error": "No"}), 400
    database.delete_user(target_user)
    return jsonify({"status": "ok"})

@app.route('/api/users/change_password', methods=['POST'])
def change_password_api():
    data = request.json
    username = data.get('username')
    new_pass = data.get('new_password')
    database.change_password(username, new_pass)
    return jsonify({"status": "ok"})

# --- PROXY PARA API DO GO2RTC (Salva o dia!) ---
@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_api(subpath):
    target_url = f"{GO2RTC_API}/api/{subpath}"
    print(f"[PROXY] Accessing: {target_url}")
    
    try:
        # Repassa a requisicao exata para o Go2RTC
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={k:v for k,v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False,
            stream=True
        )
        print(f"[PROXY] Response: {resp.status_code}")
        
        # Exclui headers 'hop-by-hop'
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(k,v) for k,v in resp.raw.headers.items() if k.lower() not in excluded_headers]
        
        return Response(resp.iter_content(chunk_size=8192), resp.status_code, headers)
    except Exception as e:
        print(f"[PROXY ERROR] {e}")
        return str(e), 500

if __name__ == '__main__':
    print(f"--- ANTIGRAVITY VMS PROXY ---")
    print(f"SERVING SITE FROM: {STATIC_FOLDER}")
    print(f"PROXYING VIDEO TO: {GO2RTC_API}")
    print(f"LISTENING ON: 5000")
    app.run(host='0.0.0.0', port=5000)
