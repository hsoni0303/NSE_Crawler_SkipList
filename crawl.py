"""Crawl historical prices from nseindia.com with Selenium.

Opens the stock's quote page, switches to the Historical Data section, picks a
period, and reads the price table from the page. Uses explicit waits instead of
fixed sleeps. NSE redesigns its pages from time to time, so every locator lives
in LOCATORS for easy updating.

  python crawl.py TATAPOWER --period 1Y
"""

import argparse
from io import StringIO

import pandas as pd

QUOTE_URL = "https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
LOCATORS = {
    "historical_tab": ("link text", "Historical Data"),
    "period": ("xpath", '//*[@id="historical-trade"]//a[normalize-space()="{period}"]'),
    "filter": ("xpath", '//*[@id="equity-historical-Date-filter"]//button'),
    "table": ("id", "equityHistoricalTable"),
}


def parse_nse_frame(df):
    """NSE price table/CSV -> {date: close}. Headers have stray spaces and mixed case."""
    df.columns = df.columns.astype(str).str.strip().str.upper()
    dates = pd.to_datetime(df["DATE"], format="%d-%b-%Y")
    close = df["CLOSE"].astype(str).str.replace(",", "").astype(float)
    return dict(zip(dates.dt.date, close))


def parse_table_html(html):
    return parse_nse_frame(pd.read_html(StringIO(html))[0])


def crawl(symbol, period="1Y", headless=True, timeout=30):
    from selenium import webdriver
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opts)  # Selenium Manager fetches a matching driver
    wait = WebDriverWait(driver, timeout)

    def click(name, **fmt):
        by, value = LOCATORS[name]
        el = wait.until(EC.element_to_be_clickable((by, value.format(**fmt))))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        el.click()

    try:
        driver.get(QUOTE_URL.format(symbol=symbol.upper()))
        click("historical_tab")
        click("period", period=period)
        click("filter")
        table = wait.until(EC.presence_of_element_located(LOCATORS["table"]))
        wait.until(lambda d: len(table.find_elements("tag name", "tr")) > 1)
        return parse_table_html(table.get_attribute("outerHTML"))
    finally:
        driver.quit()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("symbol")
    p.add_argument("--period", default="1Y", help="tab label on NSE: 1D, 1W, 1M, 3M, 6M, 1Y")
    p.add_argument("--show-browser", action="store_true")
    args = p.parse_args()
    prices = crawl(args.symbol, args.period, headless=not args.show_browser)
    for d, close in sorted(prices.items()):
        print(d, close)
