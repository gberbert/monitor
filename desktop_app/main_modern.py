# --- CONFIGURAÇÕES MISTAS (LOCAL/REMOTO) ---
import config_manager
import database as local_db
import remote_client
import time
import sys
import os
import re
import qtawesome as qta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QStackedWidget, QLabel, 
                             QLineEdit, QFormLayout, QTextEdit, QFrame, QMessageBox, 
                             QSizePolicy, QScrollArea, QGridLayout, QDialog, QDialogButtonBox, QComboBox, QSpacerItem)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QThread
from PyQt6.QtGui import QIcon, QAction, QPixmap, QImage, QPainter
from scanner import NetworkScanner
from styles import DARK_THEME
import cv2
import numpy as np
import urllib.request
from vms_core import VMSCore

# GLOBAL DATA PROVIDER (Substitui 'import database as db')
db = None 

# --- DIALOG DE CONFIGURAÇÃO ---
class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração de Conexão")
        self.setFixedWidth(450)
        self.setStyleSheet(DARK_THEME + "QDialog { background: #252526; } QLabel { color: white; }")
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        cfg = config_manager.load_config()
        
        self.inp_remote = QLineEdit(cfg.get("remote_url", ""))
        self.inp_remote.setPlaceholderText("Ex: https://cameras.meudominio.com")
        self.inp_remote.setStyleSheet("padding: 8px; background: #333; color: white; border: 1px solid #444;")
        
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["AUTO (Detectar)", "LOCAL (Forçar 127.0.0.1)", "REMOTO (Forçar URL)"])
        mode_map = {"auto": 0, "local": 1, "remote": 2}
        self.combo_mode.setCurrentIndex(mode_map.get(cfg.get("mode", "auto"), 0))
        self.combo_mode.setStyleSheet("padding: 8px; background: #333; color: white;")

        lbl_info = QLabel("Defina a URL Remota (Cloudflare) para acessar fora de casa.\nO modo AUTO tenta Local primeiro, depois Remoto.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #aaa; font-size: 11px; margin-bottom: 10px;")
        
        form.addRow("URL Remota:", self.inp_remote)
        form.addRow("Modo:", self.combo_mode)
        
        layout.addWidget(lbl_info)
        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.save_and_restart)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
        self.setLayout(layout)

    def save_and_restart(self):
        modes = ["auto", "local", "remote"]
        new_cfg = {
            "remote_url": self.inp_remote.text().strip(),
            "mode": modes[self.combo_mode.currentIndex()]
        }
        
        current = config_manager.load_config()
        current.update(new_cfg)
        config_manager.save_config(current)
        
        QMessageBox.information(self, "Salvo", "Configurações salvas!\nO aplicativo será reiniciado.")
        import sys, os
        python = sys.executable
        os.execl(python, python, *sys.argv)

def connect_to_provider():
    global db
    cfg = config_manager.load_config()
    mode = cfg.get("mode", "auto")
    remote_url = cfg.get("remote_url", "")
    
    print(f"🔄 INICIANDO CONEXÃO - MODO: {mode}")
    
    def test_remote(url):
        if not url: return False
        try:
            print(f"📡 Testando Remoto: {url}...")
            import requests
            res = requests.get(f"{url}/api/info", timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"❌ Falha Remota: {e}")
            return False

    selected_provider = None
    
    if mode == "local":
        print("✅ Selecionado MODO LOCAL (Config)")
        selected_provider = local_db
        
    elif mode == "remote":
        if not remote_url:
            QMessageBox.warning(None, "Erro", "Modo Remoto selecionado mas sem URL!")
            return False
        setup_remote(remote_url)
        selected_provider = remote_client

    else: # AUTO
        if os.path.exists(os.path.join("desktop_app", "cameras.db")) or os.path.exists("cameras.db"):
             print("✅ Detectado Banco Local. Usando MODO LOCAL.")
             selected_provider = local_db
        elif remote_url and test_remote(remote_url):
             print("✅ Detectado Conexão Remota. Usando MODO REMOTO.")
             setup_remote(remote_url)
             selected_provider = remote_client
        else:
            print("❌ Nenhuma conexão disponível.")
            return False
            
    db = selected_provider
    db.init_db()
    return True

def setup_remote(url):
    remote_client.setup(url)

class CameraDetailsDialog(QDialog):
    def __init__(self, camera_data, parent=None):
        super().__init__(parent)
        self.data = camera_data
        self.was_split = False 
        self.setWindowTitle("Ficha Técnica da Câmera")
        self.setFixedWidth(400)
        self.setStyleSheet(DARK_THEME + "QDialog { background: #252526; } QLabel { color: white; }")
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.inp_name = QLineEdit(camera_data.get('name', ''))
        self.inp_ip = QLineEdit(camera_data.get('ip', ''))
        self.inp_user = QLineEdit(camera_data.get('username', ''))
        self.inp_pass = QLineEdit(camera_data.get('password', ''))
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_url = QLineEdit(camera_data.get('url', ''))
        
        mac_audit = camera_data.get('mac', '').upper()
        self.inp_mac = QLineEdit(mac_audit)
        self.inp_mac.setInputMask("HH:HH:HH:HH:HH:HH;_") 
        
        for inp in [self.inp_name, self.inp_ip, self.inp_user, self.inp_pass, self.inp_url, self.inp_mac]:
            inp.setStyleSheet("padding: 8px; background: #333; color: white; border: 1px solid #444;")

        form.addRow("Nome:", self.inp_name)
        form.addRow("IP:", self.inp_ip)
        form.addRow("MAC ID:", self.inp_mac)
        form.addRow("Usuário:", self.inp_user)
        form.addRow("Senha:", self.inp_pass)

        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(0,0,0,0)
        url_layout.addWidget(self.inp_url)
        
        self.btn_magic = QPushButton("🪄 Reparar")
        self.btn_magic.setToolTip("Tentar encontrar o link correto automaticamente")
        self.btn_magic.setStyleSheet("background: #6200ea; color: white; padding: 5px 10px; border-radius: 4px;")
        self.btn_magic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_magic.clicked.connect(self.magic_repair_action)
        url_layout.addWidget(self.btn_magic)
        
        form.addRow("Stream URL:", url_layout)
        
        quality_layout = QHBoxLayout()
        self.btn_sd = QPushButton("⚡ SD (Rápido)")
        self.btn_sd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sd.clicked.connect(self.set_sd_stream)

        self.btn_hd = QPushButton("💎 HD (Alta Qualidade)")
        self.btn_hd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hd.clicked.connect(self.set_hd_stream)
        
        quality_layout.addWidget(self.btn_sd)
        quality_layout.addWidget(self.btn_hd)
        form.addRow("Qualidade:", quality_layout)

        self.combo_crop = QComboBox()
        self.combo_crop.addItems(["Normal (Inteira)", "Lente Superior (Topo)", "Lente Inferior (Base)"])
        self.combo_crop.setCurrentIndex(int(camera_data.get('crop_mode', 0)))
        self.combo_crop.setStyleSheet("background: #333; color: white; padding: 5px; border: 1px solid #444;")
        form.addRow("Modo de Visão:", self.combo_crop)

        self.btn_split = QPushButton("✂️ Dividir em 2 Câmeras (Dual Lens)")
        self.btn_split.setStyleSheet("background-color: #d83b01; color: white; padding: 8px; margin-top: 10px;")
        self.btn_split.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_split.clicked.connect(self.split_camera_action)
        layout.addWidget(self.btn_split)

        layout.addLayout(form)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
        self.setLayout(layout)
        self.check_quality_state()

    def check_quality_state(self):
        url = self.inp_url.text()
        is_hd = 'subtype=0' in url or 'stream=0' in url or '/main' in url
        self.update_btn_styles(sd_active=not is_hd)

    def update_btn_styles(self, sd_active):
        active_style = "background: #0078d4; color: #fff; padding: 5px; border-radius: 4px; font-weight: bold;"
        inactive_style = "background: #444; color: #ccc; padding: 5px; border-radius: 4px;"
        
        self.btn_sd.setStyleSheet(active_style if sd_active else inactive_style)
        self.btn_hd.setStyleSheet(inactive_style if sd_active else active_style)

    def magic_repair_action(self):
        user = self.inp_user.text().strip()
        pwd = self.inp_pass.text().strip()
        ip = self.inp_ip.text().strip()
        
        if not ip:
            QMessageBox.warning(self, "Aviso", "Preencha o IP primeiro.")
            return
            
        self.btn_magic.setEnabled(False)
        self.btn_magic.setText("⏳ Buscando...")
        
        self.repair_thread = MagicRepairThread(user, pwd, ip)
        self.repair_thread.checking_signal.connect(lambda t: self.btn_magic.setText("⏳ Testando..."))
        self.repair_thread.found_signal.connect(self.on_magic_found)
        self.repair_thread.finished_signal.connect(self.on_magic_finished)
        self.repair_thread.start()

    def on_magic_found(self, url):
        self.inp_url.setText(url)
        tipo = "CAMINHO HTTP (SNAPSHOT)" if "http" in url else "CAMINHO RTSP (VIDEO)"
        QMessageBox.information(self, "Sucesso", f"🪄 MÁGICA CONCLUÍDA!\n\nTipo: {tipo}\nURL: {url}\n\nClique em SALVAR para testar.")

    def on_magic_finished(self, found):
        self.btn_magic.setEnabled(True)
        self.btn_magic.setText("🪄 Reparar")
        if not found:
             QMessageBox.critical(self, "Falha", "Não foi possível conectar automaticamente.\nVerifique senha/cabo ou tente ONVIF Manager.")

    def set_sd_stream(self):
        url = self.inp_url.text()
        url = url.replace('maintype', 'subtype')
        url = url.replace('subtype=0', 'subtype=1') 
        url = url.replace('stream=0', 'stream=1')
        url = url.replace('/main', '/sub')
        self.inp_url.setText(url)
        self.update_btn_styles(sd_active=True)

    def set_hd_stream(self):
        url = self.inp_url.text()
        url = url.replace('maintype', 'subtype')
        url = url.replace('subtype=1', 'subtype=0')
        url = url.replace('stream=1', 'stream=0')
        url = url.replace('/sub', '/main')
        self.inp_url.setText(url)
        self.update_btn_styles(sd_active=False)

    def split_camera_action(self):
        if QMessageBox.question(self, "Dividir Câmera", "Isso vai configurar esta câmera como 'Topo' e criar uma cópia automática para a 'Base'. Continuar?") != QMessageBox.StandardButton.Yes:
            return

        d = self.get_data()
        mac_orig = d['mac']
        
        self.combo_crop.setCurrentIndex(1) 
        self.was_split = True
        d['crop_mode'] = 1
        d['name'] = d['name'] + " (Topo)"
        db.upsert_camera(d['mac'], d['name'], d['ip'], d['username'], d['password'], d['url'], 1)
        
        mac_new = f"{mac_orig}_B"
        name_new = d['name'].replace("(Topo)", "(Base)")
        db.upsert_camera(mac_new, name_new, d['ip'], d['username'], d['password'], d['url'], 2)
        
        QMessageBox.information(self, "Sucesso", "Câmera dividida com sucesso!")
        self.accept() 

    def get_data(self):
        return {
            "name": self.inp_name.text(),
            "ip": self.inp_ip.text(),
            "username": self.inp_user.text(),
            "password": self.inp_pass.text(),
            "url": self.inp_url.text(),
            "mac": self.inp_mac.text(),
            "crop_mode": self.combo_crop.currentIndex()
        }

class VMSReceiverThread(QThread):
    frame_received = pyqtSignal(str, object) 
    status_received = pyqtSignal(str, str) 

    def __init__(self, vms_core):
        super().__init__()
        self.vms = vms_core
        self._run_flag = True

    def run(self):
        while self._run_flag:
            frame_data = self.vms.get_frame()
            if frame_data:
                cam_id, img = frame_data
                self.frame_received.emit(cam_id, img)
            
            status_data = self.vms.get_status()
            if status_data:
                cam_id, msg = status_data
                self.status_received.emit(cam_id, msg)

            if not frame_data and not status_data:
                time.sleep(0.010)

    def stop(self):
        self._run_flag = False
        self.wait()

class VideoDisplay(QWidget):
    def __init__(self, message="Conectando...", crop_mode=0):
        super().__init__()
        self.image = None
        self.message = message
        self.crop_mode = crop_mode
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_image(self, img):
        self.image = img
        self.update() 

    def set_message(self, text):
        self.message = text
        self.image = None 
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        
        if self.image and not self.image.isNull():
            img_w = self.image.width()
            img_h = self.image.height()
            
            if img_w > 0 and img_h > 0:
                widget_w = self.width()
                widget_h = self.height()
                
                # --- LÓGICA DE VIEWPORT 16:9 ESTRITA ---
                # Ignora a geometria torta da janela. Cria uma tela 16:9 virtual dentro dela.
                target_ratio = 16.0 / 9.0
                current_ratio = widget_w / widget_h if widget_h > 0 else target_ratio
                
                vp_w, vp_h = widget_w, widget_h
                
                if current_ratio > target_ratio:
                    # Widget é mais "Largo" que 16:9 (Ex: 2.14). Sobra espaço lateral? Não, sobra espaço horizontal.
                    # Devemos limitar a LARGURA para casar com a altura.
                    # Altura é o limitante? Não.
                    # Se é muito largo, a altura define o tamanho maximo do 16:9.
                    vp_w = int(widget_h * target_ratio)
                    vp_h = widget_h
                else:
                    # Widget é mais "Alto/Quadrado" que 16:9 (Ex: 1.65).
                    # A largura define o tamanho maximo.
                    vp_w = widget_w
                    vp_h = int(widget_w / target_ratio)
                
                # Centraliza o Viewport
                vp_x = (widget_w - vp_w) // 2
                vp_y = (widget_h - vp_h) // 2
                viewport_rect = QRect(vp_x, vp_y, vp_w, vp_h)
                
                # Seta o CLIP para não desenhar fora do viewport (Garante bordas pretas limpas)
                painter.setClipRect(viewport_rect)
                
                # --- PINTA O VIDEO (COVER) DENTRO DO VIEWPORT ---
                # Agora calculamos o scale para preencher o VIEWPORT (que é 16:9)
                scale_w = vp_w / img_w
                scale_h = vp_h / img_h
                scale = max(scale_w, scale_h) # Cover
                
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                
                # Centraliza a imagem no Viewport
                x = vp_x + (vp_w - new_w) // 2
                y = vp_y + (vp_h - new_h) // 2
                
                target_rect = QRect(x, y, new_w, new_h)
                painter.drawImage(target_rect, self.image)
        else:
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.message)

class MagicRepairThread(QThread):
    found_signal = pyqtSignal(str)
    checking_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, user, pwd, ip):
        super().__init__()
        self.user = user
        self.pwd = pwd
        self.ip = ip

    def run(self):
        print("DEBUG: MAGIC REPAIR")
        import socket
        ports = [80, 554, 34567, 8899, 8000, 88, 8080, 8554, 10554, 5554]
        passwords = []
        if self.pwd: passwords.append(self.pwd)
        passwords.extend(["", "12345", "admin"])
        passwords = list(dict.fromkeys(passwords))

        def is_port_open(host, port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5) 
                result = sock.connect_ex((host, int(port)))
                sock.close()
                return result == 0
            except: return False

        old_env = os.environ.get("OPENCV_FFMPEG_CAPTURE_OPTIONS", "")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;2000"
        rtsp_backup = None

        try:
            for p in ports:
                self.checking_signal.emit(f"Ping {self.ip}:{p}...")
                if not is_port_open(self.ip, p): continue
                
                # 1. HTTP Snapshot
                for pw in passwords:
                     u = self.user
                     ts = [
                        f"http://{self.ip}:{p}/webcapture.jpg?command=snap&channel=1&user={u}&password={pw}",
                        f"http://{self.ip}:{p}/cgi-bin/snapshot.cgi?channel=1&u={u}&p={pw}",
                        f"http://{self.ip}:{p}/ISAPI/Streaming/channels/101/picture?auth={u}:{pw}"
                     ]
                     for t in ts:
                         try:
                             with urllib.request.urlopen(t, timeout=2) as req:
                                 if req.status == 200:
                                     self.found_signal.emit(t)
                                     self.finished_signal.emit(True)
                                     return
                         except: pass

                # 2. RTSP
                if p in [34567, 8899]:
                     vs = ["stream=2.sdp", "subtype=1", "stream=1.sdp", "stream=0.sdp"]
                     for v in vs:
                         test_url = f"rtsp://{self.user}:{self.pwd}@{self.ip}:{p}/user={self.user}&password={self.pwd}&channel=1&{v}"
                         try:
                             cap = cv2.VideoCapture(test_url, cv2.CAP_FFMPEG)
                             if cap.isOpened():
                                 self.found_signal.emit(test_url)
                                 cap.release()
                                 self.finished_signal.emit(True)
                                 return
                             cap.release()
                         except: pass
                     if not rtsp_backup:
                         rtsp_backup = f"rtsp://{self.user}:{self.pwd}@{self.ip}:{p}/user={self.user}&password={self.pwd}&channel=1&stream=1.sdp"

            if rtsp_backup:
                 self.found_signal.emit(rtsp_backup)
                 self.finished_signal.emit(True)
                 return

        except Exception as e:
            print(f"Erro Magic: {e}")
        finally:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = old_env
        self.finished_signal.emit(False)

class CameraWidget(QFrame):
    def __init__(self, name, parent_monitor=None, crop_mode=0):
        super().__init__()
        self.name = name
        self.crop_mode = crop_mode
        self.parent_monitor = parent_monitor
        self.setFrameShape(QFrame.Shape.Box)
        
        # 1. FORÇA PROPORÇÃO 16:9 (Container Widescreen)
        self.aspect_ratio = 16.0 / 9.0
        
        # Define politica para respeitar heightForWidth
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        
        self.setStyleSheet("background-color: black; border: 1px solid #444; border-radius: 6px;")
        
        # 2. Layout & UI Elements
        # Importante: Layout sem margens para o video colar na borda
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        # Title Bar
        title_suffix = ""
        if crop_mode == 1: title_suffix = " (Topo)"
        if crop_mode == 2: title_suffix = " (Base)"
        
        self.title_bar = QLabel(name + title_suffix)
        self.title_bar.setStyleSheet("background: rgba(0,0,0,0.8); color: white; font-weight: bold; padding: 4px;")
        self.title_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_bar.setFixedHeight(24)
        
        # Video Display (Recebe crop_mode para ajustar mensagem se precisar)
        self.video = VideoDisplay(f"Carregando {name}...", crop_mode)
        
        layout.addWidget(self.title_bar)
        layout.addWidget(self.video)
        self.setLayout(layout)

        # 3. Overlay Button (Expand)
        self.btn_full = QPushButton(self)
        self.btn_full.setIcon(qta.icon("fa5s.expand", color="white"))
        self.btn_full.setStyleSheet("background: rgba(0,0,0,0.5); border: none; border-radius: 4px;")
        self.btn_full.setFixedSize(30, 30)
        self.btn_full.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_full.clicked.connect(self.toggle_fullscreen)
        self.btn_full.hide()

    # --- Aspect Ratio Logic ---
    def heightForWidth(self, width):
        # Garante altura baseada na largura (16:9)
        return int(width / self.aspect_ratio)

    def sizeHint(self):
        return QSize(320, 180)

    # --- Events ---
    def resizeEvent(self, event):
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.btn_full.move(self.width() - 35, 35)
        self.btn_full.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_full.hide()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, e):
        if self.parent_monitor: self.parent_monitor.toggle_maximize(self)

    # --- Logic ---
    def set_aspect_locked(self, locked: bool):
        if locked:
           # Trava 16:9
           policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
           policy.setHeightForWidth(True)
           self.setSizePolicy(policy)
        else:
           # Elástico (Zoom Total)
           # Ignored = Eu quero o tamanho que o layout me der, o maximo possivel.
           policy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
           policy.setHeightForWidth(False)
           self.setSizePolicy(policy)
        self.updateGeometry()

    def toggle_fullscreen(self):
        if self.parent_monitor:
            self.parent_monitor.toggle_maximize(self)

    def update_frame(self, frame):
        self.video.update_image(frame)

    def set_status(self, msg):
        self.video.set_message(msg)

    def update_numpy_frame(self, cv_img):
        if not self.isVisible(): return
        
        # Crop Lente Dupla (Topo/Base)
        if self.crop_mode != 0:
            h, w = cv_img.shape[:2]
            if self.crop_mode == 1: cv_img = cv_img[0:h//2, :]
            elif self.crop_mode == 2: cv_img = cv_img[h//2:h, :]
        
        h, w, ch = cv_img.shape
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        
        self.video.set_image(qt_image)

class MonitorScreen(QWidget):
    cameras_loaded = pyqtSignal(list)

    def __init__(self,):
        super().__init__()
        
        # LAYOUT MESTRE (Vertical) - Para alinhar tudo ao TOPO
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.main_layout)
        
        # GRID DE CAMERAS (Fica dentro do mestre)
        # Mantemos o nome 'self.layout' para compatibilidade com o resto do codigo
        self.layout = QGridLayout()
        self.layout.setContentsMargins(5,5,5,5)
        self.layout.setSpacing(5)
        
        # Adiciona Grid
        self.main_layout.addLayout(self.layout)
        
        # Spacer Dinâmico (Salvamos a referencia para remover no zoom)
        self.spacer_item = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addItem(self.spacer_item) # Começa ALINHADO AO TOPO
        
        self.widgets = []
        self.maximized_widget = None
        self.camera_map = {} 
        self.vms = VMSCore()
        
        self.receiver = VMSReceiverThread(self.vms)
        self.receiver.frame_received.connect(self.dispatch_frame)
        self.receiver.status_received.connect(self.dispatch_status)
        self.receiver.start()

    def dispatch_frame(self, cam_id, cv_img):
        if cam_id in self.camera_map:
            self.camera_map[cam_id].update_numpy_frame(cv_img)

    def dispatch_status(self, cam_id, msg):
        if cam_id in self.camera_map:
            self.camera_map[cam_id].set_status(msg)

    def closeEvent(self, e):
        self.receiver.stop()
        self.vms.stop_all()
        super().closeEvent(e)

    def reload_single_camera(self, index, new_data):
        if index < 0 or index >= len(self.widgets): return
        cam_id = f"cam_{index}"
        self.vms.stop_camera(cam_id)
        
        old_w = self.widgets[index]
        grid_index = self.layout.indexOf(old_w)
        if grid_index == -1: return
        
        row, col, rowspan, colspan = self.layout.getItemPosition(grid_index)
        self.layout.removeWidget(old_w)
        if cam_id in self.camera_map: del self.camera_map[cam_id]
        old_w.deleteLater() 
        
        new_w = CameraWidget(new_data['name'], self, new_data.get('crop_mode', 0))
        self.layout.addWidget(new_w, row, col)
        
        self.widgets[index] = new_w
        self.camera_map[cam_id] = new_w
        self.vms.start_camera(cam_id, new_data['url'])
        
        if self.maximized_widget == old_w:
             self.maximized_widget = None
             self.reset_grid()

    def load_cameras(self):
        self.vms.stop_all()
        self.camera_map.clear()

        for w in self.widgets:
            self.layout.removeWidget(w)
            w.deleteLater()
        self.widgets = []
        self.maximized_widget = None

        cameras = db.get_all_cameras()
        self.cameras_loaded.emit(cameras)
        if not cameras: return

        import math
        count = len(cameras)
        
        if not cameras: return

        import math
        # VOLTA AO PADRÃO QUADRADO (Robusto)
        # Ex: 4 cams -> 2x2. 6 cams -> 3x2.
        cols = math.ceil(math.sqrt(len(cameras)))
        if cols < 1: cols = 1

        for i, cam in enumerate(cameras):
            cam_id = f"cam_{i}"
            w = CameraWidget(cam.get('name', f'Cam {i+1}'), self, cam.get('crop_mode', 0))
            self.layout.addWidget(w, i // cols, i % cols)
            self.widgets.append(w)
            self.camera_map[cam_id] = w
            
            # START INSTANTANEO
            self.vms.start_camera(cam_id, cam['url'])

    def reset_grid(self):
        self.maximized_widget = None
        
        # Restaura o Spacer (Align Top)
        if self.main_layout.indexOf(self.spacer_item) == -1:
             self.main_layout.addItem(self.spacer_item)

        for w in self.widgets: 
            w.show()
            w.set_aspect_locked(True) # Restaura trava 16:9
        
        count = len(self.widgets)
        import math
        cols = math.ceil(math.sqrt(count))
        if count == 2: cols = 2 # Exceçãozinha visual padrão
        if cols < 1: cols = 1

        for i, w in enumerate(self.widgets):
            self.layout.addWidget(w, i // cols, i % cols)

    def focus_camera_by_index(self, index):
        if 0 <= index < len(self.widgets):
            target = self.widgets[index]
            self.toggle_maximize(target)
            if self.maximized_widget != target:
                 self.toggle_maximize(target)

    def toggle_maximize(self, widget):
        if self.maximized_widget == widget:
            self.reset_grid()
        else:
            # Remove o Spacer (Para permitir Zoom Full Height)
            if self.main_layout.indexOf(self.spacer_item) != -1:
                self.main_layout.removeItem(self.spacer_item)
            
            for w in self.widgets: w.hide()
            
            # Destrava aspecto para encher a tela (O PaintEvent cuida do 16:9 interno com barras pretas)
            widget.set_aspect_locked(False)
            
            # Adiciona ao grid ocupando tudo
            self.layout.addWidget(widget, 0, 0)
            
            widget.show()
            self.maximized_widget = widget

class ScannerScreen(QWidget):
    def __init__(self, monitor_ref):
        super().__init__()
        self.monitor = monitor_ref
        self.scanner = NetworkScanner()
        self.scanner.log_signal.connect(self.append_log)
        self.scanner.found_signal.connect(self.on_camera_found)
        self.scanner.finished_signal.connect(self.on_scan_finished)

        layout = QVBoxLayout()
        form = QFrame()
        form.setStyleSheet("background: #2d2d2d; border-radius: 8px; padding: 10px;")
        fl = QFormLayout()
        
        self.inp_network = QLineEdit("192.168.3")
        self.inp_user = QLineEdit("admin")
        self.inp_pass = QLineEdit("")
        
        fl.addRow("Rede Base:", self.inp_network)
        fl.addRow("Usuário:", self.inp_user)
        fl.addRow("Senha:", self.inp_pass)
        form.setLayout(fl)
        layout.addWidget(form)

        self.btn_scan = QPushButton("🚀 Iniciar Varredura")
        self.btn_scan.setStyleSheet("background-color: #0078d4; color: white; padding: 12px; border-radius: 4px;")
        self.btn_scan.clicked.connect(self.start_scan)
        layout.addWidget(self.btn_scan)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        self.setLayout(layout)

    def on_scan_finished(self):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("🚀 Iniciar Varredura")
        self.append_log("🏁 Varredura Completa. Atualizando mosaico...")
        self.monitor.load_cameras()

    def start_scan(self):
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("⏳ Buscando (Aguarde)...")
        self.log_area.clear()
        self.append_log("🚀 Iniciando Motor de Busca... O processo começou.")
        QApplication.processEvents() 
        self.scanner.start_scan(self.inp_network.text(), self.inp_user.text(), self.inp_pass.text())

    def append_log(self, text):
        self.log_area.append(text)

    def on_camera_found(self, ip, url, mac):
        user = self.inp_user.text()
        password = self.inp_pass.text()
        name = f"Auto-Scan {ip}"
        if not mac: mac = f"UNKNOWN-{ip}"
        db.upsert_camera(mac, name, ip, user, password, url)
        self.append_log(f"💾 Salvo no Banco: {ip} [MAC: {mac}]")

class ModernWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AntiGravity Central V4 (Hybrid Edition)")
        self.resize(1280, 720)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 20, 0, 10)
        
        lbl = QLabel("🛡️ CENTRAL V4")
        lbl.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-left: 15px; margin-bottom: 20px;")
        side_layout.addWidget(lbl)
        
        self.btn_mon = self.create_nav("Monitoramento", "fa5s.video", 0)
        self.btn_sca = self.create_nav("Scanner Rede", "fa5s.search", 1)
        side_layout.addWidget(self.btn_mon)
        side_layout.addWidget(self.btn_sca)
        
        self.btn_cfg = QPushButton("  Configurações")
        self.btn_cfg.setIcon(qta.icon("fa5s.cog", color="#bbb"))
        self.btn_cfg.setStyleSheet("""
            QPushButton { background: transparent; color: #bbb; border: none; padding: 12px; text-align: left; font-size: 14px; }
            QPushButton:hover { background: #333; color: white; }
        """)
        self.btn_cfg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cfg.clicked.connect(self.open_config)
        side_layout.addWidget(self.btn_cfg)
        
        side_layout.addSpacing(20)
        lbl_cam = QLabel("CÂMERAS ONLINE")
        lbl_cam.setStyleSheet("color: #666; font-size: 11px; font-weight: bold; margin-left: 15px;")
        side_layout.addWidget(lbl_cam)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        self.cam_list_widget = QWidget()
        self.cam_list_widget.setStyleSheet("background: transparent;")
        self.cam_layout = QVBoxLayout(self.cam_list_widget)
        self.cam_layout.setContentsMargins(5,5,5,5)
        self.cam_layout.setSpacing(2)
        scroll.setWidget(self.cam_list_widget)
        side_layout.addWidget(scroll)

        self.stack = QStackedWidget()
        self.monitor = MonitorScreen()
        self.scanner = ScannerScreen(self.monitor)
        
        self.stack.addWidget(self.monitor)
        self.stack.addWidget(self.scanner)
        
        self.monitor.cameras_loaded.connect(self.update_camera_list)
        self.monitor.load_cameras() 
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

        self.setStyleSheet(DARK_THEME)
        self.btn_mon.setChecked(True)

    def open_config(self):
        dlg = ConfigDialog(self)
        dlg.exec()

    def create_nav(self, text, icon, idx):
        btn = QPushButton(f"  {text}")
        btn.setObjectName("SidebarButton")
        btn.setIcon(qta.icon(icon, color="#bbb"))
        btn.setIconSize(QSize(18,18))
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.switch_tab(idx))
        return btn

    def switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 0:
            self.btn_mon.setChecked(True)
            self.btn_sca.setChecked(False)
        else:
            self.btn_mon.setChecked(False)
            self.btn_sca.setChecked(True)
    
    def read_cameras_db(self):
        return db.get_all_cameras()

    def update_camera_list(self, cameras):
        while self.cam_layout.count():
            child = self.cam_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        btn_reset = QPushButton("  Ver Todas (Mosaico)")
        btn_reset.setStyleSheet("""
            QPushButton { background: #0078d4; color: white; border: none; padding: 8px; border-radius: 4px; text-align: left; }
            QPushButton:hover { background: #1084d9; }
        """)
        btn_reset.setIcon(qta.icon("fa5s.th", color="white"))
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self.monitor.reset_grid)
        btn_reset.clicked.connect(lambda: self.switch_tab(0))
        self.cam_layout.addWidget(btn_reset)
        
        btn_add = QPushButton("  Adicionar Câmera")
        btn_add.setStyleSheet("""
            QPushButton { background: #28a745; color: white; border: none; padding: 8px; border-radius: 4px; text-align: left; margin-top: 5px; }
            QPushButton:hover { background: #218838; }
        """)
        btn_add.setIcon(qta.icon("fa5s.plus", color="white"))
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.add_manual_camera)
        self.cam_layout.addWidget(btn_add)
        
        self.cam_layout.addSpacing(15)

        for i, cam in enumerate(cameras):
            name = cam.get('name', f'Cam {i+1}')
            url = cam.get('url', '')
            mac = cam.get('mac', '')
            ip = cam.get('ip')
            if not ip:
                try:
                    match = re.search(r'//([^:/]+)', url)
                    if match: ip = match.group(1)
                except: pass
            if not ip: ip = "---"
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0,0,0,0)
            row_layout.setSpacing(2)

            user = cam.get('username', 'admin')
            display_text = f" {name}\n 👤 {user}\n 🌐 {ip}\n 🆔 {mac if mac else 'SEM MAC'}"

            btn = QPushButton(display_text)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #bbb; border: none; padding: 8px; text-align: left; border-left: 2px solid transparent; font-size: 11px; }
                QPushButton:hover { background: #333; color: white; }
                QPushButton:checked { background: #252526; border-left: 2px solid #0078d4; color: white; }
            """)
            btn.setIcon(qta.icon("fa5s.camera", color="#666"))
            btn.setIconSize(QSize(14,14))
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            btn.clicked.connect(lambda checked, idx=i: self.select_camera_sidebar(idx))
            
            btn_edit = QPushButton()
            btn_edit.setIcon(qta.icon("fa5s.cog", color="#666"))
            btn_edit.setFixedSize(24, 24)
            btn_edit.setStyleSheet("background: transparent; border: none;")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, idx=i: self.edit_camera_details(idx))

            row_layout.addWidget(btn)
            row_layout.addWidget(btn_edit)
            
            self.cam_layout.addWidget(row_widget)
            
        self.cam_layout.addStretch()

    def add_manual_camera(self):
        import uuid
        empty_data = {
            "mac": "", "name": "Nova Câmera", "ip": "", 
            "username": "admin", "password": "", "url": "", "crop_mode": 0
        }
        
        dialog = CameraDetailsDialog(empty_data, self)
        if dialog.exec():
            d = dialog.get_data()
            if not d['mac']: 
                 d['mac'] = f"MANUAL-{uuid.uuid4().hex[:6].upper()}"
            
            if d['ip'] and not d['url']:
                 user = d['username']
                 pwd = d['password']
                 ip = d['ip']
                 d['url'] = f"rtsp://{user}:{pwd}@{ip}:554/user={user}&password={pwd}&channel=1&stream=0.sdp?"
            
            db.upsert_camera(d['mac'], d['name'], d['ip'], d['username'], d['password'], d['url'], d.get('crop_mode', 0))
            self.monitor.load_cameras()
            self.update_camera_list(db.get_all_cameras())
            QMessageBox.information(self, "Sucesso", "Câmera adicionada manualmente!")

    def edit_camera_details(self, index):
        cameras = db.get_all_cameras()
        if index >= len(cameras): return
        old_data = cameras[index]
        dialog = CameraDetailsDialog(old_data, self)
        if dialog.exec():
            d = dialog.get_data()
            db.upsert_camera(d['mac'], d['name'], d['ip'], d['username'], d['password'], d['url'], d.get('crop_mode', 0))
            if dialog.was_split:
                self.monitor.load_cameras()
            else:
                self.monitor.reload_single_camera(index, d)
            self.update_camera_list(db.get_all_cameras())

    def select_camera_sidebar(self, index):
        self.switch_tab(0)
        self.monitor.focus_camera_by_index(index)

if __name__ == "__main__":
    # RESTAURANDO PERFORMANCE ORIGINAL
    # Apenas TCP. Sem buffers gigantes, sem delays de analise.
    import os
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    
    app = QApplication(sys.argv)
    
    import requests
    
    if not connect_to_provider():
        QMessageBox.critical(None, "Conexão", "Não foi possível conectar ao banco de dados ou servidor.\nAbra as configurações para definir a rota.")
        cfg_dlg = ConfigDialog()
        if cfg_dlg.exec():
             if not connect_to_provider():
                 sys.exit(1)
        else:
            sys.exit(0)

    window = ModernWindow()
    window.show()
    sys.exit(app.exec())
