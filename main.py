import time
from market_data.fetch_data import fetch_historical_data
from market_data.fetch_live_data import fetch_live_data
from strategy.vwm_signals import compute_vwm_signal
from alerts.telegram_alerts import send_telegram_alert
from utils.config_loader import BANK_NIFTY_SYMBOL, NIFTY_SYMBOL
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger

# Fetch historical data for both indices
bank_nifty_history = fetch_historical_data(BANK_NIFTY_SYMBOL)
nifty_history = fetch_historical_data(NIFTY_SYMBOL)

# Track last signals to avoid duplicate trades
last_bank_signal = None
last_nifty_signal = None

# ----------------------------
# AUTOMATE TRADING EVERY 1 MINUTE
# ----------------------------
while True:
    try:
        # Fetch latest prices
        bank_nifty_price = fetch_live_data(BANK_NIFTY_SYMBOL)
        nifty_price = fetch_live_data(NIFTY_SYMBOL)

        # Default signal values
        bank_signal, bank_entry, bank_sl, bank_tp = "HOLD", None, None, None
        nifty_signal, nifty_entry, nifty_sl, nifty_tp = "HOLD", None, None, None

        # Compute trading signals
        if bank_nifty_price:
            bank_nifty_history.append({"high": bank_nifty_price, "low": bank_nifty_price, "close": bank_nifty_price})
            bank_signal, bank_entry, bank_sl, bank_tp = compute_vwm_signal(bank_nifty_history, "BANK NIFTY")

        if nifty_price:
            nifty_history.append({"high": nifty_price, "low": nifty_price, "close": nifty_price})
            nifty_signal, nifty_entry, nifty_sl, nifty_tp = compute_vwm_signal(nifty_history, "NIFTY")

        # If a new signal appears, send an alert
        if (bank_signal != "HOLD" and bank_signal != last_bank_signal) or (nifty_signal != "HOLD" and nifty_signal != last_nifty_signal):
            message = "📌 *PLACE THE ORDER*\n"

            if bank_signal != "HOLD":
                rounded_bank_entry = round_to_nearest_100(bank_entry)
                message += f"\n🔵 BANK NIFTY - {bank_signal} at {rounded_bank_entry}\n🎯 Profit Target: {bank_tp}\n🛑 Stop-Loss: {bank_sl}\n"

            if nifty_signal != "HOLD":
                rounded_nifty_entry = round_to_nearest_50(nifty_entry)
                message += f"\n🔴 NIFTY - {nifty_signal} at {rounded_nifty_entry}\n🎯 Profit Target: {nifty_tp}\n🛑 Stop-Loss: {nifty_sl}\n"

            send_telegram_alert(message)
            last_bank_signal = bank_signal
            last_nifty_signal = nifty_signal

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        send_telegram_alert(f"Script Error: {str(e)}")

    time.sleep(60)  # Fetch data every 1 minute
