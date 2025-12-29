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
    print(f"--- SYNC CAMERAS (DB -> WEB) [V2: DEDUPE & CROP] ---")
    cameras = get_db_cameras()
    print(f"Found {len(cameras)} cameras in DB.")
    
    yaml_content = []
    # Header
    # Dynamic FFmpeg Path
    ffmpeg_abs_path = "ffmpeg"

    yaml_content.extend([
        "log:",
        "  level: info",
        "  api: debug",
        "  rtsp: warn",
        "  streams: error",
        "",
        "ffmpeg:",
        f'  bin: "{ffmpeg_abs_path}"',
        "",
        "api:",
        '  listen: ":1984"',
        '  origin: "*"',
        '  static: "www"',
        "",
        "rtsp:",
        '  listen: ":8554"',
        "",
        "webrtc:",
        '  listen: ":8555"',
        "",
        "streams:"
    ])

    # 1. Deduplicate Sources (URL -> safe_id)
    # Map: source_url -> source_id
    sources = {}
    
    # First Pass: Identify unique physical sources
    for cam in cameras:
        url = cam['stream_url']
        if not url: continue
        url = url.strip() # Normalize
        
        # Use simple hash or cleaned first name as ID basis?
        # Better: use MD5 of URL to be 100% sure, or just the first cam's name that uses it.
        # Let's use MD5 to avoid name collisions.
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        if url not in sources:
            sources[url] = f"src_{url_hash}"

    # Write Physical Sources
    for url, src_id in sources.items():
        # Mask password in logs
        safe_url = re.sub(r':(.*?)\@', ':***@', url)
        print(f" -> Source Defined: {src_id} ({safe_url})")
        yaml_content.append(f"  {src_id}: {url}")

    yaml_content.append("")

    # 2. Define Logical Channels (Consuming from Sources)
    for cam in cameras:
        raw_name = cam['name']
        original_url = cam['stream_url']
        
        # Safe handling of crop_mode
        try: crop_mode = int(cam['crop_mode'])
        except: crop_mode = 0
            
        if not original_url: continue
            
        clean_id = safe_name(raw_name)
        mjpeg_id = f"{clean_id}_mjpeg"
        src_id = sources[original_url] # Get the shared source ID
        
        print(f" -> Channel: {clean_id} (Src: {src_id}, Crop: {crop_mode})")
        
        # Determine Filter String based on Crop
        # H264 Target: 1280x720
        # MJPEG Target: 640x360
        
        # Filters
        vf = ""
        if crop_mode == 0: # Normal
            vf_h264  = "scale=1920:1080"
            vf_uhd   = "scale=1920:1080"
            vf_hd    = "scale=1280:720"
            vf_mjpeg = "scale=640:360"
        elif crop_mode == 1: # 50% Top
            vf_h264  = "crop=in_w:in_h/2:0:0,scale=1920:1080"
            vf_uhd   = "crop=in_w:in_h/2:0:0,scale=1920:1080"
            vf_hd    = "crop=in_w:in_h/2:0:0,scale=1280:720"
            vf_mjpeg = "crop=in_w:in_h/2:0:0,scale=640:360"
        elif crop_mode == 2: # 50% Bottom
            vf_h264  = "crop=in_w:in_h/2:0:in_h/2,scale=1920:1080"
            vf_uhd   = "crop=in_w:in_h/2:0:in_h/2,scale=1920:1080"
            vf_hd    = "crop=in_w:in_h/2:0:in_h/2,scale=1280:720"
            vf_mjpeg = "crop=in_w:in_h/2:0:in_h/2,scale=640:360"
        elif crop_mode == 3: # 33% Top
            vf_h264  = "crop=in_w:in_h/3:0:0,scale=1920:1080"
            vf_uhd   = "crop=in_w:in_h/3:0:0,scale=1920:1080"
            vf_hd    = "crop=in_w:in_h/3:0:0,scale=1280:720"
            vf_mjpeg = "crop=in_w:in_h/3:0:0,scale=640:360"
        elif crop_mode == 4: # 33% Mid
            vf_h264  = "crop=in_w:in_h/3:0:in_h/3,scale=1920:1080"
            vf_uhd   = "crop=in_w:in_h/3:0:in_h/3,scale=1920:1080"
            vf_hd    = "crop=in_w:in_h/3:0:in_h/3,scale=1280:720"
            vf_mjpeg = "crop=in_w:in_h/3:0:in_h/3,scale=640:360"
        elif crop_mode == 5: # 33% Bot
            vf_h264  = "crop=in_w:in_h/3:0:2*in_h/3,scale=1920:1080"
            vf_uhd   = "crop=in_w:in_h/3:0:2*in_h/3,scale=1920:1080"
            vf_hd    = "crop=in_w:in_h/3:0:2*in_h/3,scale=1280:720"
            vf_mjpeg = "crop=in_w:in_h/3:0:2*in_h/3,scale=640:360"
        else:
            vf_h264  = "scale=1920:1080"
            vf_uhd   = "scale=1920:1080"
            vf_hd    = "scale=1280:720"
            vf_mjpeg = "scale=640:360"

        # MAIN STREAM (H264)
        # Consumes from LOCALHOST rtsp (reusing the source connection)
        # This keeps the logic consistent: Everything consumes the 'src' stream.
        # BUT: For 'ffmpeg:' source in Go2RTC, it's better to reference the ID directly if possible
        # or use the rtsp loopback. RTSP loopback is more robust for 'exec' commands.
        # For 'ffmpeg:' modules, we can refer to the stream name directly? 
        # Actually, Go2RTC allows `ffmpeg:src_stream#...` syntax.
        
        # H264 Stream Entry
        transcode_cmd = f"ffmpeg:{src_id}#video=h264#vf={vf_h264}"
        yaml_content.append(f"  {clean_id}: {transcode_cmd}")
        
        # MJPEG Stream Entry (EXEC FFMPEG)
        # MUST connect to localhost RTSP to reuse connection.
        # MJPEG/H264 Stream Entry (EXEC FFMPEG)
        # Fix for Spaces in Path: Use relative path "go2rtc_bin/ffmpeg.exe" (Go2RTC runs from CWD or bin)
        # Using forward slashes for YAML safety
        ffmpeg_bin = "ffmpeg"
        
        # Low FPS for mobile
        # SD Stream (Grid - 360p @ 15fps)
        mjpeg_cmd = f'exec:"{ffmpeg_bin}" -hide_banner -rtsp_transport tcp -i "rtsp://127.0.0.1:8554/{src_id}" -vf "{vf_mjpeg}" -r 15 -c:v mjpeg -an -f mjpeg -'
        yaml_content.append(f"  {mjpeg_id}: {mjpeg_cmd}")

        # HD Stream (Player - 720p @ 24fps)
        hd_id = f"{clean_id}_hd"
        hd_cmd = f'exec:"{ffmpeg_bin}" -hide_banner -rtsp_transport tcp -i "rtsp://127.0.0.1:8554/{src_id}" -vf "{vf_hd}" -r 24 -q:v 3 -c:v mjpeg -an -f mjpeg -'
        yaml_content.append(f"  {hd_id}: {hd_cmd}")
        
        # UHD Stream (Cinema - 1080p @ 24fps)
        uhd_id = f"{clean_id}_uhd"
        uhd_cmd = f'exec:"{ffmpeg_bin}" -hide_banner -rtsp_transport tcp -i "rtsp://127.0.0.1:8554/{src_id}" -vf "{vf_uhd}" -r 24 -q:v 3 -c:v mjpeg -an -f mjpeg -'
        yaml_content.append(f"  {uhd_id}: {uhd_cmd}")
        yaml_content.append("")

    # Write Config
    try:
        with open(GO2RTC_CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write("\n".join(yaml_content))
        print(f"\n[SUCCESS] Wrote configuration to {GO2RTC_CONFIG_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to write config: {e}")

if __name__ == "__main__":
    sync_config()
