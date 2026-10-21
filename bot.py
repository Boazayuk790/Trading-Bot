import MetaTrader5 as mt5
import pandas as pd

SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_H1   # CRT candles (try H1 / H4)
BARS = 500
RR_TARGET = "range"            # "range" = TP at opposite side of candle 1, or a number like 2 for fixed RR


def connect():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    print("Connected:", mt5.account_info().login)


def get_rates(symbol=SYMBOL, tf=TIMEFRAME, bars=BARS):
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def crt_signal(c1, c2):
    """
    c1 = range candle, c2 = manipulation candle (both closed).
    BUY : c2 sweeps c1 low, closes back inside range.
    SELL: c2 sweeps c1 high, closes back inside range.
    """
    # Bullish CRT
    if c2["low"] < c1["low"] and c1["low"] < c2["close"] < c1["high"]:
        entry = c2["close"]
        sl = c2["low"]
        tp = c1["high"] if RR_TARGET == "range" else entry + (entry - sl) * RR_TARGET
        return {"dir": "BUY", "entry": entry, "sl": sl, "tp": tp, "time": c2["time"]}

    # Bearish CRT
    if c2["high"] > c1["high"] and c1["low"] < c2["close"] < c1["high"]:
        entry = c2["close"]
        sl = c2["high"]
        tp = c1["low"] if RR_TARGET == "range" else entry - (sl - entry) * RR_TARGET
        return {"dir": "SELL", "entry": entry, "sl": sl, "tp": tp, "time": c2["time"]}

    return None


def scan_history(df):
    """Find every CRT setup in the data (for backtesting later)."""
    signals = []
    for i in range(1, len(df)):
        sig = crt_signal(df.iloc[i - 1], df.iloc[i])
        if sig:
            signals.append(sig)
    return signals


def latest_signal(df):
    """Check the last two CLOSED candles (ignores the forming one)."""
    return crt_signal(df.iloc[-3], df.iloc[-2])


if __name__ == "__main__":
    connect()
    df = get_rates()
    print("Latest signal:", latest_signal(df))
    print("Total setups in data:", len(scan_history(df)))
    mt5.shutdown()
