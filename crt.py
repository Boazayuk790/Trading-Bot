"""
CRT Signal Scanner (XAUUSD)
===========================
Detects Candle Range Theory (CRT) setups and prints Entry / Stop-Loss /
Take-Profit levels. Educational / research tool only: it never places trades.

  C1 = range candle, C2 = manipulation candle (both must be CLOSED)
  BUY : C2 sweeps below C1's low and closes back inside C1's range
  SELL: C2 sweeps above C1's high and closes back inside C1's range
  If C2 breaks BOTH sides of C1 the setup is ambiguous and is skipped.

Data sources:
  * MetaTrader 5 (Windows only, terminal open and logged in)
  * a CSV file with columns: time, open, high, low, close   (--csv)

Examples:
    python crt.py                       # live data from MT5
    python crt.py --csv sample_synthetic.csv
    python crt.py --tf H4 --rr 2        # H4 candles, fixed 1:2 reward:risk
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

try:                       # MetaTrader5 only installs on Windows
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

# ======================
# CONFIGURATION
# ======================
SYMBOL = "XAUUSD"
TIMEFRAME = "H1"           # "H1" or "H4" recommended
BARS = 500
RR_TARGET = "range"        # "range" = TP at far side of C1, or a number (2 = 1:2)
EXPORT_SIGNALS = True
EXPORT_FILENAME = "crt_signals.csv"
REQUIRED_COLUMNS = ["time", "open", "high", "low", "close"]


# ======================
# DATA LOADING
# ======================
def connect() -> bool:
    """Initialize the MetaTrader 5 connection."""
    if mt5 is None:
        print("MetaTrader5 package not available (Windows only). Use --csv instead.")
        return False
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    if info is None:
        print("Failed to get account info")
        mt5.shutdown()
        return False
    print(f"Connected to MT5 | Server: {info.server}")   # account number not printed
    return True


def get_rates(symbol: str = SYMBOL, tf: str = TIMEFRAME, bars: int = BARS) -> pd.DataFrame | None:
    """Fetch recent candles from MT5. The last row is the still-forming candle."""
    tf_const = getattr(mt5, f"TIMEFRAME_{tf}", None)
    if tf_const is None:
        print(f"Unknown timeframe '{tf}'")
        return None
    if not mt5.symbol_select(symbol, True):      # make sure it is in Market Watch
        print(f"Symbol {symbol} not found. Check the exact name in Market Watch.")
        return None
    rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, bars)
    if rates is None or len(rates) == 0:
        print(f"Failed to get rates for {symbol}. Error: {mt5.last_error()}")
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")     # broker server time, not UTC
    return df[REQUIRED_COLUMNS].copy()


def load_csv(path: str) -> pd.DataFrame:
    """Load candles from a CSV file. All rows are treated as closed candles."""
    file = Path(path)
    if not file.is_file():
        raise ValueError(f"File not found: {path}")
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing column(s): {', '.join(missing)}")
    df["time"] = pd.to_datetime(df["time"])
    df = df[REQUIRED_COLUMNS].dropna().sort_values("time").reset_index(drop=True)
    if len(df) < 2:
        raise ValueError("Need at least 2 candles.")
    return df


# ======================
# SIGNAL LOGIC (no MT5 needed)
# ======================
def crt_signal(c1: pd.Series, c2: pd.Series, rr=RR_TARGET) -> dict | None:
    """Return a signal dict if (c1, c2) form a CRT setup, else None."""
    swept_low = c2["low"] < c1["low"]
    swept_high = c2["high"] > c1["high"]
    if swept_low and swept_high:
        return None                      # ambiguous: both sides taken
    closed_inside = c1["low"] < c2["close"] < c1["high"]
    if not closed_inside:
        return None

    fixed_rr = None if rr == "range" else float(rr)

    if swept_low:                        # bullish
        entry, sl = c2["close"], c2["low"]
        tp = c1["high"] if fixed_rr is None else entry + (entry - sl) * fixed_rr
        direction, risk = "BUY", entry - sl
    elif swept_high:                     # bearish
        entry, sl = c2["close"], c2["high"]
        tp = c1["low"] if fixed_rr is None else entry - (sl - entry) * fixed_rr
        direction, risk = "SELL", sl - entry
    else:
        return None

    return {"direction": direction, "entry": round(float(entry), 2),
            "sl": round(float(sl), 2), "tp": round(float(tp), 2),
            "time": c2["time"], "risk": round(float(risk), 2)}


def scan_history(df: pd.DataFrame, rr=RR_TARGET, last_is_forming: bool = True) -> list[dict]:
    """Find every CRT setup. If the last row is still forming (MT5 data), skip it."""
    end = len(df) - 1 if last_is_forming else len(df)
    signals = []
    for i in range(1, end):
        sig = crt_signal(df.iloc[i - 1], df.iloc[i], rr)
        if sig:
            signals.append(sig)
    return signals


def latest_signal(df: pd.DataFrame, rr=RR_TARGET, last_is_forming: bool = True) -> dict | None:
    """Check the two most recent CLOSED candles."""
    c1_pos, c2_pos = (-3, -2) if last_is_forming else (-2, -1)
    if len(df) < abs(c1_pos):
        return None
    return crt_signal(df.iloc[c1_pos], df.iloc[c2_pos], rr)


# ======================
# OUTPUT
# ======================
def print_signal(signal: dict | None) -> None:
    if signal is None:
        print("Latest signal: None")
        return
    print("\nLatest CRT signal")
    print("-" * 30)
    print(f"Direction   : {signal['direction']}")
    print(f"Time        : {signal['time']}  (broker time for MT5 data)")
    print(f"Entry       : {signal['entry']}")
    print(f"Stop loss   : {signal['sl']}")
    print(f"Take profit : {signal['tp']}")
    print(f"Risk        : {signal['risk']}")
    print("-" * 30)


def export_signals(signals: list[dict], filename: str = EXPORT_FILENAME) -> None:
    if not signals:
        print("No signals to export.")
        return
    pd.DataFrame(signals).to_csv(filename, index=False)
    print(f"Exported {len(signals)} signals to {filename}")


# ======================
# MAIN
# ======================
def parse_rr(text: str):
    if text == "range":
        return "range"
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("--rr must be 'range' or a positive number")
    if value <= 0:
        raise argparse.ArgumentTypeError("--rr must be positive")
    return value


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CRT signal scanner (research only).")
    p.add_argument("--csv", help="read candles from this CSV instead of MT5")
    p.add_argument("--symbol", default=SYMBOL)
    p.add_argument("--tf", default=TIMEFRAME, help="MT5 timeframe, e.g. H1, H4")
    p.add_argument("--bars", type=int, default=BARS)
    p.add_argument("--rr", type=parse_rr, default=RR_TARGET,
                   help="'range' or a number such as 2 for 1:2")
    p.add_argument("--no-export", action="store_true", help="do not write the signals CSV")
    args = p.parse_args(argv)

    print(f"\nCRT Signal Scanner | {args.symbol} | {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 55)

    try:
        if args.csv:
            df, forming = load_csv(args.csv), False
        else:
            if not connect():
                return 2
            df, forming = get_rates(args.symbol, args.tf, args.bars), True
            mt5.shutdown()
            if df is None:
                return 2
    except ValueError as err:
        print(f"Error: {err}")
        return 2

    print(f"Loaded {len(df)} candles from {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
    print_signal(latest_signal(df, args.rr, forming))
    all_signals = scan_history(df, args.rr, forming)
    print(f"\nTotal CRT setups found in data: {len(all_signals)}")
    if EXPORT_SIGNALS and not args.no_export and all_signals:
        export_signals(all_signals)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
