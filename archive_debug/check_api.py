import urllib.request
import json

try:
    with urllib.request.urlopen("http://127.0.0.1:1984/api/streams") as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.status}")
except Exception as e:
    print(f"Failed to connect to API: {e}")
