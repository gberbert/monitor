import sqlite3
import os
import re

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "desktop_app", "cameras.db")
GO2RTC_CONFIG_PATH = os.path.join(BASE_DIR, "go2rtc_bin", "go2rtc.yaml")

def get_db_cameras():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at: {DB_PATH}")
        return []
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT name, stream_url, crop_mode FROM cameras")
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] Failed to read DB: {e}")
        return []

def safe_name(name):
    # Convert "Câmera da Rua" to "camera_da_rua"
    s = name.lower()
    # Normalize accents
    import unicodedata
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[^a-z0-9]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def sync_config():
    print(f"--- SYNC CAMERAS (DB -> WEB) ---")
    cameras = get_db_cameras()
    print(f"Found {len(cameras)} cameras in DB.")
    
    yaml_content = []
    yaml_content.append("log:")
    yaml_content.append("  level: info")
    yaml_content.append("  api: debug")
    yaml_content.append("  rtsp: warn")
    yaml_content.append("  streams: error")
    yaml_content.append("")
    yaml_content.append("ffmpeg:")
    yaml_content.append('  bin: "C:/antigravity_www/ffmpeg.exe"')
    yaml_content.append("")
    yaml_content.append("api:")
    yaml_content.append('  listen: ":1984"')
    yaml_content.append('  origin: "*"')
    yaml_content.append('  static: "www"')
    yaml_content.append("")
    yaml_content.append("webrtc:")
    yaml_content.append('  listen: ":8555"')
    yaml_content.append("")
    yaml_content.append("streams:")

    # Process Cameras
    for cam in cameras:
        raw_name = cam['name']
        original_url = cam['stream_url']
        # Read crop mode independently because row factory might vary
        crop_mode = 0
        try: crop_mode = int(cam['crop_mode'])
        except: pass
        
        if not original_url:
            print(f"[SKIP] Camera '{raw_name}' has no URL.")
            continue
            
        # Create IDs
        clean_id = safe_name(raw_name)
        src_id = f"{clean_id}_src"
        mjpeg_id = f"{clean_id}_mjpeg"
        
        print(f" -> Adding: {raw_name} (Crop: {crop_mode})")
        
        # 1. Source Stream (RTSP raw)
        yaml_content.append(f"  {src_id}: {original_url}")
        
        if crop_mode == 1:
            vf_filter = "crop=in_w:in_h/2:0:0,scale=1024:576"
        elif crop_mode == 2:
            vf_filter = "crop=in_w:in_h/2:0:in_h/2,scale=1024:576"
        else:
            vf_filter = "scale=1024:576"
        
        # 2. Main Stream (H.264 - WebRTC) - Keep standard magic, it usually works for H264
        # Apply crop BEFORE scaling if needed
        h264_vf = vf_filter.replace("1024:576", "1280:720") # Adjust scale for HD
        transcode_cmd = f"ffmpeg:{src_id}#video=h264#vf={h264_vf}"
        yaml_content.append(f"  {clean_id}: {transcode_cmd}")
        
        # 3. Fluid MJPEG Stream (Exec Mode - Manual Control)
        # Using 'exec:' guarantees our filters run exactly as written without Go2RTC changing them
        # "-an" = No Audio (MJPEG doesn't carry audio well usually alongside video in one pipe here)
        ffmpeg_bin = "C:/antigravity_www/ffmpeg.exe"
        # Hide credentials in logs slightly
        safe_url = original_url.replace("&", "\&") 
        
        mjpeg_cmd = f'exec:{ffmpeg_bin} -hide_banner -rtsp_transport tcp -i "{original_url}" -vf "{vf_filter}" -c:v mjpeg -an -f mjpeg -'
        
        yaml_content.append(f"  {mjpeg_id}: {mjpeg_cmd}")
        
        yaml_content.append("")

    # Write Config
    try:
        with open(GO2RTC_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write("\n".join(yaml_content))
        print(f"\n[SUCCESS] Wrote configuration to {GO2RTC_CONFIG_PATH}")
        print("Please restart Go2RTC to apply changes.")
    except Exception as e:
        print(f"[ERROR] Failed to write config: {e}")

if __name__ == "__main__":
    sync_config()
