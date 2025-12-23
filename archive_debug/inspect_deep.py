
import pkgutil
import dvrip
import importlib

print(f"Path: {dvrip.__path__}")

print("--- SUBMODULES ---")
for loader, module_name, is_pkg in pkgutil.walk_packages(dvrip.__path__):
    print(f"{module_name} (Pkg: {is_pkg})")
    try:
        importlib.import_module(f"dvrip.{module_name}")
    except Exception as e:
        print(f"  Error importing {module_name}: {e}")
