# main.py
from market_data.fetcher import fetch_historical_data
from strategy.signal_generator import compute_signals, compute_vwm_signal
from alerts.telegram import send_telegram_alert
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Symbols to track
symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK"]

while True:
    for symbol in symbols:
        logging.info(f"\U0001F50D Fetching data for {symbol}...")
        data = fetch_historical_data(symbol)

        if len(data) < 20:
            logging.warning(f"Not enough data for {symbol}")
            continue

        signal, entry, sl, pt = compute_signals(data, symbol)
        vwm_signal, vwm_entry, vwm_sl, vwm_pt = compute_vwm_signal(data, symbol)

        if signal != "HOLD":
            msg = f"\U0001F4CA ATR Multiplier Signal for {symbol}: {signal} | Entry: {entry} | SL: {sl:.2f} | PT: {pt:.2f}"
            logging.info(msg)
            send_telegram_alert(msg)

        if vwm_signal.startswith("\u26A0"):
            logging.warning(vwm_signal)
            send_telegram_alert(vwm_signal)

    logging.info("\u23F3 Waiting for next trading cycle...")
    time.sleep(60)