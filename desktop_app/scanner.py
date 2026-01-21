import socket
import cv2
import concurrent.futures
import time
import os
from PyQt6.QtCore import QObject, pyqtSignal

class NetworkScanner(QObject):
    """
    Scanner Multi-thread Robusto (Versao Turbo Race).
    """
    progress_signal = pyqtSignal(int, int) # atual, total
    found_signal = pyqtSignal(str, str, str) # ip, url, mac
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_running = False

    def get_mac(self, ip):
        """Tenta descobrir o MAC via tabela ARP do Windows"""
        try:
            stream = os.popen(f'arp -a {ip}')
            output = stream.read()
            import re
            mac = re.search(r"(([a-f\d]{1,2}\-){5}[a-f\d]{1,2})", output.lower())
            if mac:
                return mac.group(1).replace('-', ':').upper()
        except:
            pass
        return ""

    def check_port(self, ip, port=554, timeout=0.5):
        """Verifica se a porta esta aberta (TCP Connect)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((ip, port))
                return result == 0
        except:
            return False

    def scan_network_task(self, ip_base, user, password):
        """Funcao principal que roda na ThreadPool"""
        import signal
        # Permite matar o processo com CTRL+C mesmo se threads travarem
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.log_signal.emit(f"🚀 Varredura INICIADA em {ip_base}.x... (Aguarde, pode demorar alguns minutos)")

        ips_to_scan = [f"{ip_base}.{i}" for i in range(1, 255)]
        
        # Lista Ampla de Portas (Para pegar tudo que mexe)
        target_ports = [554, 80, 8000, 37777, 34567, 8080] 

        open_ips = set()
        
        # Fase 1: Scan de Portas (Mais lento/seguro para não perder nada)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            future_map = {}
            for ip in ips_to_scan:
                for port in target_ports:
                    # Timeout generoso de 1.5s para achar cameras lentas
                    future = executor.submit(self.check_port, ip, port, 1.5)
                    future_map[future] = ip

            for future in concurrent.futures.as_completed(future_map):
                if not self._is_running: break
                try:
                    if future.result():
                        ip = future_map[future]
                        if ip not in open_ips:
                            open_ips.add(ip)
                            self.log_signal.emit(f"   [+] Porta aberta: {ip}")
                except: pass
        
        if not self._is_running: return

        # Fase 2: Auth Race Mode (Turbo)
        sorted_ips = sorted(list(open_ips), key=lambda x: int(x.split('.')[-1]))
        if not sorted_ips:
            self.log_signal.emit("🏁 Nenhuma porta aberta encontrada.")
            self.finished_signal.emit()
            return

        self.log_signal.emit(f"🔎 Disparando testes simultâneos em {len(sorted_ips)} IPs...")

        def identify_worker(ip):
            if not self._is_running: return
            # A magica acontece aqui: verify_rtsp_auth dispara tudo de uma vez
            success, valid_url = self.verify_rtsp_auth(ip, user, password)
            if success:
                mac = self.get_mac(ip)
                self.log_signal.emit(f"   ✅ SUCESSO: {ip} [MAC: {mac}]")
                self.found_signal.emit(ip, valid_url, mac)
            else:
                pass 

        # 20 IPs simultaneos (cada um abre 5 threads internas = 100 threads total)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(identify_worker, sorted_ips)

        self.log_signal.emit("🏁 Varredura concluída.")
        self.finished_signal.emit()

    def verify_rtsp_auth(self, ip, user, password):
        """Validação Silenciosa e Otimizada (Anti-Lag)"""
        templates = [
            f"rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=1", 
            f"rtsp://{ip}:554/user={user}&password={password}&channel=1&stream=1.sdp", 
            f"rtsp://{user}:{password}@{ip}:554/live/ch1", 
            f"rtsp://{user}:{password}@{ip}:554/h264/ch1/main/av_stream", 
            f"rtsp://{user}:{password}@{ip}:554", 
            f"rtsp://{user}:{password}@{ip}:34567/cam/realmonitor?channel=1&subtype=1"
        ]

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp;stimeout;5000000"
        
        def is_port_reachable(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.5)
                    return s.connect_ex((ip, port)) == 0
            except: 
                return False

        checked_ports = {} 

        # Log unico para nao travar a GUI
        # self.log_signal.emit(f"   🔍 {ip}: Analisando protocolos...")

        for i, url in enumerate(templates):
            port = 554
            if ":34567" in url: port = 34567
            
            if port not in checked_ports:
                is_open = is_port_reachable(port)
                checked_ports[port] = is_open
                if not is_open:
                     if port == 554 and is_port_reachable(80):
                         # Caso raro (ONVIF Tunnel), vale logar
                         self.log_signal.emit(f"   🔓 {ip}: Porta 554 fechada. Tentando tunelamento HTTP...")
                         checked_ports[port] = True 
            
            if not checked_ports[port]:
                continue 

            try:
                # Teste silencioso
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                if cap.isOpened():
                    cap.release()
                    return True, url
            except: 
                pass
        
        return False, None

    def start_scan(self, ip_range, user, password):
        self._is_running = True
        import threading
        t = threading.Thread(target=self.scan_network_task, args=(ip_range, user, password))
        t.daemon = True
        t.start()

    def stop(self):
        self._is_running = False
