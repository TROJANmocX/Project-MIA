import warnings
warnings.filterwarnings("ignore", message="sipPyTypeDict() is deprecated")
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QComboBox, QGroupBox, QStyleFactory
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from mia_hud import HUDOverlay, SystemTray

class MIAApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIA – My Intelligent Assistant")
        icon_path = os.path.join(os.path.dirname(__file__), "mia_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(200, 200, 420, 350)
        self.processes = {}
        self.hud_overlay = None
        self.tray_icon = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Feature toggles
        self.voice_cb = QCheckBox("Voice Activation (Wake Word)")
        self.gesture_cb = QCheckBox("Gesture Control")
        self.hud_cb = QCheckBox("HUD Overlay")
        self.mood_cb = QCheckBox("Mood Detection")
        self.voice_cb.setChecked(True)
        self.gesture_cb.setChecked(True)
        self.hud_cb.setChecked(True)
        self.mood_cb.setChecked(False)
        # TTS personality
        tts_layout = QHBoxLayout()
        tts_layout.addWidget(QLabel("TTS Personality:"))
        self.tts_combo = QComboBox()
        self.tts_combo.addItems(["calm", "witty", "sarcastic", "bold"])
        tts_layout.addWidget(self.tts_combo)
        # Start/Stop buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start MIA")
        self.stop_btn = QPushButton("Stop MIA")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        # Theme toggle
        self.theme_cb = QCheckBox("Dark Theme")
        self.theme_cb.setChecked(True)
        # Layout
        features = QGroupBox("Features")
        features_layout = QVBoxLayout()
        features_layout.addWidget(self.voice_cb)
        features_layout.addWidget(self.gesture_cb)
        features_layout.addWidget(self.hud_cb)
        features_layout.addWidget(self.mood_cb)
        features.setLayout(features_layout)
        layout.addWidget(features)
        layout.addLayout(tts_layout)
        layout.addWidget(self.theme_cb)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        # Connect
        self.start_btn.clicked.connect(self.start_mia)
        self.stop_btn.clicked.connect(self.stop_mia)
        self.theme_cb.stateChanged.connect(self.toggle_theme)
        self.toggle_theme()

    def toggle_theme(self):
        if self.theme_cb.isChecked():
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            dark_palette = self.palette()
            dark_palette.setColor(self.backgroundRole(), Qt.black)
            dark_palette.setColor(self.foregroundRole(), Qt.white)
            self.setPalette(dark_palette)
        else:
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            self.setPalette(QApplication.palette())

    def start_mia(self):
        self.status_label.setText("Status: Launching...")
        project_root = os.path.abspath(os.path.dirname(__file__))
        # Start API
        if "api" not in self.processes:
            self.processes["api"] = subprocess.Popen([sys.executable, "-m", "uvicorn", "server.api:app", "--reload"], cwd=project_root)
        # Start Voice
        if self.voice_cb.isChecked() and "voice" not in self.processes:
            self.processes["voice"] = subprocess.Popen([sys.executable, "mia_assistant/voice_activation.py"], cwd=project_root)
        # Start Gesture
        if self.gesture_cb.isChecked() and "gesture" not in self.processes:
            self.processes["gesture"] = subprocess.Popen([sys.executable, "gesture_control/main.py"], cwd=project_root)
        # Start HUD overlay if enabled
        if self.hud_cb.isChecked() and self.hud_overlay is None:
            self.hud_overlay = HUDOverlay()
            self.hud_overlay.show()
        # Start system tray icon
        if self.tray_icon is None:
            self.tray_icon = SystemTray()
            self.tray_icon.show()
        self.status_label.setText("Status: MIA Running")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_mia(self):
        for name, proc in self.processes.items():
            try:
                proc.terminate()
            except Exception:
                pass
        self.processes = {}
        # Stop HUD overlay
        if self.hud_overlay is not None:
            self.hud_overlay.close()
            self.hud_overlay = None
        # Stop system tray icon
        if self.tray_icon is not None:
            self.tray_icon.hide()
            self.tray_icon = None
        self.status_label.setText("Status: Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MIAApp()
    window.show()
    sys.exit(app.exec_())
