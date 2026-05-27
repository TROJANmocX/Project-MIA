# MIA -- My Intelligent Assistant

> A privacy-first, modular AI desktop assistant that combines voice commands, gesture recognition, LLM-powered intent parsing, and a neon-styled PyQt5 control center -- all running locally on your machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-00ffc3.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3f8cff.svg)](https://python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-00ffc3.svg)](CONTRIBUTING.md)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
  - [High-Level System Diagram](#high-level-system-diagram)
  - [Data Flow](#data-flow)
  - [Component Interaction Map](#component-interaction-map)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running MIA](#running-mia)
- [Module Reference](#module-reference)
  - [Desktop UI (mia_main.py)](#desktop-ui-mia_mainpy)
  - [Voice Pipeline](#voice-pipeline)
  - [Gesture Recognition](#gesture-recognition)
  - [Command Parsing and NLP](#command-parsing-and-nlp)
  - [LLM Integration](#llm-integration)
  - [Action Execution](#action-execution)
  - [HUD Overlay](#hud-overlay)
  - [TTS Engine](#tts-engine)
  - [Mood Detection](#mood-detection)
  - [Combo Mode](#combo-mode)
  - [FastAPI Server](#fastapi-server)
  - [Agent / Planner](#agent--planner)
- [How It Works -- End to End](#how-it-works----end-to-end)
- [Configuration](#configuration)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Extending MIA](#extending-mia)
- [Security and Privacy](#security-and-privacy)
- [Roadmap](#roadmap)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

MIA (My Intelligent Assistant) is a desktop AI assistant inspired by JARVIS. It listens for a configurable wake word, accepts voice commands or hand gestures via webcam, parses intent using NLP and optional local LLMs, executes system actions, and speaks responses back with personality-driven text-to-speech -- all without sending data to the cloud.

The project ships with two architectural layers:

1. **mia_assistant/** -- A stable, production-ready assistant module set with FastAPI server, voice activation, gesture control, TTS, HUD overlay, and command parsing.
2. **mia/** -- A newer, heavier architecture that integrates transformer-based intent parsing (Canary Engine), emotion detection, intent guarding, and a PySide6-based HUD. This layer is under active development.

Both layers share the same action execution and can run independently or together.

---

## Key Features

| Category            | Capability                                                                 |
|---------------------|---------------------------------------------------------------------------|
| Voice Control       | Wake word activation ("Hey MIA"), continuous listening, Google STT         |
| Gesture Control     | MediaPipe hand tracking -- open palm, fist, swipe detection               |
| Combo Mode          | Simultaneous voice + gesture input with a 30-second timed session         |
| LLM Integration     | Ollama (llama3) for chat, Canary Engine for structured intent extraction   |
| Personality TTS     | Four personalities: Calm, Witty, Sarcastic, Bold -- each with unique tone |
| Mood Detection      | DeepFace webcam emotion analysis maps to personality selection             |
| Desktop Control     | Launch apps, take screenshots, adjust volume/brightness, lock/sleep PC    |
| HUD Overlay         | OpenCV-based visual feedback overlay with color-coded messages            |
| Neon Control Center | Full PyQt5 GUI with animated rings, system stats, command center          |
| System Tray         | Background operation with tray icon, quick actions, and auto-update       |
| Auto-Update         | Git-based update checking and one-click pull from main branch             |
| Privacy-First       | All processing local by default -- no cloud data transmission             |

---

## Screenshots

The main UI is a dark, neon-themed control center with four pages:

- **Home** -- Animated neon ring, start/stop controls, CPU/RAM stats, component status
- **Commands** -- Live transcript, search bar, command history, system controls, app launchers, web quick-links
- **Settings** -- Personality selector, privacy toggles (mic/cam), theme switcher, wake word config, keyboard shortcuts, update manager
- **About** -- Version info, component health checks, build metadata

---

## Architecture

### High-Level System Diagram

```
+-----------------------------------------------------------------------+
|                           MIA DESKTOP APPLICATION                      |
|                                                                        |
|  +------------------+    +------------------+    +------------------+  |
|  |   PyQt5 Neon UI  |    |   System Tray    |    |  Onboarding      |  |
|  |   (mia_main.py)  |    |   (pystray)      |    |  Dialog          |  |
|  +--------+---------+    +--------+---------+    +------------------+  |
|           |                       |                                    |
|           +-----------+-----------+                                    |
|                       |                                                |
|                       v                                                |
|  +--------------------+-------------------+                            |
|  |           PROCESS MANAGER              |                            |
|  |  Spawns and manages child processes:   |                            |
|  |  - FastAPI Server                      |                            |
|  |  - Voice Activation                    |                            |
|  |  - Gesture Control                     |                            |
|  |  - Mood Detection                      |                            |
|  +--------------------+-------------------+                            |
|                       |                                                |
+-----------------------------------------------------------------------+
                        |
          +-------------+-------------+-------------+
          |             |             |             |
          v             v             v             v
   +-----------+  +-----------+  +-----------+  +-----------+
   | FastAPI   |  | Voice     |  | Gesture   |  | Mood      |
   | Server    |  | Activation|  | Control   |  | Detection |
   | :8000     |  | (STT)     |  | (MediaPipe)|  | (DeepFace)|
   +-----------+  +-----------+  +-----------+  +-----------+
        |              |              |              |
        +--------------+--------------+--------------+
                       |
                       v
              +------------------+
              |  Command Router  |
              |  (Intent Parse)  |
              +--------+---------+
                       |
         +-------------+-------------+
         |             |             |
         v             v             v
   +-----------+  +-----------+  +-----------+
   | Action    |  | TTS       |  | HUD       |
   | Executor  |  | Engine    |  | Overlay   |
   +-----------+  +-----------+  +-----------+
```

### Data Flow

This diagram shows how a single user command travels through the system:

```
  User speaks            User shows
  "Hey MIA,              hand gesture
   open YouTube"         (open palm)
       |                      |
       v                      v
  +----------+          +-----------+
  | Mic +    |          | Webcam +  |
  | Google   |          | MediaPipe |
  | STT      |          | Hands     |
  +----+-----+          +-----+-----+
       |                      |
       | text: "open youtube" | gesture: "open_palm"
       |                      |
       v                      v
  +----------+          +-----------+
  | POST     |          | POST      |
  | /voice_  |          | /gesture  |
  | command  |          |           |
  +----+-----+          +-----+-----+
       |                      |
       +----------+-----------+
                  |
                  v
         +--------+--------+
         | Command Parser  |
         | (TextBlob NLP + |
         |  keyword match) |
         +--------+--------+
                  |
                  | intent: {action: "open_app", target: "YouTube"}
                  |
                  v
         +--------+--------+
         | Action Executor |
         | (actions.py)    |
         +--------+--------+
                  |
         +--------+--------+--------+
         |        |        |        |
         v        v        v        v
      Launch   Speak    Show     Log to
      YouTube  "Opening HUD      History
               YouTube" Overlay
```

### Component Interaction Map

```
+-------------------------------------------------------------------+
|                        INTERACTION MAP                             |
+-------------------------------------------------------------------+
|                                                                    |
|  voice_activation.py ----> combo_controller.py                     |
|        |                        |                                  |
|        | (wake word detected)   | (activate combo mode)            |
|        v                        v                                  |
|  POST /voice_command       tts_response.py                         |
|        |                        |                                  |
|        v                        | (speaks with personality)        |
|  command_parser.py              v                                  |
|        |                   pyttsx3 engine                          |
|        | (parsed intent)                                           |
|        v                                                           |
|  server/api.py ---------> hud_overlay.py                           |
|        |                        |                                  |
|        | (handle_action)        | (visual feedback)                |
|        v                        v                                  |
|  actions.py               OpenCV window / console fallback         |
|        |                                                           |
|        +-- launch_app()                                            |
|        +-- take_screenshot()                                       |
|        +-- change_volume()                                         |
|        +-- set_brightness()                                        |
|        +-- lock_pc() / sleep_pc()                                  |
|        +-- search_web()                                            |
|        +-- mouse_click() / mouse_scroll()                          |
|                                                                    |
+-------------------------------------------------------------------+
|                                                                    |
|  ollama_client.py (optional)                                       |
|        |                                                           |
|        +-- query_ollama() ----> Ollama API (localhost:11434)       |
|        +-- styled_reply() ----> personality-driven chat            |
|        +-- structured_plan() -> JSON action plans                  |
|                                                                    |
|  agent.py (optional)                                               |
|        |                                                           |
|        +-- plan_with_ollama() -> multi-step action planning        |
|        +-- execute_plan() -----> sequential action execution       |
|                                                                    |
+-------------------------------------------------------------------+
```

---

## Project Structure

```
PROJECT - MIA/
|
|-- mia_main.py                  # Primary entry point -- PyQt5 neon control center
|-- mia_launcher.py              # Lightweight launcher (system tray + subprocess manager)
|-- mia_hud.py                   # Standalone HUD overlay + personality selector + system tray
|-- mia_desktop.py               # Desktop integration utilities
|-- requirements.txt             # Python dependencies
|-- Launch_MIA.bat               # Windows one-click launcher
|-- build_exe.bat                # PyInstaller packaging script
|-- config.json                  # Runtime configuration (wake word, preferences)
|
|-- mia_assistant/               # [STABLE] Core assistant modules
|   |-- __init__.py
|   |-- voice_activation.py      # Wake word listener + combo mode voice input
|   |-- voice_command.py         # Voice command entry point
|   |-- voice_control.py         # Voice control utilities
|   |-- command_parser.py        # NLP intent extraction (TextBlob + keyword matching)
|   |-- actions.py               # System action executor (apps, volume, screenshots, etc.)
|   |-- agent.py                 # LLM-powered multi-step planner (Ollama)
|   |-- ollama_client.py         # Ollama HTTP API client
|   |-- tts_response.py          # Personality-driven TTS (pyttsx3)
|   |-- mood_detection.py        # Webcam emotion detection (DeepFace)
|   |-- combo_controller.py      # Combo mode state machine (voice + gesture)
|   |-- hud_overlay.py           # OpenCV-based visual feedback overlay
|
|-- mia/                         # [EXPERIMENTAL] Next-gen architecture
|   |-- main.py                  # MIASystem class -- full pipeline orchestrator
|   |-- audio/
|   |   |-- stt.py               # Speech-to-text module
|   |   |-- wake_word.py         # Wake word detection
|   |-- core/
|   |   |-- command_router.py    # Intent-to-action routing
|   |   |-- executor.py          # Action execution engine
|   |-- llm/
|   |   |-- canary_engine.py     # Transformer-based intent parser (Qwen 2.5B)
|   |   |-- intent_guard.py      # Safety validation for parsed intents
|   |   |-- emotion_detector.py  # Text-based emotion detection
|   |-- tts/
|   |   |-- speaker.py           # TTS speaker module
|   |-- hud/
|       |-- hud_window.py        # PySide6-based HUD window
|       |-- state_manager.py     # HUD state management
|
|-- gesture_control/             # MediaPipe gesture recognition
|   |-- main.py                  # Webcam gesture detection + API client
|   |-- requirements.txt         # Module-specific dependencies
|
|-- server/                      # FastAPI REST API backend
|   |-- api.py                   # Gesture + voice command endpoints
|   |-- test_api.py              # API tests
|
|-- ar_ui/                       # AR UI prototype (HTML/CSS/JS)
|   |-- index.html
|   |-- script.js
|   |-- style.css
|
|-- ui_assets/                   # Visual resources
|   |-- logo.svg                 # MIA logo
|   |-- mia_icon_new.png         # Application icon
|   |-- avatars/                 # Personality avatar images
|   |-- gestures/                # Gesture reference icons
|   |-- hud/                     # HUD overlay assets
|
|-- tests/                       # Test suite
|   |-- test_command_parser.py   # Unit tests for intent parsing
|
|-- .gitignore
|-- LICENSE                      # MIT License
|-- CONTRIBUTING.md              # Contribution guidelines
|-- README.md                    # This file
```

---

## Getting Started

### Prerequisites

| Requirement         | Version  | Notes                                          |
|---------------------|----------|------------------------------------------------|
| Python              | 3.10+    | Required                                       |
| pip                 | Latest   | Required                                       |
| Microphone          | Any      | Required for voice commands                    |
| Webcam              | Any      | Required for gesture control and mood detection|
| Git                 | Latest   | Required for auto-update feature               |
| Ollama              | Latest   | Optional -- for LLM-powered chat and planning  |
| OpenWeatherMap Key  | Free tier| Optional -- for weather queries                |

### Installation

1. **Clone the repository**

   ```sh
   git clone https://github.com/TROJANmocX/Project-MIA.git
   cd Project-MIA
   ```

2. **Create and activate a virtual environment**

   ```sh
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

   If you encounter issues with specific packages, install the core set manually:

   ```sh
   pip install fastapi uvicorn opencv-python numpy pyttsx3 SpeechRecognition pyaudio requests mediapipe textblob pystray pillow PyQt5 pyautogui
   ```

   > Note: `pyaudio` may require system-level dependencies. On Windows, consider
   > `pip install pipwin && pipwin install pyaudio`. On Ubuntu/Debian,
   > `sudo apt install portaudio19-dev` before pip install.

4. **Configure API keys (optional)**

   - **Weather**: Edit `server/api.py` and replace `YOUR_OPENWEATHERMAP_API_KEY` with your key from [openweathermap.org](https://openweathermap.org/api).
   - **LLM**: Install [Ollama](https://ollama.ai) and pull a model:
     ```sh
     ollama pull llama3
     ```

### Running MIA

**Option A -- Windows batch launcher (easiest):**

Double-click `Launch_MIA.bat` in the project root.

**Option B -- Python entry point (full GUI):**

```sh
python mia_main.py
```

This launches the neon control center with all four pages (Home, Commands, Settings, About). Click "Start MIA" to spawn the API server, voice engine, gesture control, and mood detection as background processes.

**Option C -- Lightweight system tray mode:**

```sh
python mia_launcher.py
```

This runs MIA headlessly with a system tray icon. Right-click the tray icon for settings and quit.

**Option D -- Next-gen experimental mode:**

```sh
python -m mia.main
```

This runs the newer transformer-based pipeline with Canary Engine. Requires GPU or significant RAM.

**What happens on launch:**

```
1. First-run onboarding dialog (shown once)
2. PyQt5 neon control center window opens
3. System tray icon appears
4. Auto-update check runs against GitHub
5. CPU/RAM monitoring starts (refreshes every 2 seconds)
6. Click "Start MIA" to activate:
   a. FastAPI server on 127.0.0.1:8000
   b. Voice activation (wake word listener)
   c. Gesture control (webcam + MediaPipe)
   d. Mood detection (webcam + DeepFace)
```

---

## Module Reference

### Desktop UI (mia_main.py)

The primary interface. A 1760-line PyQt5 application featuring:

- **AnimatedNeonRing** -- Custom-painted widget with pulsing glow, spinning arcs, and center dot animation
- **SideNav** -- Four-page navigation sidebar (Home, Commands, Settings, About)
- **StatCard** -- Real-time CPU and RAM monitoring cards (via psutil)
- **StatusPill** -- Color-coded status indicator (Running/Stopped/Launching)
- **PersonalityCard** -- Interactive personality selector (Calm/Witty/Sarcastic/Bold)
- **QuickCmdBtn** -- One-click app launchers and system commands
- **Toast** -- Non-blocking notification popups
- **OnboardingDialog** -- First-run welcome wizard
- **VoiceWorker** -- Threaded voice recognition with Google STT
- **UpdateWorker** -- Git-based auto-update with stash/pull/pop workflow

### Voice Pipeline

```
Microphone
    |
    v
SpeechRecognition (Google STT)
    |
    v
Wake word check ("hey mia" by default)
    |
    +-- Match found --> Activate combo mode
    |                   |
    |                   v
    |              Listen for commands (30s window)
    |                   |
    |                   v
    |              POST /voice_command to FastAPI
    |
    +-- No match --> Continue listening
```

Key files:
- `mia_assistant/voice_activation.py` -- Wake word loop and combo mode voice input
- `mia_main.py` (VoiceWorker class) -- In-UI voice recognition

### Gesture Recognition

```
Webcam Feed
    |
    v
MediaPipe Hands (min confidence 0.7)
    |
    v
Landmark Analysis
    |
    +-- thumb-to-pinky distance > 0.4 --> "open_palm" --> screenshot
    +-- index-to-wrist distance < 0.15 --> "fist" --> volume_down
    +-- (future: swipe detection)
    |
    v
POST /gesture to FastAPI (debounced at 2-second intervals)
```

Key file: `gesture_control/main.py`

### Command Parsing and NLP

The command parser uses TextBlob for sentiment analysis and keyword matching for intent extraction:

```
Input text
    |
    v
TextBlob sentiment analysis
    |
    +-- polarity > 0.3  --> mood: "bold"
    +-- polarity < -0.3 --> mood: "sarcastic"
    +-- otherwise       --> mood: "calm"
    |
    v
Keyword matching
    |
    +-- "youtube"           --> open_app (YouTube)
    +-- "screenshot"        --> screenshot
    +-- "volume up"         --> volume_up
    +-- "combo mode"        --> activate_combo
    +-- "weather"           --> get_weather
    +-- (no match)          --> unknown / forward to LLM
```

Key file: `mia_assistant/command_parser.py`

### LLM Integration

MIA supports two LLM backends:

**Ollama Client (Stable)**
- Connects to local Ollama server at `localhost:11434`
- `styled_reply()` -- Generates personality-driven responses
- `structured_plan()` -- Extracts JSON action plans from natural language

**Canary Engine (Experimental)**
- Uses HuggingFace Transformers with `nvidia/canary-qwen-2.5b`
- Converts natural language to structured JSON intents
- Includes fallback keyword parser when model is unavailable

Key files:
- `mia_assistant/ollama_client.py`
- `mia_assistant/agent.py`
- `mia/llm/canary_engine.py`
- `mia/llm/intent_guard.py`

### Action Execution

Supported system actions:

| Action            | Function           | Description                              |
|-------------------|--------------------|------------------------------------------|
| Launch App        | `launch_app()`     | Opens any app by name or path (cross-OS) |
| Screenshot        | `take_screenshot()` | Captures screen with timestamp filename  |
| Volume Up/Down    | `change_volume()`  | Simulates volume key press               |
| Brightness        | `set_brightness()` | WMI-based brightness control (Windows)   |
| Lock PC           | `lock_pc()`        | Locks the Windows workstation            |
| Sleep PC          | `sleep_pc()`       | Puts the PC to sleep                     |
| Web Search        | `search_web()`     | Opens Google search in default browser   |
| Mouse Click       | `mouse_click()`    | Simulates a mouse click                  |
| Mouse Scroll      | `mouse_scroll()`   | Simulates mouse scroll                   |

Key file: `mia_assistant/actions.py`

### HUD Overlay

A thread-safe visual feedback system using a producer-consumer queue:

- Messages are pushed to `overlay_queue` from any thread
- A dedicated display thread renders them as OpenCV windows
- Color-coded by content: green (default), red (errors), yellow (activation), orange (weather)
- Falls back to console printing when OpenCV is unavailable

Key file: `mia_assistant/hud_overlay.py`

### TTS Engine

Personality-driven text-to-speech using pyttsx3:

| Personality | Speech Rate | Prefix            | Suffix        |
|-------------|------------|--------------------|---------------|
| Calm        | 150 WPM    | "Okay,"            | (none)        |
| Witty       | 180 WPM    | "Here's a thought:" | (wink)       |
| Sarcastic   | 170 WPM    | "Oh, really?"      | "Sure thing..." |
| Bold        | 200 WPM    | "Let's do it!"     | "!"           |

Uses a dedicated worker thread with a queue to prevent blocking the UI.

Key file: `mia_assistant/tts_response.py`

### Mood Detection

Periodic webcam capture analyzed by DeepFace:

```
Webcam frame (every 10 seconds)
    |
    v
DeepFace.analyze(actions=['emotion'])
    |
    +-- happy / surprise  --> personality: "bold"
    +-- angry / sad / fear --> personality: "sarcastic"
    +-- neutral / other    --> personality: "calm"
```

Key file: `mia_assistant/mood_detection.py`

### Combo Mode

A timed session (default 30 seconds) where both voice and gesture inputs are active simultaneously:

```
Wake word detected
    |
    v
ComboModeController.activate()
    |
    +-- Starts 30-second timer
    +-- TTS: "Combo mode activated."
    +-- HUD: "Combo Mode Activated!"
    +-- Voice listener thread starts
    +-- Gesture control continues
    |
    v
Timer expires --> deactivate()
    |
    +-- TTS: "Combo mode ended."
    +-- HUD: "Combo Mode Ended"
```

Key file: `mia_assistant/combo_controller.py`

### FastAPI Server

REST API backend (runs on `127.0.0.1:8000`):

| Endpoint         | Method | Description                        |
|------------------|--------|------------------------------------|
| `/gesture`       | POST   | Receives gesture input from webcam |
| `/voice_command` | POST   | Receives parsed voice commands     |

Both endpoints route through `handle_action()` which dispatches to TTS, HUD, and system actions.

Key file: `server/api.py`

### Agent / Planner

Multi-step action planning via Ollama:

```
User text + personality + modality
    |
    v
Build prompt with available tools:
  - launch_app
  - take_screenshot
  - change_volume
    |
    v
Ollama generates JSON plan:
  {
    "say": "Opening YouTube for you!",
    "hud": "Launching YouTube...",
    "personality": "bold",
    "actions": [
      {"tool": "launch_app", "args": {"app": "youtube"}}
    ]
  }
    |
    v
Execute each action sequentially
    |
    v
Return combined results
```

Key file: `mia_assistant/agent.py`

---

## How It Works -- End to End

Here is the complete lifecycle of a voice command:

```
  [1] User says "Hey MIA, take a screenshot"
                    |
  [2] voice_activation.py detects wake word
                    |
  [3] Combo mode activates (30-second window)
                    |
  [4] Voice listener captures "take a screenshot"
                    |
  [5] POST /voice_command { text: "take a screenshot" }
                    |
  [6] command_parser.py extracts:
      { action: "screenshot", mood: "calm" }
                    |
  [7] handle_action("screenshot", ...) in api.py
                    |
  [8] Three things happen in parallel:
      a) hud_overlay shows "Screenshot taken"
      b) tts_response speaks "Screenshot taken." (calm voice)
      c) pyautogui captures the screen to screenshot_YYYYMMDD_HHMMSS.png
                    |
  [9] Response returned to caller
```

---

## Configuration

MIA stores configuration in `config.json` in the project root:

```json
{
  "wake_word": "hey mia"
}
```

You can change the wake word from:
- The Settings page in the GUI (Wake Word Configuration section)
- Directly editing `config.json`

---

## Keyboard Shortcuts

| Shortcut   | Action                          |
|------------|---------------------------------|
| Ctrl + L   | Toggle voice listening on/off   |
| Ctrl + M   | Toggle microphone mute          |
| Ctrl + 1   | Navigate to Home page           |
| Ctrl + 2   | Navigate to Commands page       |
| Ctrl + 3   | Navigate to Settings page       |
| Ctrl + 4   | Navigate to About page          |

---

## Extending MIA

MIA is designed to be modular. Here is a quick reference for common extensions:

| What you want to do            | File to edit                          | How                                                  |
|--------------------------------|---------------------------------------|------------------------------------------------------|
| Add a new voice command        | `mia_assistant/command_parser.py`     | Add a new `elif` block with keyword matching          |
| Add a new gesture              | `gesture_control/main.py`            | Add landmark detection logic + entry in GESTURE_ACTIONS |
| Add a new app to launch        | `mia_assistant/actions.py`           | The `launch_app()` function already handles arbitrary app names |
| Add a new system action        | `mia_assistant/actions.py`           | Add a new function and wire it in `execute_action()`  |
| Add a new personality          | `mia_assistant/tts_response.py`      | Add an entry to the PERSONALITIES dictionary          |
| Add a new API endpoint         | `server/api.py`                      | Add a new FastAPI route function                      |
| Add a new LLM tool             | `mia_assistant/agent.py`             | Add to the TOOLS list and handle in `execute_plan()`  |
| Swap the TTS engine            | `mia_assistant/tts_response.py`      | Replace pyttsx3 calls with ElevenLabs/Coqui/etc.     |
| Swap the STT engine            | `mia_assistant/voice_activation.py`  | Replace Google STT with Whisper/Vosk/etc.            |

---

## Security and Privacy

- **Local Processing** -- All voice recognition, gesture detection, mood analysis, and command execution run on your machine. No audio, video, or command data is transmitted to external servers by default.
- **Optional Cloud STT** -- Google Speech-to-Text is used for voice recognition. You can replace it with offline alternatives like Vosk or OpenAI Whisper for fully offline operation.
- **Optional LLM** -- Ollama runs entirely locally. No API keys or cloud services are required for LLM features.
- **Privacy Toggles** -- Microphone and camera can be independently muted from the Settings page or system tray.
- **No Telemetry** -- MIA does not collect, store, or transmit usage data.

---

## Roadmap

- [ ] Adaptive UI themes based on detected mood
- [ ] Contextual multi-turn voice conversations
- [ ] Smart room / environment detection
- [ ] AI-driven app suggestions based on usage patterns
- [ ] Plugin system for third-party extensions
- [ ] Cross-platform support (macOS, Linux)
- [ ] Offline STT via Whisper integration
- [ ] ElevenLabs TTS integration
- [ ] Multi-monitor HUD overlay support
- [ ] Gesture-based cursor control

---

## Tech Stack

| Layer             | Technology                                              |
|-------------------|---------------------------------------------------------|
| Desktop UI        | PyQt5, PySide6                                          |
| Backend API       | FastAPI, Uvicorn                                        |
| Voice Input       | SpeechRecognition, PyAudio, Google STT                  |
| Gesture Input     | OpenCV, MediaPipe                                       |
| NLP               | TextBlob (sentiment analysis)                           |
| LLM               | Ollama (llama3), HuggingFace Transformers (Qwen 2.5B)  |
| TTS               | pyttsx3                                                 |
| Emotion Detection | DeepFace                                                |
| System Control    | pyautogui, subprocess, webbrowser                       |
| System Tray       | pystray, Pillow                                         |
| Packaging         | PyInstaller                                             |

---

## Contributing

We welcome contributions from everyone. Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- How to report bugs and request features
- Setting up your development environment
- Code style and commit conventions
- The pull request process

---

## License

This project is licensed under the **MIT License** -- see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software for any purpose, including commercial use, provided that the original copyright notice and license text are included.
