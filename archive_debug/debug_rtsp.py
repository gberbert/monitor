import cv2
import time
import os

# Força TCP
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;5000"

IP = "192.168.3.27"
USER = "berbert"
PASS = "viguera2001"
PORT = 34567

urls_to_test = [
    f"rtsp://{USER}:{PASS}@{IP}:{PORT}/user={USER}&password={PASS}&channel=1&stream=2.sdp", # Mobile
    f"rtsp://{USER}:{PASS}@{IP}:{PORT}/user={USER}&password={PASS}&channel=1&stream=1.sdp", # Sub
    f"rtsp://{USER}:{PASS}@{IP}:{PORT}/user={USER}&password={PASS}&channel=1&stream=0.sdp", # Main
    f"rtsp://{USER}:{PASS}@{IP}:{PORT}/user={USER}&password={PASS}&channel=1&stream=0.sdp?tcp", # Main + flag
]

print(f"--- DIAGNOSTICO RTSP ---")

for url in urls_to_test:
    print(f"\n[TESTANDO]: {url}")
    try:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            print("[OK] CAPTURE ABERTO! Lendo frames...")
            # Tenta ler 10 frames para ver se não morre no timeout
            ok_count = 0
            for i in range(10):
                ret, frame = cap.read()
                if ret:
                    print(f"  Frame {i} OK! Shape: {frame.shape}")
                    ok_count += 1
                else:
                    print(f"  Frame {i} FALHOU.")
            
            if ok_count > 0:
                print(f"[SUCESSO] ESSA URL FUNCIONA!")
                break # Encontramos!
            else:
                print("[FALHA] Conectou mas não veio imagem (Codec H.265?)")
        else:
            print("[ERRO] Falha ao abrir Capture.")
        cap.release()
    except Exception as e:
        print(f"[EXCEPT] ERRO TESTE: {e}")

print("\n--- FIM DO TESTE ---")
