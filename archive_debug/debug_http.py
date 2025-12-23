
import socket

# Tentativa Bruta de Senha 'Admin' Padrao (Vazio)
# Mas vamos tentar 'Recuperação de Senha' (Account Locked?)

# Tentar se conectar na porta 80 via HTTP Requests para ver se responde "401 Unauthorized" ou algo assim
import urllib.request
import urllib.error

url = "http://192.168.3.27/"
print(f"Testing HTTP {url}...")
try:
    with urllib.request.urlopen(url, timeout=2) as f:
        print(f"Status: {f.status}")
        print(f"Content: {f.read(100)}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(f"Headers: {e.headers}")
except Exception as e:
    print(f"Fail: {e}")
