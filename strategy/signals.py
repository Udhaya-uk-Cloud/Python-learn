from strategy.indicators import compute_indicators
from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from utils.rounding import round_to_nearest_50, round_to_nearest_100

def compute_signals(df, symbol):
    """Computes buy/sell signals based on technical indicators + VWAP + Reversals."""
    df = compute_indicators(df)
    latest = df.iloc[-1]
    signal, entry_price = "HOLD", None

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
    df['VWAP'] = VolumeWeightedAveragePrice(df['high'], df['low'], df['close'], df['volume']).volume_weighted_average_price()

    if signal == "HOLD":  # If no trend-following signal, check VWAP
        if latest['close'] > latest['VWAP'] and latest['volume'] > df['volume'].rolling(5).mean():
            signal = "BUY"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

        elif latest['close'] < latest['VWAP'] and latest['volume'] > df['volume'].rolling(5).mean():
            signal = "SELL"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

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
