import speech_recognition as sr
import requests

API_URL = "http://127.0.0.1:8000/gesture"

# Map spoken phrases to gestures
COMMANDS = {
    "screenshot": "screenshot",
    "take screenshot": "screenshot",
    "volume up": "volume_up",
    "increase volume": "volume_up",
    "volume down": "volume_down",
    "decrease volume": "volume_down",
}

def send_gesture(gesture):
    try:
        resp = requests.post(API_URL, json={"gesture": gesture})
        print(f"Sent gesture: {gesture}, Response: {resp.json()}")
    except Exception as e:
        print(f"Failed to send gesture: {e}")

def listen_and_process():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("🎤 Voice control started. Say a command...")

    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"You said: {command}")
            for phrase, gesture in COMMANDS.items():
                if phrase in command:
                    send_gesture(gesture)
                    break
            else:
                print("Command not recognized.")
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    listen_and_process()
