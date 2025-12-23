
from desktop_app.vms_core import VMSCore
import time
import os
import multiprocessing

# Windows Multiprocessing Fix
if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    print("--- VMS CORE STANDALONE DEBUG ---")
    vms = VMSCore()
    
    # URL = "rtsp://admin:@192.168.3.14:554/cam/realmonitor?channel=1&subtype=1"
    # Testing with a potentially problematic one just in case, but let's stick to the good one first.
    URL = "rtsp://admin:@192.168.3.14:554/cam/realmonitor?channel=1&subtype=1"
    
    print(f"Starting Camera: {URL}")
    vms.start_camera("cam_debug", URL)
    
    start_time = time.time()
    frames = 0
    
    while time.time() - start_time < 10:
        # Check Status
        status = vms.get_status()
        if status:
            print(f"STATUS: {status}")
            
        # Check Frame
        frame = vms.get_frame()
        if frame:
            cam_id, img = frame
            frames += 1
            if frames % 10 == 0:
                print(f"Frame received! Shape: {img.shape}")
                
        time.sleep(0.01)
        
    print("Stopping...")
    vms.stop_all()
    print(f"Total Frames: {frames}")
