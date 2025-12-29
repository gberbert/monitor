import os
import subprocess
import glob

# Path to FFmpeg/Probe
monitor_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ffprobe_bin = os.path.join(monitor_root, "go2rtc_bin", "ffprobe.exe") # Usually in same folder? Or ffmpeg folder?
if not os.path.exists(ffprobe_bin):
    # Try generic
    ffprobe_bin = "ffprobe"

def analyze_video():
    print("--- DIAGNOSTICO DE VIDEO ---")
    
    # Find latest video
    files = glob.glob("recordings/piscina/*.mp4")
    if not files:
        print("[ERRO] Nenhum video encontrado em recordings/piscina!")
        return
        
    latest_video = max(files, key=os.path.getctime)
    print(f"Analisando: {latest_video}")
    print(f"Tamanho: {os.path.getsize(latest_video)} bytes")
    
    # Run FFprobe/FFmpeg
    ffmpeg_path = r"C:\Users\K\OneDrive\Documentos\PROJETOS ANTIGRAVITY\monitor\go2rtc_bin\ffmpeg.exe"
    try:
        # Use ffmpeg -i as probe
        cmd = [ffmpeg_path, "-hide_banner", "-i", latest_video]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        print("\n--- METADADOS (stderr) ---")
        print(result.stderr)
        
        if "h264" in result.stderr:
            print(">>> CODEC OK (H.264)")
        else:
            print(">>> CODEC PROBLEMATICO (Nao eh H.264)")
            
        if "creation_time" in result.stderr:
             print(">>> CREATION TIME ENCONTRADO!")
             # Extract logic could go here, but let's just see output first.
        else:
             print(">>> CREATION TIME AUSENTE (Usando padrao do container?)")
            
    except Exception as e:
        print(f"[ERRO] Falha ao rodar FFprobe: {e}")

if __name__ == "__main__":
    analyze_video()
