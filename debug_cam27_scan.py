import socket

TARGET_IP = "192.168.3.27"
PORTS = [80, 554, 8080, 8899, 34567]

print(f"--- SCAN DE PORTAS: {TARGET_IP} ---")

for port in PORTS:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    result = s.connect_ex((TARGET_IP, port))
    status = "ABERTA" if result == 0 else "FECHADA/TIMEOUT"
    print(f"Porta {port}: {status}")
    s.close()
