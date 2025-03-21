import json
import os
import sys
from kiteconnect import KiteConnect
from dotenv import load_dotenv
from utils.logger import logger

# ✅ Load Environment Variables from .env File
load_dotenv()

# ✅ Define Configuration Path
CONFIG_PATH = "config.json"

def load_config():
    """Load configuration from environment variables or fallback to config.json."""
    config = {}

    # ✅ Load config.json if it exists
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as config_file:
                config = json.load(config_file)
        except json.JSONDecodeError as e:
            logger.critical(f"❌ JSON Error in config.json: {e}")
            print(f"❌ ERROR: Invalid JSON format in config.json - {e}")
            sys.exit(1)  # 🚨 Exit if config.json is corrupt
    else:
        logger.warning("⚠️ config.json not found. Using only environment variables.")

    # ✅ Load API Credentials (Prefer Environment Variables)
    config["KITE_API_KEY"] = os.getenv("KITE_API_KEY", config.get("KITE_API_KEY", ""))
    config["KITE_ACCESS_TOKEN"] = os.getenv("KITE_ACCESS_TOKEN", config.get("KITE_ACCESS_TOKEN", ""))
    config["TELEGRAM_BOT_TOKEN"] = os.getenv("TELEGRAM_BOT_TOKEN", config.get("TELEGRAM_BOT_TOKEN", ""))
    config["TELEGRAM_CHAT_ID"] = os.getenv("TELEGRAM_CHAT_ID", config.get("TELEGRAM_CHAT_ID", ""))

    # ✅ Validate Required Credentials
    required_keys = ["KITE_API_KEY", "KITE_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    for key in required_keys:
        if not config[key]:
            logger.critical(f"❌ Missing '{key}' in environment variables or config.json!")
            print(f"❌ ERROR: '{key}' is required but missing. Please check your environment variables or config.json.")
            sys.exit(1)  # 🚨 Exit script if a required API key is missing

    # ✅ Load Trade Settings with Defaults
    config["TRADE_SETTINGS"] = config.get("TRADE_SETTINGS", {
        "ATR_MULTIPLIER": float(os.getenv("ATR_MULTIPLIER", 3.0)),
        "EMA_SHORT": int(os.getenv("EMA_SHORT", 9)),
        "EMA_LONG": int(os.getenv("EMA_LONG", 21)),
        "MACD_FAST": int(os.getenv("MACD_FAST", 12)),
        "MACD_SLOW": int(os.getenv("MACD_SLOW", 26)),
        "MACD_SIGNAL": int(os.getenv("MACD_SIGNAL", 9))
    })

    logger.info("✅ Configuration loaded successfully.")
    print("✅ Configuration loaded successfully.")
    return config

# ✅ Load the Config
config = load_config()

# ✅ API Credentials
KITE_API_KEY = config["KITE_API_KEY"]
KITE_ACCESS_TOKEN = config["KITE_ACCESS_TOKEN"]
TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]

# ✅ Market Symbols
BANK_NIFTY_SYMBOL = "NSE:NIFTY BANK"
NIFTY_SYMBOL = "NSE:NIFTY 50"

# ✅ Trade Settings (Dynamically Loaded)
TRADE_SETTINGS = config["TRADE_SETTINGS"]
ATR_MULTIPLIER = TRADE_SETTINGS["ATR_MULTIPLIER"]
EMA_SHORT = TRADE_SETTINGS["EMA_SHORT"]
EMA_LONG = TRADE_SETTINGS["EMA_LONG"]
MACD_FAST = TRADE_SETTINGS["MACD_FAST"]
MACD_SLOW = TRADE_SETTINGS["MACD_SLOW"]
MACD_SIGNAL = TRADE_SETTINGS["MACD_SIGNAL"]

# ✅ Initialize KiteConnect
if KITE_API_KEY and KITE_ACCESS_TOKEN:
    try:
        kite = KiteConnect(api_key=KITE_API_KEY)
        kite.set_access_token(KITE_ACCESS_TOKEN)
        logger.info("✅ KiteConnect API initialized successfully.")
        print("✅ Kite API connection established.")
    except Exception as e:
        logger.critical(f"❌ Kite API Initialization Error: {e}")
        print(f"❌ ERROR: Unable to initialize Kite API - {e}")
        sys.exit(1)  # 🚨 Exit script if Kite API fails
else:
    logger.critical("⚠️ Kite API credentials are missing. Trading bot cannot function.")
    print("❌ ERROR: Missing Kite API credentials. Please check config.json or set environment variables.")
    sys.exit(1)  # 🚨 Exit script if credentials are missing
