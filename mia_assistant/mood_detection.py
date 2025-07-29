# mia_assistant/mood_detection.py
"""
Webcam mood detection using DeepFace (stub).
"""
def detect_webcam_mood():
    try:
        from deepface import DeepFace
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return "calm"
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion = result['dominant_emotion']
        if emotion in ["happy", "surprise"]:
            return "bold"
        elif emotion in ["angry", "disgust", "fear", "sad"]:
            return "sarcastic"
        else:
            return "calm"
    except Exception as e:
        print(f"Webcam mood detection error: {e}")
        return "calm"
