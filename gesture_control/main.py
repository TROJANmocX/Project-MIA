# gesture_control/main.py
"""
MediaPipe-based gesture recognition for MIA
Maps gestures to actions and sends them to the FastAPI /gesture endpoint.
"""
import cv2
import mediapipe as mp
import requests
import time
import math

API_URL = "http://127.0.0.1:8000/gesture"

# Gesture mapping
GESTURE_ACTIONS = {
    "fist": "volume_down",
    "open_palm": "screenshot",
    "swipe_left": "switch_window",
    "swipe_right": "refresh",
    # Add more mappings as needed
}

def send_gesture(gesture):
    try:
        resp = requests.post(API_URL, json={"gesture": gesture})
        print(f"Sent gesture: {gesture}, Response: {resp.json()}")
    except Exception as e:
        print(f"Failed to send gesture: {e}")

def detect_gestures():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    cap = cv2.VideoCapture(0)
    last_gesture = None
    last_time = 0
    print("🖐️ Gesture control started. Show gestures to the camera.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        gesture = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get landmark positions
                lm = hand_landmarks.landmark
                # Simple open palm detection: distance between thumb tip and pinky tip
                thumb_tip = lm[4]
                pinky_tip = lm[20]
                palm_distance = math.hypot(thumb_tip.x - pinky_tip.x, thumb_tip.y - pinky_tip.y)
                # Fist detection: distance between index tip and palm base
                index_tip = lm[8]
                wrist = lm[0]
                fist_distance = math.hypot(index_tip.x - wrist.x, index_tip.y - wrist.y)
                if palm_distance > 0.4:
                    gesture = "open_palm"
                elif fist_distance < 0.15:
                    gesture = "fist"
                # TODO: Add swipe detection, cursor, etc.
        if gesture and (gesture != last_gesture or time.time() - last_time > 2):
            send_gesture(GESTURE_ACTIONS.get(gesture, gesture))
            last_gesture = gesture
            last_time = time.time()
        cv2.imshow("MIA Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_gestures()
