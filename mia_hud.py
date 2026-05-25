import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSystemTrayIcon, QMenu, QAction, QDialog, QGridLayout
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer, QRectF

ASSETS = os.path.join(os.path.dirname(__file__), 'ui_assets')

C_BG      = "#0a0a12"
C_SURFACE = "#11111e"
C_ACCENT  = "#00ffc3"
C_ACCENT2 = "#3f8cff"
C_BORDER  = "#1e1e35"
C_TEXT    = "#e8e8f0"
C_SUBTEXT = "#7878a0"


class NeonRing(QWidget):
    """Animated neon ring widget (pulsing + spinning arc when active)."""

    def __init__(self, color=C_ACCENT, thickness=8, parent=None):
        super().__init__(parent)
        self.color = color
        self.thickness = thickness
        self._angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1
        self._active = False
        self.setMinimumSize(200, 200)
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
        r = min(w, h) / 2 - self.thickness - 4

        # Glow layers
        glow_alpha = int(40 + 55 * self._pulse) if self._active else 18
        for gw in range(16, 0, -3):
            col = QColor(self.color)
            col.setAlpha(max(0, glow_alpha - gw * 3))
            pen = QPen(col, gw)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        # Base ring
        base = QColor(C_BORDER)
        painter.setPen(QPen(base, self.thickness))
        painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        # Spinning arc
        if self._active:
            arc_pen = QPen(QColor(self.color), self.thickness)
            arc_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r),
                            self._angle * 16, 120 * 16)
            arc_pen2 = QPen(QColor(C_ACCENT2), max(2, self.thickness - 2))
            arc_pen2.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen2)
            painter.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r),
                            (self._angle + 160) * 16, 60 * 16)
        else:
            idle = QColor(self.color)
            idle.setAlpha(70)
            painter.setPen(QPen(idle, 3))
            painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        painter.end()


class HUDOverlay(QWidget):
    """Minimal floating HUD overlay widget."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 320)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.ring = NeonRing()
        layout.addWidget(self.ring, alignment=Qt.AlignCenter)

        self.status = QLabel("Listening…")
        self.status.setStyleSheet(f"color: {C_ACCENT}; font-size: 16px; font-weight: bold; font-family: 'Segoe UI';")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        btn_row = QHBoxLayout()
        self.mute_btn = QPushButton("Mute")
        self.mute_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(63,140,255,0.18);
                color: {C_ACCENT2};
                border: 1px solid rgba(63,140,255,0.3);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: rgba(63,140,255,0.28); }}
        """)
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.06);
                color: {C_SUBTEXT};
                border: 1px solid {C_BORDER};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.10); }}
        """)
        self.close_btn.clicked.connect(self.hide)
        btn_row.addWidget(self.mute_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def set_status(self, text: str):
        self.status.setText(text)

    def set_active(self, active: bool):
        self.ring.set_active(active)


class ComboModeDialog(QDialog):
    """Floating combo-mode countdown dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Combo Mode")
        self.setStyleSheet(f"background: {C_SURFACE}; color: {C_TEXT}; border-radius: 16px;")
        self.setFixedSize(420, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        self.timer_label = QLabel("30")
        self.timer_label.setStyleSheet(f"font-size: 52px; font-weight: bold; color: {C_ACCENT}; font-family: 'Segoe UI';")
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        lbl_hint = QLabel("Speak your command…")
        lbl_hint.setStyleSheet(f"font-size: 14px; color: {C_SUBTEXT}; font-family: 'Segoe UI';")
        lbl_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_hint)

        panel_row = QHBoxLayout()
        self.voice_panel = QLabel("🎙️  Listening")
        self.voice_panel.setStyleSheet(f"background: rgba(0,255,195,0.08); border: 1px solid rgba(0,255,195,0.3); border-radius: 10px; padding: 10px 14px; color: {C_ACCENT}; font-size: 13px; font-family: 'Segoe UI';")
        self.gesture_panel = QLabel("✋  Ready")
        self.gesture_panel.setStyleSheet(f"background: rgba(63,140,255,0.08); border: 1px solid rgba(63,140,255,0.3); border-radius: 10px; padding: 10px 14px; color: {C_ACCENT2}; font-size: 13px; font-family: 'Segoe UI';")
        panel_row.addWidget(self.voice_panel)
        panel_row.addWidget(self.gesture_panel)
        layout.addLayout(panel_row)

        self.time_left = 30
        self._qt_timer = QTimer(self)
        self._qt_timer.timeout.connect(self._tick)
        self._qt_timer.start(1000)

    def _tick(self):
        self.time_left -= 1
        self.timer_label.setText(str(self.time_left))
        if self.time_left <= 0:
            self._qt_timer.stop()
            self.accept()

    def set_voice_text(self, text: str):
        self.voice_panel.setText(f"🎙️  {text}")

    def set_gesture_text(self, text: str):
        self.gesture_panel.setText(f"✋  {text}")


class PersonalitySelector(QDialog):
    """Grid dialog for picking TTS personality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Personality")
        self.setStyleSheet(f"background: {C_SURFACE}; color: {C_TEXT};")
        self.setFixedSize(480, 200)
        self.selected_personality = "calm"

        layout = QGridLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        personalities = [
            ("😌", "calm",      "Soothing & measured"),
            ("😄", "witty",     "Playful & clever"),
            ("😏", "sarcastic", "Dry & sharp"),
            ("💪", "bold",      "Confident & direct"),
        ]
        for i, (emoji, key, desc) in enumerate(personalities):
            card = QWidget()
            card.setStyleSheet(f"background: rgba(0,255,195,0.06); border: 1px solid rgba(0,255,195,0.2); border-radius: 10px;")
            card.setCursor(Qt.PointingHandCursor)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 10, 10, 10)
            cl.setSpacing(4)
            em = QLabel(emoji)
            em.setAlignment(Qt.AlignCenter)
            em.setStyleSheet("font-size: 24px;")
            cl.addWidget(em)
            nm = QLabel(key.capitalize())
            nm.setAlignment(Qt.AlignCenter)
            nm.setStyleSheet(f"color: {C_ACCENT}; font-size: 12px; font-weight: bold; font-family: 'Segoe UI';")
            cl.addWidget(nm)
            ds = QLabel(desc)
            ds.setAlignment(Qt.AlignCenter)
            ds.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 10px; font-family: 'Segoe UI';")
            cl.addWidget(ds)

            btn = QPushButton("Select")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C_ACCENT};
                    color: #0a0a12;
                    border: none;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-family: 'Segoe UI';
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: #00e6b0; }}
            """)
            btn.clicked.connect(lambda _, k=key: self._pick(k))
            cl.addWidget(btn)
            layout.addWidget(card, 0, i)

    def _pick(self, key: str):
        self.selected_personality = key
        self.accept()


class SystemTray(QSystemTrayIcon):
    """System tray icon with fully wired menu actions."""

    def __init__(self, main_window=None, parent=None):
        project_root = os.path.dirname(os.path.abspath(__file__))
        ico_new = os.path.join(project_root, 'mia_icon_new.ico')
        if os.path.exists(ico_new):
            icon = QIcon(ico_new)
        else:
            ico_path = os.path.join(ASSETS, 'logo.svg')
            icon = QIcon(ico_path) if os.path.exists(ico_path) else QIcon()
        super().__init__(icon, parent)
        self._main = main_window

        menu = QMenu()

        def add_action(label, callback=None):
            a = QAction(label)
            if callback:
                a.triggered.connect(callback)
            menu.addAction(a)
            return a

        add_action("Show MIA",       self._show)
        menu.addSeparator()
        add_action("Home",           lambda: self._goto(0))
        add_action("Commands",       lambda: self._goto(1))
        add_action("Settings",       lambda: self._goto(2))
        menu.addSeparator()
        add_action("Start MIA",      self._start)
        add_action("Stop MIA",       self._stop)
        menu.addSeparator()
        add_action("Quit MIA",       self._quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _show(self):
        if self._main:
            self._main.show()
            self._main.raise_()

    def _goto(self, idx: int):
        self._show()
        if self._main and hasattr(self._main, 'sidenav'):
            self._main.sidenav._select(idx)

    def _start(self):
        if self._main and hasattr(self._main, '_start_mia'):
            self._main._start_mia()

    def _stop(self):
        if self._main and hasattr(self._main, '_stop_mia'):
            self._main._stop_mia()

    def _quit(self):
        if self._main and hasattr(self._main, '_quit_app'):
            self._main._quit_app()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hud = HUDOverlay()
    hud.set_active(True)
    tray = SystemTray()
    tray.show()
    hud.show()
    sys.exit(app.exec_())
