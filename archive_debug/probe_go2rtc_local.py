import cv2
import time
import sys

STREAMS = [
    "camera_27_main",
    "camera_27_empty", 
    "camera_27_default", 
    "camera_27_user_app"
]

def check_stream(name):
    url = f"rtsp://127.0.0.1:8554/{name}"
    print(f"Checking {url} ...")
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"SUCCESS! Stream '{name}' is working.")
            return True, url
    return False, None

def main():
    print("Probing Go2RTC Local Streams...")
    
    # First, let's force go2rtc to add them if they aren't there from the yaml?
    # They should be there if yaml was loaded.
    
    found = False
    for s in STREAMS:
        ok, url = check_stream(s)
        if ok:
            print(f"\n>>> FOUND WORKING CONFIG: {s} <<<")
            print(f"URL: {url}")
            # Identify which credential this corresponds to
            if s == "camera_27_main": print("Creds: admin / viguera2001")
            elif s == "camera_27_empty": print("Creds: admin / <empty>")
            elif s == "camera_27_default": print("Creds: admin / admin")
            elif s == "camera_27_user_app": print("Creds: berbert / viguera2001")
            
            found = True
            break
            
    if not found:
        print("\nALL STREAMS FAILED via Go2RTC.")
        print("Possible reasons:")
        print("1. Go2RTC is not running (check background process)")
        print("2. Credentials in go2rtc.yaml are all wrong")
        print("3. Camera port 34567 is not reachable/blocked")

if __name__ == "__main__":
    main()
