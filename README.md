# TQQQ RSI(2) mean-reversion backtest

GitHub Actions downloads split/dividend-adjusted QQQ and TQQQ daily OHLC from Yahoo Finance and tests a long-only strategy.

**Signals** (QQQ close): RSI(2) crosses above 10, QQQ above its 200-day moving average, and that average is higher than 20 sessions earlier. Buy TQQQ next open. Exit at next open after QQQ RSI(2)>70 or after 3/5/7 sessions; protective stop tested at 4/5/6/8%. Stop gaps fill at open. No averaging down; risk budget 0.5% of equity per trade, capped at available cash. 5 basis points transaction cost each side.

Run via **Actions → TQQQ RSI Backtest → Run workflow**, or on each push. Download the `backtest-results` artifact with price data, trade logs, and parameter results.

**Caveats:** exploratory in-sample parameter sweep, Yahoo data may be revised, stop fills assume daily OHLC without intraday order sequencing, and historical performance is not predictive. Benchmark uses the same initial capital with buy-and-hold TQQQ.
