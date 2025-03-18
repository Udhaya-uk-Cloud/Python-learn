from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from strategy.indicators import compute_indicators
from utils.rounding import round_to_nearest_50, round_to_nearest_100

def compute_signals(df, symbol):
    """Computes buy/sell signals based on indicators + VWAP + Smart Money Concepts + Reversals."""
    df = compute_indicators(df)
    latest = df.iloc[-1]
    signal, entry_price = "HOLD", None

    # ✅ Compute VWAP
    df['VWAP'] = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume']).volume_weighted_average_price()

    # ✅ Existing Strategy (Trend Following & Breakout)
    if latest['RSI'] > 55 and latest['MACD'] > 0 and latest['close'] > latest['Bollinger_Lower']:
        if latest['Stochastic_K'] < 20:
            signal = "BUY"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    elif latest['RSI'] < 45 and latest['MACD'] < 0 and latest['close'] < latest['Bollinger_Upper']:
        if latest['Stochastic_K'] > 80:
            signal = "SELL"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    # ✅ VWAP Strategy (Institutional Order Flow)
    if signal == "HOLD":  # If no trend-following signal, check VWAP
        if latest['close'] > latest['VWAP'] and latest['volume'] > df['volume'].rolling(5).mean():
            signal = "BUY"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

        elif latest['close'] < latest['VWAP'] and latest['volume'] > df['volume'].rolling(5).mean():
            signal = "SELL"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    # ✅ Avoid Liquidity Traps (If price already moved more than 1.5x ATR, skip the trade)
    if abs(latest['close'] - latest['VWAP']) > (1.5 * latest['ATR']):
        signal = "HOLD"
    
    # ✅ Mean Reversion Strategy (Reversal Trades)
    df['Bollinger_Lower'] = BollingerBands(df['close']).bollinger_lband()
    df['Bollinger_Upper'] = BollingerBands(df['close']).bollinger_hband()
    df['RSI'] = RSIIndicator(df['close'], window=14).rsi()

    if signal == "HOLD":  # If no trend or VWAP signal, check for a reversal
        if latest['close'] <= latest['Bollinger_Lower'] and latest['RSI'] < 30:
            signal = "BUY"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

        elif latest['close'] >= latest['Bollinger_Upper'] and latest['RSI'] > 70:
            signal = "SELL"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])
    
    return signal, entry_price


def detect_market_structure(df):
    """Detects market structure changes (Break of Structure, Change of Character)."""
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if latest['high'] > previous['high']:  # BOS (Break of Structure)
        return "BULLISH_BOS"
    elif latest['low'] < previous['low']:  # BOS (Break of Structure)
        return "BEARISH_BOS"
    else:
        return "NO_CHANGE"

# Detect Market Structure
market_structure = detect_market_structure(df)

# Trade only when BOS confirms the trend
if market_structure == "BULLISH_BOS" and signal == "BUY":
    pass  # Keep trade

elif market_structure == "BEARISH_BOS" and signal == "SELL":
    pass  # Keep trade

else:
    signal = "HOLD"  # If no BOS, avoid trade
