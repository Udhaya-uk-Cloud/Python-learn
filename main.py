import time
from market_data.fetch_data import fetch_historical_data, fetch_live_data
from strategy.signals import compute_signals
from alerts.telegram_alerts import send_telegram_alert

BANK_NIFTY_SYMBOL = "NSE:NIFTY BANK"
NIFTY_SYMBOL = "NSE:NIFTY 50"

bank_nifty_history = fetch_historical_data(BANK_NIFTY_SYMBOL)
nifty_history = fetch_historical_data(NIFTY_SYMBOL)

while True:
    bank_price = fetch_live_data(BANK_NIFTY_SYMBOL)
    nifty_price = fetch_live_data(NIFTY_SYMBOL)

    if bank_price:
        bank_nifty_history.append({"high": bank_price, "low": bank_price, "close": bank_price})
        bank_signal, bank_entry = compute_signals(bank_nifty_history, "BANK NIFTY")
    
    if nifty_price:
        nifty_history.append({"high": nifty_price, "low": nifty_price, "close": nifty_price})
        nifty_signal, nifty_entry = compute_signals(nifty_history, "NIFTY")

    if bank_signal != "HOLD" or nifty_signal != "HOLD":
        message = f"Order Alert:\nBank Nifty: {bank_signal} at {bank_entry}\nNifty: {nifty_signal} at {nifty_entry}"
        send_telegram_alert(message)

    time.sleep(60)
