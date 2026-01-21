from flask import Flask, jsonify, request, send_from_directory
import os
import sqlite3
import datetime

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminho para storage do Go2RTC
STORAGE_DIR = os.path.join(BASE_DIR, "go2rtc_bin", "storage")
DB_PATH = os.path.join(BASE_DIR, "monitor.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "test_lab_hd", "nvr_module") # timeline_demo.html está aqui

app = Flask(__name__)
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    print("Warning: flask_cors not installed. CORS disabled.")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory(TEMPLATE_DIR, 'timeline_demo.html')

@app.route('/api/nvr/timeline')
def timeline():
    camera_id = request.args.get('camera', 'piscina')
    # Recebe timestamps Unix
    import time
    now = time.time()
    try:
        start_ts = float(request.args.get('start', now - 86400))
        end_ts = float(request.args.get('end', now))
        
        # O banco usa ISO Strings
        start_iso = datetime.datetime.fromtimestamp(start_ts).isoformat()
        end_iso = datetime.datetime.fromtimestamp(end_ts).isoformat()
    except:
        start_iso = datetime.datetime.now().isoformat()
        end_iso = datetime.datetime.now().isoformat()

    conn = get_db_connection()
    c = conn.cursor()
    
    # Query na tabela 'videos' - Schema: start_time, end_time, file_path
    query = """
        SELECT start_time, end_time, file_path 
        FROM videos 
        WHERE camera_name = ? 
        AND end_time >= ? 
        AND start_time <= ?
        ORDER BY start_time ASC
    """
    
    # Smart Lookup Check
    has_videos = False
    try:
        c.execute(query, (camera_id, start_iso, end_iso))
        rows = c.fetchall()
        if len(rows) > 0: has_videos = True
    except: rows = []

    # LOGGER DEBUG
    def log_debug(msg):
        try:
            with open("api_debug.log", "a") as f:
                f.write(f"{datetime.datetime.now()} [DEBUG] {msg}\n")
        except: pass

    resolved_camera = camera_id

    try:
        if not has_videos:
            log_debug(f"--- SMART LOOKUP START for {camera_id} ---")
            try:
                cam_db_path = os.path.join(BASE_DIR, "desktop_app", "cameras.db")
                
                if os.path.exists(cam_db_path):
                    cdb = sqlite3.connect(cam_db_path)
                    cc = cdb.cursor()
                    
                    # Helper Name normalization
                    def safe_name_py(n):
                        import re, unicodedata
                        try:
                            s = n.lower()
                            s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
                            s = re.sub(r'[^a-z0-9]', '_', s)
                            s = re.sub(r'_+', '_', s)
                            return s.strip('_')
                        except: return "unknown"

                    # Get Cameras
                    try:
                        cc.execute("SELECT name, rtsp_url, ip FROM cameras")
                    except:
                        log_debug("Coluna rtsp_url nao existe? Tentando old schema.")
                        cc.execute("SELECT name, '', ip FROM cameras")
                        
                    all_cams = cc.fetchall()
                    cdb.close()

                    my_url = None
                    my_ip = None
                    
                    # Encontrar Self
                    for name, url, ip in all_cams:
                        s_name = safe_name_py(name)
                        if s_name == camera_id:
                            my_url = url
                            my_ip = ip
                            log_debug(f"Self Found: {name}")
                            break
                    
                    if my_ip or my_url:
                        fallback_candidates = []
                        for name, url, ip in all_cams:
                            s_target = safe_name_py(name)
                            if s_target == camera_id: continue
                            
                            match = False
                            if my_ip and ip and ip == my_ip: match = True
                            if my_url and url and url == my_url: match = True
                            
                            if match:
                                log_debug(f"Matches Sibling: {name}")
                                fallback_candidates.append(s_target)

                        # Check Siblings
                        for cand in fallback_candidates:
                            log_debug(f"Checking {cand}...")
                            c.execute(query, (cand, start_iso, end_iso))
                            rows_sibling = c.fetchall()
                            if len(rows_sibling) > 0:
                                log_debug(f"FOUND {len(rows_sibling)} videos in {cand}!")
                                rows = rows_sibling
                                resolved_camera = cand
                                break # Found
                    else:
                        log_debug("Self not found in external DB (Sync issue?)")
                        
            except Exception as e:
                log_debug(f"EXCEPTION INNER: {e}")
        
        conn.close()
        
        segments = []
        for r in rows:
            # DB returns ISO strings
            try:
                s_dt = datetime.datetime.fromisoformat(r[0])
                e_dt = datetime.datetime.fromisoformat(r[1])
                fname = os.path.basename(r[2])
                
                segments.append({
                    "start": s_dt.timestamp(),
                    "end": e_dt.timestamp(),
                    "filename": fname,
                    "camera": camera_id,       # Logical ID
                    "src_camera": resolved_camera # Physical Folder
                })
            except Exception as e: log_debug(f"Row Parse Error: {e}")
            
        return jsonify(segments)

    except Exception as fatal:
        log_debug(f"FATAL ERROR IN TIMELINE: {fatal}")
        import traceback
        log_debug(traceback.format_exc())
        return jsonify({"error": str(fatal)}), 500

@app.route('/video/<camera_id>/<filename>')
def serve_video(camera_id, filename):
    folder = os.path.join(STORAGE_DIR, camera_id)
    return send_from_directory(folder, filename)

# --- NVR CONFIG ENDPOINTS (Moved from Proxy) ---
@app.route('/api/nvr/config', methods=['GET'])
def get_config_api():
    try:
        # Import DB logic dynamically/locally
        import sys
        sys.path.append(os.path.join(BASE_DIR, 'desktop_app'))
        import database
        
        # Safe Read Helper
        def get_float(k, d):
            try: return float(database.get_config(k, d))
            except: return float(d)

        return jsonify({
            "storage_path": database.get_config('storage_path', 'go2rtc_bin/storage'),
            "disk_quota_gb": get_float('disk_quota_gb', '500'),
            "gemini_api_key": database.get_config('gemini_api_key', ''),
            "gemini_model": database.get_config('gemini_model', 'gemini-3-pro-image-preview'),
            "gemini_model_text": database.get_config('gemini_model_text', 'gemini-2.0-flash-exp'),
            "gemini_prompt_step_a": database.get_config('gemini_prompt_step_a', 'Analise esta imagem de segurança com extrema atenção aos detalhes. Descreva o que você vê, focando em pessoas, veículos e atividades suspeitas.'),
            "gemini_prompt_qa": database.get_config('gemini_prompt_qa', 'Atue como um Auditor de QA de Visão Computacional. Valide se a imagem gerada (Output) corresponde fielmente aos elementos descritos no Prompt Original. Verifique: 1. Coerência dos objetos. 2. Realismo da iluminação. 3. Ausência de alucinações (elementos não solicitados). Dê uma nota de 0 a 10 e uma breve justificativa.')
        })
    except Exception as e:
        log_debug(f"Config GET Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/nvr/config', methods=['POST'])
def set_config_api():
    try:
        data = request.json
        import sys
        sys.path.append(os.path.join(BASE_DIR, 'desktop_app'))
        import database
        
        allowed = ['storage_path', 'disk_quota_gb', 'gemini_api_key', 'gemini_model', 'gemini_model_text', 'gemini_prompt_step_a', 'gemini_prompt_qa']
        for k in allowed:
            if k in data:
                database.set_config(k, data[k])
        
        return jsonify({"status": "ok"})
    except Exception as e:
        log_debug(f"Config POST Error: {e}")
        return jsonify({"error": str(e)}), 500

# Logger Global
def log_debug(msg):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[NVR API] {msg}") # Console
        with open("api_debug.log", "a") as f:
            f.write(f"{ts} [DEBUG] {msg}\n")
    except: pass

@app.route('/api/nvr/enhance', methods=['POST'])
def enhance_image():
    log_debug("--- START ENHANCE REQUEST ---")
    try:
        data = request.json
        
        # Support Dual Image Flow
        img_target_b64 = data.get('image_target') or data.get('image') # Fallback to old field
        img_context_b64 = data.get('image_context')
        
        if not img_target_b64:
            log_debug("Error: No target image provided")
            return jsonify({"error": "No image provided"}), 400

        log_debug(f"Payload: Target={len(img_target_b64)} chars, Context={len(img_context_b64) if img_context_b64 else 0} chars")

        # Parse Base64 Helpers
        import base64
        import numpy as np
        import cv2

        def decode_b64(b64str):
            if ',' in b64str: _, encoded = b64str.split(',', 1)
            else: encoded = b64str
            return encoded, cv2.imdecode(np.frombuffer(base64.b64decode(encoded), np.uint8), cv2.IMREAD_COLOR)

        # Decode Target (Primary)
        encoded_target, img_target = decode_b64(img_target_b64)
        if img_target is None: return jsonify({"error": "Target Decode Failed"}), 400
        
        # Decode Context (Optional)
        encoded_context = None
        if img_context_b64:
            encoded_context, _ = decode_b64(img_context_b64)

        img = img_target # For backward compatibility in logs/processing
        encoded = encoded_target # For backward compatibility

        log_debug(f"Image Decoded: {img.shape[1]}x{img.shape[0]}")

        # 1. Get Config
        cam_db_path = os.path.join(BASE_DIR, "desktop_app", "cameras.db")
        gemini_key = None
        gemini_model_img = "gemini-3-pro-image-preview" # User requested default
        gemini_model_txt = "gemini-2.0-flash-exp"       # User requested default (2.5 -> 2.0 Flash)
        qa_prompt_template = ""
        step_a_prompt = (
            "Aja como um especialista em Computer Vision. Analise as duas imagens anexadas para criar um prompt de restauração de imagem ultra-detalhado.\n"
            "Imagem Ampla (Contexto): Use esta imagem para extrair a 'assinatura visual' da cena: identifique a fonte de iluminação (natural ou artificial), o ângulo exato da câmera, a profundidade de campo e as texturas predominantes no ambiente ao redor.\n"
            "Imagem Cortada (Alvo): Identifique o objeto principal, seus materiais (metal, tecido, vidro, pele), cores exatas e quaisquer obstruções ou sombras que o atravessem.\n"
            "Sua tarefa: Gere um prompt técnico em Inglês para o modelo gemini-3-pro-image-preview focado em Enhanced Clarity and Detail.\n"
            "O prompt gerado deve seguir esta estrutura:\n"
            "Primary Subject: Descrição técnica e morfológica do objeto central no corte, mantendo sua posição original.\n"
            "Environmental Context: Integração do objeto com o chão, paredes ou elementos de fundo vistos na imagem ampla.\n"
            "Lighting & Atmosphere: Descrição da luz e sombras baseada na cena global para garantir realismo.\n"
            "Technical Fidelity: Inclua termos como 'lossless restoration', 'hyper-realistic textures', 'sharp edges', 'high-fidelity reconstruction' e 'strictly no new elements'.\n"
            "Restrição: Não adicione elementos que não existam nas fotos. O objetivo é apenas 'limpar' e 'definir' o que já está presente."
        )
        
        if os.path.exists(cam_db_path):
            try:
                cdb = sqlite3.connect(cam_db_path)
                cc = cdb.cursor()
                cc.execute("SELECT key, value FROM config")
                for k, v in cc.fetchall():
                    if k == 'gemini_api_key': gemini_key = v
                    if k == 'gemini_model': gemini_model_img = v
                    if k == 'gemini_model_text': gemini_model_txt = v
                    if k == 'gemini_model_text': gemini_model_txt = v
                    if k == 'gemini_prompt_step_a' and v and len(v) > 10: step_a_prompt = v
                    if k == 'gemini_prompt_qa': qa_prompt_template = v
                cdb.close()
                log_debug(f"Config Loaded. Key present? {bool(gemini_key)}")
            except Exception as e_db:
                log_debug(f"DB Config Error: {e_db}")

        # 2. Local Enhancement (Base Layer)
        log_debug("Applying OpenCV Filters (Base Layer)...")
        gaussian = cv2.GaussianBlur(img, (0, 0), 3.0)
        unsharp_image = cv2.addWeighted(img, 2.0, gaussian, -1.0, 0)
        processed_img = cv2.convertScaleAbs(unsharp_image, alpha=1.1, beta=10)
        
        ai_prompt = "AI Processing Skipped (No Key)"
        
        # 3. AI TWO-STEP FLOW (Vision -> Image)
        if gemini_key and len(gemini_key) > 5:
            import requests
            
            # --- STEP A: VISION TO PROMPT (Expert Engineering) ---
            log_debug(f"--- STEP A: Analyzing with {gemini_model_txt} (Dual Image: {bool(encoded_context)}) ---")
            
            url_vision = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model_txt}:generateContent?key={gemini_key}"
            
            step_a_prompt = (
                "INSTRUCTION: Act as a Computer Vision Expert. Analyze the TWO attached images (Wide Context + Cropped Target) to write a single, highly detailed image generation prompt for a text-to-image model.\n"
                "GOAL: Restore the Cropped Target with high fidelity using the lighting/environment from Wide Context.\n"
                "OUTPUT FORMAT: Return ONLY the final prompt text. Do NOT write introductions like 'Here is the prompt' or 'As an expert...'. Just the description.\n"
                "PROMPT CONTENT: Describe the subject, material, color, lighting, shadows, and perspective precisely. Use keywords: '8k', 'cctv restoration', 'photorealistic'."
            )
            
            # Override from DB if available and valid
            if os.path.exists(cam_db_path):
                try:
                    cdb = sqlite3.connect(cam_db_path)
                    cc = cdb.cursor()
                    cc.execute("SELECT key, value FROM config")
                    for k, v in cc.fetchall():
                        if k == 'gemini_api_key': gemini_key = v
                        if k == 'gemini_model': gemini_model_img = v
                        if k == 'gemini_model_text': gemini_model_txt = v
                        if k == 'gemini_model_text': gemini_model_txt = v
                        if k == 'gemini_prompt_step_a' and v and len(v) > 10: step_a_prompt = v
                        if k == 'gemini_prompt_qa': qa_prompt_template = v
                    cdb.close()
                except: pass

            expert_system_prompt = step_a_prompt

            # Build Parts
            parts = [{"text": expert_system_prompt}]
            
            if encoded_context:
                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": encoded_context}})
            
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": encoded_target}}) # Target last

            payload_vision = { "contents": [{ "parts": parts }] }
            
            ai_prompt = "AI Processing..."
            
            try:
                r_vis = requests.post(url_vision, json=payload_vision, timeout=25) # Vision pode demorar
                if r_vis.status_code == 200:
                    res_json = r_vis.json()
                    ai_prompt = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # SANITIZATION (Remove Chat Garbage)
                    if ":" in ai_prompt[:25]: # "Here is the prompt: ..."
                        ai_prompt = ai_prompt.split(":", 1)[1].strip()
                    if "prompt" in ai_prompt[:50].lower(): # "The prompt is..."
                        p_idx = ai_prompt.lower().find("prompt")
                        if p_idx >= 0:
                            # Tenta pegar o que vem depois, heuristicamente
                            pass
                    
                    # Remove quotes
                    ai_prompt = ai_prompt.strip().strip('"').strip("'")
                    
                    log_debug(f"STEP A PROMPT GENERATED: {ai_prompt[:150]}...")
                else:
                    log_debug(f"Step A Failed: {r_vis.text}")
            except Exception as e_vis:
                log_debug(f"Step A Exception: {e_vis}")
                ai_prompt = f"Error: {str(e_vis)}"


            # --- STEP B: IMAGE RECONSTRUCTION (Prompt + Original Img) ---
            if "Error" not in ai_prompt and len(ai_prompt) > 10:
                log_debug(f"--- STEP B: Generating Image with {gemini_model_img} (Img2Img Guided) ---")
                
                url_gen = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model_img}:generateContent?key={gemini_key}"
                
                # Combine Generated Prompt with Enforcement
                final_prompt = (
                    f"{ai_prompt} "
                    "Make it photorealistic, 8k resolution, highly detailed, CCTV restoration style."
                )
                
                payload_gen = {
                    "contents": [{
                        "parts": [
                            {"text": final_prompt},
                            # Enviamos a imagem original novamente para REFERENCE/Img2Img se o modelo suportar
                            {"inline_data": {"mime_type": "image/jpeg", "data": encoded}}
                        ]
                    }]
                }
            
            try:
                # Timeout 60s
                r_gen = requests.post(url_gen, json=payload_gen, timeout=60)
                
                if r_gen.status_code == 200:
                    gen_json = r_gen.json()
                    try:
                        b64_img = gen_json['candidates'][0]['content']['parts'][0]['inlineData']['data']
                        
                        if b64_img and len(b64_img) > 1000:
                            log_debug(f"Step B Success! Image Generated ({len(b64_img)} bytes)")
                            gen_arr = np.frombuffer(base64.b64decode(b64_img), np.uint8)
                            gen_cv2 = cv2.imdecode(gen_arr, cv2.IMREAD_COLOR)
                            
                            if gen_cv2 is not None:
                                processed_img = gen_cv2
                                ai_prompt = "AI Enhancement Applied (Img2Img)"
                            else:
                                log_debug("Step B Error: Decode Failed.")
                        else:
                            log_debug("Step B Error: No inlineData.")
                    except KeyError:
                        try:
                            refusal = gen_json['candidates'][0]['content']['parts'][0]['text']
                            log_debug(f"Step B Refusal/Text: {refusal}")
                            ai_prompt = "AI Refusal (Safety?)"
                        except:
                            log_debug(f"Step B Parse Error: {str(gen_json)[:200]}")
                else:
                    log_debug(f"Step B HTTP Error: {r_gen.status_code} - {r_gen.text}")
                    ai_prompt = f"AI Error {r_gen.status_code}"
            except Exception as e_gen:
                log_debug(f"Step B Exception: {e_gen}")
                ai_prompt = "AI Timeout/Error"
        else:
            log_debug("Skipping AI (Key missing)")
            ai_prompt = "AI Skipped (No Key)"
            
        # 4. Encode back to Base64
        _, buffer = cv2.imencode('.jpg', processed_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        img_str = base64.b64encode(buffer).decode('utf-8')
        
        log_debug("Returning Success Response")
        
        return jsonify({
            "success": True,
            "image": f"data:image/jpeg;base64,{img_str}",
            "message": f"AI A: {ai_prompt[:50]}..."
        })

    except Exception as e:
        log_debug(f"FATAL ENHANCE ERROR: {e}")
        import traceback
        log_debug(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("--- NVR API v2 (PORT 5002) ---")
    print(f"Lendo videos de: {STORAGE_DIR}")
    app.run(host='0.0.0.0', port=5002, use_reloader=False)
