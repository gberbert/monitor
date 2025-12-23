import socket
import struct
import json
import binascii

# --- CONFIGURACAO ISOLADA ---
TARGET_IP = "192.168.3.27"
PORT = 34567

# Tente usuarios comuns de ICSEE
USER = "admin"
# Deixe vazio se nao tiver senha, ou coloque a senha aqui para testar
PASSWORD = "" 

def create_login_packet(user, password, magic):
    data = {
        "EncryptType": "MD5",
        "LoginType": "DVRIP-Web", 
        "PassWord": password,
        "UserName": user
    }
    json_body = json.dumps(data)
    # Alguns firmwares pedem \x0a\x00 no final
    body_bytes = json_body.encode('utf-8') + b'\x0a\x00'
    
    # Header
    head_magic = magic # 0xff ou 0x20
    session = b'\x00\x00\x00\x00'
    seq = b'\x00\x00\x00\x00'
    msg_type = b'\xe8\x03\x00\x00' # 1000
    
    total_len = 20 + len(body_bytes)
    len_bytes = struct.pack('<I', total_len)
    
    return head_magic + session + seq + len_bytes + msg_type + body_bytes

def debug_connection():
    magics = [
        (b'\xff\x00\x00\x00', "OLD_HEADER_FF"),
        (b'\x20\x00\x00\x00', "NEW_HEADER_20")
    ]

    print(f"--- SONDA SOFIA V2 (MULTI-HEADER) ---")
    print(f"Alvo: {TARGET_IP}:{PORT}")

    for magic_bytes, label in magics:
        print(f"\n[TEST] Tentando Header: {label} ...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3) # Timeout curto
        
        try:
            s.connect((TARGET_IP, PORT))
            pkt = create_login_packet(USER, PASSWORD, magic_bytes)
            s.sendall(pkt)
            
            resp = s.recv(1024)
            if resp:
                print(f"[SUCCESS] Resposta recebida com {label}!")
                print("HEX:", binascii.hexlify(resp, ' ', 1).decode('utf-8'))
                print("TXT:", resp[20:].decode('utf-8', errors='ignore'))
                break
            else:
                print("[FAIL] Conexao fechada sem dados.")
        except socket.timeout:
            print("[TIMEOUT] Sem resposta.")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            s.close()

if __name__ == "__main__":
    debug_connection()
