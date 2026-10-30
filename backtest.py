import itertools
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path("results")
OUT.mkdir(exist_ok=True)
COST = 0.0005
INITIAL = 10000.0

def prices(ticker):
    df = yf.download(ticker, start="2010-01-01", auto_adjust=True,
                     progress=False, threads=False)
    if df.empty:
        raise RuntimeError(f"No data returned for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].dropna().sort_index()
    df.to_csv(OUT / f"{ticker}_prices.csv")
    return df

def rsi(close, period=2):
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    down = (-delta).clip(lower=0).ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    result = 100 - 100 / (1 + up / down.replace(0, np.nan))
    return result.mask((down == 0) & (up > 0), 100).mask((up == 0) & (down > 0), 0).fillna(50)

def simulate(q, t, stop, hold):
    idx = q.index.intersection(t.index)
    q, t = q.loc[idx], t.loc[idx]
    indicator = rsi(q.Close)
    sma = q.Close.rolling(200).mean()
    entries = (indicator.shift(1) <= 10) & (indicator > 10) & (q.Close > sma) & (sma > sma.shift(20))
    exits = indicator > 70
    cash, shares, entry, cost, held, entry_date = INITIAL, 0, 0.0, 0.0, 0, None
    equity, trades = [], []
    for i, date in enumerate(idx):
        o, lo, c = map(float, (t.Open.iloc[i], t.Low.iloc[i], t.Close.iloc[i]))
        exited = False
        if shares:
            held += 1
            stop_price = entry * (1 - stop)
            reason, fill = None, None
            if o <= stop_price:
                reason, fill = "gap_stop", o
            elif lo <= stop_price:
                reason, fill = "stop", stop_price
            elif i > 0 and (bool(exits.iloc[i-1]) or held >= hold):
                reason, fill = "signal_or_time", o
            if reason:
                proceeds = shares * fill * (1 - COST)
                cash += proceeds
                trades.append(dict(entry_date=entry_date, exit_date=date, entry=entry,
                                   exit=fill, pnl=proceeds-cost, reason=reason))
                shares, held, exited = 0, 0, True
        if not shares and not exited and i > 0 and bool(entries.iloc[i-1]):
            n = int(min(cash/(o*(1+COST)), cash*0.005/(o*stop)))
            if n > 0:
                shares, entry, entry_date, held = n, o, date, 0
                cost = shares*o*(1+COST)
                cash -= cost
        equity.append(cash + shares*c)
    curve = pd.Series(equity, index=idx, name="equity")
    tr = pd.DataFrame(trades)
    returns = curve.pct_change().fillna(0)
    years = (idx[-1]-idx[0]).days/365.25
    gains = tr.loc[tr.pnl > 0, "pnl"].sum() if len(tr) else 0
    losses = tr.loc[tr.pnl < 0, "pnl"].sum() if len(tr) else 0
    metrics = dict(stop=stop, hold=hold, trades=len(tr),
                   cagr=(curve.iloc[-1]/INITIAL)**(1/years)-1,
                   max_drawdown=(curve/curve.cummax()-1).min(),
                   win_rate=float((tr.pnl>0).mean()) if len(tr) else np.nan,
                   profit_factor=gains/abs(losses) if losses else np.nan,
                   final_equity=curve.iloc[-1])
    return curve, tr, metrics

def main():
    q, t = prices("QQQ"), prices("TQQQ")
    metrics = []
    for stop, hold in itertools.product((.04,.05,.06,.08), (3,5,7)):
        curve, trades, row = simulate(q,t,stop,hold)
        metrics.append(row)
        if stop == .05 and hold == 5:
            curve.to_csv(OUT/"baseline_equity.csv")
            trades.to_csv(OUT/"baseline_trades.csv",index=False)
    idx = q.index.intersection(t.index)
    bench = t.loc[idx,"Close"]
    bh = INITIAL * bench / bench.iloc[0]
    years = (idx[-1]-idx[0]).days/365.25
    pd.DataFrame([dict(cagr=(bh.iloc[-1]/INITIAL)**(1/years)-1,
                       max_drawdown=(bh/bh.cummax()-1).min(),
                       final_equity=bh.iloc[-1])]).to_csv(OUT/"buy_hold_benchmark.csv",index=False)
    table = pd.DataFrame(metrics).sort_values("cagr",ascending=False)
    table.to_csv(OUT/"parameter_comparison.csv",index=False)
    print(table.to_string(index=False))
    print("Buy-and-hold benchmark:")
    print(pd.read_csv(OUT/"buy_hold_benchmark.csv").to_string(index=False))

if __name__ == "__main__":
    main()
