import requests
import time
from utils.config_loader import config
from utils.logger import logger

TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info("Telegram alert sent!")
                return
            else:
                logger.error(f"Telegram error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Telegram API error: {e}")

        time.sleep(2 ** attempt)
