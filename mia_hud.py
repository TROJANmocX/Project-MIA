import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSystemTrayIcon, QMenu, QAction, QDialog, QGridLayout)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QRectF
import os

ASSETS = os.path.join(os.path.dirname(__file__), 'ui_assets')

class NeonRing(QWidget):
    def __init__(self, color='#00ffc3', thickness=8, parent=None):
        super().__init__(parent)
        self.color = color
        self.thickness = thickness
        self.setMinimumSize(200, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.thickness, self.thickness, self.width()-2*self.thickness, self.height()-2*self.thickness)
        pen = painter.pen()
        pen.setColor(QColor(self.color))
        pen.setWidth(self.thickness)
        painter.setPen(pen)
        painter.drawEllipse(rect)

class HUDOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        # Neon ring
        self.ring = NeonRing()
        layout.addWidget(self.ring, alignment=Qt.AlignCenter)
        # Status label
        self.status = QLabel('Listening...')
        self.status.setStyleSheet('color: #00ffc3; font-size: 20px; font-weight: bold;')
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        # Quick actions
        btn_layout = QHBoxLayout()
        self.mute_btn = QPushButton('Mute')
        self.mute_btn.setStyleSheet('background: #3f8cff; color: #fff; border-radius: 8px; padding: 8px 16px;')
        self.settings_btn = QPushButton('Settings')
        self.settings_btn.setStyleSheet('background: #00ffc3; color: #0d0d0d; border-radius: 8px; padding: 8px 16px;')
        btn_layout.addWidget(self.mute_btn)
        btn_layout.addWidget(self.settings_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

class ComboModeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Combo Mode')
        self.setStyleSheet('background: #181828; color: #fff;')
        self.setFixedSize(420, 320)
        layout = QVBoxLayout()
        self.timer_label = QLabel('30')
        self.timer_label.setStyleSheet('font-size: 48px; color: #00ffc3;')
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)
        # Voice and gesture panels
        panel_layout = QHBoxLayout()
        self.voice_panel = QLabel('Voice: ...')
        self.voice_panel.setStyleSheet('background: #222; border: 1.5px solid #00ffc3; border-radius: 12px; padding: 16px;')
        self.gesture_panel = QLabel('Gesture: ...')
        self.gesture_panel.setStyleSheet('background: #222; border: 1.5px solid #3f8cff; border-radius: 12px; padding: 16px;')
        panel_layout.addWidget(self.voice_panel)
        panel_layout.addWidget(self.gesture_panel)
        layout.addLayout(panel_layout)
        self.setLayout(layout)
        # Timer
        self.time_left = 30
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        self.timer_label.setText(str(self.time_left))
        if self.time_left <= 0:
            self.timer.stop()
            self.accept()

class PersonalitySelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Select Personality')
        self.setStyleSheet('background: #181828; color: #fff;')
        self.setFixedSize(420, 320)
        layout = QGridLayout()
        avatars = ['calm_face.png', 'witty_face.png', 'sarcastic_face.png']
        names = ['Calm', 'Witty', 'Sarcastic']
        descs = ['Soothing and friendly', 'Playful and clever', 'Dry and sharp']
        for i, (avatar, name, desc) in enumerate(zip(avatars, names, descs)):
            vbox = QVBoxLayout()
            img = QLabel()
            img.setPixmap(QPixmap(os.path.join(ASSETS, 'avatars', avatar)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img.setAlignment(Qt.AlignCenter)
            vbox.addWidget(img)
            label = QLabel(name)
            label.setStyleSheet('color: #00ffc3; font-size: 18px;')
            label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)
            desc_label = QLabel(desc)
            desc_label.setStyleSheet('color: #aaaaaa; font-size: 12px;')
            desc_label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(desc_label)
            layout.addLayout(vbox, 0, i)
        self.setLayout(layout)

class SystemTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(QIcon(os.path.join(ASSETS, 'logo.svg')), parent)
        menu = QMenu()
        dashboard = QAction('Open Dashboard')
        mute_mic = QAction('Mute Microphone')
        mute_cam = QAction('Mute Camera')
        change_personality = QAction('Change Personality')
        settings = QAction('Settings')
        quit_action = QAction('Quit MIA')
        menu.addAction(dashboard)
        menu.addAction(mute_mic)
        menu.addAction(mute_cam)
        menu.addAction(change_personality)
        menu.addAction(settings)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    hud = HUDOverlay()
    tray = SystemTray()
    tray.show()
    hud.show()
    sys.exit(app.exec_())
