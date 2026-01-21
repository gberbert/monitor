import socket
import datetime
import requests
from requests.auth import HTTPDigestAuth

TARGET_IP = "192.168.3.125"
USER = "admin"
PASS_ATTEMPTS = ["viguera2001", "vigueraberbert@2025", "vigueraberbert%402025"]

def log(msg): print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

log(f"--- DIAGNOSTICO INTELBRAS {TARGET_IP} ---")

# 1. Ping TCP (Portas 554 e 37777)
for port in [554, 37777, 80]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((TARGET_IP, port))
        status = "ABERTA" if result == 0 else f"FECHADA ({result})"
        log(f"Porta {port}: {status}")
        s.close()
    except Exception as e:
        log(f"Porta {port}: Erro {e}")

# 2. Teste RTSP (Simples Socket Handshake)
# Tenta validar qual senha o servidor aceita via RTSP DESCRIBE
def test_rtsp_auth(password):
    url = f"rtsp://{USER}:{password}@{TARGET_IP}:554/cam/realmonitor?channel=1&subtype=1"
    # Nota: Requests nao fala RTSP nativo, mas podemos usar cv2 ou apenas inferir logica
    # Vamos usar uma abordagem mais simples: Montar a URL e tentar conectar via OpenCV ou FFmpeg seria ideal
    # Mas para nao depender de libs pesadas, vamos assumir que o erro 34... veio de outra tentativa.
    log(f"Testando credencial: {password} ... (Logica de teste simplificada via HTTP Digest na porta 80 se disponivel)")

# 3. Teste HTTP (Porta 80)
# Intelbras costuma ter interface web. Vamos tentar logar nela.
for pwd in PASS_ATTEMPTS:
    try:
        # Tenta pegar snapshot ou info via HTTP
        # URL comum Intelbras: /cgi-bin/snapshot.cgi
        test_url = f"http://{TARGET_IP}/cgi-bin/snapshot.cgi?channel=1"
        r = requests.get(test_url, auth=HTTPDigestAuth(USER, pwd), timeout=3)
        if r.status_code == 200:
            log(f"[SUCESSO] Senha CORRETA via HTTP (Porta 80): '{pwd}'")
            break
        elif r.status_code == 401:
            log(f"[FALHA] Senha INCORRETA via HTTP: '{pwd}' (401)")
        else:
            log(f"[INFO] HTTP Retornou: {r.status_code}")
    except Exception as e:
        log(f"[ERRO] Falha HTTP: {e}")

log("--- FIM ---")
