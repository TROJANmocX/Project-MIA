# mia_assistant/mood_detection.py
"""
Webcam mood detection. Runs as a persistent subprocess.
Requires: deepface, opencv-python
Falls back gracefully if either is unavailable.
"""
import time
import sys

def detect_webcam_mood() -> str:
    """Capture one frame and return a personality string."""
    try:
        from deepface import DeepFace
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return "calm"
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        # DeepFace can return a list or dict depending on version
        if isinstance(result, list):
            result = result[0]
        emotion = result.get('dominant_emotion', 'neutral')
        if emotion in ["happy", "surprise"]:
            return "bold"
        elif emotion in ["angry", "disgust", "fear", "sad"]:
            return "sarcastic"
        else:
            return "calm"
    except ImportError:
        return "calm"
    except Exception as e:
        print(f"[MoodDetection] Error: {e}", flush=True)
        return "calm"


def run_loop(interval: int = 10):
    """Persistent loop — detects mood every `interval` seconds."""
    print("[MoodDetection] Starting mood detection loop...", flush=True)
    while True:
        mood = detect_webcam_mood()
        print(f"[MoodDetection] Detected mood -> personality: {mood}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_loop(interval)
