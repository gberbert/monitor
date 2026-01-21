import os
import requests
import re

CONFIG_FILE = os.path.join("go2rtc_bin", "go2rtc.yaml")
API_URL = "http://127.0.0.1:1984/api/streams"

def parse_and_push():
    print(f"Reading {CONFIG_FILE}...")
    with open(CONFIG_FILE, 'r') as f:
        lines = f.readlines()

    in_streams = False
    for line in lines:
        line = line.strip()
        if line == "streams:":
            in_streams = True
            continue
        
        if in_streams and ":" in line:
            # simple parsing: key: value
            # Handle comments or empty lines
            if not line or line.startswith("#"): continue
            
            parts = line.split(":", 1)
            if len(parts) < 2: continue
            
            key = parts[0].strip()
            val = parts[1].strip()
            
            # Remove quotes if present
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            if val.startswith("'") and val.endswith("'"):
                val = val[1:-1]

            print(f"Pushing {key}...")
            try:
                r = requests.put(API_URL, params={"name": key, "src": val})
                if r.status_code != 200:
                    print(f"Failed to push {key}: {r.text}")
            except Exception as e:
                print(f"Error pushing {key}: {e}")

if __name__ == "__main__":
    try:
        parse_and_push()
        print("\nHot Reload Complete!")
    except Exception as e:
        print(f"Fatal Error: {e}")
