import json
import os

CONFIG_FILE = "desktop_config.json"

DEFAULT_CONFIG = {
    "server_url": "http://localhost:5000",
    "remote_url": "",
    "auth_token": "",
    "mode": "auto",  # auto, local, remote
    "use_gpu": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
