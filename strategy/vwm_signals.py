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
        print(f"\n📊 DEBUG {symbol}: RSI={latest['RSI']:.2f}, MACD={latest['MACD_Diff']:.2f}, EMA_Short={latest['EMA_Short']:.2f}, EMA_Long={latest['EMA_Long']:.2f}, ATR={latest['ATR']:.2f}, Close={latest['close']:.2f}")

        # ✅ Adjusted Buy/Sell Signal Conditions for More Signals
        if (
            latest["RSI"] > 52 and  # RSI above 52 for better momentum
            latest["MACD_Diff"] > 0 and  # MACD positive to confirm trend
            latest["close"] > latest["EMA_Long"]  # Price above EMA_Long for trend confirmation
        ):
            new_signal = "BUY"
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])

        elif (
            latest["RSI"] < 48 and  # RSI below 48 for sell signal
            latest["MACD_Diff"] < 0 and  # MACD negative to confirm downtrend
            latest["close"] < latest["EMA_Long"]  # Price below EMA_Long for sell confirmation
        ):
            new_signal = "SELL"
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])

        # ✅ ATR-Based Stop-Loss & Profit Target (Dynamic)
        atr_multiplier = 2.5  # Increased multiplier for better trade flexibility

        if entry_price is not None:
            stop_loss = round(entry_price - (atr_multiplier * latest["ATR"])) if new_signal == "BUY" else round(entry_price + (atr_multiplier * latest["ATR"]))
            profit_target = round(entry_price + (4.0 * latest["ATR"])) if new_signal == "BUY" else round(entry_price - (4.0 * latest["ATR"]))
        else:
            stop_loss, profit_target = None, None

        # ✅ Prevent Duplicate Trades at Similar Levels
        if new_signal != "HOLD" and abs(self.last_trade_price[symbol] - entry_price) < 20:
            print(f"⚠️ Preventing Duplicate Trade in {symbol} at {entry_price}")
            return "HOLD", None, None, None

        # ✅ Show Signal & Send Telegram Alert (If Not HOLD)
        if new_signal != "HOLD":
            print(f"🚀 {symbol} Trade Alert: {new_signal} at {entry_price} | 🎯 Target: {profit_target} | 🛑 Stop-Loss: {stop_loss}")
        
        # ✅ Store Last Trade Price to Prevent Immediate Re-Entry
        self.last_signals[symbol] = new_signal
        self.last_trade_price[symbol] = entry_price

        return new_signal, entry_price, stop_loss, profit_target

# ✅ Instantiate Processor Globally
vwm_processor = VWMSignalProcessor()
