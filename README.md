# CRT Signal Scanner (XAUUSD)

Python tool that detects Candle Range Theory (CRT) setups on gold (XAUUSD) price data and
prints Entry, Stop-Loss and Take-Profit levels. It can read live candles from MetaTrader 5
or a CSV file.

**Educational / research tool only. It never places trades and is not financial advice.**

## How the CRT rule is implemented

- **C1** = range candle, **C2** = manipulation candle. Both must be closed candles.
- **BUY:** C2's low is below C1's low, and C2 closes inside C1's range.
- **SELL:** C2's high is above C1's high, and C2 closes inside C1's range.
- If C2 breaks **both** sides of C1, the setup is ambiguous and is skipped.
- **Entry** = C2's close. **Stop-loss** = C2's wick extreme. **Take-profit** = the far side of
  C1 (`range` mode) or a fixed reward:risk such as `2` for 1:2.
- The `time` field is C2's bar-open time. The signal is only known once C2 has closed.

## Results

Findings from my own testing (not a trading recommendation):
- CRT on H1: no edge found.
- H4 sweep + M15 change-of-character variant: pooled profit factor 0.93 (market entry) and 0.79 (order-block entry), i.e. below break-even.
- Break and retest on XAUUSD M15: failed my out-of-sample bar.

Method: 50,000 M15 bars across 6 symbols, split into first and second halves. My pass bar was profit factor above 1.2 in both halves, or above 1.1 after doubling costs. I did not tune parameters to improve results.

These numbers come from separate research scripts that are not part of this repo. The `crt.py` in this repo has not been backtested, and the tested logic was an earlier version that did not skip candles sweeping both sides of C1.

This project is a signal scanner and research exercise, not a profitable strategy.

## Requirements

- Tested on Python 3.10
- For live data: Windows, MetaTrader 5 terminal installed and logged in (a demo account is fine), XAUUSD visible in Market Watch
- For CSV mode: any OS

```bash
git clone https://github.com/Boazayuk790/Trading-Bot.git
cd Trading-Bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Live data from MT5 (Windows)
python crt.py

# Different timeframe and fixed 1:2 reward:risk
python crt.py --tf H4 --rr 2

# From a CSV file (columns: time, open, high, low, close), works without MT5
python crt.py --csv sample_synthetic.csv
```

`sample_synthetic.csv` is made-up demo data. It is not real market data.

Example output on the sample file:

```text
Loaded 8 candles from 2024-01-01 00:00:00 to 2024-01-01 07:00:00
Latest signal: None

Total CRT setups found in data: 2
```

Times from MT5 are broker server time, not UTC.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests use hand-made candles and need no MetaTrader installation.

## Limitations

- Live mode is Windows only and needs the MT5 terminal open
- Signal generation only, no order execution
- Stop-loss sits exactly on C2's wick, so spread is not accounted for
- The detection rule is loose: on H1 gold, roughly one candle in three can qualify
- No demonstrated trading edge (see Results)

## Author

Boaz Ayuk, [GitHub: Boazayuk790](https://github.com/Boazayuk790)