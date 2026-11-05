# NSE Crawler + Skip List

Crawl historical prices for two National Stock Exchange (India) stocks from
**nseindia.com** with Selenium, then compare them over their **common trading
days**, using a **skip list** built from scratch as the date-ordered index.

```bash
$ python stocks.py TATAPOWER RELIANCE --days 180
TATAPOWER: 124 days | RELIANCE: 124 days | common: 124
  TATAPOWER        433.20 ->     364.95  (-15.8%)
  RELIANCE        1388.20 ->    1315.70  (-5.2%)
  daily-return correlation: 0.35
  TATAPOWER closes in the last 30 days (range query): 22 rows
Saved comparison.png
```

![TATAPOWER vs RELIANCE, rebased to 100](docs/comparison.png)

## Why a skip list?

Every stock is stored as a sorted map `date → closing price`. A skip list
supports exactly the operations this needs, and it is a simpler alternative
to a balanced BST:

| Operation | Used for | Cost |
|---|---|---|
| `insert(date, close)` | building the index | O(log n) expected |
| `get(date)` | price lookup on a given day | O(log n) expected |
| `range(lo, hi)` | "all closes in the last 30 days" | O(log n + k) |
| `intersection(other)` | trading days both stocks share | O(n + m) linear merge |
| `delete(date)` | removing bad rows | O(log n) expected |

### How it works

```
Level 3:  head ─────────────────────────────► 14 ────────────────► None
Level 2:  head ─────────► 05 ───────────────► 14 ────────► 21 ───► None
Level 1:  head ─► 02 ───► 05 ─────► 09 ─────► 14 ─► 17 ──► 21 ───► None
Level 0:  head ─► 02 ─► 03 ─► 05 ─► 09 ─► 11 ─► 14 ─► 17 ─► 19 ─► 21 ─► None
```

- Level 0 is a sorted linked list of all keys. Each node is also promoted
  to the next level up with probability `p = 0.5`, so level *i* holds about
  *n / 2ⁱ* nodes.
- **Search** starts at the top level and moves right while the next key is
  smaller than the target, then drops a level. Each level roughly halves the
  remaining range, which gives O(log n) expected time with no rebalancing.
- **Intersection** walks level 0 of both lists at once, like the merge step
  of merge sort. That is O(n + m), better than doing *n* separate searches
  (O(n log m)) when the lists are of similar size.

The implementation is in [`skiplist.py`](skiplist.py) and has no
dependencies. Tests check it against a Python `dict` over 2,000 random
operations.

## The crawler

[`crawl.py`](crawl.py) drives Chrome with Selenium 4:

1. Open `nseindia.com/get-quotes/equity?symbol=…`.
2. Click **Historical Data**, choose a period tab (`1M`, `3M`, `6M`, `1Y`)
   and apply the filter.
3. Wait for the price table to load, then parse its HTML with pandas into
   `{date: close}`.

It uses **explicit waits** (`WebDriverWait`) instead of fixed `sleep`s, and
Selenium Manager downloads a matching chromedriver automatically. NSE
redesigns its pages from time to time, so all element locators are kept in
one `LOCATORS` dict. When the site changes, that dict is the only thing to
update. The table-parsing half is unit-tested offline.

NSE sometimes blocks automated browsers. When that happens, use the CSV or
yfinance loaders below; they feed the same skip-list analysis.

## Usage

```bash
pip install -r requirements.txt

# Crawl nseindia.com (needs Google Chrome installed)
python stocks.py TATAPOWER RELIANCE --crawl --period 1Y
python crawl.py TATAPOWER --show-browser       # watch the crawler work

# Alternatives with the same analysis:
python stocks.py TATAPOWER RELIANCE --days 365      # Yahoo Finance (NSE tickers)
python stocks.py --csv TATAPOWER.csv RELIANCE.csv  # CSVs exported from NSE's Historical Data page

pytest -q
```

## Project structure

```
├── crawl.py               # Selenium crawler for NSE historical data + table parsing
├── skiplist.py            # SkipList: insert/get/delete/range/intersection
├── stocks.py              # data sources (crawl / yfinance / CSV), comparison, plot
└── tests/test_skiplist.py # randomized reference test, range, intersection, CSV + HTML parsing
```

## History

v1 crawled nseindia.com with Selenium 3. It used fixed sleeps, hardcoded a
chromedriver path, and used APIs that Selenium 4 later removed. v2 rewrites
the crawler with Selenium 4, explicit waits and centralized locators, and
adds yfinance and CSV loaders as fallbacks. It also fixes the original
skip-list design, which was keyed by **price**, so its "intersection"
matched two stocks that happened to close at the same value. The list is now
keyed by **date**, which makes the intersection meaningful.
