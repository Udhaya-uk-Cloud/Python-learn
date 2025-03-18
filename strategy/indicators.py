import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands
from utils.logger import logger

def compute_indicators(df):
    """Computes various technical indicators for market analysis with logging."""
    logger.info("📊 Computing technical indicators...")
    
    df['RSI'] = RSIIndicator(df['close'], 14).rsi()
    df['EMA_Short'] = EMAIndicator(df['close'], 9).ema_indicator()
    df['EMA_Long'] = EMAIndicator(df['close'], 21).ema_indicator()
    df['ATR'] = AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    df['MACD'] = MACD(df['close']).macd_diff()
    df['Bollinger_Lower'] = BollingerBands(df['close'], window=20, window_dev=2).bollinger_lband()
    df['Bollinger_Upper'] = BollingerBands(df['close'], window=20, window_dev=2).bollinger_hband()
    df['Stochastic_K'] = StochasticOscillator(df['high'], df['low'], df['close'], window=14).stoch()
    
    logger.info(f"✅ Indicators computed: RSI={df['RSI'].iloc[-1]:.2f}, MACD={df['MACD'].iloc[-1]:.2f}, ATR={df['ATR'].iloc[-1]:.2f}")
    print(f"✅ Indicators computed: RSI={df['RSI'].iloc[-1]:.2f}, MACD={df['MACD'].iloc[-1]:.2f}, ATR={df['ATR'].iloc[-1]:.2f}")
    
    return df