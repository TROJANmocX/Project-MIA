"""HUD overlay with safe fallback when OpenCV/NumPy is unavailable."""

import threading
import queue
import time

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    CV2_AVAILABLE = True
except Exception:
    cv2 = None  # type: ignore
    np = None  # type: ignore
    CV2_AVAILABLE = False

# Queue for overlay messages
overlay_queue = queue.Queue()

def overlay_display_loop():
    if not CV2_AVAILABLE:
        # Fallback: just drain and print messages
        while True:
            message = overlay_queue.get()
            if message is None:
                break
            print(f"[HUD] {message}")
            overlay_queue.task_done()
        return

    while True:
        message = overlay_queue.get()  # Blocks until a message is available
        if message is None:
            break  # Allows for clean shutdown if needed
        overlay = np.zeros((300, 600, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (0, 255, 0)
        lower = message.lower()
        if "error" in lower or "sorry" in lower:
            color = (0, 0, 255)
        elif "activated" in lower:
            color = (255, 255, 0)
        elif "weather" in lower:
            color = (255, 128, 0)
        cv2.putText(overlay, message, (50, 150), font, 1, color, 2, cv2.LINE_AA)
        cv2.imshow("MIA HUD", overlay)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()
        overlay_queue.task_done()

def display_message(message="Screenshot Taken"):
    overlay_queue.put(message)

# Start the display thread at import time
display_thread = threading.Thread(target=overlay_display_loop, daemon=True)
display_thread.start()

if __name__ == "__main__":
    display_message("Test Overlay")
    time.sleep(1)
