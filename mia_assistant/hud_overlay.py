# mia_assistant/hud_overlay.py

import cv2
import numpy as np
import threading
import queue
import time

# Queue for overlay messages
overlay_queue = queue.Queue()

# Display thread function
def overlay_display_loop():
    while True:
        message = overlay_queue.get()  # Blocks until a message is available
        if message is None:
            break  # Allows for clean shutdown if needed
        # Create black image
        overlay = np.zeros((300, 600, 3), dtype=np.uint8)
        # Display message with color/mood (simple color logic)
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (0, 255, 0)
        if "error" in message.lower() or "sorry" in message.lower():
            color = (0, 0, 255)
        elif "activated" in message.lower():
            color = (255, 255, 0)
        elif "weather" in message.lower():
            color = (255, 128, 0)
        cv2.putText(overlay, message, (50, 150), font, 1, color, 2, cv2.LINE_AA)
        # Show window
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
    time.sleep(3)  # Give time for the overlay to show before script exits
