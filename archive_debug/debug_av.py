
import av
import time
import os

URL = "rtsp://berbert:viguera2001@192.168.3.27:34567/user=berbert&password=viguera2001&channel=1&stream=1.sdp"
# URL = "rtsp://berbert:viguera2001@192.168.3.27:554/user=berbert&password=viguera2001&channel=1&stream=1.sdp" # Teste porta 554

print(f"Connecting to {URL} using PyAV...")

try:
    # Verbose logging (if possible via env, though av python bindings act differently)
    # Using TCP is crucial
    container = av.open(URL, options={'rtsp_transport': 'tcp', 'stimeout': '5000000', 'probesize': '10485760'})
    print("Container opened!")
    print(f"Format: {container.format.name}")
    print(f"Streams: {len(container.streams)}")
    
    stream = container.streams.video[0]
    print(f"Stream: {stream.type} | Codec: {stream.codec_context.name}")
    print(f"Profile: {stream.codec_context.profile}")
    
    print("Decoding frames...")
    count = 0
    for frame in container.decode(stream):
        print(f"Frame {count}: {frame.width}x{frame.height} | Keyframe: {frame.key_frame}")
        count += 1
        if count > 10:
            break
            
    print("Success!")
except Exception as e:
    print(f"FAILED: {e}")

