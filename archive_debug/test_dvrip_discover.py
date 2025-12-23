
from dvrip.discover import discover
import json

print("Searching for cameras...")
cameras = discover()
print(f"Found {len(cameras)} cameras")
for cam in cameras:
    print(cam)
