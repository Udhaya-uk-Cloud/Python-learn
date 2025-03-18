import requests
from kiteconnect import KiteConnect
from collections import deque
from datetime import datetime
from utils.config_loader import config
from utils.logger import logger

# Initialize KiteConnect
kite = KiteConnect(api_key=config["KITE_API_KEY"])
kite.set_access_token(config["KITE_ACCESS_TOKEN"])

INDEX_TOKENS = {
    "NSE:NIFTY 50": 256265,
    "NSE:NIFTY BANK": 260105
}

def fetch_historical_data(symbol):
    """Fetches historical market data from Kite API."""
    today = datetime.now().date()
    start_time = datetime(today.year, today.month, today.day, 9, 15, 0)
    end_time = datetime(today.year, today.month, today.day, 15, 15, 0)

    try:
        instrument_token = INDEX_TOKENS.get(symbol)
        if not instrument_token:
            logger.error(f"Instrument token not found for {symbol}")
            return deque([], maxlen=25)

        historical_data = kite.historical_data(instrument_token, start_time, end_time, "minute")

        return deque(
            [{"high": c["high"], "low": c["low"], "close": c["close"], "volume": c["volume"]} for c in historical_data],
            maxlen=25
        )
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return deque([], maxlen=25)

def fetch_live_data(symbol):
    """Fetches live market data."""
    try:
        live_data = kite.ltp(symbol)
        if isinstance(live_data, dict) and symbol in live_data:
            return live_data[symbol].get("last_price", None)
        logger.error(f"Unexpected API response for {symbol}: {live_data}")
        return None
    except Exception as e:
        logger.error(f"Error fetching live data for {symbol}: {e}")
        return None
