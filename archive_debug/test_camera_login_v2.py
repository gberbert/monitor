
import socket
import struct
import json
import time
import hashlib

TARGET_IP = "192.168.3.27"
PORT = 34567

# Protocol Specs
HEAD_MAGIC = 0xff
VERSION = 1
CMD_LOGIN_REQ = 1000

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest().upper()

def make_packet(user, password, encrypt_type="MD5"):
    login_data = {
        "EncryptType": encrypt_type, 
        "LoginType": "TreeView",
        "PassWord": password,
        "UserName": user,
        "Name": "PythonClient"
    }
    
    json_str = json.dumps(login_data)
    data_bytes = json_str.encode('utf-8')
    total_len = len(data_bytes) + 24
    
    header = struct.pack("<BBHIIIIHBB", 
                         HEAD_MAGIC, VERSION, 0, 
                         0, 0, 
                         total_len, len(data_bytes), 
                         CMD_LOGIN_REQ, 0, 0)
    return header + data_bytes

def try_one_connection(user, password, encrypt_mode, display_pass_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((TARGET_IP, PORT))
        pkt = make_packet(user, password, encrypt_mode)
        s.sendall(pkt)
        
        # Header
        head = s.recv(24)
        if len(head) < 24: return False, "No Header"
        _, _, _, _, _, _, cur_len, _, _, _ = struct.unpack("<BBHIIIIHBB", head)
        
        # Payload
        if cur_len > 0:
            payload = s.recv(cur_len)
            try:
                resp = json.loads(payload)
                ret = resp.get("Ret")
                if ret == 100:
                    print(f"\n[SUCCESS] User: {user} | Pass: {display_pass_name} | Mode: {encrypt_mode}")
                    return True, "OK"
                else:
                    return False, f"Ret: {ret}"
            except:
                 return False, "Bad JSON"
        return False, "No Data"
    except Exception as e:
        return False, str(e)
    finally:
        s.close()

def main():
    print("=== ADVANCED AUTH TESTER ===")
    
    credentials = [
        ("admin", ""),
        ("admin", "admin"),
        ("admin", "123456"),
        ("berbert", "viguera2001"),
        ("default", ""),
    ]
    
    # User Input
    print("Enter any specific password to test (or press enter to skip):")
    custom = input("Password: ").strip()
    if custom:
        credentials.append(("admin", custom))
        credentials.append(("berbert", custom))
        
    for user, pwd in credentials:
        print(f"\nTesting {user} / '{pwd}'")
        
        # 1. Plain with MD5 label (Standard)
        ok, msg = try_one_connection(user, pwd, "MD5", pwd)
        print(f"  Standard: {msg}")
        if ok: return
        
        # 2. Plain with NONE label
        ok, msg = try_one_connection(user, pwd, "NONE", pwd)
        print(f"  Type=NONE: {msg}")
        if ok: return

        # 3. MD5 Hash in Password Field
        if pwd:
            hashed = md5_hash(pwd)
            # Try upper and lower case hash
            ok, msg = try_one_connection(user, hashed, "MD5", f"HASH({pwd})")
            print(f"  Hashed_Upper: {msg}")
            if ok: return
            
            ok, msg = try_one_connection(user, hashed.lower(), "MD5", f"HASH_lower({pwd})")
            print(f"  Hashed_Lower: {msg}")
            if ok: return

    print("\nNo luck.")

if __name__ == "__main__":
    main()
