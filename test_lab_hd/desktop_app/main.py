import sys
import cv2
import json
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QVBoxLayout, QInputDialog, QFrame, QMessageBox, QSizePolicy)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage, QAction, QMouseEvent

# Forçar TCP é vital para estabilidade em Wi-Fi/5G
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'cameras.json')

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._run_flag = True

    def run(self):
        self.status_signal.emit("Conectando...")
        cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # OTIMIZAÇÃO MAXIMA: Forçar 640x360 sempre
                cv_img = cv2.resize(cv_img, (640, 360), interpolation=cv2.INTER_NEAREST)

                rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.change_pixmap_signal.emit(qt_image)
            else:
                self.status_signal.emit("Sinal Perdido...")
                time.sleep(2)
                cap.release()
                cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            
            # 10 FPS Limit
            time.sleep(0.1)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class CameraWidget(QFrame):
    def __init__(self, name, url, parent_grid=None):
        super().__init__()
        self.name = name
        self.url = url
        self.parent_grid = parent_grid
        self.is_maximized = False

        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("background-color: #000; border: 1px solid #444;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Titulo
        self.title = QLabel(name)
        self.title.setStyleSheet("background: rgba(0,0,0,0.7); color: white; padding: 4px; font-weight: bold;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFixedHeight(25)
        
        # Video
        self.video_label = QLabel("Aguardando Stream...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("color: #666;")
        
        # CORREÇÃO DO ZOOM INFINITO
        self.video_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.video_label.setScaledContents(True) # O Qt fará o resize na GPU
        
        layout.addWidget(self.title)
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        # Iniciar thread
        self.thread = VideoThread(url)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status)
        self.thread.start()

    def update_image(self, qt_image):
        # Sem resize manual do Python = Sem loop infinito
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def update_status(self, text):
        self.video_label.setText(text)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.parent_grid:
            self.parent_grid.toggle_maximize(self)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Monitoramento - AntiGravity V3")
        self.resize(1280, 720)
        self.setStyleSheet("background-color: #222; color: #EEE;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.grid = QGridLayout()
        self.central_widget.setLayout(self.grid)
        
        # Menu
        bar = self.menuBar()
        bar.setStyleSheet("background: #333; color: white;")
        menu = bar.addMenu("Sistema")
        menu.addAction("Adicionar Câmera", self.add_camera)
        menu.addAction("Recarregar Layout", self.load_cameras)

        self.widgets = []
        self.load_cameras()

    def load_cameras(self):
        # Limpar widgets antigos
        for w in self.widgets:
            w.thread.stop()
            w.setParent(None)
            w.deleteLater()
        self.widgets = []

        # Ler JSON
        cameras = []
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cameras = json.load(f)
            except:
                pass

        # Montar Grid
        import math
        cols = 2
        if len(cameras) > 4: cols = 3
        
        for i, cam in enumerate(cameras):
            name = cam.get('name', f'Cam {i+1}')
            # Fix encoding bug
            try: name = name.encode('latin1').decode('utf-8')
            except: pass
            
            w = CameraWidget(name, cam['url'], self)
            self.grid.addWidget(w, i // cols, i % cols)
            self.widgets.append(w)

    def toggle_maximize(self, widget):
        if widget.is_maximized:
            self.grid.removeWidget(widget)
            self.load_cameras() # Reset total
        else:
            for w in self.widgets: w.hide()
            self.grid.addWidget(widget, 0, 0, 0, 0)
            widget.show()
            widget.is_maximized = True

    def add_camera(self):
        url, ok = QInputDialog.getText(self, "Nova Câmera", "URL RTSP:")
        if ok and url:
            name, _ = QInputDialog.getText(self, "Nome", "Nome:")
            
            cams = []
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f: cams = json.load(f)
            
            cams.append({"name": name or "Nova Cam", "url": url})
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cams, f, indent=2, ensure_ascii=False)
            
            self.load_cameras()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
