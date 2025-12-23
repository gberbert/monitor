
import cv2
import time
import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

URL = "rtsp://admin:@192.168.3.14:554/cam/realmonitor?channel=1&subtype=1"

print(f"--- TESTING OPENCV SINGLE CONNECTION ---")
print(f"URL: {URL}")

try:
    print("1. Opening VideoCapture...")
    cap = cv2.VideoCapture(URL, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("   -> Failed to open!")
        exit(1)
        
    print("   -> Success!")
    
    print("2. Reading 10 Frames...")
    t0 = time.time()
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            print(f"   Frame {i+1}: {frame.shape}")
        else:
            print("   -> Read failed!")
            break
            
        if time.time() - t0 > 10:
            print("   -> Timeout!")
            break
            
    cap.release()
    print("--- SUCCESS ---")
    
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
