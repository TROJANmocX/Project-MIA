import pyttsx3
import threading
import queue

engine = pyttsx3.init()
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)

PERSONALITIES = {
    "calm":    {"rate": 150, "pre": "Okay,", "post": "", "voice": 1},
    "witty":   {"rate": 180, "pre": "Here's a thought:", "post": "😉", "voice": 1},
    "sarcastic": {"rate": 170, "pre": "Oh, really?", "post": "Sure thing...", "voice": 0},
    "bold":    {"rate": 200, "pre": "Let's do it!", "post": "!", "voice": 1},
}

tts_queue = queue.Queue()

def tts_worker():
    while True:
        message, mood = tts_queue.get()
        if message is None:
            break
        settings = PERSONALITIES.get(mood, PERSONALITIES["calm"])
        engine.setProperty('rate', settings["rate"])
        if voices and 0 <= settings["voice"] < len(voices):
            engine.setProperty('voice', voices[settings["voice"]].id)
        full_message = f'{settings["pre"]} {message} {settings["post"]}'
        engine.say(full_message)
        engine.runAndWait()
        tts_queue.task_done()

def speak(message="Hello, I am MIA.", mood="calm"):
    tts_queue.put((message, mood))

# Start the TTS worker thread at import time
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()
