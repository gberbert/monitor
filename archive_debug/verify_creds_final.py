
import socket
import struct
import json
import time
import hashlib
import binascii

TARGET_IP = "192.168.3.27"
PORT = 34567

# Protocol Specs
HEAD_MAGIC = 0xff
VERSION = 1
CMD_LOGIN_REQ = 1000

def make_packet(user, password):
    login_data = {
        "EncryptType": "MD5", 
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

def raw_login(user, password):
    pkt = make_packet(user, password)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((TARGET_IP, PORT))
        s.sendall(pkt)
        
        # Read a big chunk
        resp = s.recv(1024)
        
        # Find JSON start
        idx = resp.find(b'{')
        if idx != -1:
            json_bytes = resp[idx:]
            # Clean up nulls
            json_bytes = json_bytes.rstrip(b'\x00')
            try:
                js = json.loads(json_bytes)
                return True, js
            except:
                return False, f"Invalid JSON: {json_bytes}"
        else:
            return False, f"No JSON found in {binascii.hexlify(resp)}"
            
    except Exception as e:
        return False, str(e)
    finally:
        s.close()

def main():
    print("=== FINAL CREDENTIAL VERIFIER ===")
    
    users = ["admin", "default", "system", "nonexistentuser"]
    passwords = [
        "", 
        "admin", 
        "123456", 
        "viguera2001", 
        "12345", 
        "1234567890", 
        "icsee", 
        "xmeye",
        "888888"
    ]
    
    print("Enter custom password if you have one:")
    c = input("> ").strip()
    if c: passwords.insert(0, c)
    
    for u in users:
        for p in passwords:
            print(f"Testing {u}:{p}... ", end="")
            ok, resp = raw_login(u, p)
            if ok:
                ret = resp.get("Ret")
                if ret == 100:
                    print("SUCCESS!!!")
                    print(f"VALID CREDENTIALS: {u} / {p}")
                    return
                elif ret == 102:
                    print(f"Refused (Wrong Pass)")
                elif ret == 101:
                    print(f"Refused (User Invalid)")
                else:
                    print(f"Refused (Ret: {ret})")
            else:
                print(f"Error: {resp}")
                
    print("\n--- TEST FINISHED ---")
    print("If you see 'Refused (Wrong Pass)', the camera is REJECTING the password.")
    print("Try creating a NEW USER in the ICSEE App with a simple password like '123456'.")

if __name__ == "__main__":
    main()
