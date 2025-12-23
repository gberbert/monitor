
import socket
import struct
import json
import time
import binascii

TARGET_IP = "192.168.3.27"
PORT = 34567

# Protocol Specs
HEAD_MAGIC = 0xff
VERSION = 1
CMD_LOGIN_REQ = 1000

def debug_packet(user, password):
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
    packet = header + data_bytes
    
    print(f"\nSending {len(packet)} bytes to {TARGET_IP}:{PORT}...")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((TARGET_IP, PORT))
        s.sendall(packet)
        
        # Read whatever comes back
        raw = s.recv(1024)
        print(f"Received {len(raw)} bytes.")
        if len(raw) > 0:
            print(f"Raw Hex: {binascii.hexlify(raw)}")
            try:
                # Try to find header
                if raw[0] == 0xff:
                    # Parse header
                    if len(raw) >= 24:
                        _, _, _, sess, _, _, cur_len, msg_id, _, _ = struct.unpack("<BBHIIIIHBB", raw[:24])
                        print(f"Header decoded: MsgID={msg_id} CurLen={cur_len} SessionID={sess}")
                        if len(raw) >= 24 + cur_len:
                            payload = raw[24:24+cur_len]
                            print(f"Payload: {payload}")
                        else:
                            # Sometimes packet is fragmented, but for login response usually it fits
                            print(f"Payload incomplete or separate: {len(raw)} bytes total")
                            if len(raw) > 24:
                                print(f"Remaining bytes: {raw[24:]}")
                    else:
                        print(f"Useable data too short: {len(raw)} < 24")
            except Exception as e:
                print(f"Parse error: {e}")
                
            print(f"Raw Text: {raw}")
            
    except Exception as e:
        print(f"Socket Error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    debug_packet("admin", "")
    debug_packet("admin", "admin")
    debug_packet("berbert", "viguera2001")
