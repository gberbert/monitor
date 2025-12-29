import sys
import os
import time
from nvr_core import NVREngine

# Test Configuration
CAMERA_NAME = "piscina"
# RTSP URL from Test Lab Go2RTC (Port 8556) - Trying RAW Source
RTSP_URL = "rtsp://127.0.0.1:8556/src_5187bd74"

def run_test():
    print(f"--- TESTE DE GRAVAÇÃO NVR ---")
    print(f"Target: {CAMERA_NAME} via {RTSP_URL}")
    
    # Init Engine
    engine = NVREngine()
    
    # Start Recording
    print("[1] Iniciando Motor de Gravação...")
    # Passing map: {id: url}
    engine.start_recording({CAMERA_NAME: RTSP_URL})
    
    print("[2] Gravando por 60 segundos (Aguardando chunks de 10s)...")
    # Agora com chunks de 10s, vamos esperar 60s para ter certeza que cria uns 4-5 arquivos.
    try:
        for i in range(60):
            time.sleep(1)
            sys.stdout.write(f".")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
        
    print("\n[3] Verificando arquivos no disco...")
    
    # Stop Engine to release lock and exit thread
    engine.stop_recording()
    time.sleep(2) # Give time to close files

    rec_path = os.path.join("recordings", CAMERA_NAME)
    if os.path.exists(rec_path):
        files = os.listdir(rec_path)
        print(f"Arquivos encontrados em {rec_path}: {files}")
        if len(files) > 0:
            print(">>> SUCESSO: Arquivos de vídeo estão sendo criados!")
        else:
            print(">>> AVISO: Pasta criada, mas vazia (FFmpeg ainda bufferizando ou falhou?)")
    else:
        print(f">>> FALHA: Pasta {rec_path} não foi criada.")

    print("\n[Nota]: Para parar a gravação, você deve matar o processo python ou fechar esta janela.")
    print("Este é um teste 'Fire and Forget' do ingestor.")

if __name__ == "__main__":
    run_test()
