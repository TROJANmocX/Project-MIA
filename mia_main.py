import sys
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os
import threading
import queue
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QListWidget, QListWidgetItem, QFrame, QSpacerItem, QSizePolicy, QListView, QDialog, QDialogButtonBox
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import QUrl

print("THIS IS THE NEW MIA MAIN")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Voice recognition imports
try:
    import speech_recognition as sr
except ImportError:
    sr = None

class NeonNavBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(120)
        self.setStyleSheet('''
            QFrame {
                background: #101020;
                border-right: 2px solid #00ffc3;
            }
            QListWidget {
                background: transparent;
                color: #fff;
                border: none;
            }
            QListWidget::item {
                padding: 18px 0;
                margin: 0 8px;
                border-radius: 12px;
            }
            QListWidget::item:selected {
                background: #00ffc355;
                color: #00ffc3;
                border: 1.5px solid #00ffc3;
            }
        ''')
        self.nav = QListWidget()
        self.nav.setFont(QFont('Segoe UI', 12))
        self.nav.setSpacing(6)
        self.nav.setFrameShape(QFrame.NoFrame)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav.setSelectionMode(QListWidget.SingleSelection)
        self.nav.addItem(QListWidgetItem(QIcon(), "Home"))
        self.nav.addItem(QListWidgetItem(QIcon(), "Commands"))
        self.nav.addItem(QListWidgetItem(QIcon(), "Settings"))
        self.nav.addItem(QListWidgetItem(QIcon(), "About"))
        self.nav.setCurrentRow(0)
        layout = QVBoxLayout()
        layout.addWidget(self.nav)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

class VoiceWorker(QObject):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    listening_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._running = False
        self._thread = None

    def start_listening(self):
        if sr is None:
            self.error_signal.emit("SpeechRecognition not installed.")
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        self.listening_signal.emit(True)

    def stop_listening(self):
        self._running = False
        self.listening_signal.emit(False)

    def _listen_loop(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
        while self._running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
                try:
                    text = recognizer.recognize_google(audio)
                    self.result_signal.emit(text)
                except sr.UnknownValueError:
                    self.error_signal.emit("Could not understand audio.")
                except sr.RequestError:
                    self.error_signal.emit("Speech recognition service error.")
            except Exception as e:
                self.error_signal.emit(str(e))
                break

class Toast(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background: rgba(20,20,40,0.95); color: #00ffc3; border: 2px solid #00ffc3; border-radius: 12px; font-size: 16px; padding: 18px;')
        layout = QVBoxLayout()
        label = QLabel(message)
        label.setStyleSheet('color: #00ffc3;')
        layout.addWidget(label)
        self.setLayout(layout)
        self.adjustSize()
        QTimer.singleShot(2000, self.accept)

class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to MIA")
        self.setStyleSheet('background: #181828; color: #fff; border-radius: 16px;')
        layout = QVBoxLayout()
        label = QLabel("Welcome to MIA!\n\n- Use the sidebar to navigate.\n- Start/Stop MIA from the Home page.\n- Use Settings for privacy and theme.\n- Try voice commands!\n\nEnjoy your futuristic assistant.")
        label.setStyleSheet('font-size: 16px; color: #00ffc3;')
        layout.addWidget(label)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)
        self.setLayout(layout)
        self.adjustSize()

class NeonMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        print("NeonMainWindow init")
        self.setWindowTitle("MIA – My Intelligent Assistant")
        icon_path = resource_path(os.path.join("ui_assets", "logo.svg"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet('''
            QWidget {
                background: #0d0d0d;
                color: #fff;
            }
        ''')
        self.voice_worker = VoiceWorker()
        self.voice_worker.result_signal.connect(self.on_voice_result)
        self.voice_worker.error_signal.connect(self.on_voice_error)
        self.voice_worker.listening_signal.connect(self.on_listening_state)
        self.voice_history = []
        self.init_ui()

    def init_ui(self):
        print("init_ui called")
        main_layout = QHBoxLayout(self)
        # Neon NavBar
        self.navbar = NeonNavBar()
        main_layout.addWidget(self.navbar)
        # Stacked Pages
        self.pages = QStackedWidget()
        self.pages.addWidget(self.page_home())
        self.pages.addWidget(self.page_commands())
        self.pages.addWidget(self.page_settings())
        self.pages.addWidget(self.page_about())
        main_layout.addWidget(self.pages)
        self.setLayout(main_layout)
        self.navbar.nav.currentRowChanged.connect(self.pages.setCurrentIndex)

    def page_home(self):
        print("Loading Home Page")
        from mia_hud import NeonRing
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("MIA HUD Overlay")
        title.setFont(QFont('Segoe UI', 24, QFont.Bold))
        title.setStyleSheet('color: #00ffc3;')
        layout.addWidget(title, alignment=Qt.AlignLeft)
        # Neon animated ring
        neon_ring = NeonRing()
        layout.addWidget(neon_ring, alignment=Qt.AlignCenter)
        # Status label
        self.status = QLabel("Status: Ready")
        self.status.setStyleSheet('color: #00ffc3; font-size: 20px; font-weight: bold; margin-top: 24px;')
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        # Start/Stop buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton('Start MIA')
        self.start_btn.setStyleSheet('background: #00ffc3; color: #0d0d0d; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
        self.stop_btn = QPushButton('Stop MIA')
        self.stop_btn.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
        # Quick actions
        quick_btn_layout = QHBoxLayout()
        mute_btn = QPushButton('Mute')
        mute_btn.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 8px 16px;')
        settings_btn = QPushButton('Settings')
        settings_btn.setStyleSheet('background: #00ffc3; color: #0d0d0d; border-radius: 8px; padding: 8px 16px;')
        quick_btn_layout.addWidget(mute_btn)
        quick_btn_layout.addWidget(settings_btn)
        layout.addLayout(quick_btn_layout)
        layout.addStretch()
        page.setLayout(layout)
        # Connect start/stop
        self.start_btn.clicked.connect(self.start_mia)
        self.stop_btn.clicked.connect(self.stop_mia)
        return page

    def start_mia(self):
        import subprocess
        self.status.setText("Status: Launching...")
        self.processes = getattr(self, 'processes', {})
        project_root = os.path.abspath(os.path.dirname(__file__))
        # Start API
        if "api" not in self.processes:
            self.processes["api"] = subprocess.Popen([sys.executable, "-m", "uvicorn", "server.api:app", "--reload"], cwd=project_root)
        # Start Voice
        if "voice" not in self.processes:
            self.processes["voice"] = subprocess.Popen([sys.executable, "mia_assistant/voice_activation.py"], cwd=project_root)
        # Start Gesture
        if "gesture" not in self.processes:
            self.processes["gesture"] = subprocess.Popen([sys.executable, "gesture_control/main.py"], cwd=project_root)
        # Start Mood Detection (stub)
        if "mood" not in self.processes:
            self.processes["mood"] = subprocess.Popen([sys.executable, "mia_assistant/mood_detection.py"], cwd=project_root)
        self.status.setText("Status: MIA Running")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.show_toast("MIA Started")

    def stop_mia(self):
        for name, proc in getattr(self, 'processes', {}).items():
            try:
                proc.terminate()
            except Exception:
                pass
        self.processes = {}
        self.status.setText("Status: Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.show_toast("MIA Stopped")

    def page_commands(self):
        print("Loading Commands Page")
        page = QWidget()
        self.cmd_layout = QVBoxLayout()
        title = QLabel("Voice Command Center")
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet('color: #00ffc3;')
        self.cmd_layout.addWidget(title, alignment=Qt.AlignLeft)
        # Live transcript
        self.transcript_label = QLabel("Press 'Start Listening' and speak...")
        self.transcript_label.setStyleSheet('color: #fff; font-size: 18px; margin-top: 30px; background: #181828; border-radius: 10px; padding: 12px;')
        self.cmd_layout.addWidget(self.transcript_label, alignment=Qt.AlignCenter)
        # Start/Stop button
        self.listen_btn = QPushButton("Start Listening")
        self.listen_btn.setStyleSheet('background: #00ffc3; color: #0d0d0d; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
        self.listen_btn.clicked.connect(self.toggle_listening)
        self.cmd_layout.addWidget(self.listen_btn, alignment=Qt.AlignCenter)
        # Command history
        self.history_label = QLabel("Command History:")
        self.history_label.setStyleSheet('color: #3f8cff; font-size: 16px; margin-top: 30px;')
        self.cmd_layout.addWidget(self.history_label, alignment=Qt.AlignLeft)
        self.history_list = QListWidget()
        self.history_list.setStyleSheet('background: #101020; color: #fff; border: 1.5px solid #00ffc3; border-radius: 8px;')
        self.history_list.setViewMode(QListView.ListMode)
        self.cmd_layout.addWidget(self.history_list)
        self.cmd_layout.addStretch()
        page.setLayout(self.cmd_layout)
        return page

    def page_settings(self):
        print("Loading Settings Page")
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Settings")
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet('color: #00ffc3;')
        layout.addWidget(title, alignment=Qt.AlignLeft)
        # Privacy toggles
        self.mic_cb = QPushButton("Mute Microphone")
        self.mic_cb.setCheckable(True)
        self.mic_cb.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
        self.mic_cb.clicked.connect(self.toggle_mic)
        layout.addWidget(self.mic_cb, alignment=Qt.AlignLeft)
        self.cam_cb = QPushButton("Mute Camera")
        self.cam_cb.setCheckable(True)
        self.cam_cb.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
        self.cam_cb.clicked.connect(self.toggle_cam)
        layout.addWidget(self.cam_cb, alignment=Qt.AlignLeft)
        # TTS personality
        tts_label = QLabel("TTS Personality:")
        tts_label.setStyleSheet('color: #00ffc3; font-size: 16px; margin-top: 24px;')
        layout.addWidget(tts_label, alignment=Qt.AlignLeft)
        self.tts_combo = QListWidget()
        for p in ["calm", "witty", "sarcastic", "bold"]:
            item = QListWidgetItem(p.capitalize())
            self.tts_combo.addItem(item)
        self.tts_combo.setCurrentRow(0)
        self.tts_combo.setMaximumHeight(100)
        self.tts_combo.setStyleSheet('background: #101020; color: #fff; border: 1.5px solid #00ffc3; border-radius: 8px;')
        layout.addWidget(self.tts_combo, alignment=Qt.AlignLeft)
        # Theme toggle
        self.theme_btn = QPushButton("Switch to Light Theme")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setChecked(False)
        self.theme_btn.setStyleSheet('background: #00ffc3; color: #0d0d0d; border-radius: 8px; padding: 10px 24px; font-size: 16px; margin-top: 24px;')
        self.theme_btn.clicked.connect(self.toggle_theme_btn)
        layout.addWidget(self.theme_btn, alignment=Qt.AlignLeft)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def page_about(self):
        print("Loading About Page")
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("About MIA")
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet('color: #00ffc3;')
        layout.addWidget(title, alignment=Qt.AlignLeft)
        about_label = QLabel("MIA (My Intelligent Assistant)\nFuturistic AI desktop assistant with voice, gesture, and AR UI.\nInspired by Jarvis, designed for privacy and extensibility.")
        about_label.setStyleSheet('color: #fff; font-size: 16px; margin-top: 30px;')
        layout.addWidget(about_label, alignment=Qt.AlignCenter)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def show_toast(self, message):
        toast = Toast(message, self)
        toast.move(self.geometry().center() - toast.rect().center())
        toast.show()
        QTimer.singleShot(2000, toast.close)

    def play_sound(self, sound_file):
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(sound_file))
        effect.setVolume(0.5)
        effect.play()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_L:
                self.toggle_listening()
            elif event.key() == Qt.Key_M:
                self.toggle_mic()
        super().keyPressEvent(event)

    def start_mia(self):
        import subprocess
        self.status.setText("Status: Launching...")
        self.processes = getattr(self, 'processes', {})
        project_root = os.path.abspath(os.path.dirname(__file__))
        # Start API
        if "api" not in self.processes:
            self.processes["api"] = subprocess.Popen([sys.executable, "-m", "uvicorn", "server.api:app", "--reload"], cwd=project_root)
        # Start Voice
        if "voice" not in self.processes:
            self.processes["voice"] = subprocess.Popen([sys.executable, "mia_assistant/voice_activation.py"], cwd=project_root)
        # Start Gesture
        if "gesture" not in self.processes:
            self.processes["gesture"] = subprocess.Popen([sys.executable, "gesture_control/main.py"], cwd=project_root)
        # Start Mood Detection (stub)
        if "mood" not in self.processes:
            self.processes["mood"] = subprocess.Popen([sys.executable, "mia_assistant/mood_detection.py"], cwd=project_root)
        self.status.setText("Status: MIA Running")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.show_toast("MIA Started")

    def stop_mia(self):
        for name, proc in getattr(self, 'processes', {}).items():
            try:
                proc.terminate()
            except Exception:
                pass
        self.processes = {}
        self.status.setText("Status: Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.show_toast("MIA Stopped")

    def toggle_listening(self):
        if self.listen_btn.text() == "Start Listening":
            self.voice_worker.start_listening()
            self.listen_btn.setText("Stop Listening")
            self.transcript_label.setText("Listening... Speak now.")
        else:
            self.voice_worker.stop_listening()
            self.listen_btn.setText("Start Listening")
            self.transcript_label.setText("Press 'Start Listening' and speak...")

    def on_voice_result(self, text):
        self.transcript_label.setText(f"You said: {text}")
        self.voice_history.append(text)
        self.history_list.addItem(text)

    def on_voice_error(self, msg):
        self.transcript_label.setText(f"Error: {msg}")
        self.show_toast(f"Voice Error: {msg}")

    def on_listening_state(self, listening):
        if not listening:
            self.listen_btn.setText("Start Listening")

    def toggle_mic(self):
        if self.mic_cb.isChecked():
            self.mic_cb.setText("Microphone Muted")
            self.mic_cb.setStyleSheet('background: #F87171; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
            self.show_toast("Microphone Muted")
        else:
            self.mic_cb.setText("Mute Microphone")
            self.mic_cb.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
            self.show_toast("Microphone Unmuted")

    def toggle_cam(self):
        if self.cam_cb.isChecked():
            self.cam_cb.setText("Camera Muted")
            self.cam_cb.setStyleSheet('background: #F87171; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
            self.show_toast("Camera Muted")
        else:
            self.cam_cb.setText("Mute Camera")
            self.cam_cb.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 10px 24px; font-size: 16px;')
            self.show_toast("Camera Unmuted")

    def toggle_theme_btn(self):
        if self.theme_btn.isChecked():
            self.theme_btn.setText("Switch to Dark Theme")
            self.setStyleSheet('QWidget { background: #fff; color: #0d0d0d; }')
            self.show_toast("Light Theme Enabled")
        else:
            self.theme_btn.setText("Switch to Light Theme")
            self.setStyleSheet('QWidget { background: #0d0d0d; color: #fff; }')
            self.show_toast("Dark Theme Enabled")

if __name__ == "__main__":
    print("Running as main")
    app = QApplication(sys.argv)
    # Onboarding dialog on first launch
    first_run_flag = os.path.join(os.path.dirname(__file__), '.mia_first_run')
    if not os.path.exists(first_run_flag):
        dlg = OnboardingDialog()
        dlg.exec_()
        with open(first_run_flag, 'w') as f:
            f.write('1')
    window = NeonMainWindow()
    window.show()
    sys.exit(app.exec_())
