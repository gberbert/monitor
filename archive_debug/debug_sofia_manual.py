
import socket
import struct
import time
import hashlib
import binascii

def login_sofia(ip, port, user, password):
    print(f"--- TENTATIVA DE LOGIN SOFIA (NETIP) EM {ip}:{port} ---")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect((ip, port))
        print("1. Conexão TCP: OK")
    except Exception as e:
        print(f"1. Conexão TCP: FALHA ({e})")
        return

    # Protocolo Sofia (Engenharia Reversa Simplificada)
    # Header: 0xFF 00 00 00
    # Session: 00 00 00 00
    # Sequence: 00 00 00 00
    # Total Len: 00 00 00 00
    # Msg ID: E8 03 (1000 - LOGIN_REQ)
    
    # Payload JSON
    # Hash de senha antiga XM: MD5 truncado ou vazia? Vamos tentar plain ou hash simples.
    # Na verdade o protocolo LoginReq usa uma struct binaria em versoes antigas e JSON nas novas.
    
    # Vamos tentar o payload JSON moderno.
    # OpType: 1000 (Login)
    
    # Hash Password logic (XMEye specific)
    # Usually md5(password) unless empty
    pass_hash = ""
    if password:
        # Simple MD5
        pass_hash = hashlib.md5(password.encode()).hexdigest().upper()
        # Some firmwares do weird hashing, but standard is MD5 hex upper.
    
    # "Mac" field is often required but can be fake.
    json_body = '{"EncryptType":"MD5","LoginType":"cn","PassWord":"%s","UserName":"%s"}\n' % (pass_hash, user)
    body_bytes = json_body.encode()
    
    # Construct Header (20 bytes)
    # Head(1) Ver(1) Res(2) Sess(4) Seq(4) TotalLen(4) CurLen(4) MsgID(2) Res(1) Encode(1)
    # Head: FF 01
    
    # 0xFF + Version(1)
    head = b'\xff\x01\x00\x00'
    session = b'\x00\x00\x00\x00'
    seq = b'\x00\x00\x00\x00'
    
    # Lengths including header? No, usually body length plus overhead?
    # NetIP Header is 20 bytes.
    # But Structure varies.
    # Let's use the AlexxIT implementation logic:
    # 0xFF01 + 2 bytes res + 4 session + 4 seq + 4 total_len + 4 cur_len + 2 msg_id + 2 res
    
    # MsgID 1000 = 0x03E8
    msg_id = 1000
    
    total_len = len(body_bytes) + 1 # +1 for null terminator?
    
    # Pack header
    # I = unsigned int (4), H = unsigned short (2), B = uchar (1)
    # < = Little Endian
    
    # Padrão: 
    # HEAD (1B) = 0xFF
    # RSERV(1B) = 0x00
    # VER(2B) = 01 00 (Ver 1.0)
    # SESS(4B)
    # SEQ(4B)
    # TOTAL_LEN(4B)
    # CUR_LEN(4B)
    # MSG_ID(2B)
    # PRESERVED(2B)
    
    header = struct.pack("<BB2sIIIIHH", 
        0xFF, 0x01, b'\x00\x00', # Head, Ver=1, Res
        0, 0, # Session, Seq
        len(body_bytes), len(body_bytes), # Lengths
        1000, # MsgID (Login)
        0 # Res
    )
    
    packet = header + body_bytes
    
    print(f"2. Enviando Pacote Login ({len(packet)} bytes)...")
    # print(f"Dump: {packet.hex()}")
    
    sock.send(packet)
    
    try:
        resp = sock.recv(1024)
        print(f"3. Resposta Recebida ({len(resp)} bytes)")
        print(f"Dump Resp: {resp.hex()}")
        
        # Parse result
        if len(resp) >= 20:
             # Skip header
             body = resp[20:]
             print(f"Body: {body.decode(errors='ignore')}")
             
             if b'"Ret":100' in body or b'"Ret": 100' in body:
                 print("\n>>> LOGIN SUCESSO! Credenciais Válidas <<<")
                 print("NOTA: A câmera está viva e logada. O problema é apenas que video RTSP está OFF.")
             elif b'"Ret":' in body:
                 print("\n>>> LOGIN RECUSADO (Senha/User Incorreto?) <<<")
             else:
                 print(">>> Resposta desconhecida.")
                 
    except socket.timeout:
        print("Timeout aguardando resposta de login.")
    
    sock.close()

login_sofia("192.168.3.27", 34567, "berbert", "viguera2001")
