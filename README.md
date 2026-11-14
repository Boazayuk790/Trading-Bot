# CRT Signal Scanner (XAUUSD)

A small, tested Python CLI that detects **Candle Range Theory (CRT)** setups on gold price data and prints Entry, Stop-Loss and Take-Profit levels. It reads live candles from MetaTrader 5 or a CSV file.

> **Research tool only. It never places trades, and it is not financial advice.**
> **My own backtests found no trading edge (see [Results](#results)).** This repo is about the engineering, not a profitable strategy.

## What this project shows

- **Signal logic kept separate from I/O.** `crt_signal()` is a pure function with no MT5 dependency, so it is testable with hand-made candles.
- **Explicit edge-case rules, each covered by a test:** a close exactly on C1's boundary does not count as "inside", a candle that sweeps both sides of C1 is skipped, and a still-forming candle is never used.
- **Two data sources, one code path:** live MT5 or CSV, so the tool works on any OS without MetaTrader.
- **Honest results:** negative findings are published, not hidden.

## How the CRT rule is implemented

- **C1** = range candle, **C2** = manipulation candle. Both must be closed.
- **BUY:** C2's low is below C1's low, and C2 closes strictly inside C1's range.
- **SELL:** C2's high is above C1's high, and C2 closes strictly inside C1's range.
- If C2 breaks **both** sides of C1, the setup is ambiguous and is skipped.
- **Entry** = C2's close. **Stop-loss** = C2's wick extreme. **Take-profit** = the far side of C1 (`range` mode) or a fixed reward:risk such as `2` for 1:2.
- The `time` field is C2's bar-open time. The signal is only known once C2 has closed.

## Quick start

```bash
git clone https://github.com/Boazayuk790/Trading-Bot.git
cd Trading-Bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# No MetaTrader needed:
python crt.py --csv sample_synthetic.csv
```

Expected output on the sample file:

```text
Loaded 8 candles from 2024-01-01 00:00:00 to 2024-01-01 07:00:00
Latest signal: None

Total CRT setups found in data: 2
```

`sample_synthetic.csv` is made-up demo data (one BUY and one SELL setup). It is not real market data.

## Usage

```bash
# Live data from MT5 (Windows, terminal open and logged in)
python crt.py

# Different timeframe and fixed 1:2 reward:risk
python crt.py --tf H4 --rr 2

# From a CSV file (columns: time, open, high, low, close)
python crt.py --csv sample_synthetic.csv
```

Each run scans once and exits. Check the `Loaded N candles from ... to ...` line: if the end date is old, the MT5 terminal's history is stale and the signal is meaningless. Times from MT5 are broker server time, not UTC.

## Tests

```bash
python -m unittest discover -s tests -v
```

13 tests cover bullish and bearish setups, fixed reward:risk, no sweep, a sweep that closes outside the range, a close exactly on the boundary, both-sides sweeps, forming-candle handling, CSV loading errors and the CLI on the sample file. They use hand-made candles and need no MetaTrader installation.

## Verified so far

- 13/13 tests pass, including from a fresh clone with a clean virtual environment (Python 3.10, Windows).
- Live connection works against a MetaTrader 5 demo account (MetaQuotes-Demo).

## Results

Findings from my own testing (not a trading recommendation):

- CRT on H1: no edge found.
- H4 sweep + M15 change-of-character variant: pooled profit factor 0.93 (market entry) and 0.79 (order-block entry), below break-even.
- Break and retest on XAUUSD M15: failed my out-of-sample bar.

Method: 50,000 M15 bars across 6 symbols, split into first and second halves. Pass bar: profit factor above 1.2 in both halves, or above 1.1 after doubling costs. I did not tune parameters to improve results.

These numbers come from separate research scripts that are not part of this repo. The `crt.py` in this repo has not been backtested, and the tested logic was an earlier version that did not skip candles sweeping both sides of C1.

## Limitations

- Live mode is Windows only and needs the MT5 terminal open.
- Signal generation only, no order execution.
- Stop-loss sits exactly on C2's wick, so spread is not accounted for.
- The detection rule is loose: on H1 gold, roughly one candle in three can qualify.
- No demonstrated trading edge.

## License

MIT. See [LICENSE](LICENSE).

## Author

Boaz Ayuk, [GitHub: Boazayuk790](https://github.com/Boazayuk790)
