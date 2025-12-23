
import av
import time
import sys

# URL known to be good (Piscina)
URL = "rtsp://admin:@192.168.3.14:554/cam/realmonitor?channel=1&subtype=1"

print(f"--- TESTING PYAV SINGLE CONNECTION ---")
print(f"URL: {URL}")

try:
    print("1. Opening Container (Timeout 5s)...")
    # Using 'tcp' is critical
    container = av.open(URL, options={'rtsp_transport': 'tcp', 'stimeout': '5000000'})
    print("   -> Success!")
    
    print("2. Finding Video Stream...")
    stream = container.streams.video[0]
    print(f"   -> Stream Found: {stream.type} / {stream.codec_context.name}")
    
    print("3. Decoding 10 Frames...")
    count = 0
    t0 = time.time()
    for frame in container.decode(stream):
        count += 1
        print(f"   Frame {count}: {frame.width}x{frame.height} pts={frame.pts}")
        if count >= 10:
            break
        if time.time() - t0 > 10:
             print("   -> Timeout decoding loop!")
             break
             
    print("--- SUCCESS ---")
    
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
