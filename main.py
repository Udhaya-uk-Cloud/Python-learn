import sys
import os
import ta

#sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Ensure Python finds the installed packages
sys.path.append("C:\\Users\\udhay\\AppData\\Roaming\\Python\\Python313\\site-packages")

import time
import concurrent.futures
import pandas as pd
from market_data.fetch_data import fetch_historical_data
from market_data.fetch_live_data import fetch_live_data
from alerts.telegram_alerts import send_telegram_alert
from utils.config_loader import BANK_NIFTY_SYMBOL, NIFTY_SYMBOL
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger
from strategy.signals import vwm_processor, detect_market_structure

# ✅ Fetch historical data
logger.info("🚀 Fetching historical data for Bank Nifty and Nifty...")
bank_nifty_history = fetch_historical_data(BANK_NIFTY_SYMBOL)
nifty_history = fetch_historical_data(NIFTY_SYMBOL)
logger.info("✅ Historical data fetched successfully.")

# ✅ Detect Market Structure
df_nifty = pd.DataFrame(list(fetch_historical_data(NIFTY_SYMBOL)))
df_bank_nifty = pd.DataFrame(list(fetch_historical_data(BANK_NIFTY_SYMBOL)))

if len(df_nifty) > 1:
    market_structure_nifty = detect_market_structure(df_nifty)
    logger.info(f"📊 NIFTY Market Structure: {market_structure_nifty}")
if len(df_bank_nifty) > 1:
    market_structure_bank = detect_market_structure(df_bank_nifty)
    logger.info(f"📊 BANK NIFTY Market Structure: {market_structure_bank}")

# ✅ Compute Trade Signals
signal_nifty, entry_price_nifty, stop_loss_nifty, profit_target_nifty = vwm_processor.compute_vwm_signal(df_nifty, NIFTY_SYMBOL)
signal_bank_nifty, entry_price_bank_nifty, stop_loss_bank_nifty, profit_target_bank_nifty = vwm_processor.compute_vwm_signal(df_bank_nifty, BANK_NIFTY_SYMBOL)

logger.info(f"📊 Trade Signal for NIFTY: {signal_nifty} | Entry: {entry_price_nifty} | SL: {stop_loss_nifty} | PT: {profit_target_nifty}")
logger.info(f"📊 Trade Signal for BANK NIFTY: {signal_bank_nifty} | Entry: {entry_price_bank_nifty} | SL: {stop_loss_bank_nifty} | PT: {profit_target_bank_nifty}")

# ✅ Send Telegram Alerts
if signal_nifty != "HOLD":
    send_telegram_alert(
        f"📢 Trade Alert: {signal_nifty} NIFTY\n"
        f"🎯 Entry: {entry_price_nifty}\n"
        f"🛑 Stop-Loss: {stop_loss_nifty}\n"
        f"🎯 Target: {profit_target_nifty}"
    )

if signal_bank_nifty != "HOLD":
    send_telegram_alert(
        f"📢 Trade Alert: {signal_bank_nifty} BANK NIFTY\n"
        f"🎯 Entry: {entry_price_bank_nifty}\n"
        f"🛑 Stop-Loss: {stop_loss_bank_nifty}\n"
        f"🎯 Target: {profit_target_bank_nifty}"
    )

# ✅ Prevent Trading in Sideways Markets
if signal_nifty == "HOLD" and signal_bank_nifty == "HOLD":
    logger.warning("⚠️ No strong trade signals. Market might be sideways. Skipping trade execution.")
    send_telegram_alert("⚠️ No strong trade signals. Market might be sideways. Skipping trade execution.")

# Track last signals
last_bank_signal = None
last_nifty_signal = None

# Graceful exit flag
running = True

def fetch_and_process(symbol, history, last_signal):
    """Fetch live data, compute signals, and return updated signal."""
    logger.info(f"🔍 Fetching live price for {symbol}...")
    price = fetch_live_data(symbol)

    if price:
        logger.info(f"📊 Live Market Data: {symbol} - Price: {price}")
        history.append({"high": price, "low": price, "close": price})
        
        # ✅ Compute trade signals with live data
        signal, entry, sl, tp = vwm_processor.compute_vwm_signal(pd.DataFrame(list(history)), symbol)

        # ✅ Log trade signal with entry, stop-loss, and target
        logger.info(f"📈 Trade Signal for {symbol}: {signal} | Entry: {entry} | SL: {sl} | PT: {tp}")

        # ✅ Alert only if new trade signal is different from the last one
        if signal != "HOLD" and signal != last_signal:
            rounded_entry = round_to_nearest_100(entry) if "BANK" in symbol else round_to_nearest_50(entry)
            message = f"\n🔹 {symbol} - {signal} at {rounded_entry}\n🎯 Profit Target: {tp}\n🛑 Stop-Loss: {sl}\n"
            logger.info(f"🚀 New Trade Alert: {message}")
            send_telegram_alert(message)
            return signal
    else:
        logger.warning(f"⚠️ No live data received for {symbol}.")
    return last_signal

# Graceful shutdown handler
def stop_trading():
    global running
    running = False
    logger.info("🛑 Stopping the trading bot...")
    print("🛑 Trading bot stopped.")

# ✅ Main trading loop
logger.info("📈 Trading bot is now running...")
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
            send_telegram_alert(f"❌ Script Error: {str(e)}")
        
        logger.info("⏳ Waiting for next trading cycle...")
        time.sleep(60)  # Fetch data every 1 minute
