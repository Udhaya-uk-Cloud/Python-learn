class VWMSignalProcessor:
    def __init__(self):
        self.last_signals = {}
        self.confirmation_counters = {}
        self.last_trade_price = {}

    def compute_vwm_signal(self, prices, symbol):
        """Compute signals using Volume-Weighted Market (VWM) strategy."""
        df = pd.DataFrame(list(prices))
        if len(df) < 20:
            return "HOLD", None, None, None

        df["RSI"] = RSIIndicator(df["close"], window=14).rsi().fillna(50)
        df["EMA_Short"] = EMAIndicator(df["close"], window=9).ema_indicator().bfill()
        df["EMA_Long"] = EMAIndicator(df["close"], window=21).ema_indicator().bfill()
        df["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["MACD_Diff"] = MACD(df["close"]).macd_diff().fillna(0)

        latest = df.iloc[-1]

        # Use instance variables instead of global ones
        self.last_signals.setdefault(symbol, "HOLD")
        self.confirmation_counters.setdefault(symbol, 0)
        self.last_trade_price.setdefault(symbol, 0)

        # Compute signals as before...

        return new_signal, entry_price, stop_loss, profit_target

# Instantiate processor globally
vwm_processor = VWMSignalProcessor()
