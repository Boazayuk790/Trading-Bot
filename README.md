# CRT Signal Scanner (XAUUSD)

Python tool that connects to MetaTrader 5, pulls historical price data for Gold (XAUUSD), and detects **Candle Range Theory (CRT)** trading setups.

It identifies bullish and bearish CRT patterns and returns clear Entry, Stop-Loss, and Take-Profit levels.

> Educational / research tool only. Does **not** place real trades.

## Features
- Connects to MetaTrader 5
- Fetches historical OHLCV data
- Detects CRT setups (range candle + manipulation candle)
- Calculates Entry / SL / TP (range-based or fixed Risk:Reward)
- Scans full history + checks latest closed candles
- Clean terminal output

## Requirements
- Windows (MetaTrader 5 limitation)
- Python 3.9+
- MetaTrader 5 terminal installed and logged in
- XAUUSD visible in Market Watch

## Installation
```bash
git clone [https://github.com/Boazayuk790/Trading-Bot.git](https://github.com/Boazayuk790/Trading-Bot.git)
cd Trading-Bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

Usage
1. Open MetaTrader 5 and log in (demo account is fine)
2. Run:
BASH
python bot.py
• LTE
64)
• Copy
Example Output
• Copy
Connected: 12345678
Latest signal: {'dir': 'BUY',
'entry': 2650.45,
's1': 2648.20, 'tp': 2654.10, 'time':
...}
Total setups in data: 37
How CRT Logic Works
• C1 = Range candle
• c2 = Manipulation candle
Bullish: c2 sweeps below c1 low and closes back inside the range.
Bearish: c2 sweeps above c1 high and closes back inside the range

Configurable: SYMBOL, TIMEFRAME, RR_TARGET
Limitations
•  Windows only
•  Signal generation only (no order execution)
•  No full backtesting metrics yet
•  Requires MT5 to be open
Author
Boaz Lawrence Ayuk
GitHub: Boazayuk790