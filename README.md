# MIA – My Intelligent Assistant

A futuristic AI-powered desktop assistant blending gesture control, voice commands, and visual overlays for a smart, immersive user experience.

## Features
- Wake word activation ("Hey MIA")
- Combo mode: simultaneous voice + gesture input
- TTS with personality (calm, witty, sarcastic, bold)
- HUD overlay with thread-safe queue
- MediaPipe-based gesture control
- Modular command parser
- App launching, weather info, and more
- Mood/environment awareness (stub)

## Modules
- `server/api.py` – FastAPI server, central router
- `mia_assistant/tts_response.py` – TTS with personality
- `mia_assistant/hud_overlay.py` – Visual feedback overlay
- `mia_assistant/combo_controller.py` – Combo mode state/timer
- `mia_assistant/command_parser.py` – Intent extraction
- `mia_assistant/voice_activation.py` – Wake word + voice input
- `gesture_control/main.py` – Gesture recognition (MediaPipe)
- `mia_assistant/mood_detection.py` – Mood detection stub

## How to Run
1. Install dependencies:
   ```sh
   pip install fastapi uvicorn opencv-python numpy pyttsx3 SpeechRecognition pyaudio requests mediapipe textblob pystray pillow PyQt5 deepface
   ```
2. Place your custom icon as `mia_icon.png` in the project root (optional).
3. Start the all-in-one app:
   ```sh
   python mia_launcher.py
   ```
   - MIA will run in the system tray. Right-click for settings or to quit.

## Packaging (Windows)
- Install PyInstaller: `pip install pyinstaller`
- Build: `pyinstaller --onefile --add-data "mia_icon.png;." mia_launcher.py`
- Find your `.exe` in the `dist/` folder.

## Extending MIA
- Add new commands/intents in `command_parser.py`
- Add new gestures in `gesture_control/main.py`
- Integrate real mood detection in `mood_detection.py`
- Expand app launching in `api.py`
- Add settings/privacy controls in `settings.py`

## Security & Privacy
- All processing is local by default
- No voice or gesture data leaves your machine
- Settings allow you to mute mic/camera and control privacy

## Upcoming Features
- Adaptive UI based on mood
- Contextual voice replies
- Smart room/environment detection
- Mood-based desktop themes
- AI-driven app suggestions
- Personality selector GUI

## Privacy & Security
- Everything is processed locally
- No data sent to the cloud
- Mic and cam can be toggled from system tray

### 🛠️ File Reference Table

| 📌 Action                      | 🗂️ File to Edit                        |
|-------------------------------|----------------------------------------|
| Add voice commands            | `mia_assistant/command_parser.py`      |
| Add gestures (scroll, click)  | `gesture_control/main.py`              |
| New personality styles        | `mia_assistant/tts_response.py`        |
| Extend API actions            | `server/api.py`                        |
| Add smart overlay visuals     | `mia_assistant/hud_overlay.py`         |


## Developer Notes
This assistant is modular. You can:
- Replace MediaPipe with LeapMotion or webcam-free input
- Add OpenAI integration for smarter replies
- Build plugin modules for more gestures or voice actions
