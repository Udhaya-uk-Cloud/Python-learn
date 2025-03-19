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
        """Compute signals using a refined Volume-Weighted Market (VWM) strategy."""
        df = pd.DataFrame(list(prices))
        if len(df) < 20:
            return "HOLD", None, None, None

        # ✅ Compute Indicators
        df["RSI"] = RSIIndicator(df["close"], window=14).rsi().fillna(50)
        df["EMA_Short"] = EMAIndicator(df["close"], window=9).ema_indicator().bfill()
        df["EMA_Long"] = EMAIndicator(df["close"], window=21).ema_indicator().bfill()
        df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["MACD_Diff"] = MACD(df["close"]).macd_diff().fillna(0)

        latest = df.iloc[-1]
        new_signal = "HOLD"
        entry_price = None

        # ✅ Store previous values to prevent duplicate trades
        self.last_signals.setdefault(symbol, "HOLD")
        self.confirmation_counters.setdefault(symbol, 0)
        self.last_trade_price.setdefault(symbol, 0)

        # ✅ Debug Log: Print Indicator Values for Analysis
        print(f"\n📊 DEBUG {symbol}:")
        print(f"RSI={latest['RSI']:.2f}, MACD={latest['MACD_Diff']:.2f}, EMA_Short={latest['EMA_Short']:.2f}, EMA_Long={latest['EMA_Long']:.2f}, ATR={latest['ATR']:.2f}, Close={latest['close']:.2f}")

        # ✅ Adjusted Buy/Sell Signal Conditions for More Signals
        if (
            latest["RSI"] > 52 and  # Loosened RSI condition
            latest["MACD_Diff"] > -0.2 and  # Adjusted MACD sensitivity
            latest["close"] > latest["EMA_Short"] and
            latest["close"] > latest["EMA_Long"]
        ):
            new_signal = "BUY"
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
            print(f"🚀 BUY Signal for {symbol} at {entry_price}")

        elif (
            latest["RSI"] < 48 and  # Loosened RSI condition
            latest["MACD_Diff"] < 0 and
            latest["close"] < latest["EMA_Long"]
        ):
            new_signal = "SELL"
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
            print(f"📉 SELL Signal for {symbol} at {entry_price}")

        # ✅ ATR-Based Stop-Loss & Profit Target (Dynamic)
        atr_multiplier = 2.0  # Adjusted for better risk management

        if entry_price is not None:
            stop_loss = round(entry_price - (atr_multiplier * latest["ATR"])) if new_signal == "BUY" else round(entry_price + (atr_multiplier * latest["ATR"]))
            profit_target = round(entry_price + (3.0 * latest["ATR"])) if new_signal == "BUY" else round(entry_price - (3.0 * latest["ATR"]))
        else:
            stop_loss, profit_target = None, None

        # ✅ Only Show Signal if It’s Not "HOLD"
        if new_signal != "HOLD":
            print(f"🚀 {symbol} Trade Alert: {new_signal} at {entry_price} | 🎯 Target: {profit_target} | 🛑 Stop-Loss: {stop_loss}")

        return new_signal, entry_price, stop_loss, profit_target

# ✅ Instantiate Processor Globally
vwm_processor = VWMSignalProcessor()

