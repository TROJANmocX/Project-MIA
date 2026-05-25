import threading
import time
from mia_assistant import tts_response, hud_overlay

class ComboModeController:
    def __init__(self):
        self.active = False
        self.timer = None
        self.duration = 30
        self.on_activate = None
        self.on_deactivate = None

    def activate(self, duration=None):
        if self.active:
            self.reset_timer(duration)
            return
        self.active = True
        if self.on_activate:
            self.on_activate()
        self.reset_timer(duration)

    def reset_timer(self, duration=None):
        if self.timer:
            self.timer.cancel()
        d = duration if duration is not None else self.duration
        self.timer = threading.Timer(d, self.deactivate)
        self.timer.start()

    def deactivate(self):
        self.active = False
        if self.on_deactivate:
            self.on_deactivate()


def combo_activated():
    tts_response.speak("Combo mode activated.", mood="bold")
    hud_overlay.display_message("Combo Mode Activated!")

def combo_deactivated():
    tts_response.speak("Combo mode ended.", mood="calm")
    hud_overlay.display_message("Combo Mode Ended")


combo_controller = ComboModeController()
combo_controller.on_activate = combo_activated
combo_controller.on_deactivate = combo_deactivated
