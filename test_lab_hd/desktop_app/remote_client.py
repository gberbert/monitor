import requests
import json

class RemoteClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        print(f"📡 Remote Client Initialized: {self.base_url}")

    def init_db(self):
        # Remote DB is managed by server
        pass

    def get_all_cameras(self):
        try:
            url = f"{self.base_url}/api/cameras"
            print(f"GET {url}")
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                # REWRITE URLs for Remote Access (Tunneling)
                # Local RTSP (192.168...) won't work remotely.
                # We replace it with the Proxy MJPEG stream.
                for cam in data:
                    clean_id = self._to_safe_id(cam['name'])
                    # Use the MJPEG proxy endpoint
                    # Append timestamp to prevent aggressive caching if needed, though requests handles stream
                    cam['url'] = f"{self.base_url}/api/stream.mjpeg?src={clean_id}_mjpeg"
                    print(f"Remote Rewrote URL: {cam['url']}")
                
                print(f"Received {len(data)} cameras from remote.")
                return data
            else:
                print(f"Error fetching cameras: {res.status_code}")
                return []
        except Exception as e:
            print(f"Remote Fetch Error: {e}")
            return []

    def _to_safe_id(self, name):
        import unicodedata, re
        # Same logic as JS/Python proxy
        n = name.lower()
        n = unicodedata.normalize('NFD', n).encode('ascii', 'ignore').decode("utf-8")
        n = re.sub(r'[^a-z0-9]', '_', n)
        n = re.sub(r'_+', '_', n)
        return n.strip('_')

    def upsert_camera(self, mac, name, ip, username, password, url, crop_mode=0):
        try:
            payload = {
                "mac": mac,
                "name": name,
                "ip": ip,
                "username": username,
                "password": password,
                "url": url,
                "crop_mode": crop_mode
            }
            res = requests.post(f"{self.base_url}/api/save_camera", json=payload, timeout=5)
            if res.status_code != 200:
                print(f"Remote Save Failed: {res.text}")
        except Exception as e:
            print(f"Remote Upsert Exception: {e}")

# Global instance pattern (similar to module usage)
_instance = None

def setup(url):
    global _instance
    _instance = RemoteClient(url)

# Module-level wrapper functions to mimic database.py
def init_db():
    if _instance: _instance.init_db()

def get_all_cameras():
    if _instance: return _instance.get_all_cameras()
    return []

def upsert_camera(mac, name, ip, username, password, url, crop_mode=0):
    if _instance: _instance.upsert_camera(mac, name, ip, username, password, url, crop_mode)
