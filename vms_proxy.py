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
            
            # --- Lógica de Match do Go2RTC ---
            # O Go2RTC pode ter chaves como 'Minha_Camera', 'Minha_Camera_mjpeg', etc.
            # Vamos tentar achar a chave "principal"
            
            found_key = None
            
            # Candidatos normais e suas versoes minusculas
            raw_candidates = [
                cam_name,
                cam_name.replace(" ", "_"),
                cam_name.replace("(", "").replace(")", "").strip(),
                cam_name.replace(" ", "").replace("(", "").replace(")", "")
            ]
            
            candidates = []
            for c in raw_candidates:
                candidates.append(c)
                candidates.append(c.lower()) # CRITICO: Go2RTC usa minusculo (ex: rua_base)
            
            # Verifica exatos
            for k in candidates:
                if k in active_streams: found_key = k; break
                if f"{k}_mjpeg" in active_streams: found_key = f"{k}_mjpeg"; break
            
            # Verifica Fuzzy (Contém) se nao achou
            if not found_key:
                # Normaliza: tudo minusculo, sem especial
                import re
                safe_db = re.sub(r'[^a-z0-9]', '', cam_name.lower())
                
                for stream_key in active_streams.keys():
                    safe_stream = re.sub(r'[^a-z0-9]', '', stream_key.lower())
                    # Se um contiver o outro (evitar falso positivo muito curto)
                    if len(safe_db) > 3 and safe_db in safe_stream:
                        found_key = stream_key
                        break

            # Monta Objeto Final
            is_online = (found_key is not None)
            
            # Se achou chave ex: 'Rua_mjpeg', a chave 'base' pro player deve ser 'Rua'
            base_key = found_key
            snapshot_key = found_key # Padrao: usa a propria chave

            if found_key:
                 # Normaliza para achar a raiz
                 if found_key.endswith('_mjpeg'):
                     base_key = found_key.replace('_mjpeg', '')
                 elif found_key.endswith('_src'):
                     base_key = found_key.replace('_src', '')
                 else:
                     base_key = found_key

                 # Se existir uma versao MJPEG explicita, use ela para o SNAPSHOT (mais rapido/confiavel)
                 if f"{base_key}_mjpeg" in active_streams:
                     snapshot_key = f"{base_key}_mjpeg"
                 # Se nao, usa a propria (vai forçar transcode no Go2RTC, pode ser lento)
                
            enriched_cams.append({
                **cam,
                "is_online": is_online,
                "stream_key": base_key if found_key else None,
                "snapshot_url": f"/api/frame.jpeg?src={snapshot_key}" if found_key else "placeholder_error.png"
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

@app.route('/api/save_camera', methods=['POST'])
def save_camera():
    try:
        data = request.json
        # Call safe DB upsert
        database.upsert_camera(
            data.get('mac'),
            data.get('name'),
            data.get('ip'),
            data.get('username'),
            data.get('password'),
            data.get('url'),
            data.get('crop_mode', 0)
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Save Error: {e}")
        return str(e), 500

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
