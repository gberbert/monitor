import socket
import os
import sys
import time

TARGET_IP = "192.168.3.125"
PORTS = [554, 80, 37777, 8000, 8080, 34567]
CREDS = [
    ("admin", "admin"),
    ("admin", "admin123"),
    ("admin", "123456"),
    ("admin", "intelbras"),
    ("admin", "viguera2001"), # Sua senha padrao
    ("admin", "")
]

def check_ping(ip):
    print(f"[*] Pinging {ip}...")
    # Windows uses -n, Linux -c. Assuming Windows based on env.
    response = os.system(f"ping -n 1 -w 1000 {ip} >nul 2>&1")
    return response == 0

def check_port(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try:
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except:
        return False

def main():
    print(f"--- DIAGNOSTICO INTELBRAS: {TARGET_IP} ---")
    
    # 1. Ping
    if check_ping(TARGET_IP):
        print(f"[OK] {TARGET_IP} responde ao Ping.")
    else:
        print(f"[ERR] {TARGET_IP} NAO responde ao Ping. Verifique se o IP esta correto, ou se esta ligada.")
        print("      Tentando portas mesmo assim (alguns firewalls bloqueiam ping)...")

    # 2. Port Scan
    print("\n[*] Verificando portas de servico...")
    open_ports = []
    for p in PORTS:
        if check_port(TARGET_IP, p):
            print(f"  [ABERTA] Porta {p}")
            open_ports.append(p)
        else:
            # print(f"  [FECHADA] Porta {p}")
            pass
            
    if not open_ports:
        print("\n[FALHA TOTAL] Nenhuma porta aberta encontrada. A camera esta offline ou o IP esta errado.")
        return

    # 3. Analise
    print("\n[*] STATUS:")
    if 554 in open_ports:
        print("  -> RTSP (Video) esta ATIVO.")
    else:
        print("  -> RTSP (Video 554) esta FECHADO. Isso e um problema para streaming padrao.")

    if 37777 in open_ports:
        print("  -> Porta TCP Intelbras (37777) detectada. É definitivamente uma Intelbras/Dahua.")
    
    # 4. Sugestao de URLs
    print("\n[*] Tente adicionar com estas configurações:")
    if 554 in open_ports:
        print(f"  URL Padrao: rtsp://admin:SENHA@{TARGET_IP}:554/cam/realmonitor?channel=1&subtype=0")
        print("  (Substitua 'SENHA' pela senha da camera, ex: admin, intelbras, viguera2001)")
    elif 34567 in open_ports:
         print(f"  URL Padrao (Câmera chinesa XMeye detectada?): rtsp://admin:SENHA@{TARGET_IP}:554/user=admin&password=SENHA&channel=1&stream=0.sdp?")

    print("\n[DICA] Se a porta 80 estiver aberta, tente acessar http://" + TARGET_IP + " no navegador para ver se pede login.")

if __name__ == "__main__":
    main()
