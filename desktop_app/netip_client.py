import socket
import struct
import json
import time

# Constantes do Protocolo NetIP (Sofia/Xiongmai)
HEAD_MAGIC = 0xff
VERSION = 1
CMD_LOGIN_REQ = 1000
CMD_LOGIN_RES = 1001
CMD_KEEPALIVE_REQ = 1006
CMD_SYSTEM_INFO_REQ = 1020
CMD_SNAPSHOT_REQ = 1500  # Padrão para pedir I-Frame JPEG

class NetIPCamera:
    def __init__(self, ip, port=34567, user='admin', password=''):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.session_id = 0
        self.seq = 0
        self.sock = None
        self.connected = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0) # Timeout maior
            print(f"[NetIP] Conectando socket em {self.ip}:{self.port}...")
            self.sock.connect((self.ip, self.port))
            print(f"[NetIP] Socket Aberto. Tentando Login...")
            
            # Tentar Login
            if self._login():
                self.connected = True
                print(f"[NetIP] Conectado e Logado em {self.ip}")
                return True
            else:
                print(f"[NetIP] Falha no Login")
                self.close()
                return False
        except Exception as e:
            print(f"[NetIP] Erro de Conexão: {e}")
            self.close()
            return False

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except: pass
        self.sock = None
        self.connected = False

    def get_snapshot(self):
        if not self.connected: 
            return None
        
        # O comando 1500 (OPSNAP) pede uma foto
        # Payload tipico: {"Channel":0}
        req_data = {"Channel": 0} 
        
        try:
            self._send_packet(CMD_SNAPSHOT_REQ, req_data)
            
            # Ler resposta
            msg_id, data = self._recv_packet()
            
            # Algumas cameras retornam a foto direto no corpo da resposta
            # Ou retornam um header indicando o tamanho
            
            if msg_id == 1501: # Resposta de Sucesso do Snapshot
                # Pode conter "Ret": 404 se falhar ou bytes se sucesso
                # Mas protocolo Sofia costuma mandar a imagem DEPOIS da resposta JSON
                # Se o data for pequeno (JSON), lemos de novo
                
                # Verifica se é JPEG (FF D8 ... FF D9)
                if data.startswith(b'\xff\xd8'):
                    return data # É a imagem!
                
                # Se for JSON, analisar
                try:
                    js = json.loads(data)
                    # Se response code ok...
                except:
                    # Se não é json e não é jpeg, estranho.
                    pass
                
                # Tentar ler o próximo pacote, que deve ser a stream de dados
                # AS vezes o snapshot vem como um pacote de "Monitor Claim" modificado
                # Mas para simplificar, vamos ver se conseguimos ler bytes extras
                
                # Hack: Tenta ler até achar fim de imagem se nao veio
                return None
                
        except Exception as e:
            # print(f"Erro Snap: {e}")
            self.close()
        
        return None

    def _login(self):
        # Payload de Login
        # Type: "Old" ou "TreeView" costumam funcionar
        login_data = {
            "EncryptType": "MD5",
            "LoginType": "TreeView",
            "PassWord": self.password,
            "UserName": self.user,
            "Name": "PythonClient"
        }
        self._send_packet(CMD_LOGIN_REQ, login_data)
        
        # Receber resposta
        msg_id, data = self._recv_packet()
        if msg_id == CMD_LOGIN_RES:
            try:
                resp = json.loads(data)
                if resp.get("Ret") == 100:
                    self.session_id = resp.get("SessionID", 0)
                    return True
            except: pass
        return False

    def _send_packet(self, msg_id, data_dict):
        json_str = json.dumps(data_dict)
        data_bytes = json_str.encode('utf-8')
        total_len = len(data_bytes) + 24 # Header de 24 bytes
        
        # Struct Header:
        # Head(1), Ver(1), Res(2), Sess(4), Seq(4), TotLen(4), CurLen(4), MsgID(2), Res(1), Enc(1)
        # 0xFF + 0x01 + 0x0000 + Sess + Seq + Tot + Cur + Msg + 0 + 0
        
        header = struct.pack("<BBHIIIIHBB", 
                             HEAD_MAGIC, VERSION, 0, 
                             self.session_id, self.seq, 
                             total_len, len(data_bytes), # Corrige TotalLen tbm
                             msg_id, 0, 0)
        
        self.sock.sendall(header + data_bytes)
        self.seq += 1

    def _recv_packet(self):
        # Ler Header (24 bytes)
        head_buf = self._recv_all(24)
        if not head_buf: raise Exception("Sem dados")
        
        # Unpack
        _, _, _, sess, seq, tot_len, cur_len, msg_id, _, _ = struct.unpack("<BBHIIIIHBB", head_buf)
        
        # Ler Payload
        payload = self._recv_all(cur_len)
        return msg_id, payload

    def _recv_all(self, n):
        data = b''
        start = time.time()
        while len(data) < n:
            if time.time() - start > 2: raise Exception("Timeout Recv")
            chunk = self.sock.recv(n - len(data))
            if not chunk: break
            data += chunk
        return data

# Teste Rápido (Se rodar direto)
if __name__ == "__main__":
    cam = NetIPCamera("192.168.3.27", 34567, "berbert", "viguera2001")
    if cam.connect():
        print("Tirando foto...")
        # Nota: Snapshot via comando 1500 é dificil acertar sem a doc exata.
        # Mas vamos testar.
        # Se falhar, pelo menos o login funcionou e sabemos que a senha esta certa.
        cam.close()
