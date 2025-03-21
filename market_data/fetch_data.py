# market_data/fetcher.py
import logging
from datetime import datetime
from kiteconnect import KiteConnect
from collections import deque
import json

# Load API config
with open("config.json") as config_file:
    config = json.load(config_file)

KITE_API_KEY = config["KITE_API_KEY"]
KITE_ACCESS_TOKEN = config["KITE_ACCESS_TOKEN"]

# Initialize KiteConnect
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(KITE_ACCESS_TOKEN)

# Index instrument tokens
INDEX_TOKENS = {
    "NSE:NIFTY 50": 256265,
    "NSE:NIFTY BANK": 260105
}

def fetch_historical_data(symbol):
    today = datetime.now().date()
    start_time = datetime(today.year, today.month, today.day, 9, 15, 0)
    end_time = datetime(today.year, today.month, today.day, 15, 15, 0)

    try:
        instrument_token = INDEX_TOKENS.get(symbol)
        if not instrument_token:
            logging.error(f"Instrument token not found for {symbol}")
            return deque([], maxlen=25)

        candles = kite.historical_data(instrument_token, start_time, end_time, "minute")

        return deque(
            [{"high": c[2], "low": c[3], "close": c[4], "volume": c[5]} for c in candles],
            maxlen=25
        )
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return deque([], maxlen=25)
