
import dvrip
import inspect

print("--- DVRIP MODULE CONTENT ---")
print(dir(dvrip))

print("\n--- ATTRIBUTES ---")
for name in dir(dvrip):
    if not name.startswith("_"):
        attr = getattr(dvrip, name)
        print(f"{name}: {type(attr)}")

try:
    from dvrip import DVRIPCam
    print("\n[SUCCESS] from dvrip import DVRIPCam")
except ImportError as e:
    print(f"\n[FAIL] from dvrip import DVRIPCam: {e}")

