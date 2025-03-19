import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger

class VWMSignalProcessor:
    def __init__(self):
        self.last_signals = {}
        self.confirmation_counters = {}
        self.last_trade_price = {}

    def compute_vwm_signal(self, prices, symbol):
        """Compute signals using Volume-Weighted Market (VWM) strategy."""
        df = pd.DataFrame(list(prices))
        if len(df) < 20:
            return "HOLD", None, None, None

        df["RSI"] = RSIIndicator(df["close"], window=14).rsi().fillna(50)
        df["EMA_Short"] = EMAIndicator(df["close"], window=9).ema_indicator().bfill()
        df["EMA_Long"] = EMAIndicator(df["close"], window=21).ema_indicator().bfill()
        df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["MACD_Diff"] = MACD(df["close"]).macd_diff().fillna(0)

        latest = df.iloc[-1]
        new_signal = "HOLD"
        entry_price = None

        # Use instance variables instead of global ones
        self.last_signals.setdefault(symbol, "HOLD")
        self.confirmation_counters.setdefault(symbol, 0)
        self.last_trade_price.setdefault(symbol, 0)

        # Signal computation logic
        if latest["RSI"] > 55 and latest["MACD_Diff"] > 0 and latest["close"] > latest["EMA_Long"]:
            new_signal = "BUY"
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
        elif latest["RSI"] < 45 and latest["MACD_Diff"] < 0 and latest["close"] < latest["EMA_Long"]:
            new_signal = "SELL"
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])

        # ATR-based dynamic stop-loss and profit target
        stop_loss = round(entry_price - (2 * latest["ATR"])) if new_signal == "BUY" else round(entry_price + (2 * latest["ATR"]))
        profit_target = round(entry_price + (3 * latest["ATR"])) if new_signal == "BUY" else round(entry_price - (3 * latest["ATR"]))

        return new_signal, entry_price, stop_loss, profit_target

# Instantiate processor globally
vwm_processor = VWMSignalProcessor()