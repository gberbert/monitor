import requests
import json
import time

print("--- DIAGNOSTICO GO2RTC ---")
try:
    # 1. Check API Connection
    print("Conectando na API do Go2RTC (1984)...")
    r = requests.get("http://127.0.0.1:1984/api/streams", timeout=2)
    data = r.json()
    
    print("API OK. Verificando streams...")
    
    # 2. Check Source Stream (RTSP -> Go2RTC)
    if "pool_cam_src" in data:
        src = data["pool_cam_src"]
        producers = src.get("producers", [])
        if producers:
            print(f"[OK] Camera FÍSICA conectada! (Source active)")
        else:
            print(f"[FALHA] Camera FÍSICA não conectou! (Verifique IP/Senha/Rede)")
    else:
        print("[ERRO] Stream 'pool_cam_src' não existe na config!")

    # 3. Check Transcoded Stream (FFmpeg -> Go2RTC)
    if "pool_cam" in data:
        dst = data["pool_cam"]
        producers = dst.get("producers", [])
        if producers:
            print(f"[OK] FFmpeg rodando! (Transcoded stream active)")
        else:
            print(f"[FALHA] FFmpeg não iniciou! (Transcoding fail)")
            print("Causa provavel: Caminho do FFmpeg incorreto ou erro na execução.")
    else:
        print("[ERRO] Stream 'pool_cam' não existe na config!")
        
    #print(json.dumps(data, indent=2))

except Exception as e:
    print(f"\n[CRITICO] Não foi possível conectar no Go2RTC: {e}")
    print("Verifique se a janela preta do Go2RTC está aberta.")
