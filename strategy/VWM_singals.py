import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
from utils.rounding import round_to_nearest_50, round_to_nearest_100
from utils.logger import logger

# Global dictionaries to track last signals & confirmation counts
last_signals = {}
confirmation_counters = {}
last_trade_price = {}

def compute_vwm_signal(prices, symbol):
    """Computes signals using Volume-Weighted Market (VWM) strategy."""
    global last_signals, confirmation_counters, last_trade_price

    df = pd.DataFrame(list(prices))  
    if len(df) < 20:
        return "HOLD", None, None, None

    # Compute indicators
    df["RSI"] = RSIIndicator(df["close"], window=14).rsi().fillna(50)
    df["EMA_Short"] = EMAIndicator(df["close"], window=9).ema_indicator().bfill()
    df["EMA_Long"] = EMAIndicator(df["close"], window=21).ema_indicator().bfill()
    df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["MACD_Diff"] = MACD(df["close"]).macd_diff().fillna(0)

    # Extract latest values
    latest_close = df.iloc[-1]["close"]
    latest_atr = df.iloc[-1]["ATR"]
    latest_rsi = df.iloc[-1]["RSI"]
    latest_ema_short = df.iloc[-1]["EMA_Short"]
    latest_ema_long = df.iloc[-1]["EMA_Long"]
    latest_macd_diff = df.iloc[-1]["MACD_Diff"]

    # Define entry price based on instrument
    entry_price = round_to_nearest_100(latest_close) if "BANK" in symbol else round_to_nearest_50(latest_close)

    # Initialize signal
    new_signal = "HOLD"

    # Ensure tracking variables are initialized
    last_signals.setdefault(symbol, "HOLD")
    confirmation_counters.setdefault(symbol, 0)
    last_trade_price.setdefault(symbol, 0)

    # ATR-based Stop-Loss & Profit Target (Dynamic Scaling)
    atr_mean = df["ATR"].rolling(20).mean().iloc[-1]
    atr_ratio = latest_atr / atr_mean if atr_mean != 0 else 1
    atr_multiplier = max(2.5, min(5.5, round(3 + (atr_ratio - 1) * 2, 1)))

    stop_loss = round(entry_price - (atr_multiplier * latest_atr), 2)
    profit_target = round(entry_price + (atr_multiplier * latest_atr), 2)

    logger.info(f"📊 ATR Multiplier: {atr_multiplier} | Entry: {entry_price} | SL: {stop_loss} | PT: {profit_target}")

    # Detect sudden price spikes (manipulation)
    price_change = abs(df["close"].pct_change().iloc[-1])
    avg_price_change = df["close"].pct_change().rolling(10).mean().iloc[-1]
    std_price_change = df["close"].pct_change().rolling(10).std().iloc[-1]

    if price_change > (avg_price_change + 2.5 * std_price_change):
        logger.warning(f"❌ Potential Manipulation Detected in {symbol}: Price Spike {price_change:.2%}")

    # Prevent Executing Trades in Sideways Market
    sideways_threshold = latest_atr * 0.3
    if abs(latest_ema_short - latest_ema_long) < sideways_threshold:
        logger.info(f"⚠️ Avoiding Trade in {symbol} - Sideways Market Detected")
        return "HOLD", None, None, None

    # Prevent back-to-back trades at the same level
    if last_signals[symbol] == new_signal and abs(last_trade_price[symbol] - entry_price) < 20:
        logger.info(f"⚠️ Preventing Duplicate Trade in {symbol} at {entry_price}")
        return "HOLD", None, None, None

    # Avoid Weak Trends (Choppy Market)
    ema_gap = abs(latest_ema_short - latest_ema_long)
    atr_threshold = latest_atr * 1.5  
    if ema_gap < atr_threshold:
        logger.info(f"⚠️ Weak Trend in {symbol}: EMA Gap {ema_gap:.2f} too small (Threshold: {atr_threshold:.2f})")

    # Avoid Overbought/Oversold Conditions
    if new_signal == "BUY" and latest_rsi > 70:
        logger.info(f"⚠️ Overbought Condition in {symbol}: RSI {latest_rsi:.2f} > 70, skipping BUY signal")
        return "HOLD", None, None, None

    if new_signal == "SELL" and latest_rsi < 30:
        logger.info(f"⚠️ Oversold Condition in {symbol}: RSI {latest_rsi:.2f} < 30, skipping SELL signal")
        return "HOLD", None, None, None

    # Stability Filter to Prevent False Reversals
    if latest_rsi > 50 and latest_ema_short > latest_ema_long and latest_macd_diff > 0:
        new_signal = "BUY"
    elif latest_rsi < 50 and latest_ema_short < latest_ema_long and latest_macd_diff < 0:
        new_signal = "SELL"

    # Confirm Reversals with Stability Filter
    confirmation_threshold = 3
   
