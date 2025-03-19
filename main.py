import time
import concurrent.futures
import pandas as pd
from market_data.fetch_data import fetch_historical_data
from market_data.fetch_live_data import fetch_live_data
from strategy.signals import compute_vwm_signal, detect_market_structure
from alerts.telegram_alerts import send_telegram_alert
from utils.config_loader import BANK_NIFTY_SYMBOL, NIFTY_SYMBOL
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger

# Fetch historical data
print("🚀 Fetching historical data for Bank Nifty and Nifty...")
bank_nifty_history = fetch_historical_data(BANK_NIFTY_SYMBOL)
nifty_history = fetch_historical_data(NIFTY_SYMBOL)
print("✅ Historical data fetched successfully.")

# Detect Market Structure before live trading
df_nifty = pd.DataFrame(list(fetch_historical_data(NIFTY_SYMBOL)))
df_bank_nifty = pd.DataFrame(list(fetch_historical_data(BANK_NIFTY_SYMBOL)))

if len(df_nifty) > 1:
    market_structure_nifty = detect_market_structure(df_nifty)
    print(f"📊 NIFTY Market Structure: {market_structure_nifty}")
if len(df_bank_nifty) > 1:
    market_structure_bank = detect_market_structure(df_bank_nifty)
    print(f"📊 BANK NIFTY Market Structure: {market_structure_bank}")

# Track last signals
last_bank_signal = None
last_nifty_signal = None

# Graceful exit flag
running = True

def fetch_and_process(symbol, history, last_signal):
    """Fetch live data, compute signals, and return updated signal."""
    print(f"🔍 Fetching live price for {symbol}...")
    price = fetch_live_data(symbol)
    
    if price:
        print(f"📊 Live price of {symbol}: {price}")
        history.append({"high": price, "low": price, "close": price})
        signal, entry, sl, tp = compute_vwm_signal(pd.DataFrame(list(history)), symbol)

        if signal != "HOLD" and signal != last_signal:
            rounded_entry = round_to_nearest_100(entry) if "BANK" in symbol else round_to_nearest_50(entry)
            message = f"\n🔹 {symbol} - {signal} at {rounded_entry}\n🎯 Profit Target: {tp}\n🛑 Stop-Loss: {sl}\n"
            print(f"🚀 New Trade Alert: {message}")
            send_telegram_alert(message)
            return signal
    else:
        print(f"⚠️ No live data received for {symbol}.")
    return last_signal

# Graceful shutdown handler
def stop_trading():
    global running
    running = False
    logger.info("🛑 Stopping the trading bot...")
    print("🛑 Trading bot stopped.")

# Main trading loop
print("📈 Trading bot is now running...")
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    while running:
        try:
            bank_future = executor.submit(fetch_and_process, BANK_NIFTY_SYMBOL, bank_nifty_history, last_bank_signal)
            nifty_future = executor.submit(fetch_and_process, NIFTY_SYMBOL, nifty_history, last_nifty_signal)

            last_bank_signal = bank_future.result()
            last_nifty_signal = nifty_future.result()

        except KeyboardInterrupt:
            stop_trading()
            break

        except Exception as e:
            logger.error(f"❌ Error during execution: {e}")
            send_telegram_alert(f"Script Error: {str(e)}")
            print(f"❌ Error occurred: {e}")

        print("⏳ Waiting for next trading cycle...")
        time.sleep(60)  # Fetch data every 1 minute