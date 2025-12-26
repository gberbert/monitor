import os
import yaml
import requests
import urllib.parse

# Path to config
CONFIG_FILE = os.path.join("go2rtc_bin", "go2rtc.yaml")
API_URL = "http://127.0.0.1:1984/api/streams"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("Config not found.")
        return None
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def apply_streams():
    config = load_config()
    if not config or 'streams' not in config:
        print("No streams in config.")
        return

    print(f"Applying {len(config['streams'])} streams to Go2RTC...")
    
    for name, src in config['streams'].items():
        # Handle list or string
        if isinstance(src, list):
            src_str = src[0] # Simplification
        else:
            src_str = src
            
        # Encode params
        params = {
            "name": name,
            "src": src_str
        }
        
        try:
            # PUT creates/updates the stream
            r = requests.put(API_URL, params=params)
            if r.status_code in [200, 201]:
                print(f"OK: {name}")
            else:
                print(f"FAIL: {name} ({r.status_code}) - {r.text}")
        except Exception as e:
            print(f"ERR: {name} - {e}")

if __name__ == "__main__":
    # Ensure pyyaml is installed? 
    # Whatever, simple parsing if yaml not available or try to install
    try:
        import yaml
    except:
        os.system("pip install pyyaml")
        import yaml
        
    apply_streams()
