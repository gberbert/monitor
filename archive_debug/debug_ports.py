
import socket

ip = "192.168.3.27"
ports = [554, 80, 8080, 34567, 8899, 5800]

print(f"Scanning {ip}...")
for p in ports:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((ip, p))
    if result == 0:
        print(f"Port {p}: OPEN")
    else:
        print(f"Port {p}: CLOSED")
    sock.close()
