
import multiprocessing
import time
import numpy as np
import cv2
import queue
import os

# Configurações de Buffer
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

class CameraProcess(multiprocessing.Process):
    def __init__(self, camera_id, url, frame_queue, status_queue, command_queue):
        super().__init__()
        self.camera_id = camera_id
        self.url = url
        self.frame_queue = frame_queue 
        self.status_queue = status_queue
        self.command_queue = command_queue
        self._running = True

    def run(self):
        # Configurar opções FFMPEG (embora ja configurado no main, é bom garantir no processo filho se necessario, 
        # mas env vars geralmente herdam. Porem, no Windows multiprocessing 'spawn', precisamos redefinir?)
        # Melhor definir aqui também por segurança.
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|hwaccel;0|probesize;2097152|analyzeduration;2000000|reorder_queue_size;50"
        
        self.status_queue.put((self.camera_id, "STARTING"))
        
        while self._running:
            try:
                # Checar comandos
                try:
                    cmd = self.command_queue.get_nowait()
                    if cmd == "STOP":
                        self._running = False
                        break
                except queue.Empty: pass

                self.status_queue.put((self.camera_id, "CONNECTING..."))
                
                # OpenCV Capture
                cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                
                if not cap.isOpened():
                     self.status_queue.put((self.camera_id, "OFFLINE"))
                     time.sleep(5)
                     continue
                     
                self.status_queue.put((self.camera_id, "ONLINE"))
                
                fps_limit = 15
                prev_time = 0
                fail_count = 0
                
                while self._running:
                    # Checar comandos durante loop
                    try:
                        if self.command_queue.get_nowait() == "STOP":
                            self._running = False
                            break
                    except queue.Empty: pass
                    
                    ret, frame = cap.read()
                    if not ret:
                        fail_count += 1
                        if fail_count > 30: # 30 frames falhos = reconectar
                             self.status_queue.put((self.camera_id, "LOST SIGNAL"))
                             break
                        time.sleep(0.1)
                        continue
                        
                    fail_count = 0
                    
                    # Limitar FPS
                    now = time.time()
                    if (now - prev_time) < (1.0/fps_limit):
                        continue
                    prev_time = now
                    
                    try:
                        # Resize se necessario
                        h, w = frame.shape[:2]
                        if w > 1280:
                             frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)

                        # Enviar para fila (Drop oldest strategy)
                        if self.frame_queue.full():
                            try: self.frame_queue.get_nowait()
                            except: pass
                        
                        self.frame_queue.put((self.camera_id, frame))
                        
                    except Exception as e:
                        print(f"[{self.camera_id}] Frame Error: {e}")
                        pass
                
                cap.release()
                
            except Exception as e:
                self.status_queue.put((self.camera_id, "ERROR"))
                print(f"[{self.camera_id}] Critical: {e}")
                time.sleep(5)
                
        self.status_queue.put((self.camera_id, "STOPPED"))


class VMSCore:
    def __init__(self):
        self.processes = {}
        # Filas Multiprocessing
        self.frame_queue = multiprocessing.Queue(maxsize=30) 
        self.status_queue = multiprocessing.Queue()
        self.command_queues = {}
        
    def start_camera(self, cam_id, url):
        self.stop_camera(cam_id)
        cmd_q = multiprocessing.Queue()
        p = CameraProcess(cam_id, url, self.frame_queue, self.status_queue, cmd_q)
        p.start()
        self.processes[cam_id] = p
        self.command_queues[cam_id] = cmd_q
        print(f"Camera Process Started: {cam_id}")
        
    def stop_camera(self, cam_id):
        if cam_id in self.processes:
            try: self.command_queues[cam_id].put("STOP")
            except: pass
            
            # Não bloquear UI com join longo
            
            del self.processes[cam_id]
            del self.command_queues[cam_id]

    def stop_all(self):
        for cid in list(self.processes.keys()):
            self.stop_camera(cid)

    def get_frame(self):
        try: return self.frame_queue.get_nowait()
        except queue.Empty: return None
            
    def get_status(self):
        try: return self.status_queue.get_nowait()
        except queue.Empty: return None
