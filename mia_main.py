import sys
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="sipPyTypeDict")
import os
import json
import threading
import queue
import subprocess
import math
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QListWidget, QListWidgetItem, QFrame, QSpacerItem,
    QSizePolicy, QDialog, QSystemTrayIcon, QMenu, QAction, QScrollArea,
    QLineEdit, QProgressBar, QGraphicsDropShadowEffect, QSlider
)
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPen, QLinearGradient, QBrush, QRadialGradient
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QRectF, QPropertyAnimation, QPoint

print("MIA Starting...")

# ── Constants ─────────────────────────────────────────────────────────────────
VERSION = "1.0.0"
BUILD_DATE = "2026-05-25"

C_BG        = "#0a0a12"
C_SURFACE   = "#11111e"
C_SURFACE2  = "#181828"
C_BORDER    = "#1e1e35"
C_ACCENT    = "#00ffc3"
C_ACCENT2   = "#3f8cff"
C_DANGER    = "#ff4d6d"
C_WARN      = "#ffd166"
C_TEXT      = "#e8e8f0"
C_SUBTEXT   = "#7878a0"

NAV_ITEMS = [
    ("🏠", "Home"),
    ("🎙️", "Commands"),
    ("⚙️", "Settings"),
    ("ℹ️", "About"),
]

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def _is_frozen():
    return getattr(sys, 'frozen', False)

# ── Config helpers ─────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.abspath("."), "config.json")

def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"wake_word": "hey mia"}

def save_config(data: dict):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Config] Save error: {e}")

# Optional imports ─────────────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


# ── Animated Neon Ring ─────────────────────────────────────────────────────────
class AnimatedNeonRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setMaximumSize(220, 220)
        self._angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_active(self, active: bool):
        self._active = active

    def _tick(self):
        self._angle = (self._angle + 3) % 360
        self._pulse += 0.04 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 16

        # Outer glow ring
        glow_alpha = int(40 + 60 * self._pulse) if self._active else 20
        for gw in range(18, 0, -3):
            col = QColor(C_ACCENT)
            col.setAlpha(max(0, glow_alpha - gw * 3))
            pen = QPen(col, gw)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        # Background ring
        pen = QPen(QColor(C_BORDER), 6)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        # Spinning arc
        if self._active:
            arc_pen = QPen(QColor(C_ACCENT), 6)
            arc_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r),
                            (self._angle * 16), 120 * 16)
            # Second arc (trailing)
            arc_pen2 = QPen(QColor(C_ACCENT2), 4)
            arc_pen2.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen2)
            painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r),
                            ((self._angle + 150) * 16), 60 * 16)
        else:
            idle_col = QColor(C_ACCENT)
            idle_col.setAlpha(80)
            pen = QPen(idle_col, 3)
            painter.setPen(pen)
            painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        # Center dot
        dot_r = 6 if not self._active else (6 + 3 * self._pulse)
        dot_col = QColor(C_ACCENT) if self._active else QColor(C_SUBTEXT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(dot_col))
        painter.drawEllipse(QRectF(cx - dot_r, cy - dot_r, 2 * dot_r, 2 * dot_r))

        painter.end()


# ── Voice Worker ───────────────────────────────────────────────────────────────
class VoiceWorker(QObject):
    result_signal  = pyqtSignal(str)
    error_signal   = pyqtSignal(str)
    listening_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._running = False

    def start_listening(self):
        if not SR_AVAILABLE:
            self.error_signal.emit("SpeechRecognition library not installed.")
            return
        self._running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        self.listening_signal.emit(True)

    def stop_listening(self):
        self._running = False
        self.listening_signal.emit(False)

    def _listen_loop(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception as e:
            self.error_signal.emit(f"Mic error: {e}")
            self.listening_signal.emit(False)
            return
        while self._running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                text = recognizer.recognize_google(audio)
                self.result_signal.emit(text)
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                self.error_signal.emit("Google STT unavailable. Check internet.")
                break
            except Exception as e:
                self.error_signal.emit(str(e))
                break
        self.listening_signal.emit(False)


# ── Update Worker ──────────────────────────────────────────────────────────────
class UpdateWorker(QObject):
    status_signal         = pyqtSignal(str, bool)
    update_complete_signal = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()

    def check_for_updates(self):
        threading.Thread(target=self._check_loop, daemon=True).start()

    def _check_loop(self):
        if _is_frozen():
            self.status_signal.emit("Up to date (Packaged)", False)
            return
        try:
            cwd = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(["git", "fetch"], cwd=cwd, capture_output=True, text=True, timeout=15)
            res = subprocess.run(
                ["git", "rev-list", "HEAD...origin/main", "--count"],
                cwd=cwd, capture_output=True, text=True, timeout=10
            )
            count = int(res.stdout.strip() or "0")
            if count > 0:
                self.status_signal.emit(f"Update Available ({count} commit{'s' if count > 1 else ''})", True)
            else:
                self.status_signal.emit("Up to date ✓", False)
        except Exception:
            self.status_signal.emit("Update check failed", False)

    def perform_update(self):
        threading.Thread(target=self._update_loop, daemon=True).start()

    def _update_loop(self):
        try:
            cwd = os.path.dirname(os.path.abspath(__file__))
            subprocess.run(["git", "stash"], cwd=cwd, capture_output=True)
            res = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=cwd, capture_output=True, text=True, timeout=60
            )
            if res.returncode != 0:
                if "unrelated histories" in res.stderr:
                    res = subprocess.run(
                        ["git", "pull", "origin", "main", "--allow-unrelated-histories"],
                        cwd=cwd, capture_output=True, text=True, timeout=60
                    )
            if res.returncode != 0:
                subprocess.run(["git", "fetch", "origin"], cwd=cwd, capture_output=True)
                res = subprocess.run(
                    ["git", "reset", "--hard", "origin/main"],
                    cwd=cwd, capture_output=True, text=True
                )
            subprocess.run(["git", "stash", "pop"], cwd=cwd, capture_output=True)
            if res.returncode == 0:
                self.update_complete_signal.emit(True, "Update successful! Please restart MIA.")
            else:
                self.update_complete_signal.emit(False, f"Update failed: {res.stderr.strip()}")
        except Exception as e:
            self.update_complete_signal.emit(False, str(e))


# ── Toast Notification ─────────────────────────────────────────────────────────
class Toast(QDialog):
    def __init__(self, message, parent=None, duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QDialog {{
                background: {C_SURFACE2};
                border: 1px solid {C_ACCENT};
                border-radius: 12px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        icon = QLabel("✦")
        icon.setStyleSheet(f"color: {C_ACCENT}; font-size: 14px;")
        layout.addWidget(icon)
        label = QLabel(message)
        label.setStyleSheet(f"color: {C_TEXT}; font-size: 14px; font-family: 'Segoe UI';")
        layout.addWidget(label)
        self.adjustSize()
        QTimer.singleShot(duration, self.close)


# ── Sidebar NavBar ─────────────────────────────────────────────────────────────
class SideNav(QFrame):
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(140)
        self.setStyleSheet(f"""
            QFrame {{
                background: {C_SURFACE};
                border-right: 1px solid {C_BORDER};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 24, 8, 24)
        layout.setSpacing(4)

        # Logo area
        logo_label = QLabel("MIA")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"""
            color: {C_ACCENT};
            font-size: 22px;
            font-weight: bold;
            font-family: 'Segoe UI';
            letter-spacing: 4px;
            padding: 12px 0 20px 0;
        """)
        layout.addWidget(logo_label)

        self._buttons = []
        self._current = 0
        for i, (icon, label) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setCheckable(True)
            btn.setStyleSheet(self._btn_style(False))
            btn.clicked.connect(lambda checked, idx=i: self._select(idx))
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

        # Version tag
        ver_label = QLabel(f"v{VERSION}")
        ver_label.setAlignment(Qt.AlignCenter)
        ver_label.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 10px; font-family: 'Segoe UI';")
        layout.addWidget(ver_label)

        self._select(0)

    def _btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: rgba(0,255,195,0.12);
                    color: {C_ACCENT};
                    border: 1px solid rgba(0,255,195,0.3);
                    border-radius: 10px;
                    padding: 12px 6px;
                    font-size: 11px;
                    font-family: 'Segoe UI';
                    font-weight: bold;
                }}
            """
        return f"""
            QPushButton {{
                background: transparent;
                color: {C_SUBTEXT};
                border: 1px solid transparent;
                border-radius: 10px;
                padding: 12px 6px;
                font-size: 11px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.05);
                color: {C_TEXT};
                border: 1px solid {C_BORDER};
            }}
        """

    def _select(self, idx: int):
        for i, btn in enumerate(self._buttons):
            is_active = (i == idx)
            btn.setChecked(is_active)
            btn.setStyleSheet(self._btn_style(is_active))
        self._current = idx
        self.page_changed.emit(idx)


# ── Stat Card ──────────────────────────────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, title, value, color=None, parent=None):
        super().__init__(parent)
        color = color or C_ACCENT
        self.setStyleSheet(f"""
            QFrame {{
                background: {C_SURFACE2};
                border: 1px solid {C_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        self.val_label = QLabel(value)
        self.val_label.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: bold; font-family: 'Segoe UI';")
        self.val_label.setAlignment(Qt.AlignCenter)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; font-family: 'Segoe UI';")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.val_label)
        layout.addWidget(title_label)

    def set_value(self, v: str):
        self.val_label.setText(v)


# ── Status Pill ────────────────────────────────────────────────────────────────
class StatusPill(QFrame):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(0,255,195,0.08);
                border: 1px solid rgba(0,255,195,0.3);
                border-radius: 16px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(6)
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {C_ACCENT}; font-size: 9px;")
        layout.addWidget(self.dot)
        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 12px; font-family: 'Segoe UI'; font-weight: bold;")
        layout.addWidget(self.lbl)

    def set_state(self, text: str, ok: bool):
        color = C_ACCENT if ok else C_DANGER
        self.dot.setStyleSheet(f"color: {color}; font-size: 9px;")
        self.lbl.setText(text)
        self.lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-family: 'Segoe UI'; font-weight: bold;")
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba({'0,255,195' if ok else '255,77,109'},0.08);
                border: 1px solid rgba({'0,255,195' if ok else '255,77,109'},0.3);
                border-radius: 16px;
            }}
        """)


# ── Section Header ─────────────────────────────────────────────────────────────
def section_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {C_SUBTEXT};
        font-size: 10px;
        font-weight: bold;
        font-family: 'Segoe UI';
        letter-spacing: 2px;
        padding: 0 0 6px 0;
    """)
    return lbl


# ── Primary Button ─────────────────────────────────────────────────────────────
def make_btn(text: str, style="primary", icon="") -> QPushButton:
    label = f"{icon}  {text}" if icon else text
    btn = QPushButton(label)
    btn.setCursor(Qt.PointingHandCursor)
    if style == "primary":
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT};
                color: #0a0a12;
                border: none;
                border-radius: 8px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: #00e6b0; }}
            QPushButton:disabled {{ background: #1e1e35; color: {C_SUBTEXT}; }}
        """)
    elif style == "secondary":
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(63,140,255,0.15);
                color: {C_ACCENT2};
                border: 1px solid rgba(63,140,255,0.35);
                border-radius: 8px;
                padding: 10px 22px;
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: rgba(63,140,255,0.25); }}
            QPushButton:disabled {{ opacity: 0.4; }}
        """)
    elif style == "danger":
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,77,109,0.15);
                color: {C_DANGER};
                border: 1px solid rgba(255,77,109,0.35);
                border-radius: 8px;
                padding: 10px 22px;
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: rgba(255,77,109,0.25); }}
        """)
    elif style == "ghost":
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_SUBTEXT};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                padding: 10px 22px;
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.05); color: {C_TEXT}; }}
        """)
    return btn


# ── Toggle Button ──────────────────────────────────────────────────────────────
class ToggleButton(QPushButton):
    def __init__(self, text_on: str, text_off: str, parent=None):
        super().__init__(parent)
        self._text_on = text_on
        self._text_off = text_off
        self.setCheckable(True)
        self.setChecked(False)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.toggled.connect(self._update_style)

    def _update_style(self):
        if self.isChecked():
            self.setText(self._text_on)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0,255,195,0.12);
                    color: {C_ACCENT};
                    border: 1px solid rgba(0,255,195,0.4);
                    border-radius: 8px;
                    padding: 10px 22px;
                    font-size: 13px;
                    font-family: 'Segoe UI';
                    font-weight: bold;
                }}
            """)
        else:
            self.setText(self._text_off)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,77,109,0.10);
                    color: {C_DANGER};
                    border: 1px solid rgba(255,77,109,0.3);
                    border-radius: 8px;
                    padding: 10px 22px;
                    font-size: 13px;
                    font-family: 'Segoe UI';
                }}
                QPushButton:hover {{ background: rgba(255,77,109,0.18); }}
            """)


# ── Personality Card ───────────────────────────────────────────────────────────
class PersonalityCard(QFrame):
    selected = pyqtSignal(str)

    PERSONALITIES = [
        ("😌", "Calm",      "Soothing & measured"),
        ("😄", "Witty",     "Playful & clever"),
        ("😏", "Sarcastic", "Dry & sharp"),
        ("💪", "Bold",      "Confident & direct"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._current = "calm"
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        self._cards = {}
        for emoji, name, desc in self.PERSONALITIES:
            card = QFrame()
            card.setCursor(Qt.PointingHandCursor)
            card.setFixedSize(90, 90)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(4)
            em = QLabel(emoji)
            em.setAlignment(Qt.AlignCenter)
            em.setStyleSheet("font-size: 22px;")
            cl.addWidget(em)
            nm = QLabel(name)
            nm.setAlignment(Qt.AlignCenter)
            nm.setStyleSheet(f"color: {C_TEXT}; font-size: 11px; font-weight: bold; font-family: 'Segoe UI';")
            cl.addWidget(nm)
            layout.addWidget(card)
            self._cards[name.lower()] = card
            card.mousePressEvent = lambda e, n=name.lower(): self._pick(n)
        self._pick("calm")

    def _pick(self, key: str):
        self._current = key
        for k, c in self._cards.items():
            if k == key:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: rgba(0,255,195,0.12);
                        border: 1.5px solid {C_ACCENT};
                        border-radius: 12px;
                    }}
                """)
            else:
                c.setStyleSheet(f"""
                    QFrame {{
                        background: {C_SURFACE2};
                        border: 1px solid {C_BORDER};
                        border-radius: 12px;
                    }}
                    QFrame:hover {{
                        border: 1px solid rgba(255,255,255,0.2);
                    }}
                """)
        self.selected.emit(key)

    def get_personality(self) -> str:
        return self._current


# ── Quick Command Button ───────────────────────────────────────────────────────
class QuickCmdBtn(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(110, 70)
        self.setStyleSheet(f"""
            QFrame {{
                background: {C_SURFACE2};
                border: 1px solid {C_BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background: rgba(0,255,195,0.06);
                border: 1px solid rgba(0,255,195,0.3);
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)
        em = QLabel(icon)
        em.setAlignment(Qt.AlignCenter)
        em.setStyleSheet("font-size: 20px;")
        layout.addWidget(em)
        nm = QLabel(text)
        nm.setAlignment(Qt.AlignCenter)
        nm.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 10px; font-family: 'Segoe UI';")
        layout.addWidget(nm)

    def mousePressEvent(self, event):
        self.clicked.emit()


# ══════════════════════════════════════════════════════════════════════════════
# ── Main Window ───────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
class NeonMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIA – My Intelligent Assistant")
        ico_new = resource_path("mia_icon_new.ico")
        if os.path.exists(ico_new):
            self.setWindowIcon(QIcon(ico_new))
        else:
            ico = resource_path(os.path.join("ui_assets", "logo.svg"))
            if os.path.exists(ico):
                self.setWindowIcon(QIcon(ico))
            elif os.path.exists(resource_path("mia_icon.ico")):
                self.setWindowIcon(QIcon(resource_path("mia_icon.ico")))

        self.setGeometry(80, 80, 1020, 660)
        self.setMinimumSize(860, 580)
        self.setStyleSheet(f"QWidget {{ background: {C_BG}; color: {C_TEXT}; }}")

        # Workers
        self.voice_worker = VoiceWorker()
        self.voice_worker.result_signal.connect(self._on_voice_result)
        self.voice_worker.error_signal.connect(self._on_voice_error)
        self.voice_worker.listening_signal.connect(self._on_listening_state)
        self.voice_history = []

        self.update_worker = UpdateWorker()
        self.update_worker.status_signal.connect(self._on_update_status)
        self.update_worker.update_complete_signal.connect(self._on_update_complete)

        self.processes = {}
        self._personality = "calm"
        self._mic_muted = False
        self._cam_muted = False
        self._mia_running = False

        self._build_ui()
        self._init_tray()

        # Auto update check
        self.update_worker.check_for_updates()

        # System stats timer
        if PSUTIL_AVAILABLE:
            self._stats_timer = QTimer(self)
            self._stats_timer.timeout.connect(self._refresh_stats)
            self._stats_timer.start(2000)
            self._refresh_stats()

    # ── UI Build ────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidenav = SideNav()
        self.sidenav.page_changed.connect(self._switch_page)
        root.addWidget(self.sidenav)

        # Content area
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("QStackedWidget { background: transparent; }")
        self.pages.addWidget(self._build_home())
        self.pages.addWidget(self._build_commands())
        self.pages.addWidget(self._build_settings())
        self.pages.addWidget(self._build_about())
        root.addWidget(self.pages)

    def _switch_page(self, idx: int):
        self.pages.setCurrentIndex(idx)

    # ── Home Page ───────────────────────────────────────────────────────────
    def _build_home(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        # Header
        header = QHBoxLayout()
        title = QLabel("Control Center")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 22px; font-weight: bold; font-family: 'Segoe UI';")
        header.addWidget(title)
        header.addStretch()
        self.status_pill = StatusPill("Idle")
        header.addWidget(self.status_pill)
        outer.addLayout(header)
        outer.addSpacing(24)

        # Main content row
        content_row = QHBoxLayout()
        content_row.setSpacing(24)

        # Ring + controls (left)
        left = QVBoxLayout()
        left.setSpacing(20)
        left.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.neon_ring = AnimatedNeonRing()
        left.addWidget(self.neon_ring, alignment=Qt.AlignHCenter)

        # Status label under ring
        self.ring_status_label = QLabel("Ready")
        self.ring_status_label.setAlignment(Qt.AlignCenter)
        self.ring_status_label.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 13px; font-family: 'Segoe UI';")
        left.addWidget(self.ring_status_label)

        # Start/Stop buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.start_btn = make_btn("Start MIA", "primary", "▶")
        self.stop_btn  = make_btn("Stop MIA",  "danger",  "■")
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_mia)
        self.stop_btn.clicked.connect(self._stop_mia)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        left.addLayout(btn_row)
        content_row.addLayout(left, 1)

        # Right: stats + process status
        right = QVBoxLayout()
        right.setSpacing(14)
        right.setAlignment(Qt.AlignTop)

        right.addWidget(section_header("SYSTEM STATS"))
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.cpu_card = StatCard("CPU", "—%", C_ACCENT2)
        self.ram_card = StatCard("RAM", "—%", C_WARN)
        stats_row.addWidget(self.cpu_card)
        stats_row.addWidget(self.ram_card)
        right.addLayout(stats_row)

        right.addSpacing(8)
        right.addWidget(section_header("COMPONENTS"))
        self._proc_labels = {}
        components = [
            ("api",     "🔌", "API Server"),
            ("voice",   "🎙️", "Voice Engine"),
            ("gesture", "✋", "Gesture Control"),
            ("mood",    "😶", "Mood Detection"),
        ]
        for key, icon, name in components:
            row = QHBoxLayout()
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("font-size: 14px;")
            lbl_name = QLabel(name)
            lbl_name.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-family: 'Segoe UI';")
            row.addWidget(lbl_icon)
            row.addWidget(lbl_name)
            row.addStretch()
            status_lbl = QLabel("○ Stopped")
            status_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 12px; font-family: 'Segoe UI';")
            row.addWidget(status_lbl)
            self._proc_labels[key] = status_lbl
            right.addLayout(row)

        content_row.addLayout(right, 1)
        outer.addLayout(content_row)
        outer.addStretch()
        return page

    def _refresh_stats(self):
        if not PSUTIL_AVAILABLE:
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.cpu_card.set_value(f"{cpu:.0f}%")
            self.ram_card.set_value(f"{ram:.0f}%")
        except Exception:
            pass

    def _update_proc_label(self, key: str, running: bool):
        lbl = self._proc_labels.get(key)
        if lbl:
            if running:
                lbl.setText("● Running")
                lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 12px; font-family: 'Segoe UI';")
            else:
                lbl.setText("○ Stopped")
                lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 12px; font-family: 'Segoe UI';")

    # ── Commands Page ───────────────────────────────────────────────────────
    def _build_commands(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 6px; } QScrollBar::handle:vertical { background: #1e1e35; border-radius: 3px; }")
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(0)

        title = QLabel("Command Center")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 22px; font-weight: bold; font-family: 'Segoe UI';")
        outer.addWidget(title)
        outer.addSpacing(18)

        # ── Split: Left (voice) | Right (system dashboard) ──────────────────
        split = QHBoxLayout()
        split.setSpacing(20)

        # ── LEFT PANEL ──────────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        # Live transcript
        left.addWidget(section_header("LIVE TRANSCRIPT"))
        self.transcript_box = QFrame()
        self.transcript_box.setFixedHeight(60)
        self.transcript_box.setStyleSheet(f"""
            QFrame {{ background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 12px; }}
        """)
        tl = QHBoxLayout(self.transcript_box)
        self.transcript_label = QLabel("Press 'Start Listening' or say Hey MIA...")
        self.transcript_label.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 13px; font-family: 'Segoe UI';")
        self.transcript_label.setWordWrap(True)
        tl.addWidget(self.transcript_label)
        left.addWidget(self.transcript_box)

        self.listen_btn = make_btn("Start Listening", "primary", "🎙️")
        self.listen_btn.clicked.connect(self._toggle_listening)
        left.addWidget(self.listen_btn)

        # Search / command bar
        left.addWidget(section_header("SEARCH / COMMAND"))
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or ask anything...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C_SURFACE}; border: 1px solid {C_BORDER};
                border-radius: 8px; padding: 9px 14px;
                color: {C_TEXT}; font-size: 13px; font-family: 'Segoe UI';
            }}
            QLineEdit:focus {{ border: 1px solid {C_ACCENT}; }}
        """)
        self.search_input.returnPressed.connect(self._do_typed_search)
        search_row.addWidget(self.search_input)
        go_btn = make_btn("Go", "primary")
        go_btn.setFixedWidth(64)
        go_btn.clicked.connect(self._do_typed_search)
        search_row.addWidget(go_btn)
        left.addLayout(search_row)

        # History
        left.addWidget(section_header("HISTORY"))
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(f"""
            QListWidget {{
                background: {C_SURFACE}; border: 1px solid {C_BORDER};
                border-radius: 10px; color: {C_TEXT};
                font-size: 12px; font-family: 'Segoe UI'; padding: 4px;
            }}
            QListWidget::item {{ padding: 7px 10px; border-radius: 6px; }}
            QListWidget::item:hover {{ background: rgba(255,255,255,0.04); }}
            QListWidget::item:selected {{ background: rgba(0,255,195,0.1); color: {C_ACCENT}; }}
            QScrollBar:vertical {{ width: 5px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {C_BORDER}; border-radius: 3px; }}
        """)
        left.addWidget(self.history_list)
        split.addLayout(left, 55)

        # ── RIGHT PANEL ─────────────────────────────────────────────────────
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 5px; } QScrollBar::handle:vertical { background: #1e1e35; border-radius: 3px; }")
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right = QVBoxLayout(right_widget)
        right.setSpacing(14)
        right.setContentsMargins(0, 0, 0, 0)

        # ── System Controls Card ─────────────────────────────────────────────
        sys_card = QFrame()
        sys_card.setStyleSheet(f"QFrame {{ background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 14px; }}")
        sys_layout = QVBoxLayout(sys_card)
        sys_layout.setContentsMargins(16, 14, 16, 14)
        sys_layout.setSpacing(12)
        sys_layout.addWidget(section_header("SYSTEM CONTROLS"))

        # Volume slider
        vol_row = QHBoxLayout()
        vol_lbl = QLabel("Volume")
        vol_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 12px; font-family: 'Segoe UI'; min-width: 58px;")
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(50)
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #1e1e35; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00ffc3; width: 14px; height: 14px; border-radius: 7px; margin: -5px 0; }
            QSlider::sub-page:horizontal { background: #00ffc3; border-radius: 2px; }
        """)
        self.vol_val_lbl = QLabel("50%")
        self.vol_val_lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 11px; font-family: 'Segoe UI'; min-width: 32px;")
        self.vol_slider.valueChanged.connect(lambda v: (self.vol_val_lbl.setText(f"{v}%"), self._set_volume(v)))
        vol_row.addWidget(vol_lbl)
        vol_row.addWidget(self.vol_slider)
        vol_row.addWidget(self.vol_val_lbl)
        sys_layout.addLayout(vol_row)

        # Brightness slider
        br_row = QHBoxLayout()
        br_lbl = QLabel("Brightness")
        br_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 12px; font-family: 'Segoe UI'; min-width: 58px;")
        self.br_slider = QSlider(Qt.Horizontal)
        self.br_slider.setRange(0, 100)
        self.br_slider.setValue(80)
        self.br_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #1e1e35; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffd166; width: 14px; height: 14px; border-radius: 7px; margin: -5px 0; }
            QSlider::sub-page:horizontal { background: #ffd166; border-radius: 2px; }
        """)
        self.br_val_lbl = QLabel("80%")
        self.br_val_lbl.setStyleSheet(f"color: {C_WARN}; font-size: 11px; font-family: 'Segoe UI'; min-width: 32px;")
        self.br_slider.valueChanged.connect(lambda v: (self.br_val_lbl.setText(f"{v}%"), self._set_brightness(v)))
        br_row.addWidget(br_lbl)
        br_row.addWidget(self.br_slider)
        br_row.addWidget(self.br_val_lbl)
        sys_layout.addLayout(br_row)

        # Power buttons
        power_row = QHBoxLayout()
        power_row.setSpacing(8)
        lock_btn = make_btn("Lock PC", "secondary", "🔒")
        lock_btn.clicked.connect(self._do_lock_pc)
        sleep_btn = make_btn("Sleep", "ghost", "🌙")
        sleep_btn.clicked.connect(self._do_sleep_pc)
        ss_btn = make_btn("Screenshot", "ghost", "📸")
        ss_btn.clicked.connect(self._do_screenshot)
        power_row.addWidget(lock_btn)
        power_row.addWidget(sleep_btn)
        power_row.addWidget(ss_btn)
        sys_layout.addLayout(power_row)

        # App launchers
        sys_layout.addWidget(section_header("APP LAUNCHERS"))
        app_grid = QHBoxLayout()
        app_grid.setSpacing(8)
        apps = [
            ("📁", "Explorer",   "explorer"),
            ("📝", "Notepad",    "notepad"),
            ("⚙️", "Task Mgr",  "taskmgr"),
            ("💻", "Terminal",   "cmd"),
            ("🧮", "Calculator", "calc"),
        ]
        for icon, label, cmd in apps:
            b = QuickCmdBtn(icon, label)
            b.clicked.connect(lambda c=cmd: self._launch_app(c))
            app_grid.addWidget(b)
        app_grid.addStretch()
        sys_layout.addLayout(app_grid)
        right.addWidget(sys_card)

        # ── Web Quick-Links Card ─────────────────────────────────────────────
        web_card = QFrame()
        web_card.setStyleSheet(f"QFrame {{ background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 14px; }}")
        web_layout = QVBoxLayout(web_card)
        web_layout.setContentsMargins(16, 14, 16, 14)
        web_layout.setSpacing(10)
        web_layout.addWidget(section_header("QUICK WEB LINKS"))

        web_sites = [
            ("▶",  "YouTube",   "https://youtube.com"),
            ("G",  "Google",    "https://google.com"),
            ("✦",  "ChatGPT",   "https://chat.openai.com"),
            ("◆",  "GitHub",    "https://github.com"),
            ("M",  "Gmail",     "https://mail.google.com"),
            ("N",  "Netflix",   "https://netflix.com"),
            ("♫",  "Spotify",   "https://spotify.com"),
            ("R",  "Reddit",    "https://reddit.com"),
            ("T",  "Twitter/X", "https://x.com"),
            ("W",  "Wikipedia", "https://wikipedia.org"),
            ("Li", "LinkedIn",  "https://linkedin.com"),
            ("A",  "Amazon",    "https://amazon.in"),
        ]

        SITE_COLORS = [
            "#ff0000", "#4285f4", "#10a37f", "#e8e8f0",
            "#ea4335", "#e50914", "#1db954", "#ff4500",
            "#1d9bf0", "#888",    "#0077b5", "#ff9900",
        ]

        web_grid_rows = [QHBoxLayout(), QHBoxLayout(), QHBoxLayout()]
        for i, (icon, label, url) in enumerate(web_sites):
            row_idx = i // 4
            color = SITE_COLORS[i]
            cell = QFrame()
            cell.setCursor(Qt.PointingHandCursor)
            cell.setFixedSize(90, 64)
            cell.setStyleSheet(f"""
                QFrame {{
                    background: {C_SURFACE2};
                    border: 1px solid {C_BORDER};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    background: rgba(255,255,255,0.07);
                    border: 1px solid {color};
                }}
            """)
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(6, 6, 6, 6)
            cl.setSpacing(3)
            ic = QLabel(icon)
            ic.setAlignment(Qt.AlignCenter)
            ic.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold; font-family: 'Segoe UI';")
            cl.addWidget(ic)
            nm = QLabel(label)
            nm.setAlignment(Qt.AlignCenter)
            nm.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 9px; font-family: 'Segoe UI';")
            cl.addWidget(nm)
            cell.mousePressEvent = lambda e, u=url: webbrowser.open(u)
            web_grid_rows[row_idx].addWidget(cell)

        for row_layout in web_grid_rows:
            row_layout.addStretch()
            web_layout.addLayout(row_layout)

        right.addWidget(web_card)
        right.addStretch()
        right_scroll.setWidget(right_widget)
        split.addWidget(right_scroll, 45)

        outer.addLayout(split)
        scroll.setWidget(page)
        return scroll

    # ── Settings Page ───────────────────────────────────────────────────────
    def _build_settings(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 6px; } QScrollBar::handle:vertical { background: #1e1e35; border-radius: 3px; }")

        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        title = QLabel("Settings")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 22px; font-weight: bold; font-family: 'Segoe UI';")
        outer.addWidget(title)
        outer.addSpacing(24)

        # Personality
        outer.addWidget(section_header("TTS PERSONALITY"))
        outer.addSpacing(8)
        self.personality_card = PersonalityCard()
        self.personality_card.selected.connect(self._on_personality_change)
        outer.addWidget(self.personality_card)
        outer.addSpacing(24)

        # Privacy
        outer.addWidget(section_header("PRIVACY"))
        outer.addSpacing(8)
        privacy_row = QHBoxLayout()
        privacy_row.setSpacing(12)
        self.mic_btn = ToggleButton("🎙️  Mic Active", "🚫  Mic Muted")
        self.mic_btn.setChecked(True)
        self.mic_btn.toggled.connect(self._on_mic_toggle)
        self.cam_btn = ToggleButton("📷  Cam Active", "🚫  Cam Muted")
        self.cam_btn.setChecked(True)
        self.cam_btn.toggled.connect(self._on_cam_toggle)
        privacy_row.addWidget(self.mic_btn)
        privacy_row.addWidget(self.cam_btn)
        privacy_row.addStretch()
        outer.addLayout(privacy_row)
        outer.addSpacing(24)

        # Theme
        outer.addWidget(section_header("APPEARANCE"))
        outer.addSpacing(8)
        theme_row = QHBoxLayout()
        self.theme_dark_btn = make_btn("Dark Theme", "primary")
        self.theme_dark_btn.clicked.connect(lambda: self._apply_theme("dark"))
        self.theme_light_btn = make_btn("Light Theme", "ghost")
        self.theme_light_btn.clicked.connect(lambda: self._apply_theme("light"))
        theme_row.addWidget(self.theme_dark_btn)
        theme_row.addWidget(self.theme_light_btn)
        theme_row.addStretch()
        outer.addLayout(theme_row)
        outer.addSpacing(24)

        # ── Wake Word Configurator ───────────────────────────────────────────
        outer.addWidget(section_header("WAKE WORD CONFIGURATION"))
        outer.addSpacing(8)
        wake_card = QFrame()
        wake_card.setStyleSheet(f"QFrame {{ background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 12px; }}")
        wake_layout = QVBoxLayout(wake_card)
        wake_layout.setContentsMargins(16, 14, 16, 14)
        wake_layout.setSpacing(10)

        cfg = load_config()
        ww_hint = QLabel(f"Current wake word: '{cfg.get('wake_word', 'hey mia')}'")
        ww_hint.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px; font-family: 'Segoe UI';")
        wake_layout.addWidget(ww_hint)

        ww_row = QHBoxLayout()
        ww_row.setSpacing(10)
        self.wake_word_input = QLineEdit()
        self.wake_word_input.setPlaceholderText("e.g. hey jarvis, computer, mia...")
        self.wake_word_input.setText(cfg.get("wake_word", "hey mia"))
        self.wake_word_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C_SURFACE2}; border: 1px solid {C_BORDER};
                border-radius: 8px; padding: 9px 14px;
                color: {C_TEXT}; font-size: 13px; font-family: 'Segoe UI';
            }}
            QLineEdit:focus {{ border: 1px solid {C_ACCENT}; }}
        """)
        apply_ww_btn = make_btn("Apply & Restart Voice", "primary", "🔄")
        apply_ww_btn.clicked.connect(self._apply_wake_word)
        ww_row.addWidget(self.wake_word_input)
        ww_row.addWidget(apply_ww_btn)
        wake_layout.addLayout(ww_row)

        ww_note = QLabel("Changes take effect immediately — voice engine restarts with new wake word.")
        ww_note.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 10px; font-family: 'Segoe UI';")
        ww_note.setWordWrap(True)
        wake_layout.addWidget(ww_note)
        outer.addWidget(wake_card)
        outer.addSpacing(24)

        # ── Keybinds Reference ───────────────────────────────────────────────
        outer.addWidget(section_header("GLOBAL KEYBOARD SHORTCUTS"))
        outer.addSpacing(8)
        kb_card = QFrame()
        kb_card.setStyleSheet(f"QFrame {{ background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 12px; }}")
        kb_layout = QVBoxLayout(kb_card)
        kb_layout.setContentsMargins(16, 14, 16, 14)
        kb_layout.setSpacing(6)
        keybinds = [
            ("Ctrl + L",   "Toggle voice listening on/off"),
            ("Ctrl + M",   "Toggle microphone mute"),
            ("Ctrl + 1",   "Navigate to Home page"),
            ("Ctrl + 2",   "Navigate to Commands page"),
            ("Ctrl + 3",   "Navigate to Settings page"),
            ("Ctrl + 4",   "Navigate to About page"),
        ]
        for key, desc in keybinds:
            kb_row = QHBoxLayout()
            key_lbl = QLabel(key)
            key_lbl.setFixedWidth(90)
            key_lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 12px; font-weight: bold; font-family: 'Consolas', 'Segoe UI';")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 12px; font-family: 'Segoe UI';")
            kb_row.addWidget(key_lbl)
            kb_row.addWidget(desc_lbl)
            kb_row.addStretch()
            kb_layout.addLayout(kb_row)
        outer.addWidget(kb_card)
        outer.addSpacing(24)

        # Updates
        outer.addWidget(section_header("APPLICATION UPDATE"))
        outer.addSpacing(8)
        update_row = QHBoxLayout()
        self.update_btn = make_btn("Checking for updates...", "ghost")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.update_status_lbl = QLabel("")
        self.update_status_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 12px; font-family: 'Segoe UI';")
        update_row.addWidget(self.update_btn)
        update_row.addWidget(self.update_status_lbl)
        update_row.addStretch()
        outer.addLayout(update_row)
        outer.addStretch()

        scroll.setWidget(page)
        return scroll

    # ── About Page ──────────────────────────────────────────────────────────
    def _build_about(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(0)

        title = QLabel("About MIA")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 22px; font-weight: bold; font-family: 'Segoe UI';")
        outer.addWidget(title)
        outer.addSpacing(20)

        # Hero card
        hero = QFrame()
        hero.setStyleSheet(f"""
            QFrame {{
                background: {C_SURFACE2};
                border: 1px solid {C_BORDER};
                border-radius: 16px;
            }}
        """)
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(28, 24, 28, 24)
        hl.setSpacing(8)
        mia_lbl = QLabel("MIA")
        mia_lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 36px; font-weight: bold; font-family: 'Segoe UI'; letter-spacing: 8px;")
        mia_lbl.setAlignment(Qt.AlignCenter)
        hl.addWidget(mia_lbl)
        sub_lbl = QLabel("My Intelligent Assistant")
        sub_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 14px; font-family: 'Segoe UI'; letter-spacing: 2px;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        hl.addWidget(sub_lbl)
        outer.addWidget(hero)
        outer.addSpacing(20)

        # Info grid
        outer.addWidget(section_header("BUILD INFO"))
        outer.addSpacing(8)
        info_grid = QHBoxLayout()
        info_grid.setSpacing(12)
        for lbl, val in [("Version", VERSION), ("Build Date", BUILD_DATE), ("Python", sys.version.split()[0])]:
            card = StatCard(lbl, val, C_ACCENT2)
            info_grid.addWidget(card)
        outer.addLayout(info_grid)
        outer.addSpacing(24)

        # Component health
        outer.addWidget(section_header("COMPONENT HEALTH"))
        outer.addSpacing(8)
        health_components = [
            ("PyQt5 UI",          True),
            ("Speech Recognition", SR_AVAILABLE),
            ("psutil (Stats)",    PSUTIL_AVAILABLE),
        ]
        # Check optional imports
        try:
            import cv2
            health_components.append(("OpenCV (Gestures)", True))
        except ImportError:
            health_components.append(("OpenCV (Gestures)", False))
        try:
            import pyttsx3
            health_components.append(("pyttsx3 (TTS)", True))
        except ImportError:
            health_components.append(("pyttsx3 (TTS)", False))
        try:
            import mediapipe
            health_components.append(("MediaPipe", True))
        except ImportError:
            health_components.append(("MediaPipe", False))

        for comp_name, ok in health_components:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {C_ACCENT if ok else C_DANGER}; font-size: 10px;")
            row.addWidget(dot)
            lbl_c = QLabel(comp_name)
            lbl_c.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-family: 'Segoe UI';")
            row.addWidget(lbl_c)
            row.addStretch()
            status = QLabel("Installed" if ok else "Missing")
            status.setStyleSheet(f"color: {C_ACCENT if ok else C_DANGER}; font-size: 12px; font-family: 'Segoe UI';")
            row.addWidget(status)
            outer.addLayout(row)

        outer.addStretch()

        desc = QLabel("Futuristic AI desktop assistant with voice, gesture, and AR UI.\nInspired by JARVIS. Built for privacy — all processing is local.")
        desc.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 12px; font-family: 'Segoe UI'; line-height: 1.6;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        outer.addWidget(desc)
        outer.addSpacing(8)
        return page

    # ── Tray ────────────────────────────────────────────────────────────────
    def _init_tray(self):
        ico_path = resource_path(os.path.join("ui_assets", "logo.svg"))
        ico = QIcon(ico_path) if os.path.exists(ico_path) else QIcon()
        self.tray_icon = QSystemTrayIcon(ico, self)
        menu = QMenu()

        def styled_action(text):
            a = QAction(text, self)
            return a

        show_a = styled_action("Show MIA")
        show_a.triggered.connect(self.show)

        home_a = styled_action("Home")
        home_a.triggered.connect(lambda: (self.show(), self.sidenav._select(0)))

        cmd_a = styled_action("Commands")
        cmd_a.triggered.connect(lambda: (self.show(), self.sidenav._select(1)))

        mic_a = styled_action("Toggle Mic")
        mic_a.triggered.connect(lambda: self.mic_btn.click())

        start_a = styled_action("Start MIA")
        start_a.triggered.connect(self._start_mia)

        stop_a = styled_action("Stop MIA")
        stop_a.triggered.connect(self._stop_mia)

        quit_a = styled_action("Quit")
        quit_a.triggered.connect(self._quit_app)

        menu.addAction(show_a)
        menu.addSeparator()
        menu.addAction(home_a)
        menu.addAction(cmd_a)
        menu.addSeparator()
        menu.addAction(mic_a)
        menu.addAction(start_a)
        menu.addAction(stop_a)
        menu.addSeparator()
        menu.addAction(quit_a)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show() if not self.isVisible() else self.hide()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def _quit_app(self):
        self._stop_mia()
        QApplication.quit()

    # ── MIA Start/Stop ───────────────────────────────────────────────────────
    def _start_mia(self):
        if self._mia_running:
            return
        self._mia_running = True
        self.ring_status_label.setText("Launching…")
        self.status_pill.set_state("Launching…", True)
        self.neon_ring.set_active(True)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        project_root = os.path.abspath(os.path.dirname(__file__))

        if _is_frozen():
            # In-process mode for packaged app
            try:
                import uvicorn
                from server.api import app as fastapi_app
                def _run_api():
                    uvicorn.Server(uvicorn.Config(fastapi_app, host="127.0.0.1", port=8000)).run()
                threading.Thread(target=_run_api, daemon=True).start()
                self._update_proc_label("api", True)
            except Exception as e:
                print(f"API start failed: {e}")

            try:
                from mia_assistant.voice_activation import listen_for_wake_word
                threading.Thread(target=listen_for_wake_word, daemon=True).start()
                self._update_proc_label("voice", True)
            except Exception as e:
                print(f"Voice start failed: {e}")
        else:
            # Dev mode: subprocess
            def launch(key, args, label):
                if key not in self.processes:
                    try:
                        self.processes[key] = subprocess.Popen(args, cwd=project_root)
                        self._update_proc_label(key, True)
                    except Exception as e:
                        print(f"{label} start failed: {e}")

            launch("api", [sys.executable, "-m", "uvicorn", "server.api:app",
                           "--host", "127.0.0.1", "--port", "8000"], "API")
            if not self._mic_muted:
                launch("voice", [sys.executable, "mia_assistant/voice_activation.py",
                                 self._personality], "Voice")
            try:
                __import__("cv2")
                if not self._cam_muted:
                    launch("gesture", [sys.executable, "gesture_control/main.py"], "Gesture")
            except ImportError:
                print("Gesture disabled: OpenCV not available")
            launch("mood", [sys.executable, "mia_assistant/mood_detection.py"], "Mood")

        self.status_pill.set_state("Running", True)
        self.ring_status_label.setText("Running")
        self._show_toast("MIA is running ✦")

    def _stop_mia(self):
        for key, proc in list(self.processes.items()):
            try:
                proc.terminate()
            except Exception:
                pass
            self._update_proc_label(key, False)
        self.processes = {}
        self._mia_running = False
        self.neon_ring.set_active(False)
        self.ring_status_label.setText("Stopped")
        self.status_pill.set_state("Stopped", False)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._show_toast("MIA stopped")

    # ── Voice ────────────────────────────────────────────────────────────────
    def _toggle_listening(self):
        if self.listen_btn.text().startswith("Stop"):
            self.voice_worker.stop_listening()
            self.listen_btn.setText("🎙️  Start Listening")
            self.listen_btn.setStyleSheet(make_btn("", "primary").styleSheet())
            self.transcript_label.setText("Press 'Start Listening' or say Hey MIA…")
            self.transcript_label.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 14px; font-family: 'Segoe UI';")
        else:
            if self._mic_muted:
                self._show_toast("Microphone is muted!", duration=2000)
                return
            self.voice_worker.start_listening()
            self.listen_btn.setText("■  Stop Listening")

    def _on_voice_result(self, text: str):
        self.transcript_label.setText(f"You said: {text}")
        self.transcript_label.setStyleSheet(f"color: {C_ACCENT}; font-size: 14px; font-family: 'Segoe UI';")
        self.voice_history.append(text)
        item = QListWidgetItem(f"🎙️  {text}")
        item.setForeground(QColor(C_TEXT))
        self.history_list.insertItem(0, item)
        # Auto-process typed command
        self._process_command(text)

    def _on_voice_error(self, msg: str):
        self.transcript_label.setText(f"Error: {msg}")
        self.transcript_label.setStyleSheet(f"color: {C_DANGER}; font-size: 14px; font-family: 'Segoe UI';")
        self._show_toast(f"⚠ {msg}", duration=4000)

    def _on_listening_state(self, listening: bool):
        if not listening and self.listen_btn.text().startswith("■"):
            self.listen_btn.setText("🎙️  Start Listening")

    # ── Quick commands ───────────────────────────────────────────────────────
    def _do_screenshot(self):
        try:
            from mia_assistant.actions import take_screenshot
            result = take_screenshot()
            self._show_toast(f"📸 {result}")
            self._add_history(f"[Screenshot] {result}")
        except Exception as e:
            self._show_toast(f"Screenshot failed: {e}")

    def _do_volume_up(self):
        try:
            from mia_assistant.actions import change_volume
            result = change_volume("up")
            self._show_toast(f"🔊 {result}")
            self._add_history("[Volume] Up")
        except Exception as e:
            self._show_toast(f"Volume error: {e}")

    def _do_volume_down(self):
        try:
            from mia_assistant.actions import change_volume
            result = change_volume("down")
            self._show_toast(f"🔇 {result}")
            self._add_history("[Volume] Down")
        except Exception as e:
            self._show_toast(f"Volume error: {e}")

    def _do_web_search(self):
        query = self.search_input.text().strip()
        if not query:
            self._show_toast("Enter something in the search box first")
            return
        try:
            from mia_assistant.actions import search_web
            result = search_web(query)
            self._show_toast(f"🌐 {result}")
            self._add_history(f"[Search] {query}")
        except Exception as e:
            self._show_toast(f"Search error: {e}")

    def _do_typed_search(self):
        query = self.search_input.text().strip()
        if query:
            self._process_command(query)
            self.search_input.clear()

    def _process_command(self, text: str):
        """Route typed/spoken command through the parser."""
        try:
            from mia_assistant.command_parser import parse_command
            from mia_assistant.actions import execute_action
            from mia_assistant.ollama_client import styled_reply
            parsed = parse_command(text)
            if parsed.get("intent") == "chat":
                response = styled_reply(text, self._personality)
            else:
                response = execute_action(parsed)
            self._add_history(f"[{parsed.get('intent', 'cmd')}] {text} → {response}")
            # TTS feedback (non-blocking)
            try:
                from mia_assistant.tts_response import speak_text
                speak_text(response, self._personality)
            except Exception:
                pass
        except Exception as e:
            self._add_history(f"[Error] {e}")

    def _add_history(self, text: str):
        item = QListWidgetItem(text)
        item.setForeground(QColor(C_TEXT))
        self.history_list.insertItem(0, item)

    # ── Settings Handlers ────────────────────────────────────────────────────
    def _on_personality_change(self, key: str):
        self._personality = key
        self._show_toast(f"Personality: {key.capitalize()}")

    def _on_mic_toggle(self, checked: bool):
        self._mic_muted = not checked
        state = "active" if checked else "muted"
        self._show_toast(f"Mic {state}")

    def _on_cam_toggle(self, checked: bool):
        self._cam_muted = not checked
        state = "active" if checked else "muted"
        self._show_toast(f"Camera {state}")

    def _apply_theme(self, theme: str):
        if theme == "light":
            self.setStyleSheet("QWidget { background: #f5f5fa; color: #111; }")
            self._show_toast("Light theme applied")
        else:
            self.setStyleSheet(f"QWidget {{ background: {C_BG}; color: {C_TEXT}; }}")
            self._show_toast("Dark theme applied")

    # ── Update Handlers ──────────────────────────────────────────────────────
    def _on_update_status(self, text: str, available: bool):
        self.update_btn.setText(text)
        if available:
            self.update_btn.setEnabled(True)
            self.update_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0,255,195,0.15);
                    color: {C_ACCENT};
                    border: 1px solid rgba(0,255,195,0.4);
                    border-radius: 8px;
                    padding: 10px 22px;
                    font-size: 13px;
                    font-weight: bold;
                    font-family: 'Segoe UI';
                }}
                QPushButton:hover {{ background: rgba(0,255,195,0.22); }}
            """)
            self.update_status_lbl.setText("New version available on GitHub")
            self.update_status_lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 12px; font-family: 'Segoe UI';")
        else:
            self.update_btn.setEnabled(False)
            self.update_btn.setStyleSheet(make_btn("", "ghost").styleSheet())
            self.update_status_lbl.setText("Your build is current")
            self.update_status_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 12px; font-family: 'Segoe UI';")

    def _on_update_clicked(self):
        self.update_btn.setText("⟳  Updating…")
        self.update_btn.setEnabled(False)
        self.update_status_lbl.setText("Stashing local changes and pulling…")
        self.update_worker.perform_update()

    def _on_update_complete(self, success: bool, message: str):
        self._show_toast(message, duration=5000)
        if success:
            self.update_btn.setText("✓  Restart Required")
            self.update_status_lbl.setText(message)
            self.update_status_lbl.setStyleSheet(f"color: {C_ACCENT}; font-size: 12px; font-family: 'Segoe UI';")
        else:
            self.update_btn.setText("✕  Update Failed")
            self.update_btn.setEnabled(True)
            self.update_status_lbl.setText(message)
            self.update_status_lbl.setStyleSheet(f"color: {C_DANGER}; font-size: 12px; font-family: 'Segoe UI';")

    # ── Toast ────────────────────────────────────────────────────────────────
    def _show_toast(self, message: str, duration: int = 3000):
        toast = Toast(message, self, duration)
        toast.move(self.geometry().x() + self.width() - toast.width() - 24,
                   self.geometry().y() + self.height() - toast.height() - 24)
        toast.show()

    # ── Keyboard shortcuts ───────────────────────────────────────────────────
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_L:
                self._toggle_listening()
            elif event.key() == Qt.Key_M:
                self.mic_btn.click()
            elif event.key() == Qt.Key_1:
                self.sidenav._select(0)
            elif event.key() == Qt.Key_2:
                self.sidenav._select(1)
            elif event.key() == Qt.Key_3:
                self.sidenav._select(2)
            elif event.key() == Qt.Key_4:
                self.sidenav._select(3)
        super().keyPressEvent(event)


# ── Onboarding Dialog ──────────────────────────────────────────────────────────
class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to MIA")
        self.setFixedSize(480, 380)
        self.setStyleSheet(f"""
            QDialog {{
                background: {C_SURFACE2};
                border: 1px solid {C_BORDER};
                border-radius: 16px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)

        lbl_title = QLabel("Welcome to MIA ✦")
        lbl_title.setStyleSheet(f"color: {C_ACCENT}; font-size: 24px; font-weight: bold; font-family: 'Segoe UI';")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Your intelligent local desktop assistant")
        lbl_sub.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 13px; font-family: 'Segoe UI';")
        lbl_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_sub)

        layout.addSpacing(12)

        tips = [
            ("🏠", "Home",     "Start/stop MIA, monitor CPU & RAM"),
            ("🎙️", "Commands", "Voice commands, quick actions, search"),
            ("⚙️", "Settings", "Personality, privacy, and updates"),
            ("ℹ️", "About",   "Component health checks"),
        ]
        for icon, name, desc in tips:
            row = QHBoxLayout()
            row.setSpacing(12)
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 18px;")
            ic.setFixedWidth(28)
            row.addWidget(ic)
            txt = QLabel(f"<b style='color:{C_ACCENT};'>{name}</b> — {desc}")
            txt.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-family: 'Segoe UI';")
            row.addWidget(txt)
            layout.addLayout(row)

        layout.addStretch()
        ok_btn = make_btn("Get Started", "primary")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignCenter)


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI", 10))

    first_run_flag = os.path.join(os.path.dirname(__file__), '.mia_first_run')
    if not os.path.exists(first_run_flag):
        dlg = OnboardingDialog()
        dlg.exec_()
        with open(first_run_flag, 'w') as f:
            f.write('1')

    window = NeonMainWindow()
    window.show()
    sys.exit(app.exec_())
