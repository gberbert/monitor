import requests

API = "http://127.0.0.1:1984/api/streams"

def log(m): print(f"[HOTFIX V2] {m}")

def run():
    # 1. Criar o NOVO source (ID calculado pelo sync.py com a nova senha)
    # src_3bc6ecf4
    new_src_id = "src_3bc6ecf4"
    new_url = "rtsp://admin:vigueraberbert%402025@192.168.3.125:554/cam/realmonitor?channel=1&subtype=0"
    
    log(f"Criando source {new_src_id}...")
    r = requests.put(API, params={"src": new_src_id, "url": new_url})
    log(f"Status Source: {r.status_code} {r.text}")
    
    # 2. Atualizar o channel 'porteiro' para usar esse novo source
    # O sync define: porteiro: ffmpeg:src_3bc6ecf4#video=h264#vf=scale=1920:1080
    channel_cmd = f"ffmpeg:{new_src_id}#video=h264#vf=scale=1920:1080"
    
    log(f"Atualizando channel 'porteiro' -> {channel_cmd}")
    r2 = requests.put(API, params={"src": "porteiro", "url": channel_cmd})
    log(f"Status Channel: {r2.status_code} {r2.text}")

if __name__ == "__main__":
    run()
