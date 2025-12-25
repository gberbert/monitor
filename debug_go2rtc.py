import requests
import json

try:
    r = requests.get("http://127.0.0.1:1984/api/streams")
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))
        
        # Check specific keys
        print("\nChecking keys:")
        for k in data.keys():
            print(f"- {k}")
            
    else:
        print(r.text)
except Exception as e:
    print(f"Error: {e}")
