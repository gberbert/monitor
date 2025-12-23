
import socket
import cv2
import time
import urllib.request
import urllib.error
import base64

TARGET_IP = "192.168.3.27"
PORTS_TO_SCAN = [80, 554, 8899, 8000, 8080, 34567, 37777]
CREDENTIALS = [
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "123456"),
    ("berbert", "viguera2001"),
    ("default", "")
]

def scan_ports(ip):
    print(f"\n--- Scanning Ports on {ip} ---")
    open_ports = []
    for port in PORTS_TO_SCAN:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex((ip, port))
        if result == 0:
            print(f"[OPEN] Port {port}")
            open_ports.append(port)
        else:
            print(f"[CLOSED] Port {port}")
        s.close()
    return open_ports

def check_rtsp(ip, port, user, password):
    url = f"rtsp://{user}:{password}@{ip}:{port}/user={user}&password={password}&channel=1&stream=0.sdp?"
    print(f"Testing RTSP: rtsp://{user}:***@{ip}:{port}...")
    try:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"  [SUCCESS] RTSP Stream OK!")
                cap.release()
                return True
        cap.release()
    except:
        pass
    print(f"  [FAIL] Could not read frame.")
    return False

def check_http_snapshot(ip, port, user, password):
    # Common snapshot URLs for XMeye/ICSEE
    paths = [
        f"/cgi-bin/snapshot.cgi?loginuse={user}&loginpas={password}",
        f"/web/cgi-bin/hi3510/snap.cgi?&-getstream&-chn=1",
        f"/cgi-bin/net_jpeg.cgi?ch=1" # Auth header often needed, but URL params might work
    ]
    
    for path in paths:
        url = f"http://{ip}:{port}{path}"
        print(f"Testing HTTP Snapshot: {url} ...")
        try:
            req = urllib.request.Request(url)
            # Add Basic Auth just in case
            if user and password:
                auth_str = base64.b64encode(f'{user}:{password}'.encode('utf-8')).decode('utf-8')
                req.add_header("Authorization", f"Basic {auth_str}")
                
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    ctype = response.headers.get('Content-Type', '')
                    data = response.read(4)
                    if 'image' in ctype or data.startswith(b'\xff\xd8'):
                         print(f"  [SUCCESS] Snapshot Found!")
                         return True
        except Exception as e:
            # print(f"  [Error] {e}")
            pass
    return False

def main():
    print(f"DIAGNOSING CAMERA {TARGET_IP}")
    
    # 1. SCAN PORTS
    open_ports = scan_ports(TARGET_IP)
    
    # 2. IF 554 OPEN, TRY RTSP
    if 554 in open_ports:
        for user, pwd in CREDENTIALS:
            if check_rtsp(TARGET_IP, 554, user, pwd):
                print(f"\nSOLUTION FOUND: RTSP Port 554, User: {user}, Pass: {pwd}")
                return

    # 4. IF 80 OPEN, TRY SNAPSHOTS
    if 80 in open_ports:
         print("\n--- Testing HTTP Snapshots ---")
         for user, pwd in CREDENTIALS:
             if check_http_snapshot(TARGET_IP, 80, user, pwd):
                 print(f"\nSOLUTION FOUND: HTTP Snapshot, Port 80, User: {user}, Pass: {pwd}")
                 return

    print("\n--- DIAGNOSIS COMPLETE --")
    if 34567 in open_ports and 554 not in open_ports:
        print("CONCLUSION: Only Media/DVR Port 34567 is open.")
        print("This camera likely REQUIRES the proprierary NETIP/SOFIA protocol or RTSP is disabled.")
        print("You must enable RTSP in the camera settings (via IE/CMS) or use a NetIP client.")

if __name__ == "__main__":
    main()
