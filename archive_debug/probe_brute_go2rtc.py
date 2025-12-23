import cv2
import time
import sys

def check_stream(name):
    url = f"rtsp://127.0.0.1:8554/{name}"
    print(f"Checking {url} ...")
    # Use extreme timeout to fail fast? 
    # OpenCV doesn't respect timeout well for RTSP unless via environment.
    # But localhost should accept/reject fast.
    
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            print(f"SUCCESS! Stream '{name}' is working.")
            return True
    return False

def main():
    print("Probing Go2RTC Brute Force Streams (1-48)...")
    
    found = False
    for i in range(1, 49):
        s = f"cam_try_{i}"
        if check_stream(s):
            print(f"\n>>> FOUND WORKING CONFIG: {s} <<<")
            found = True
            break
            
    if not found:
        print("\nALL STREAMS FAILED via Go2RTC.")

if __name__ == "__main__":
    main()
