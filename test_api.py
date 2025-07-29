import requests

# Example gesture payload
payload = {"gesture": "volume_up"}

try:
    response = requests.post("http://127.0.0.1:8000/gesture", json=payload)
    print("✅ Status:", response.status_code)
    print("📨 Response:", response.json())
except requests.exceptions.RequestException as e:
    print("🚫 Error:", e)
