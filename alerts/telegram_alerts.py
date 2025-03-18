import requests
import time
from utils.config_loader import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.logger import logger

def send_telegram_alert(message):
    """Sends alerts via Telegram API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info("✅ Telegram Alert Sent!")
                return
            else:
                logger.warning(f"⚠️ Telegram Error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"❌ Telegram API Error: {e}")

        time.sleep(2 ** attempt)
    
    logger.error("❌ Failed to send Telegram alert after 3 attempts")

