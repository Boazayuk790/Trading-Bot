"""Unit tests (no MetaTrader needed).  Run:  python -m unittest discover -s tests -v"""
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import crt


def candle(low, high, close, open_=None, t="2024-01-01"):
    return pd.Series({"time": pd.Timestamp(t), "open": open_ if open_ is not None else close,
                      "high": high, "low": low, "close": close})


C1 = candle(low=100, high=110, close=105)   # range candle: 100..110


class TestSignal(unittest.TestCase):
    def test_bullish(self):
        sig = crt.crt_signal(C1, candle(low=98, high=108, close=104))
        self.assertEqual((sig["direction"], sig["entry"], sig["sl"], sig["tp"], sig["risk"]),
                         ("BUY", 104, 98, 110, 6))

    def test_bearish(self):
        sig = crt.crt_signal(C1, candle(low=102, high=112, close=106))
        self.assertEqual((sig["direction"], sig["entry"], sig["sl"], sig["tp"], sig["risk"]),
                         ("SELL", 106, 112, 100, 6))

    def test_no_sweep(self):
        self.assertIsNone(crt.crt_signal(C1, candle(low=101, high=109, close=105)))

    def test_sweep_but_close_outside_range(self):
        self.assertIsNone(crt.crt_signal(C1, candle(low=95, high=108, close=97)))
        self.assertIsNone(crt.crt_signal(C1, candle(low=102, high=115, close=113)))

    def test_close_exactly_on_boundary_is_not_inside(self):
        self.assertIsNone(crt.crt_signal(C1, candle(low=98, high=108, close=100)))
        self.assertIsNone(crt.crt_signal(C1, candle(low=102, high=112, close=110)))

    def test_both_sides_swept_is_skipped(self):
        self.assertIsNone(crt.crt_signal(C1, candle(low=98, high=112, close=105)))

    def test_fixed_rr(self):
        buy = crt.crt_signal(C1, candle(low=98, high=108, close=104), rr=2)
        self.assertEqual(buy["tp"], 116)          # 104 + 6*2
        sell = crt.crt_signal(C1, candle(low=102, high=112, close=106), rr=2)
        self.assertEqual(sell["tp"], 94)          # 106 - 6*2


class TestScanning(unittest.TestCase):
    def setUp(self):
        rows = [candle(100, 110, 105, t="2024-01-01 00:00"),
                candle(98, 108, 104, t="2024-01-01 01:00"),     # BUY setup vs row 0
                candle(99, 107, 103, t="2024-01-01 02:00")]       # no setup vs row 1
        self.df = pd.DataFrame(rows).reset_index(drop=True)

    def test_scan_counts_setup(self):
        self.assertEqual(len(crt.scan_history(self.df, last_is_forming=False)), 1)

    def test_scan_ignores_forming_candle(self):
        df = self.df.iloc[:2]                    # setup is on the LAST row
        self.assertEqual(len(crt.scan_history(df, last_is_forming=True)), 0)
        self.assertEqual(len(crt.scan_history(df, last_is_forming=False)), 1)

    def test_latest_signal_uses_closed_candles(self):
        # forming=True -> compares rows -3,-2 (the setup); forming=False -> rows -2,-1 (none)
        self.assertEqual(crt.latest_signal(self.df, last_is_forming=True)["direction"], "BUY")
        self.assertIsNone(crt.latest_signal(self.df, last_is_forming=False))

    def test_too_few_candles(self):
        self.assertIsNone(crt.latest_signal(self.df.iloc[:2], last_is_forming=True))


class TestCsvAndCli(unittest.TestCase):
    def test_load_csv_errors(self):
        with self.assertRaises(ValueError):
            crt.load_csv("nope.csv")
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.csv"
            bad.write_text("time,open\n2024-01-01,1\n")
            with self.assertRaises(ValueError):
                crt.load_csv(str(bad))

    def test_cli_on_sample_file(self):
        sample = Path(__file__).resolve().parent.parent / "sample_synthetic.csv"
        self.assertEqual(crt.main(["--csv", str(sample), "--no-export"]), 0)
        self.assertEqual(crt.main(["--csv", "missing.csv"]), 2)


if __name__ == "__main__":
    unittest.main()
