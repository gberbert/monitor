import socket
import concurrent.futures
import time

# Configuração da Rede (Ajuste se necessário, mas vou tentar detectar)
NETWORK_PREFIX = "192.168.3."
PORTS_TO_SCAN = [554, 34567, 80, 8080, 8899] # 34567 é a chave para ICSEE

print(f"--- INICIANDO DIAGNÓSTICO DE CÂMERAS ---")
print(f"Rede Alvo: {NETWORK_PREFIX}0/24")
print(f"Portas Alvo: {PORTS_TO_SCAN}")
print("-" * 50)

found_devices = []

def scan_host(ip_end):
    ip = f"{NETWORK_PREFIX}{ip_end}"
    open_ports = []
    
    for port in PORTS_TO_SCAN:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3) # Timeout curto para ser rápido
            result = s.connect_ex((ip, port))
            s.close()
            
            if result == 0:
                open_ports.append(port)
        except:
            pass
            
    if open_ports:
        return (ip, open_ports)
    return None

start_time = time.time()

# Usando 100 threads para varrer rápido
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(scan_host, i) for i in range(1, 255)]
    
    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        if res:
            ip, ports = res
            print(f"[ACHOU] IP: {ip} | Portas Abertas: {ports}")
            
            # Identificação básica
            desc = "Desconhecido"
            if 34567 in ports: desc = "Provável ICSEE/XMeye (NETIP)"
            elif 554 in ports: desc = "Câmera RTSP Genérica / Intelbras"
            elif 80 in ports: desc = "Dispositivo Web (pode ser NVR/DVR)"
            
            print(f"        -> {desc}")
            found_devices.append(res)

print("-" * 50)
print(f"Fim da varredura em {time.time() - start_time:.2f} segundos.")
print(f"Total de dispositivos encontrados: {len(found_devices)}")
input("Pressione ENTER para sair...")
