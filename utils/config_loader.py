import json
import os
from kiteconnect import KiteConnect
from utils.logger import logger

# Load configuration
CONFIG_PATH = "config.json"

def load_config():
    """Load configuration with validation."""
    if not os.path.exists(CONFIG_PATH):
        logger.error("⚠️ Missing config.json file. Ensure it exists in the project directory.")
        return {}

    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)

    required_keys = ["KITE_API_KEY", "KITE_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    for key in required_keys:
        if key not in config:
            logger.warning(f"⚠️ Missing '{key}' in config.json! Using default values.")

    return config

config = load_config()

# API Credentials
KITE_API_KEY = config.get("KITE_API_KEY", "")
KITE_ACCESS_TOKEN = config.get("KITE_ACCESS_TOKEN", "")
TELEGRAM_BOT_TOKEN = config.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = config.get("TELEGRAM_CHAT_ID", "")

# Initialize KiteConnect
if KITE_API_KEY and KITE_ACCESS_TOKEN:
    kite = KiteConnect(api_key=KITE_API_KEY)
    kite.set_access_token(KITE_ACCESS_TOKEN)
else:
    logger.error("⚠️ Kite API credentials are missing. Trading bot cannot function.")
