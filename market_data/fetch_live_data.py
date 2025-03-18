from utils.config_loader import kite
from utils.logger import logger

def fetch_live_data(symbol):
    """Fetches live market data from Kite API."""
    try:
        live_data = kite.ltp(symbol)
        if isinstance(live_data, dict) and symbol in live_data:
            return live_data[symbol].get("last_price", None)
        else:
            logger.error(f"❌ API Error: Unexpected response for {symbol}, Data: {live_data}")
            return None
    except Exception as e:
        logger.error(f"❌ Error fetching live data for {symbol}: {e}")
        return None
