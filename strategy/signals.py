import pandas as pd
from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger
from market_data.fetch_data import fetch_historical_data

class VWMSignalProcessor:
    def __init__(self):
        self.last_signals = {}
        self.last_trade_price = {}

    def compute_vwm_signal(self, prices, symbol):
        """Compute trading signals using VWM strategy with VWAP, ATR, and momentum indicators."""
        df = pd.DataFrame(list(prices))
        if len(df) < 20:
            return "HOLD", None, None, None

        # ✅ Compute Technical Indicators
        df["RSI"] = RSIIndicator(df["close"], window=14).rsi().fillna(50)
        df["EMA_Short"] = EMAIndicator(df["close"], window=9).ema_indicator().bfill()
        df["EMA_Long"] = EMAIndicator(df["close"], window=21).ema_indicator().bfill()
        df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["MACD_Diff"] = MACD(df["close"]).macd_diff().fillna(0)

        # ✅ Compute VWAP
        df["VWAP"] = VolumeWeightedAveragePrice(df["high"], df["low"], df["close"], df["volume"]).volume_weighted_average_price()

        # ✅ Bollinger Bands & Stochastic Oscillator
        bollinger = BollingerBands(df["close"])
        df["Bollinger_Lower"] = bollinger.bollinger_lband()
        df["Bollinger_Upper"] = bollinger.bollinger_hband()

        stochastic = StochasticOscillator(df["high"], df["low"], df["close"], window=14)
        df["Stochastic_K"] = stochastic.stoch()

        latest = df.iloc[-1]
        signal = "HOLD"
        entry_price = None

        # ✅ Trend Following Strategy (Breakout Confirmation)
        if latest["RSI"] > 55 and latest["MACD_Diff"] > 0 and latest["close"] > latest["EMA_Long"]:
            if latest["Stochastic_K"] < 20:
                signal = "BUY"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                print(f"🚀 Time to enter {symbol}: Signal = {signal}, Entry Price = {entry_price}")

        elif latest["RSI"] < 45 and latest["MACD_Diff"] < 0 and latest["close"] < latest["EMA_Long"]:
            if latest["Stochastic_K"] > 80:
                signal = "SELL"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                print(f"📉 Time to enter {symbol}: Signal = {signal}, Entry Price = {entry_price}")

        # ✅ VWAP Confirmation Strategy
        if signal == "HOLD":
            if latest["close"] > latest["VWAP"] and latest["volume"] > df["volume"].rolling(5).mean():
                signal = "BUY"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                print(f"🚀 VWAP Confirmation: {symbol} is moving up. BUY at {entry_price}")

            elif latest["close"] < latest["VWAP"] and latest["volume"] > df["volume"].rolling(5).mean():
                signal = "SELL"
                entry_price = round_to_nearest_100(latest["close"]) if "BANK" in symbol else round_to_nearest_50(latest["close"])
                print(f"📉 VWAP Confirmation: {symbol} is moving down. SELL at {entry_price}")

        # ✅ Liquidity Trap Prevention
        if abs(latest["close"] - latest["VWAP"]) > (1.5 * latest["ATR"]):
            signal = "HOLD"
            print(f"⚠️ {symbol}: Liquidity trap detected. Skipping trade.")

        # ✅ ATR-Based Stop-Loss & Profit Target
        atr_multiplier = 3.0  # Adjusted ATR multiplier
        if entry_price is not None:
            stop_loss = round(entry_price - (atr_multiplier * latest["ATR"])) if signal == "BUY" else round(entry_price + (atr_multiplier * latest["ATR"]))
            profit_target = round(entry_price + (4.0 * latest["ATR"])) if signal == "BUY" else round(entry_price - (4.0 * latest["ATR"]))
        else:
            stop_loss, profit_target = None, None

        # ✅ Prevent Duplicate Trades
        if signal != "HOLD" and abs(self.last_trade_price.get(symbol, 0) - entry_price) < 20:
            print(f"⚠️ Preventing Duplicate Trade in {symbol} at {entry_price}")
            return "HOLD", None, None, None

        # ✅ Show Signal & Store Last Trade Price
        if signal != "HOLD":
            print(f"🚀 {symbol} Trade Alert: {signal} at {entry_price} | 🎯 Target: {profit_target} | 🛑 Stop-Loss: {stop_loss}")
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

# ✅ Fetch Market Data for NIFTY & Detect Market Structure
df = fetch_historical_data("NSE:NIFTY 50")

if len(df) > 1:
    market_structure = detect_market_structure(df)
    print(f"📊 Market Structure Detected: {market_structure}")
else:
    market_structure = "NO_DATA"
    print("⚠️ Market data not available. Skipping market structure detection.")
