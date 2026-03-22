# DeMark/TD Charting Tool — Project Blueprint

## Stack
- Python 3.11+
- pandas, numpy, mplfinance, matplotlib

## Module Layout

```
tom_demark_indicator/
  tom_demark_indicator/
    config.py
    data_loader.py
    indicators.py
    td_sequential.py
    plotting_mpf.py   # mplfinance-specific plotting
    cli.py
```

---

## Data Format

OHLCV as a `pandas.DataFrame` with:
- `DatetimeIndex` (name `'Date'` or default)
- Columns: `Open`, `High`, `Low`, `Close`, `Volume` (capitalization matches mplfinance defaults)

---

## Indicators (`indicators.py`, `td_sequential.py`)

Computed as pure pandas/numpy columns on the DataFrame — no plotting coupling:

| Column | Description |
|---|---|
| `ema_10`, `ema_30`, ... | Exponential moving averages |
| `macd`, `macd_signal`, `macd_hist` | MACD components |
| `volume_ma` | Volume moving average |
| `td_buy_setup` | TD buy setup count (1–9, 0 = none) |
| `td_sell_setup` | TD sell setup count (1–9, 0 = none) |
| `td_buy_9` | Boolean: completed buy setup (count == 9) |
| `td_sell_9` | Boolean: completed sell setup (count == 9) |

---

## Plotting (`plotting_mpf.py`)

### Main entry point

```python
def plot_with_mplfinance(df: pd.DataFrame, config: PlotConfig, output_path: str | None = None) -> None:
    """
    df: OHLCV + indicator columns
    config: symbol, EMA periods, etc.
    output_path: if given, save PNG; else show interactively
    """
```

### Panel layout

| Panel index | Content |
|---|---|
| 0 | Candlestick + EMA overlays + TD markers |
| 1 | Volume + volume MA |
| 2 | MACD line, signal, histogram |

### addplot construction

```python
apds = []

# EMAs on price panel (panel 0 by default)
apds.append(mpf.make_addplot(df["ema_10"], color="blue"))
apds.append(mpf.make_addplot(df["ema_30"], color="orange"))

# Volume MA on volume panel
apds.append(mpf.make_addplot(df["volume_ma"], panel=1, color="cyan"))

# MACD on panel 2
apds.append(mpf.make_addplot(df["macd"],        panel=2, color="purple"))
apds.append(mpf.make_addplot(df["macd_signal"], panel=2, color="grey"))
apds.append(mpf.make_addplot(df["macd_hist"],   panel=2, type="bar", color="dimgray"))

# TD DeMark markers
# td_buy_marker: series = Low - offset where td_buy_setup > 0, else NaN
# td_sell_marker: series = High + offset where td_sell_setup > 0, else NaN
apds.append(mpf.make_addplot(td_buy_marker,  type="scatter", marker="^", color="green", markersize=50))
apds.append(mpf.make_addplot(td_sell_marker, type="scatter", marker="v", color="red",   markersize=50))
```

### mpf.plot call

```python
mpf.plot(
    df,
    type="candle",
    volume=True,
    addplot=apds,
    style=style,          # mpf.make_mpf_style(...)
    figratio=(12, 6),
    title=config.symbol,
    savefig=output_path,  # None = interactive
)
```

### TD numeric labels (enhancement)

Use `returnfig=True` to get `fig, axes` back, then:

```python
fig, axes = mpf.plot(..., returnfig=True)
for i, (ts, row) in enumerate(df.iterrows()):
    if row["td_buy_setup"] > 0:
        axes[0].text(i, row["Low"] - offset, str(int(row["td_buy_setup"])),
                     ha="center", va="top", color="green", fontsize=7)
    if row["td_sell_setup"] > 0:
        axes[0].text(i, row["High"] + offset, str(int(row["td_sell_setup"])),
                     ha="center", va="bottom", color="red", fontsize=7)
```

---

## CLI (`cli.py`)

Options:
- `--show` vs `--save path.png`
- `--show-td` — toggle DeMark overlays
- `--ema 10 30` — EMA periods
- `--macd 12 26 9` — MACD fast/slow/signal

---

## Key mplfinance conventions

1. DataFrame index must be `DatetimeIndex`.
2. Column names must be exactly `Open`, `High`, `Low`, `Close`, `Volume`.
3. `make_addplot` series must share the same index as the main DataFrame.
4. Use `panel=` integer to control subplot placement.
5. `savefig=None` → interactive window; `savefig="file.png"` → save to disk.
