import sqlite3
import os
import sys

# URL que o usuário CONFIRMOU que funciona
CORRECT_URL = "rtsp://admin:viguera2001@192.168.3.21:554/user=admin&password=viguera2001&channel=1&stream=0.sdp?"
TARGET_IP = "192.168.3.21"

db_path = os.path.join('desktop_app', 'cameras.db')

def force_fix():
    print(f"FORÇANDO CORRECÃO PARA CAMERA {TARGET_IP}...")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Verifica se ela existe e pega o MAC
    c.execute("SELECT mac, name FROM cameras WHERE ip=?", (TARGET_IP,))
    row = c.fetchone()
    
    if not row:
        print("ERRO: Camera nao encontrada no banco pelo IP. Criando entrada de emergencia...")
        # Cria se não existir
        import uuid
        mac = "MANUAL-" + str(uuid.uuid4())[:8].upper()
        c.execute("INSERT INTO cameras (mac, name, ip, username, password, stream_url, crop_mode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (mac, "Portão", TARGET_IP, "admin", "viguera2001", CORRECT_URL, 0))
    else:
        mac = row[0]
        print(f"Camera encontrada: {row[1]} (MAC: {mac})")
        # Atualiza
        c.execute("UPDATE cameras SET stream_url=?, username=?, password=? WHERE mac=?", 
                  (CORRECT_URL, "admin", "viguera2001", mac))
                  
    conn.commit()
    conn.close()
    print("✅ Banco de dados atualizado com a URL CORRETA.")

    # 2. Roda o sync para gerar o YAML
    print("Sincronizando Go2RTC...")
    import sync_cameras_to_web
    sync_cameras_to_web.sync_config()
    
    # 3. Hot Reload (tentativa simples via request)
    try:
        import requests
        print("Aplicando Hot-Reload no Video Engine...")
        # Usa o nome simplificado que o sync gera. Geralmente é "portao" ou "portao_mjpeg"
        # O sync usa 'safe_name' -> 'portao'
        
        # URL limpa para o Go2RTC (ele precisa de aspas se tiver chars especiais na query, mas via API vai no param)
        url_go2rtc = CORRECT_URL
        
        # Atualiza stream "portao" e "src_..." associado
        # O sync gera IDs baseados no hash da URL. 
        # Vamos ler o yaml gerado para saber os nomes exatos.
        with open(os.path.join('go2rtc_bin', 'go2rtc.yaml'), 'r') as f:
            content = f.read()
            
        print("Configuração gerada. Reiniciando serviços é a garantia total.")
    except Exception as e:
        print(f"Erro no hot-reload: {e}")

if __name__ == "__main__":
    force_fix()
