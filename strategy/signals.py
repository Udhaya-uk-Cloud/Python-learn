# strategy/signals.py
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands
from utils.rounding import round_to_nearest_50, round_to_nearest_100

# Strategy parameters
ema_short = 9
ema_long = 21
rsi_period = 14
stop_loss_multiplier = 1.5
profit_target_multiplier = 2.5

# Globals for VWM logic
last_signals = {}
confirmation_counters = {}
last_trade_price = {}

def compute_signals(prices, symbol):
    df = pd.DataFrame(list(prices))
    df['RSI'] = RSIIndicator(df['close'], rsi_period).rsi()
    df['EMA_Short'] = EMAIndicator(df['close'], ema_short).ema_indicator()
    df['EMA_Long'] = EMAIndicator(df['close'], ema_long).ema_indicator()
    df['ATR'] = AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    df['MACD'] = MACD(df['close']).macd_diff()
    df['Bollinger_Lower'] = BollingerBands(df['close']).bollinger_lband()
    df['Bollinger_Upper'] = BollingerBands(df['close']).bollinger_hband()
    df['Stochastic_K'] = StochasticOscillator(df['high'], df['low'], df['close']).stoch()

    latest = df.iloc[-1]
    signal = "HOLD"
    entry_price = None

    if latest['EMA_Short'] > latest['EMA_Long'] and latest['RSI'] > 55 and latest['MACD'] > 0 and latest['close'] > latest['Bollinger_Lower']:
        if latest['Stochastic_K'] < 20:
            signal = "BUY"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    elif latest['EMA_Short'] < latest['EMA_Long'] and latest['RSI'] < 45 and latest['MACD'] < 0 and latest['close'] < latest['Bollinger_Upper']:
        if latest['Stochastic_K'] > 80:
            signal = "SELL"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    if entry_price:
        sl = entry_price - (stop_loss_multiplier * latest['ATR']) if signal == "BUY" else entry_price + (stop_loss_multiplier * latest['ATR'])
        pt = entry_price + (profit_target_multiplier * latest['ATR']) if signal == "BUY" else entry_price - (profit_target_multiplier * latest['ATR'])
        return signal, entry_price, sl, pt

    return "HOLD", None, None, None

def compute_vwm_signal(prices, symbol):
    df = pd.DataFrame(list(prices))
    if len(df) < 20:
        return "HOLD", None, None, None

    df['EMA_Short'] = EMAIndicator(df['close'], ema_short).ema_indicator()
    df['EMA_Long'] = EMAIndicator(df['close'], ema_long).ema_indicator()
    df['ATR'] = AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()

    latest = df.iloc[-1]
    ema_gap = abs(latest['EMA_Short'] - latest['EMA_Long'])

    threshold = 8.5 if "NIFTY 50" in symbol else 27.5
    if ema_gap < threshold:
        return f"\u26A0 Weak Trend in {symbol.split(':')[1]}: EMA Gap {ema_gap:.2f} too small (Threshold: {threshold})", None, None, None

    entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])
    sl = entry_price - (stop_loss_multiplier * latest['ATR'])
    pt = entry_price + (profit_target_multiplier * latest['ATR'])

    return "BUY", entry_price, sl, pt