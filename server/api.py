from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from mia_assistant import tts_response, hud_overlay, command_parser, combo_controller
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper: handle actions from both gesture and voice

def handle_action(action, background_tasks, mood="calm"):
    if action == "volume_up":
        background_tasks.add_task(tts_response.speak, "Volume increased.", mood)
    elif action == "volume_down":
        background_tasks.add_task(tts_response.speak, "Volume decreased.", mood)
    elif action == "screenshot":
        background_tasks.add_task(hud_overlay.display_message, "Screenshot taken")
        background_tasks.add_task(tts_response.speak, "Screenshot taken.", mood)
    elif action == "open_app":
        target = intent.get("target", "App") if 'intent' in locals() else "App"
        background_tasks.add_task(tts_response.speak, f"Launching {target}.", mood)
        background_tasks.add_task(hud_overlay.display_message, f"Launching {target}...")
        # Launch apps (expand as needed)
        if target.lower() == "youtube":
            subprocess.Popen(["cmd", "/c", "start https://youtube.com"])
        elif target.lower() == "vscode":
            subprocess.Popen(["code"])
        elif target.lower() == "spotify":
            subprocess.Popen(["cmd", "/c", "start spotify:"])
    elif action == "get_weather":
        # Fetch weather from OpenWeatherMap
        import requests as pyrequests
        WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"  # <-- Replace with your API key
        CITY = "London"  # Optionally, parse city from intent
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
            resp = pyrequests.get(url)
            data = resp.json()
            if data.get("main"):
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                weather_msg = f"It's {temp}°C and {desc} in {CITY}."
            else:
                weather_msg = "Sorry, I couldn't fetch the weather."
        except Exception as e:
            weather_msg = "Weather service error."
        background_tasks.add_task(tts_response.speak, weather_msg, mood)
        background_tasks.add_task(hud_overlay.display_message, weather_msg)
    elif action == "activate_combo":
        combo_controller.combo_controller.activate()
        background_tasks.add_task(tts_response.speak, "Combo mode activated.", "bold")
        background_tasks.add_task(hud_overlay.display_message, "Combo Mode Activated!")
    else:
        background_tasks.add_task(tts_response.speak, "Sorry, I didn't understand that command.", "sarcastic")
        background_tasks.add_task(hud_overlay.display_message, "Unknown command")

@app.post("/gesture")
async def receive_gesture(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        gesture = data.get("gesture")
        print(f"✅ Received gesture: {gesture}")
        # In combo mode, gestures are always accepted
        handle_action(gesture, background_tasks)
        return {"status": "Gesture processed"}
    except Exception as e:
        print(f"❌ Error processing gesture: {e}")
        return {"status": "Error", "details": str(e)}

@app.post("/voice_command")
async def receive_voice_command(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        text = data.get("text", "")
        mood = data.get("mood", "calm")
        print(f"🗣️ Received voice command: {text}")
        intent = command_parser.parse_command(text)
        action = intent.get("action")
        handle_action(action, background_tasks, mood)
        return {"status": "Voice command processed", "intent": intent}
    except Exception as e:
        print(f"❌ Error processing voice command: {e}")
        return {"status": "Error", "details": str(e)}
