import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from pathlib import Path

# ======================
# CONFIGURATION
# ======================
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_H1          # H1 or H4 recommended
BARS = 500
RR_TARGET = "range"                   # "range" or a number (e.g. 2 for 1:2 RR)
EXPORT_SIGNALS = True                 # Set to False if you don't want CSV export
EXPORT_FILENAME = "crt_signals.csv"


def connect() -> bool:
    """Initialize connection to MetaTrader 5."""
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return False

    account_info = mt5.account_info()
    if account_info is None:
        print("❌ Failed to get account info")
        mt5.shutdown()
        return False

    print(f"✅ Connected to MT5 | Account: {account_info.login} | Server: {account_info.server}")
    return True


def get_rates(symbol: str = SYMBOL, tf=TIMEFRAME, bars: int = BARS) -> pd.DataFrame | None:
    """Fetch historical rates and return as a clean DataFrame."""
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
    
    if rates is None or len(rates) == 0:
        print(f"❌ Failed to get rates for {symbol}. Error: {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df[["time", "open", "high", "low", "close", "tick_volume"]].copy()
    return df


def crt_signal(c1: pd.Series, c2: pd.Series) -> dict | None:
    """
    Detect CRT (Candle Range Theory) setup.
    
    c1 = range candle
    c2 = manipulation candle (both must be closed)
    
    BUY  : c2 sweeps below c1 low and closes back inside the range
    SELL : c2 sweeps above c1 high and closes back inside the range
    """
    # Bullish CRT
    if c2["low"] < c1["low"] and c1["low"] < c2["close"] < c1["high"]:
        entry = c2["close"]
        sl = c2["low"]
        tp = c1["high"] if RR_TARGET == "range" else entry + (entry - sl) * float(RR_TARGET)
        return {
            "direction": "BUY",
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "time": c2["time"],
            "risk": round(entry - sl, 2)
        }

    # Bearish CRT
    if c2["high"] > c1["high"] and c1["low"] < c2["close"] < c1["high"]:
        entry = c2["close"]
        sl = c2["high"]
        tp = c1["low"] if RR_TARGET == "range" else entry - (sl - entry) * float(RR_TARGET)
        return {
            "direction": "SELL",
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "time": c2["time"],
            "risk": round(sl - entry, 2)
        }

    return None


def scan_history(df: pd.DataFrame) -> list[dict]:
    """Scan the entire dataframe for CRT setups (useful for research)."""
    signals = []
    for i in range(1, len(df)):
        signal = crt_signal(df.iloc[i - 1], df.iloc[i])
        if signal:
            signals.append(signal)
    return signals


def latest_signal(df: pd.DataFrame) -> dict | None:
    """
    Check the last two *closed* candles.
    We use -3 and -2 because the very last candle is still forming.
    """
    if len(df) < 3:
        return None
    return crt_signal(df.iloc[-3], df.iloc[-2])


def print_signal(signal: dict | None) -> None:
    """Pretty print a single signal."""
    if signal is None:
        print("Latest signal: None")
        return

    print("\n📈 Latest CRT Signal")
    print("-" * 40)
    print(f"Direction : {signal['direction']}")
    print(f"Time      : {signal['time']}")
    print(f"Entry     : {signal['entry']}")
    print(f"Stop Loss : {signal['sl']}")
    print(f"Take Profit: {signal['tp']}")
    print(f"Risk      : {signal['risk']}")
    print("-" * 40)


def export_signals(signals: list[dict], filename: str = EXPORT_FILENAME) -> None:
    """Save all detected signals to a CSV file."""
    if not signals:
        print("No signals to export.")
        return

    df = pd.DataFrame(signals)
    df.to_csv(filename, index=False)
    print(f"\n💾 Exported {len(signals)} signals → {filename}")


def main():
    print(f"\n🚀 CRT Signal Scanner | {SYMBOL} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    if not connect():
        return

    df = get_rates()
    if df is None:
        mt5.shutdown()
        return

    print(f"📊 Loaded {len(df)} candles from {df['time'].iloc[0]} to {df['time'].iloc[-1]}")

    # Latest signal
    current = latest_signal(df)
    print_signal(current)

    # Full history scan
    all_signals = scan_history(df)
    print(f"\n🔍 Total CRT setups found in history: {len(all_signals)}")

    # Optional export
    if EXPORT_SIGNALS and all_signals:
        export_signals(all_signals)

    mt5.shutdown()
    print("\n✅ Done. MT5 connection closed.")


if __name__ == "__main__":
    main()