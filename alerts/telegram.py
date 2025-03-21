# alerts/telegram.py
import requests
import json

# Load Telegram config
with open("config.json") as config_file:
    config = json.load(config_file)

TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Telegram error: {response.text}")
    except Exception as e:
        print(f"❌ Telegram exception: {e}")