
import socket
import struct
import json
import time

TARGET_IP = "192.168.3.27"
PORT = 34567

# Protocol Specs
HEAD_MAGIC = 0xff
VERSION = 1
CMD_LOGIN_REQ = 1000

def try_login(user, password):
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
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((TARGET_IP, PORT))
        s.sendall(header + data_bytes)
        
        # Read Header
        head_buf = s.recv(24)
        if len(head_buf) < 24: return False, "No Header"
        
        _, _, _, sess, _, _, cur_len, msg_id, _, _ = struct.unpack("<BBHIIIIHBB", head_buf)
        
        if cur_len > 0:
            payload = s.recv(cur_len)
            try:
                resp = json.loads(payload)
                ret_code = resp.get("Ret")
                if ret_code == 100:
                    return True, "LOGIN SUCCESS (Ret: 100)"
                elif ret_code == 102:
                    return False, "WRONG PASSWORD/LOCKED (Ret: 102)"
                else:
                    return False, f"FAILED (Ret: {ret_code})"
            except:
                return False, "Bad JSON Response"
                
        return False, "Empty Payload"
        
    except Exception as e:
        return False, f"Connection/Socket Error: {e}"
    finally:
        s.close()

def main():
    print("=== CAMERA CREDENTIAL TESTER (Port 34567) ===")
    print(f"Target: {TARGET_IP}")
    
    while True:
        print("\nEnter credentials to test (or 'q' to quit):")
        u = input("Username (default: admin): ").strip()
        if u.lower() == 'q': break
        if not u: u = "admin"
        
        p = input("Password: ").strip()
        
        print(f"Testing {u} / {p} ...")
        success, msg = try_login(u, p)
        print(f"Result: {msg}")
        
        if success:
            print("\n!!! SUCCESS !!!")
            print("Please update monitoring/go2rtc_bin/go2rtc.yaml with these credentials!")
            break

if __name__ == "__main__":
    main()
