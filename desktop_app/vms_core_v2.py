
import multiprocessing
import time
import ctypes
import numpy as np
import cv2
import av
import queue
from multiprocessing import shared_memory
import socket

# Configurações de Buffer
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
CHANNELS = 3
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT * CHANNELS
BUFFER_COUNT = 3 # Triple buffering

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
        self.status_queue.put((self.camera_id, "STARTING"))
        
        while self._running:
            try:
                # Verifica comandos
                try:
                    cmd = self.command_queue.get_nowait()
                    if cmd == "STOP":
                        self._running = False
                        break
                except queue.Empty:
                    pass

                self.status_queue.put((self.camera_id, "CONNECTING..."))
                
                # Check de Porta Removido (Causava falso negativo)
                pass

                # PyAV: A solução "Bala de Prata" para H.265/Chinese Cams
                try:
                    container = av.open(self.url, options={'rtsp_transport': 'tcp', 'stimeout': '5000000'})
                    stream = container.streams.video[0]
                    stream.thread_type = 'AUTO' 
                    
                    self.status_queue.put((self.camera_id, "STREAMING"))
                    
                    fps_limit = 15 
                    prev_time = 0
                    
                    for frame in container.decode(stream):
                        if not self._running: break
                        
                        now = time.time()
                        if (now - prev_time) < (1.0/fps_limit):
                            continue
                        prev_time = now
                        
                        try:
                            # Frame PyAV -> Numpy BGR
                            img = frame.to_ndarray(format='bgr24')
                            
                            # Resize Safe
                            h, w = img.shape[:2]
                            if w > 1280:
                                 img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_AREA)

                            if self.frame_queue.full():
                                try: self.frame_queue.get_nowait()
                                except: pass
                            self.frame_queue.put((self.camera_id, img))
                            
                        except Exception as e:
                            # print(f"[{self.camera_id}] Decode Error: {e}")
                            continue
                except Exception as e:
                    # Tratamento Generico para evitar Crash de Import
                    err_str = str(e)
                    # print(f"[{self.camera_id}] AV Error: {err_str}")
                    
                    if "Invalid data" in err_str: msg = "INVALID URL"
                    elif "10061" in err_str or "refused" in err_str: msg = "CONN REFUSED" 
                    elif "timeout" in err_str.lower(): msg = "TIMEOUT"
                    elif "401" in err_str: msg = "AUTH FAIL"
                    elif "No such file" in err_str: msg = "PATH ERROR"
                    else: msg = "ERROR" # Mensagem curta pra caber na UI
                    
                    self.status_queue.put((self.camera_id, msg))
                    time.sleep(5) # Espera antes de reconectar
                        
            except Exception as e:
                self.status_queue.put((self.camera_id, "CRITICAL ERROR"))
                print(f"[{self.camera_id}] CRITICAL LOOP ERROR: {e}")
                time.sleep(5)
                
        self.status_queue.put((self.camera_id, "STOPPED"))

class VMSCore:
    def __init__(self):
        self.processes = {}
        self.frame_queue = multiprocessing.Queue(maxsize=30) 
        self.status_queue = multiprocessing.Queue()
        self.command_queues = {}
        
    def start_camera(self, cam_id, url):
        if cam_id in self.processes:
            self.stop_camera(cam_id)
            
        cmd_q = multiprocessing.Queue()
        p = CameraProcess(cam_id, url, self.frame_queue, self.status_queue, cmd_q)
        p.daemon = True
        p.start()
        
        self.processes[cam_id] = p
        self.command_queues[cam_id] = cmd_q
        
    def stop_camera(self, cam_id):
        if cam_id in self.processes:
            self.command_queues[cam_id].put("STOP")
            # Give it a second to stop gracefully
            self.processes[cam_id].join(timeout=1.0)
            if self.processes[cam_id].is_alive():
                self.processes[cam_id].terminate()
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
