
import socket

ip = "192.168.3.27"
ports = [554, 80, 5000, 8080, 34567, 8899, 9988]

print(f"--- RASTREAMENTO DE PORTAS: {ip} ---")
for p in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0) # Timeout curto para nao travar
    result = sock.connect_ex((ip, p))
    status = "ABERTA (OK)" if result == 0 else "FECHADA (X)"
    print(f"Porta {p}: {status}")
    sock.close()
