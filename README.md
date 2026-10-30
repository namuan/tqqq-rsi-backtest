# TQQQ RSI(2) mean-reversion backtest

GitHub Actions downloads dividend/split-adjusted daily QQQ and TQQQ prices and tests a long-only, QQQ-signaled/TQQQ-executed RSI(2) strategy.

**Strategy:** QQQ RSI(2) crosses upward through 10 while QQQ closes above its 200-day SMA, which is above its level 20 sessions earlier. Enter TQQQ at the next open. Exit at the next open after RSI(2)>70 or after a maximum of 3/5/7 holding sessions; test 4/5/6/8% protective stops. No averaging down. Planned stop risk: 0.5% of account cash per trade, with available-cash cap. Transaction costs: 5 basis points per side.

## Corrected historical comparison

Source: [successful GitHub Actions run #41016829300](https://github.com/namuan/tqqq-rsi-backtest/actions/runs/41016829300), [results artifact](https://github.com/namuan/tqqq-rsi-backtest/actions/runs/41016829300/artifacts/12959333345). Starting capital: **$10,000**. The strategy shown is the **best in-sample CAGR of the 12 tested configurations** (8% stop; 7-session maximum hold). Results are not out-of-sample validated.

| Metric | RSI strategy (8% / 7 sessions) | QQQ buy-and-hold | TQQQ buy-and-hold |
|---|---:|---:|---:|
| CAGR | **0.082%** | 19.234% | 41.674% |
| Maximum drawdown | **−6.33%** | −35.12% | −81.66% |
| Final equity | **$10,138.23** | $189,129 | $3,375,487 |
| Average capital exposure | **0.44%** | 100% | 100% |
| Annualized volatility | **1.06%** | 20.63% | 61.08% |
| Closed trades | 148 | N/A | N/A |
| Win rate | 65.54% | N/A | N/A |
| Profit factor | 1.07 | N/A | N/A |
| Average winning trade | $21.42 | N/A | N/A |
| Average losing trade | −$38.03 | N/A | N/A |
| Largest losing trade | −$159.27 | N/A | N/A |
| Total strategy transaction fees | $94.11 | Not modeled | Not modeled |

**Critical interpretation:** The strategy's low drawdown is not directly comparable to continuously invested QQQ/TQQQ: its *average capital exposure is only 0.44%*. Its winners are substantially smaller than its losers and its profit factor is barely above one. Increasing risk or exposure without further analysis may increase losses rather than improve risk-adjusted performance.

### Fixed 5% stop / 5-session baseline

The originally proposed baseline, re-evaluated with the corrected execution engine, had **−0.151% CAGR, −9.79% maximum drawdown, 59.60% winning trades, 0.924 profit factor and $9,750.58 ending capital**. Its average capital exposure was **0.60%**.

### Running the backtest

GitHub **Actions → TQQQ RSI Backtest → Run workflow**. Pushing changes to `backtest.py`, `requirements.txt` or the workflow also triggers a run. Download the `backtest-results` artifact for the data and diagnostic CSVs.

Exported files include: `QQQ_prices.csv`, `TQQQ_prices.csv`, `parameter_comparison.csv`, `baseline_equity.csv`, `baseline_trades.csv`, `baseline_diagnostics.csv`, `annual_returns.csv` and `buy_hold_benchmarks.csv`.

**Limitations:** In-sample parameter selection risks overfitting. Adjusted OHLC and daily-bar stop assumptions are approximations, not tick-level tradable fills. Trading costs and benchmark costs are not modeled symmetrically. The buy-and-hold benchmark invests at an adjusted closing price and assumes no transaction costs. Reported exposure is daily close notional exposure, averaged over the entire period. Do not interpret historical results as projected trading performance.
