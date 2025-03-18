from strategy.indicators import compute_indicators
from utils.rounding import round_to_nearest_50, round_to_nearest_100

def compute_signals(df, symbol):
    df = compute_indicators(df)
    latest = df.iloc[-1]
    signal, entry_price = "HOLD", None

    if latest['RSI'] > 55 and latest['MACD'] > 0 and latest['close'] > latest['Bollinger_Lower']:
        if latest['Stochastic_K'] < 20:
            signal = "BUY"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    elif latest['RSI'] < 45 and latest['MACD'] < 0 and latest['close'] < latest['Bollinger_Upper']:
        if latest['Stochastic_K'] > 80:
            signal = "SELL"
            entry_price = round_to_nearest_100(latest['close']) if "BANK" in symbol else round_to_nearest_50(latest['close'])

    return signal, entry_price
