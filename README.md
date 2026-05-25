# MIA – My Intelligent Assistant

A futuristic AI-powered desktop assistant blending gesture control, voice commands, visual overlays, and personality-driven interactions for a smart, immersive user experience.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running MIA](#running-mia)
- [Modules](#modules)
  - [Core Modules](#core-modules)
  - [UI & HUD](#ui--hud)
  - [AI & LLM Integration](#ai--llm-integration)
- [Extending MIA](#extending-mia)
- [Security & Privacy](#security--privacy)
- [Upcoming Features](#upcoming-features)
- [Developer Notes](#developer-notes)

---

## Features

MIA combines cutting-edge technologies to deliver a seamless, intuitive desktop assistant experience:

- **Wake Word Activation**: Always listening for "Hey MIA" to activate
- **Dual Input Mode**: Control via voice commands or MediaPipe-powered gesture recognition
- **Combo Mode**: Simultaneous voice + gesture input for advanced interactions
- **Personality-Driven TTS**: Text-to-Speech with multiple personality styles (calm, witty, sarcastic, bold)
- **HUD Overlay**: Visual feedback overlay with thread-safe queue system
- **App Launching**: Open apps like YouTube, VSCode, Spotify, etc., via voice or gesture
- **Weather Information**: Fetch real-time weather data (requires OpenWeatherMap API key)
- **Screenshot Capture**: Take screenshots with a simple gesture or voice command
- **Volume Control**: Adjust system volume using voice or gestures
- **Mood Awareness**: Sentiment-based mood detection (TextBlob) for adaptive responses
- **Local Processing**: All voice/gesture processing runs locally by default

---

## Architecture

MIA follows a modular, service-oriented architecture:

```
┌─────────────────┐     ┌───────────────┐     ┌─────────────────┐
│  Voice Input    │     │  Gesture Input│     │   HUD Overlay   │
│ (mic + STT)     │────▶│  FastAPI      │◀────│ (Visual Feedbk) │
└─────────────────┘     └───────┬───────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Command Router │
                         └───────┬─────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TTS Engine    │    │   Action Exec   │    │   LLM Engine    │
│ (Personality)   │    │ (Apps, System)  │    │ (Ollama, etc.)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Project Structure

```
PROJECT - MIA/
├── ar_ui/                      # AR UI prototype (HTML/CSS/JS)
├── gesture_control/            # MediaPipe-based gesture recognition
│   ├── main.py                 # Gesture detection & API client
│   └── requirements.txt        # Gesture module dependencies
├── mia/                        # Core MIA system (newer architecture)
│   ├── audio/                  # Audio processing (STT, wake word)
│   ├── core/                   # Command routing & execution
│   ├── hud/                    # HUD window & state management
│   ├── llm/                    # LLM integration (Canary, emotion)
│   └── tts/                    # Text-to-speech
├── mia_assistant/              # Legacy assistant modules (stable)
│   ├── actions.py              # Action execution logic
│   ├── agent.py                # Planner/agent system
│   ├── combo_controller.py     # Combo mode state machine
│   ├── command_parser.py       # Intent extraction
│   ├── hud_overlay.py          # HUD overlay UI
│   ├── mood_detection.py       # Mood detection stub
│   ├── ollama_client.py        # Ollama LLM client
│   ├── tts_response.py         # TTS with personality
│   └── voice_activation.py     # Wake word & voice input
├── server/                      # FastAPI backend
│   ├── api.py                  # REST API endpoints
│   └── test_api.py             # API tests
├── tests/                       # Test suite
├── ui_assets/                   # UI resources (avatars, icons, etc.)
│   ├── avatars/                 # Personality avatars
│   ├── gestures/                # Gesture icons
│   └── hud/                     # HUD assets
├── venv/                        # Virtual environment (gitignored)
├── .gitignore
├── README.md                    # This file
├── requirements.txt             # Project dependencies
├── mia_launcher.py              # Main entry point (system tray)
└── Launch_MIA.bat               # Windows batch launcher
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Webcam (for gesture recognition)
- Microphone (for voice commands)
- Optional: Ollama (for LLM integration)

### Installation

1. **Clone the repository**
   ```sh
   git clone <repo-url>
   cd "PROJECT - MIA"
   ```

2. **Create a virtual environment**
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

   > Note: The requirements.txt may have merge conflicts - resolve them or install manually:
   ```sh
   pip install fastapi uvicorn opencv-python numpy pyttsx3 SpeechRecognition pyaudio requests mediapipe textblob pystray pillow PyQt5 deepface
   ```

4. **(Optional) Configure API keys**
   - For weather: Open `server/api.py` and set `WEATHER_API_KEY` to your OpenWeatherMap API key
   - For LLM: Install Ollama and pull a model (e.g., `ollama pull llama3`)

### Running MIA

**Windows (easy way):**
Double-click `Launch_MIA.bat`

**Manual launch:**
```sh
python mia_launcher.py
```

MIA will:
- Start the FastAPI server in the background
- Launch gesture recognition
- Start voice activation
- Show a system tray icon (right-click to quit)

---

## Modules

### Core Modules

#### server/api.py
- FastAPI backend with CORS enabled
- Endpoints:
  - `/gesture`: Receives gesture input
  - `/voice_command`: Receives voice commands
  - `/inference`: Unified inference endpoint (LLM planner)

#### mia_assistant/command_parser.py
- Intent extraction from natural language
- Sentiment analysis (TextBlob) for mood detection
- Maps commands to intents (e.g., "open youtube" → launch_app)

#### gesture_control/main.py
- MediaPipe Hands integration for gesture recognition
- Detects:
  - Open palm (screenshot)
  - Fist (volume down)
  - (More gestures can be added)
- Sends gestures to `/gesture` API endpoint

### UI & HUD

#### mia_assistant/hud_overlay.py
- Visual feedback overlay using PyQt5
- Thread-safe message queue
- Displays:
  - Speech bubbles
  - Notifications
  - Combo mode timer ring

### AI & LLM Integration

#### mia_assistant/ollama_client.py
- Client for Ollama LLM
- Personality-driven responses
- Fallback to classic parser if LLM fails

#### mia_assistant/agent.py
- Planner/agent system for complex tasks
- Multi-step action planning

---

## Extending MIA

MIA is designed to be highly modular and extensible:

### Add New Voice Commands
Edit `mia_assistant/command_parser.py` and add new intent patterns.

### Add New Gestures
1. Edit `gesture_control/main.py` to detect the new gesture
2. Add mapping in `GESTURE_ACTIONS`
3. Handle the action in `server/api.py`

### Add New Personalities
Edit `mia_assistant/tts_response.py` and add new personality styles.

### Add New Apps to Launch
Edit `server/api.py` and add new target apps in the `open_app` action.

---

## Security & Privacy

- **Local Processing**: All voice and gesture processing runs locally by default
- **No Data Leaks**: No audio, video, or command data is sent to the cloud
- **Privacy Controls**: Mic and camera can be toggled (settings stub in system tray)
- **Optional LLM**: LLM integration is optional and configurable

---

## Upcoming Features

- [ ] Adaptive UI based on detected mood
- [ ] Contextual voice replies
- [ ] Smart room/environment detection
- [ ] Mood-based desktop themes
- [ ] AI-driven app suggestions
- [ ] Personality selector GUI
- [ ] Plugin system for third-party extensions
- [ ] Cross-platform support (macOS, Linux)

---

## Developer Notes

### Tech Stack
- **Backend**: FastAPI, Uvicorn
- **Computer Vision**: OpenCV, MediaPipe
- **Audio**: SpeechRecognition, pyttsx3, sounddevice, librosa
- **UI**: PyQt5, PySide6
- **AI/ML**: TextBlob, Transformers, Ollama (optional)
- **System Tray**: pystray

### Architecture Patterns
- Modular design for easy replacement of components
- Thread-safe queues for inter-process communication
- Service-oriented with REST API
- Fallback mechanisms for reliability

### Replaceable Components
- Swap MediaPipe for Leap Motion or other input devices
- Replace pyttsx3 with ElevenLabs or other TTS services
- Add OpenAI/Claude API integration for smarter replies
- Build plugin modules for custom gestures or voice actions

---

### 🛠️ Quick Reference Table

| 📌 Action                      | 🗂️ File to Edit                        |
|-------------------------------|----------------------------------------|
| Add voice commands            | `mia_assistant/command_parser.py`      |
| Add gestures                  | `gesture_control/main.py`              |
| New personality styles        | `mia_assistant/tts_response.py`        |
| Extend API actions            | `server/api.py`                        |
| Add smart overlay visuals     | `mia_assistant/hud_overlay.py`         |
| LLM integration               | `mia_assistant/ollama_client.py`       |

---

## License

This project is for educational and personal use.
