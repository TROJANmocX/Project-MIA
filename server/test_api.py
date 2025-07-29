import requests

data = {"gesture": "click"}

try:
    res = requests.post("http://127.0.0.1:8000/gesture", json=data)
    print(f"✅ Status: {res.status_code}")
    print("📩 Response:", res.json())
except requests.exceptions.RequestException as e:
    print("🚫 Error:", e)
