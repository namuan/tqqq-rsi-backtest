"""Daily-bar RSI(2) backtest. Signals use prior close; fills use next open."""
import itertools
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path("results")
OUT.mkdir(exist_ok=True)
INITIAL = 10000.0
FEE = 0.0005
RISK = 0.005

def prices(symbol):
    df = yf.download(symbol, start="2010-01-01", auto_adjust=True, progress=False, threads=False)
    if df.empty:
        raise RuntimeError(f"No price data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].dropna().sort_index()
    df.to_csv(OUT / f"{symbol}_prices.csv")
    return df

def rsi(close, n=2):
    change = close.diff()
    up = change.clip(lower=0).ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    down = (-change).clip(lower=0).ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    result = 100 - 100 / (1 + up / down.replace(0, np.nan))
    result = result.mask((down == 0) & (up > 0), 100)
    result = result.mask((up == 0) & (down > 0), 0)
    return result.fillna(50)

def summary(curve, trades, exposure=None):
    years = (curve.index[-1] - curve.index[0]).days / 365.25
    dd = curve / curve.cummax() - 1
    ret = curve.pct_change().fillna(0)
    wins = trades.loc[trades.pnl > 0, "pnl"] if len(trades) else pd.Series(dtype=float)
    losses = trades.loc[trades.pnl < 0, "pnl"] if len(trades) else pd.Series(dtype=float)
    return dict(
        cagr=float((curve.iloc[-1]/INITIAL)**(1/years)-1),
        max_drawdown=float(dd.min()),
        final_equity=float(curve.iloc[-1]),
        trades=int(len(trades)),
        win_rate=float((trades.pnl > 0).mean()) if len(trades) else np.nan,
        profit_factor=float(wins.sum()/abs(losses.sum())) if len(losses) else np.nan,
        avg_win=float(wins.mean()) if len(wins) else np.nan,
        avg_loss=float(losses.mean()) if len(losses) else np.nan,
        largest_loss=float(trades.pnl.min()) if len(trades) else np.nan,
        total_fees=float(trades.fees.sum()) if len(trades) else 0.0,
        exposure=float(exposure.mean()) if exposure is not None else 1.0,
        annualized_vol=float(ret.std()*np.sqrt(252)),
    )

def simulate(q, t, stop, hold):
    idx = q.index.intersection(t.index)
    q, t = q.loc[idx], t.loc[idx]
    indicator = rsi(q.Close)
    sma = q.Close.rolling(200).mean()
    entries = ((indicator.shift(1) <= 10) & (indicator > 10) &
               (q.Close > sma) & (sma > sma.shift(20))).fillna(False)
    exits = (indicator > 70).fillna(False)

    cash, shares, entry_price, entry_cost, entry_fee = INITIAL, 0, 0.0, 0.0, 0.0
    entry_date, entry_index = None, None
    equity, exposure, trades = [], [], []

    for i, date in enumerate(idx):
        op, low, close = map(float, (t.Open.iloc[i], t.Low.iloc[i], t.Close.iloc[i]))
        exited = False
        if shares:
            days_held = i - entry_index  # entry day is day 0
            # A prior-close signal or scheduled holding-period exit fills at today's open.
            # This must precede today's intraday stop checks.
            signal_exit = i > 0 and bool(exits.iloc[i-1])
            time_exit = days_held >= hold
            stop_price = entry_price * (1-stop)
            reason, fill = None, None
            if signal_exit:
                reason, fill = "rsi_exit", op
            elif time_exit:
                reason, fill = "time_exit", op
            elif op <= stop_price:
                reason, fill = "gap_stop", op
            elif low <= stop_price:
                reason, fill = "stop", stop_price
            if reason:
                exit_fee = shares * fill * FEE
                proceeds = shares * fill - exit_fee
                cash += proceeds
                trades.append(dict(entry_date=entry_date, exit_date=date,
                                   entry=entry_price, exit=fill, shares=shares,
                                   holding_sessions=days_held, pnl=proceeds-entry_cost,
                                   fees=entry_fee+exit_fee, reason=reason))
                shares = 0
                exited = True

        # Never re-enter on the same day as an exit.
        if not shares and not exited and i > 0 and bool(entries.iloc[i-1]):
            n = int(min(cash/(op*(1+FEE)), cash*RISK/(op*stop)))
            if n > 0:
                shares, entry_price, entry_date, entry_index = n, op, date, i
                entry_fee = n*op*FEE
                entry_cost = n*op+entry_fee
                cash -= entry_cost
        equity.append(cash + shares*close)
        exposure.append(shares*close/(cash+shares*close) if shares else 0.0)

    # Liquidate any open position at final close, applying the same exit fee.
    if shares:
        date = idx[-1]
        close = float(t.Close.iloc[-1])
        fee = shares*close*FEE
        proceeds = shares*close-fee
        cash += proceeds
        trades.append(dict(entry_date=entry_date, exit_date=date, entry=entry_price,
                           exit=close, shares=shares, holding_sessions=len(idx)-1-entry_index,
                           pnl=proceeds-entry_cost, fees=entry_fee+fee, reason="end_of_data"))
        equity[-1] = cash
        exposure[-1] = 0.0

    curve = pd.Series(equity, index=idx, name="equity")
    tr = pd.DataFrame(trades, columns=["entry_date","exit_date","entry","exit","shares",
                                      "holding_sessions","pnl","fees","reason"])
    return curve, tr, summary(curve, tr, pd.Series(exposure, index=idx))

def benchmark(df, idx, symbol):
    # Invest at the first available adjusted close; no strategy stop or sizing constraint.
    p = df.loc[idx, "Close"]
    curve = INITIAL * p/p.iloc[0]
    curve.name = symbol
    empty = pd.DataFrame(columns=["pnl","fees"])
    metrics = summary(curve, empty)
    metrics["symbol"] = symbol
    metrics["trades"] = np.nan
    metrics["win_rate"] = np.nan
    metrics["profit_factor"] = np.nan
    return curve, metrics

def main():
    q, t = prices("QQQ"), prices("TQQQ")
    idx = q.index.intersection(t.index)
    q, t = q.loc[idx], t.loc[idx]
    all_metrics = []
    baseline = None
    for stop, hold in itertools.product((.04,.05,.06,.08), (3,5,7)):
        curve, trades, metrics = simulate(q, t, stop, hold)
        all_metrics.append(dict(stop=stop, hold=hold, **metrics))
        if stop == .05 and hold == 5:
            baseline = curve
            curve.to_csv(OUT/"baseline_equity.csv")
            trades.to_csv(OUT/"baseline_trades.csv", index=False)
            pd.DataFrame([metrics]).to_csv(OUT/"baseline_diagnostics.csv", index=False)
    table = pd.DataFrame(all_metrics).sort_values("cagr", ascending=False)
    table.to_csv(OUT/"parameter_comparison.csv", index=False)
    q_curve, q_metrics = benchmark(q, idx, "QQQ")
    t_curve, t_metrics = benchmark(t, idx, "TQQQ")
    pd.DataFrame([q_metrics, t_metrics]).to_csv(OUT/"buy_hold_benchmarks.csv", index=False)
    pd.DataFrame({"baseline":baseline, "QQQ_buy_hold":q_curve,
                  "TQQQ_buy_hold":t_curve}).resample("YE").last().pct_change().to_csv(
                      OUT/"annual_returns.csv")
    print("Strategy variants:")
    print(table.to_string(index=False))
    print("\nBuy-and-hold benchmarks:")
    print(pd.DataFrame([q_metrics, t_metrics]).to_string(index=False))
    print("\nNOTE: prior README figures were produced by an older execution-order implementation.")
    print("NOTE: no out-of-sample validation yet; benchmark assumes frictionless adjusted-close holding.")

if __name__ == "__main__":
    main()
