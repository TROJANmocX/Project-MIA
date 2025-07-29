import threading
import subprocess
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from pystray import Icon, Menu, MenuItem
from PIL import Image

# --- Process management ---
processes = []

project_root = os.path.abspath(os.path.dirname(__file__))

def run_api():
    p = subprocess.Popen([sys.executable, "-m", "uvicorn", "server.api:app", "--reload"], cwd=project_root)
    processes.append(p)

def run_voice():
    p = subprocess.Popen([sys.executable, "mia_assistant/voice_activation.py"], cwd=project_root)
    processes.append(p)

def run_gesture():
    p = subprocess.Popen([sys.executable, "gesture_control/main.py"], cwd=project_root)
    processes.append(p)

def on_quit(icon, item):
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    icon.stop()
    sys.exit(0)

def main():
    # Start all modules in background threads
    threading.Thread(target=run_api, daemon=True).start()
    threading.Thread(target=run_voice, daemon=True).start()
    threading.Thread(target=run_gesture, daemon=True).start()

    # Tray icon with custom image
    import os
    icon_path = os.path.join(os.path.dirname(__file__), "mia_icon.png")
    try:
        image = Image.open(icon_path)
    except Exception:
        image = Image.new('RGB', (64, 64), color=(0, 128, 255))
    menu = Menu(MenuItem('Settings', lambda icon, item: open_settings()), MenuItem('Quit', on_quit))
    icon = Icon("MIA", image, "MIA Assistant", menu)
    icon.run()

# Settings window stub (PyQt5)
def open_settings():
    try:
        from PyQt5.QtWidgets import QApplication, QWidget, QLabel
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        w = QWidget()
        w.setWindowTitle('MIA Settings')
        w.setGeometry(100, 100, 300, 200)
        label = QLabel('Settings window (privacy, hotkeys, etc.)', w)
        label.move(20, 80)
        w.show()
        app.exec_()
    except Exception as e:
        print(f"Settings window error: {e}")

if __name__ == "__main__":
    main()
