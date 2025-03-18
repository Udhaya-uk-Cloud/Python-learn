from datetime import datetime
from collections import deque
from utils.config_loader import kite
from utils.logger import logger

# Define Instrument Tokens
INDEX_TOKENS = {
    "NSE:NIFTY 50": 256265,
    "NSE:NIFTY BANK": 260105
}

def fetch_historical_data(symbol):
    """Fetches historical market data from Kite API with logging."""
    today = datetime.now().date()
    start_time = datetime(today.year, today.month, today.day, 9, 15, 0)
    end_time = datetime(today.year, today.month, today.day, 15, 15, 0)

    logger.info(f"📡 Fetching historical data for {symbol}...")
    
    try:
        instrument_token = INDEX_TOKENS.get(symbol)
        if instrument_token is None:
            logger.error(f"❌ Instrument token not found for {symbol}")
            return deque([], maxlen=25)

        historical_data = kite.historical_data(instrument_token, start_time, end_time, "minute")
        
        if not historical_data:
            logger.warning(f"⚠️ No historical data found for {symbol}")
            return deque([], maxlen=25)
        
        logger.info(f"✅ Successfully fetched {len(historical_data)} data points for {symbol}")
        print(f"✅ Historical data fetched for {symbol}: {len(historical_data)} entries")

        return deque(
            [{"high": c["high"], "low": c["low"], "close": c["close"], "volume": c["volume"]} for c in historical_data],
            maxlen=25
        )
    except Exception as e:
        logger.error(f"❌ Error fetching historical data for {symbol}: {e}")
        print(f"❌ Error fetching historical data for {symbol}: {e}")
        return deque([], maxlen=25)