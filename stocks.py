"""Compare two NSE stocks using skip lists keyed by trading date.

  python stocks.py TATAPOWER RELIANCE --days 180
  python stocks.py TATAPOWER RELIANCE --crawl        # crawl nseindia.com with Selenium
  python stocks.py --csv TATAPOWER.csv RELIANCE.csv   # NSE "Historical Data" CSV exports
"""

import argparse
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from crawl import crawl, parse_nse_frame
from skiplist import SkipList


def from_yfinance(symbol, days):
    import yfinance as yf

    df = yf.download(f"{symbol}.NS", start=date.today() - timedelta(days=days),
                     progress=False, auto_adjust=False)
    if df.empty:
        raise SystemExit(f"No data for {symbol} (check the NSE symbol).")
    close = df["Close"].squeeze()
    return {d.date(): float(v) for d, v in close.items()}


def from_nse_csv(path):
    """Parse the CSV that nseindia.com's Historical Data page exports."""
    return parse_nse_frame(pd.read_csv(path))


def build_index(prices):
    sl = SkipList(seed=0)
    for d, close in prices.items():
        sl.insert(d, close)
    return sl


def compare(name_a, a, name_b, b):
    common = a.intersection(b)
    print(f"{name_a}: {len(a)} days | {name_b}: {len(b)} days | common: {len(common)}")
    if len(common) < 2:
        return common

    first, last = common[0], common[-1]
    for name, sl in ((name_a, a), (name_b, b)):
        ret = 100 * (sl.get(last) / sl.get(first) - 1)
        print(f"  {name:<12} {sl.get(first):>10.2f} -> {sl.get(last):>10.2f}  ({ret:+.1f}%)")

    # Daily-return correlation over the shared trading days.
    ra = pd.Series([a.get(d) for d in common]).pct_change()
    rb = pd.Series([b.get(d) for d in common]).pct_change()
    print(f"  daily-return correlation: {ra.corr(rb):.2f}")

    last_month = list(a.range(last - timedelta(days=30), last))
    print(f"  {name_a} closes in the last 30 days (range query): {len(last_month)} rows")
    return common


def plot(name_a, a, name_b, b, common, out="comparison.png"):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 5))
    for name, sl in ((name_a, a), (name_b, b)):
        base = sl.get(common[0])
        ax.plot(common, [100 * sl.get(d) / base for d in common], label=name)
    ax.set(title="Closing price, rebased to 100", ylabel="Index", xlabel="Date")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    print(f"Saved {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("symbols", nargs="*", help="two NSE symbols, e.g. TATAPOWER RELIANCE")
    p.add_argument("--csv", nargs=2, metavar="FILE", help="two NSE historical-data CSV exports")
    p.add_argument("--crawl", action="store_true", help="crawl nseindia.com instead of using yfinance")
    p.add_argument("--period", default="1Y", help="NSE period tab when crawling (1M, 3M, 6M, 1Y)")
    p.add_argument("--days", type=int, default=365, help="history length for yfinance")
    args = p.parse_args()

    if args.csv:
        names = [Path(f).stem for f in args.csv]
        data = [from_nse_csv(f) for f in args.csv]
    elif len(args.symbols) == 2:
        names = [s.upper() for s in args.symbols]
        data = [crawl(s, args.period) if args.crawl else from_yfinance(s, args.days) for s in names]
    else:
        p.error("give two symbols or --csv FILE FILE")

    a, b = map(build_index, data)
    common = compare(names[0], a, names[1], b)
    if len(common) >= 2:
        plot(names[0], a, names[1], b, common)


if __name__ == "__main__":
    main()
