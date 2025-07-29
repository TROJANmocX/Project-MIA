# mia_assistant/command_parser.py

# Simple intent parser for voice commands
from textblob import TextBlob

def parse_command(text):
    text = text.lower()
    # Sentiment analysis for mood
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.3:
        mood = "bold"
    elif polarity < -0.3:
        mood = "sarcastic"
    else:
        mood = "calm"
    if "youtube" in text:
        return {"action": "open_app", "target": "YouTube", "mood": mood}
    elif "weather" in text:
        return {"action": "get_weather", "mood": mood}
    elif "code editor" in text or "vs code" in text:
        return {"action": "open_app", "target": "VSCode", "mood": mood}
    elif "spotify" in text:
        return {"action": "open_app", "target": "Spotify", "mood": mood}
    elif "screenshot" in text:
        return {"action": "screenshot", "mood": mood}
    elif "volume up" in text or "increase volume" in text:
        return {"action": "volume_up", "mood": mood}
    elif "volume down" in text or "decrease volume" in text:
        return {"action": "volume_down", "mood": mood}
    elif "combo mode" in text or "activate combo" in text:
        return {"action": "activate_combo", "mood": mood}
    elif "switch window" in text or "next window" in text:
        return {"action": "switch_window", "mood": mood}
    elif "refresh" in text or "reload" in text:
        return {"action": "refresh", "mood": mood}
    # Add more intents as needed
    else:
        return {"action": "unknown", "raw": text, "mood": mood}
