import os
import shutil
import subprocess
import pyautogui
import platform
import webbrowser

def launch_app(app_name: str) -> str:
    """Launch an application by name or path across OSes."""
    try:
        system_name = platform.system()
        if system_name == "Windows":
            # If it's an absolute/relative path, try startfile first
            if os.path.exists(app_name):
                os.startfile(app_name)
                return f"Opened {app_name}."
            # If it's on PATH, use start via cmd to resolve properly
            exe = shutil.which(app_name) or shutil.which(f"{app_name}.exe")
            if exe:
                subprocess.Popen([exe])
                return f"Opened {app_name}."
            # Fallback to shell 'start' (lets Windows resolve installed apps)
            subprocess.Popen(["cmd", "/c", "start", "", app_name], shell=True)
            return f"Opened {app_name}."
        elif system_name == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app_name])
            return f"Opened {app_name}."
        else:  # Linux
            exe = shutil.which(app_name)
            if exe:
                subprocess.Popen([exe])
                return f"Opened {app_name}."
            subprocess.Popen(app_name, shell=True)
            return f"Opened {app_name}."
    except Exception as e:
        return f"Could not open {app_name}: {e}"

def take_screenshot():
    """Takes a screenshot."""
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        return f"Screenshot taken and saved as {filename}."
    except Exception as e:
        # Fallback using Pillow's ImageGrab
        try:
            from PIL import ImageGrab
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            img = ImageGrab.grab()
            img.save(filename)
            return f"Screenshot taken and saved as {filename}."
        except Exception as e2:
            return f"Could not take screenshot: {e2}"

def change_volume(direction):
    """Changes the system volume."""
    try:
        if direction == "up":
            pyautogui.press("volumeup")
            return "Volume increased."
        elif direction == "down":
            pyautogui.press("volumedown")
            return "Volume decreased."
        else:
            return "Invalid volume direction."
    except Exception as e:
        return f"Could not change volume: {e}"

def search_web(query: str) -> str:
    if not query:
        return "What should I search for?"
    try:
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Searching for {query}."
    except Exception as e:
        return f"Could not open browser: {e}"

def mouse_click():
    """Performs a mouse click."""
    try:
        pyautogui.click()
        return "Clicked."
    except Exception as e:
        return f"Could not click: {e}"

def mouse_scroll(amount):
    """Scrolls the mouse."""
    try:
        pyautogui.scroll(amount)
        return "Scrolled."
    except Exception as e:
        return f"Could not scroll: {e}"

def set_brightness(level: int) -> str:
    """Set screen brightness using Windows WMI via PowerShell."""
    try:
        system_name = platform.system()
        if system_name == "Windows":
            level = max(0, min(100, int(level)))
            cmd = f"powershell -Command \"(Get-WmiObject -Namespace root/WMINet_Write -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})\""
            subprocess.Popen(cmd, shell=True)
            return f"Brightness set to {level}%."
        return "Brightness control only supported on Windows."
    except Exception as e:
        return f"Could not set brightness: {e}"

def lock_pc() -> str:
    """Lock the Windows workstation."""
    try:
        system_name = platform.system()
        if system_name == "Windows":
            subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
            return "PC locked."
        return "Lock PC only supported on Windows."
    except Exception as e:
        return f"Could not lock PC: {e}"

def sleep_pc() -> str:
    """Put the PC to sleep."""
    try:
        system_name = platform.system()
        if system_name == "Windows":
            subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "PC entering sleep mode."
        return "Sleep PC only supported on Windows."
    except Exception as e:
        return f"Could not sleep PC: {e}"

def execute_action(parsed_command):
    """Executes the action based on the parsed command."""
    intent = parsed_command.get("intent")
    if intent == "launch_app":
        app = parsed_command.get("app")
        if app:
            return launch_app(app)
    elif intent == "take_screenshot":
        return take_screenshot()
    elif intent == "change_volume":
        direction = parsed_command.get("direction")
        if direction:
            return change_volume(direction)
    elif intent == "set_brightness":
        level = parsed_command.get("level", 50)
        return set_brightness(level)
    elif intent == "lock_pc":
        return lock_pc()
    elif intent == "sleep_pc":
        return sleep_pc()
    elif intent == "search_web":
        return search_web(parsed_command.get("query", ""))
    elif intent == "mouse_click":
        return mouse_click()
    elif intent == "mouse_scroll":
        amount = parsed_command.get("amount", 0)
        return mouse_scroll(amount)
    return "Unknown action."
