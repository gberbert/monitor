import socket
import struct
import json
import time

def get_snapshot(ip, port, user, password):
    # Packet Constants
    HEAD_MAGIC = 0xff
    VERSION = 1
    # Command IDs
    CMD_LOGIN = 1000
    CMD_LOGIN_RESP = 1001
    CMD_SNAPSHOT = 1500 # ou parecido, vamos testar

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    
    try:
        sock.connect((ip, port))
        print(f"Conectado a {ip}:{port}")
        
        # 1. LOGIN
        # Payload JSON
        login_data = {
            "EncryptType": "MD5",
            # Senha vazia para teste inicial ou hash se precisar. 
            # Sofia usa hash especifico, mas muitas aceitam LoginType: "Old" com senha texto plano em alguns campos
            # Vamos tentar o payload mais simples possivel
            "LoginType": "TreeView", 
            "PassWord": password,
            "UserName": user,
            "Name": "PythonClient"
        }
        
        login_json = json.dumps(login_data).encode('utf-8')
        
        # Header: (Magic[1], Ver[1], Res[2], Session[4], Seq[4], TotalLen[2], CurLen[2], MsgID[2], Res[1], Enc[1])
        # Ops, header do Sofia é:
        # 0xff (1) + 0x00 (1) + len(2) + ... nao, 
        # Estrutura padrao: 0xff000000 + Session + Seq + ...
        
        # Vamos usar a lib dvrip para o LOGIN que ela ja faz (no debug anterior funcionou)
        # E só tentar usar o socket dela para o snapshot? Não, objeto socket fica privado.
        
        # Vamos usar o payload exato que o WireShark mostraria.
        # Mas sem a lib `dvrip` funcionando com snapshot, é dificil adivinhar o hash.
        
        # OK, vamos desistir de reimplementar a roda do Protocolo Binário agora.
        pass

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        sock.close()

# Se chegamos aqui, é melhor voltar a tentar o HTTP na porta 8899 ou 8080.
# O log do usuário mostrou varios "Socket Check" OK para essas portas?
# Log do usuário:
# DEBUG: Socket Check 192.168.3.27:8000
# DEBUG: Socket Check 192.168.3.27:88
# DEBUG: Socket Check 192.168.3.27:8080
# ...
# DEBUG: Nenhum HTTP achado.
# Isso significa que as portas estavam FECHADAS ou não responderam HTTP 200.

# O único caminho é RTSP que funcione.
