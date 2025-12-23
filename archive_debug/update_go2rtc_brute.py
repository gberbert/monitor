import os

YAML_PATH = r"c:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\go2rtc_bin\go2rtc.yaml"

USERS = ["admin", "default", "berbert", "system"]
PASSWORDS = [
    "", 
    "admin", 
    "123456", 
    "12345", 
    "viguera2001", 
    "888888", 
    "666666", 
    "password", 
    "xmhdipc", 
    "tlJwpbo6", 
    "111111", 
    "000000"
]

def generate_yaml():
    content = "streams:\n"
    count = 0
    
    for u in USERS:
        for p in PASSWORDS:
            count += 1
            stream_name = f"cam_try_{count}"
            # dvrip://user:pass@ip:port
            # If pass is empty, it might need special handling? dvrip://user:@ip...
            
            # Go2RTC URL encoding needs? Usually user:pass is fine.
            # If pass is empty: user:@ip
            
            url = f"dvrip://{u}:{p}@192.168.3.27:34567"
            print(f"Generated: {stream_name} -> {u}:{p}")
            content += f"  {stream_name}: {url}\n"
            
            # Also try channel=1 just in case
            # content += f"  {stream_name}_ch1: {url}&channel=1\n"
            
    with open(YAML_PATH, "w") as f:
        f.write(content)
    
    print(f"\nUpdated {YAML_PATH} with {count} streams.")

if __name__ == "__main__":
    generate_yaml()
