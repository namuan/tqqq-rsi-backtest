# TQQQ RSI(2) mean-reversion backtest

GitHub Actions downloads split/dividend-adjusted QQQ and TQQQ daily OHLC from Yahoo Finance and tests a long-only strategy.

**Signals** (QQQ close): RSI(2) crosses above 10, QQQ above its 200-day moving average, and that average is higher than 20 sessions earlier. Buy TQQQ next open. Exit at next open after QQQ RSI(2)>70 or after 3/5/7 sessions; protective stop tested at 4/5/6/8%. Stop gaps fill at open. No averaging down; risk budget 0.5% of equity per trade, capped at available cash. 5 basis points transaction cost each side.

## Historical results

Results from [GitHub Actions run #41016365244](https://github.com/namuan/tqqq-rsi-backtest/actions/runs/41016365244), using a $10,000 starting account. The strategy row is the **best CAGR among 12 in-sample configurations**, not an out-of-sample result.

| Metric | RSI(2) strategy (8% stop, 7-day hold) | TQQQ buy-and-hold |
|---|---:|---:|
| CAGR | **0.049%** | **41.674%** |
| Maximum drawdown | **−6.79%** | −81.66% |
| Final portfolio value | $10,082.38 | $3,375,488 |
| Number of closed trades | 148 | N/A (continuous holding) |
| Win rate | 64.86% | N/A |
| Profit factor | 1.04 | N/A |

**Interpretation:** The tested RSI strategy had much smaller historical drawdowns, but it barely grew the initial capital. Buy-and-hold generated dramatically greater returns at the cost of an extreme drawdown. These are **not risk-equivalent strategies**: the RSI system holds substantial cash, and its position sizing caps planned trade risk at 0.5% of account equity.

**Important limitations:** exploratory parameter selection on the same historical period; Yahoo data can be revised; stop fills use daily OHLC assumptions rather than intraday execution; transaction costs are approximations. The buy-and-hold benchmark is a price-based adjusted-close series and does not apply the strategy's per-trade transaction costs. Do not treat these results as a live-trading forecast.

Run via **Actions → TQQQ RSI Backtest → Run workflow**, or on each push. Download the `backtest-results` artifact with price data, trade logs, and parameter results.

**Caveats:** exploratory in-sample parameter sweep, Yahoo data may be revised, stop fills assume daily OHLC without intraday order sequencing, and historical performance is not predictive. Benchmark uses the same initial capital with buy-and-hold TQQQ.
