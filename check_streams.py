import requests
import json

try:
    print("Querying Go2RTC streams...")
    r = requests.get("http://127.0.0.1:1984/api/streams")
    if r.status_code == 200:
        streams = r.json()
        print(json.dumps(streams, indent=2))
        print(f"\nTotal streams found: {len(streams)}")
    else:
        print(f"Error: Status {r.status_code}")
except Exception as e:
    print(f"Connection failed: {e}")
