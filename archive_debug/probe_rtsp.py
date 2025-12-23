
import socket
import struct
import time

def send_netip_login(ip, port, user, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect((ip, port))
        print(f"Connected to {ip}:{port}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Basic Login Packet (Simplified)
    # This is a shot in the dark without a full library, but standard XM login structure is:
    # Header: FF 01 00 00
    # Session: 00 00 00 00
    # Sequence: 00 00 00 00
    # Total Len: (JSON Len + 4?)
    # Cur Len: ...
    # Msg ID: E8 03 (1000)
    # ...
    
    # Actually, simpler: just read the HELLO from server? 
    # Usually NETIP server sends nothing on connect. Client speaks first.
    
    # Let's try to just see if it keeps connection open.
    # If "Invalid Data" on RTSP, it means it sent SOMETHING back when we sent RTSP DESCRIBE?
    
    # Let's send "OPTIONS rtsp://..." manually and see what we get.
    rtsp_req = f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: python\r\n\r\n"
    sock.send(rtsp_req.encode())
    
    try:
        data = sock.recv(1024)
        print(f"Response (Hex): {data.hex()}")
        print(f"Response (Text): {data.decode(errors='ignore')}")
    except socket.timeout:
        print("Timeout - No response to RTSP OPTIONS")
    
    sock.close()

ip = "192.168.3.27"
port = 34567    
print(f"--- PROBING PORT {port} FOR RTSP RESPONSE ---")
send_netip_login(ip, port, "berbert", "viguera2001")
