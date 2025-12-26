import sqlite3
import subprocess
import os
import sys

# Config
DB_FILE = os.path.join('desktop_app', 'cameras.db')
ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'go2rtc_bin', 'ffmpeg.exe'))

def get_cameras():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT mac, name, ip, username, password, stream_url FROM cameras")
    rows = c.fetchall()
    conn.close()
    return rows

def update_camera_url(mac, url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE cameras SET stream_url = ? WHERE mac = ?", (url, mac))
    conn.commit()
    conn.close()
    print(f"\n[SUCESSO] URL atualizada no banco para: {url}")

def test_stream(url):
    print(f"Testando: {url} ... ", end='', flush=True)
    try:
        cmd = [ffmpeg_path, "-hide_banner", "-rtsp_transport", "tcp", "-i", url, "-t", "1", "-f", "null", "-"]
        # Timeout Generoso
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        if res.returncode == 0:
            print("OK! (Conectado)")
            return True
        else:
            print(f"Falhou (Erro ffmpeg: {res.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print("Timeout (15s)")
        return False
    except FileNotFoundError:
        print("Erro: ffmpeg não encontrado no PATH.")
        return False

def main():
    print("=== FERRAMENTA DE CORREÇÃO DE CÂMERA ICSEE ===")
    
    # 1. Listar Câmeras
    cameras = get_cameras()
    if not cameras:
        print("Nenhuma câmera encontrada no banco.")
        return

    print("\nCâmeras encontradas:")
    for i, cam in enumerate(cameras):
        print(f"{i+1}. {cam[1]} (IP: {cam[2]}) - URL Atual: {cam[5]}")

    # 2. Selecionar
    try:
        sel = int(input("\nDigite o número da câmera que parou de funcionar: ")) - 1
        if sel < 0 or sel >= len(cameras):
            raise ValueError
    except:
        print("Seleção inválida.")
        return

    target = cameras[sel]
    mac, name, ip, user, pwd, old_url = target
    
    print(f"\nDiagnostico para: {name} ({ip})")
    print(f"Usuario: {user} | Senha: {pwd}")
    
    # 3. Lista de URLs Potenciais para ICSEE
    candidates = [
        # Tenta preservar a antiga se não for a genérica ruim
        old_url,
        # ICSEE Porta 34567 (Protocolo Nativo/RTSP Custom)
        f"rtsp://{user}:{pwd}@{ip}:34567/user={user}&password={pwd}&channel=1&stream=0.sdp?",
        # ICSEE Porta 554 Direta
        f"rtsp://{user}:{pwd}@{ip}:554/user={user}&password={pwd}&channel=1&stream=0.sdp?",
        # ICSEE Alternativa
        f"rtsp://{user}:{pwd}@{ip}:554/live/0/admin/{pwd}", 
        # ONVIF Genérico
        f"rtsp://{user}:{pwd}@{ip}:554/live/ch1",
        f"rtsp://{user}:{pwd}@{ip}:554/11"
    ]
    
    # Remove duplicadas e vazias
    candidates = list(dict.fromkeys([c for c in candidates if c]))

    valid_url = None
    
    # 4. Testar
    for url in candidates:
        if url.endswith(":554/"): # Ignora a raiz quebrada
            continue
            
        if test_stream(url):
            valid_url = url
            break
            
    if valid_url:
        print(f"\n>>> SOLUÇÃO ENCONTRADA:\n{valid_url}")
        conf = input("Deseja salvar essa URL no banco? (S/N): ")
        if conf.upper() == 'S':
            update_camera_url(mac, valid_url)
            print("Reinicie o servidor web para aplicar.")
    else:
        print("\n[ERRO] Nenhuma URL funcionou. Verifique se a câmera está online, se a senha está correta e se o IP não mudou.")

if __name__ == "__main__":
    main()
