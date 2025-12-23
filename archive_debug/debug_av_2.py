
import av
import sys

# Test 2: Standard RTSP port 554
URL = "rtsp://berbert:viguera2001@192.168.3.27:554/user=berbert&password=viguera2001&channel=1&stream=1.sdp"
print(f"Connecting to {URL}...")

try:
    container = av.open(URL, options={'rtsp_transport': 'tcp'})
    print("Container opened!")
    # Just need to know if it opens
    sys.exit(0)
except Exception as e:
    print(f"FAILED 554: {e}")

# Test 3: Simple path (sometimes url parameters are passed differently)
URL = "rtsp://berbert:viguera2001@192.168.3.27:554/live/ch1"
print(f"Connecting to {URL}...")
try:
    container = av.open(URL, options={'rtsp_transport': 'tcp'})
    print("Container opened!")
    sys.exit(0)
except Exception as e:
    print(f"FAILED Simple Path: {e}")

# Test 4: H264 specific path (if camera supports it)
URL = "rtsp://berbert:viguera2001@192.168.3.27:554/cam/realmonitor?channel=1&subtype=1"
print(f"Connecting to {URL}...")
try:
    container = av.open(URL, options={'rtsp_transport': 'tcp'})
    print("Container opened!")
    sys.exit(0)
except Exception as e:
    print(f"FAILED Realmonitor: {e}")
