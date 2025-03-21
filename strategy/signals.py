import pandas as pd
from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator, StochasticOscillator
import pandas_ta as ta
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
import numpy as np
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger
from market_data.fetch_data import fetch_historical_data
from utils.config_loader import ATR_MULTIPLIER, EMA_SHORT, EMA_LONG, MACD_FAST, MACD_SLOW, MACD_SIGNAL

class VWMSignalProcessor:
    def __init__(self):
        self.last_signals = {}
        self.last_trade_price = {}

    def compute_vwm_signal(self, prices, symbol):
        """Compute trading signals using VWM strategy with VWAP, ATR, and momentum indicators."""
        df = pd.DataFrame(list(prices))

        # ✅ Check for missing or empty data
        if df.empty or df.isnull().values.any():
            logger.warning(f"⚠️ {symbol}: Missing or incomplete data detected. Skipping signal computation.")
            return "HOLD", None, None, None

        if len(df) < 20:
            return "HOLD", None, None, None

        # ✅ Compute Technical Indicators using dynamic values
        df["RSI"] = RSIIndicator(df["close"], window=14).rsi().fillna(50)
        df["EMA_Short"] = EMAIndicator(df["close"], window=EMA_SHORT).ema_indicator().bfill()
        df["EMA_Long"] = EMAIndicator(df["close"], window=EMA_LONG).ema_indicator().bfill()
        df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["MACD_Diff"] = MACD(df["close"], window_slow=MACD_SLOW, window_fast=MACD_FAST, window_sign=MACD_SIGNAL).macd_diff().fillna(0)
        df["VWAP"] = VolumeWeightedAveragePrice(df["high"], df["low"], df["close"], df["volume"]).volume_weighted_average_price()
        df["SuperTrend"] = ta.supertrend(df["high"], df["low"], df["close"], length=10, multiplier=3)["SUPERT_10_3.0"]

        # ✅ Ensure NaN values are handled correctly
        df.fillna(method='bfill', inplace=True)  # ✅ Backfill missing values
        df.fillna(method='ffill', inplace=True)  # ✅ Forward-fill if needed
        
        # ✅ Compute VWAP
        df["VWAP"] = VolumeWeightedAveragePrice(df["high"], df["low"], df["close"], df["volume"]).volume_weighted_average_price()

        # ✅ Bollinger Bands & Stochastic Oscillator
        bollinger = BollingerBands(df["close"])
        df["Bollinger_Lower"] = bollinger.bollinger_lband()
        df["Bollinger_Upper"] = bollinger.bollinger_hband()

        stochastic = StochasticOscillator(df["high"], df["low"], df["close"], window=14)
        df["Stochastic_K"] = stochastic.stoch()

        latest = df.iloc[-1]  # ✅ Correct placement for latest data

        # ✅ Debug log for indicator values
        logger.debug(f"{symbol} Indicators - RSI: {latest['RSI']}, MACD Diff: {latest['MACD_Diff']}, EMA Gap: {latest['EMA_Long'] - latest['EMA_Short']}, ATR: {latest['ATR']}")

        signal = "HOLD"
        entry_price = None

        # ✅ Sideways Market Detection
        sideways_threshold = latest["ATR"] * 0.3
        if abs(latest["EMA_Short"] - latest["EMA_Long"]) < sideways_threshold:
            logger.warning(f"⚠️ Avoiding Trade in {symbol} - Sideways Market Detected")
            return "HOLD", None, None, None
        
        signal = "HOLD"
        entry_price = None

        # ✅ SuperTrend Confirmation for Stronger Trend Detection
        if latest["SuperTrend"] < latest["close"] and latest["RSI"] > 48 and latest["MACD_Diff"] > -0.5:
            if latest["Stochastic_K"] < 40:
                signal = "BUY"
        elif latest["SuperTrend"] > latest["close"] and latest["RSI"] < 52 and latest["MACD_Diff"] < 0.3:
            if latest["Stochastic_K"] > 60:
                signal = "SELL"
        
        if signal != "HOLD":
            entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])

        # ✅ ATR-Based Stop-Loss & Profit Target
        atr_mean = df["ATR"].rolling(20).mean().iloc[-1]
        atr_ratio = latest["ATR"] / atr_mean if atr_mean != 0 else 1
        atr_multiplier = round(3 + (atr_ratio - 1) * 2, 1)
        atr_multiplier = max(2.5, min(5.5, atr_multiplier))
        stop_loss = round(entry_price - (atr_multiplier * latest["ATR"])) if signal == "BUY" else round(entry_price + (atr_multiplier * latest["ATR"]))
        profit_target = round(entry_price + (3.0 * latest["ATR"])) if signal == "BUY" else round(entry_price - (3.0 * latest["ATR"]))
        
        # ✅ Confirmation Mechanism to Reduce False Signals
        confirmation_threshold = 3
        if symbol not in self.confirmation_counters:
            self.confirmation_counters[symbol] = 0
        if signal != "HOLD":
            if signal == self.last_signals.get(symbol, "HOLD"):
                self.confirmation_counters[symbol] = 0
            else:
                self.confirmation_counters[symbol] += 1
                if self.confirmation_counters[symbol] < confirmation_threshold:
                    return "HOLD", None, None, None


        # ✅ Trend Following Strategy (Breakout Confirmation)
        if latest["RSI"] > 48 and latest["MACD_Diff"] > -0.5 and latest["close"] > latest["EMA_Long"]:
            if latest["Stochastic_K"] < 40:
                signal = "BUY"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                logger.info(f"🚀 Time to enter {symbol}: Signal = {signal}, Entry Price = {entry_price}")

        elif latest["RSI"] < 52 and latest["MACD_Diff"] < 0.3 and latest["close"] < latest["EMA_Long"]:
            if latest["Stochastic_K"] > 60:
                signal = "SELL"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                logger.info(f"📉 Time to enter {symbol}: Signal = {signal}, Entry Price = {entry_price}")

        # ✅ VWAP Confirmation Strategy
        if signal == "HOLD":
            if latest["close"] > latest["VWAP"] and latest["volume"] > df["volume"].rolling(5).mean():
                signal = "BUY"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                logger.info(f"🚀 VWAP Confirmation: {symbol} is moving up. BUY at {entry_price}")

            elif latest["close"] < latest["VWAP"] and latest["volume"] > df["volume"].rolling(5).mean():
                signal = "SELL"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                logger.info(f"📉 VWAP Confirmation: {symbol} is moving down. SELL at {entry_price}")

        # ✅ Liquidity Trap Prevention
        if abs(latest["close"] - latest["VWAP"]) > (1.5 * latest["ATR"]):
            signal = "HOLD"
            logger.warning(f"⚠️ {symbol}: Liquidity trap detected. Skipping trade.")

        # ✅ ATR-Based Stop-Loss & Profit Target
        if entry_price is not None:
            stop_loss = round(entry_price - (ATR_MULTIPLIER * latest["ATR"])) if signal == "BUY" else round(entry_price + (ATR_MULTIPLIER * latest["ATR"]))
            profit_target = round(entry_price + (3.0 * latest["ATR"])) if signal == "BUY" else round(entry_price - (3.0 * latest["ATR"]))
        else:
            stop_loss, profit_target = None, None

        # ✅ Prevent Duplicate Trades
        if signal != "HOLD" and abs(self.last_trade_price.get(symbol, 0) - entry_price) < 20:
            logger.warning(f"⚠️ Preventing Duplicate Trade in {symbol} at {entry_price}")
            return "HOLD", None, None, None

        # ✅ Show Signal & Store Last Trade Price
        if signal != "HOLD":
            logger.info(f"🚀 {symbol} Trade Alert: {signal} at {entry_price} | 🎯 Target: {profit_target} | 🛑 Stop-Loss: {stop_loss}")
            self.last_signals[symbol] = signal
            self.last_trade_price[symbol] = entry_price

        return signal, entry_price, stop_loss, profit_target

# ✅ Market Structure Detection
def detect_market_structure(df):
    """Detects market structure changes (Break of Structure, Change of Character)."""
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(list(df))  # Convert deque to DataFrame

    if len(df) < 2:
        return "NO_DATA"

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if latest["high"] > previous["high"]:  
        return "BULLISH_BOS"  # ✅ Break of Structure (Bullish)
    elif latest["low"] < previous["low"]:  
        return "BEARISH_BOS"  # ✅ Break of Structure (Bearish)
    else:
        return "NO_CHANGE"

# ✅ Instantiate Processor Globally
vwm_processor = VWMSignalProcessor()
