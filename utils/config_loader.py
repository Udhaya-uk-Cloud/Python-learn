import json
from kiteconnect import KiteConnect

def load_config():
    """Load configuration from config.json."""
    with open("config.json") as config_file:
        return json.load(config_file)

# Load Configurations
config = load_config()

# API Credentials
KITE_API_KEY = config["KITE_API_KEY"]
KITE_ACCESS_TOKEN = config["KITE_ACCESS_TOKEN"]
TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]

# Initialize KiteConnect API
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(KITE_ACCESS_TOKEN)
