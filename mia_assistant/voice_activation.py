import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import speech_recognition as sr
import threading
import time
import requests
from mia_assistant.combo_controller import combo_controller

API_URL = "http://127.0.0.1:8000/voice_command"
WAKE_WORD = "hey mia"

# Listen for voice commands during combo mode
def listen_for_commands(duration=30):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    end_time = time.time() + duration
    print("Combo mode: Listening for voice commands...")
    while time.time() < end_time and combo_controller.active:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening for command...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"You said: {command}")
            # Send to API for intent parsing and action
            resp = requests.post(API_URL, json={"text": command})
            print(f"API response: {resp.json()}")
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
        except Exception as e:
            print(f"Error: {e}")

# Main loop: listen for wake word, then enter combo mode
def listen_for_wake_word(wake_word=WAKE_WORD):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print(f"Listening for wake word: '{wake_word}'...")
    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"Heard: {command}")
            if wake_word in command:
                print("Wake word detected! Activating combo mode.")
                combo_controller.activate()
                # Start a thread to listen for commands during combo mode
                threading.Thread(target=listen_for_commands, args=(combo_controller.duration,), daemon=True).start()
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    listen_for_wake_word()
