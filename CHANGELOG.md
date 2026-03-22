# Changelog

## 2026-03-22 — Scheduled task (Tue-Sat 10:15 AM NZST) + output/ folder

### Added
- `output/` folder — daily signal reports saved as `{Weekday}_{YYYYMMDD_HHMMSS}.txt`
- `run_daily.py` — entry point called by Windows Task Scheduler; runs full watchlist and writes output file
- Windows Task Scheduler job `TDSequentialDailySignals` — runs Tue to Sat at 10:15 AM NZST, next run: 2026-03-24

### Changed
- `signals.py` — added `write_output` parameter; uses `_TeeWriter` to mirror console output to a file simultaneously; `_output_path()` generates timestamped path in `output/`
- `.gitignore` — `output/` contents excluded, folder kept via `.gitkeep`

### Output file format
Filename: `Tuesday_20260324_101500.txt`
Contents: full console report (signal table + chart/data paths + any alerts)

## 2026-03-22 — STOCK_LIST env var and daily signal engine

### Added
- `.env` — `STOCK_LIST=AAPL,TSLA,SPY,QQQ` (gitignored; copy from `.env.example`)
- `.env.example` — template for environment configuration
- `tom_demark_indicator/signals.py` — `run_daily_signals()` reads `STOCK_LIST`, loops each ticker, prints TD status table, warns and alerts on invalid/missing symbols
- `get_stock_list()` utility — parses and validates `STOCK_LIST` from environment

### Changed
- `cli.py` — omitting a symbol now triggers the full watchlist loop via `run_daily_signals()`; single ticker mode unchanged
- `pyproject.toml` — added `python-dotenv>=1.0` dependency
- `.gitignore` — `.env` excluded from version control
- `__init__.py` — exports `run_daily_signals`, `get_stock_list`

### Signal output format
```
=== Daily TD Sequential Signals [2026-03-22] ===
Watchlist: AAPL, TSLA, SPY, QQQ

  AAPL   | Buy  Setup  7/9 | Close $247.99 | 2026-03-20
  QQQ    | Buy  Setup  9/9 | Close $582.06 | 2026-03-20  *** BUY 9 COMPLETE ***

  [ALERT] The following symbols were not found or failed to load: FAKEXYZ
```

## 2026-03-22 — images/ and data/ folders, JSON export

### Added
- `images/` folder — all PNG charts saved here automatically with timestamped filenames (`{SYMBOL}_{interval}_{YYYYMMDD_HHMMSS}.png`)
- `data/` folder — all chart data saved here as JSON with timestamped filenames (`{SYMBOL}_{interval}_{YYYYMMDD_HHMMSS}.json`)
- `tom_demark_indicator/exporter.py` — `save_data_json()` serialises the full DataFrame (OHLCV + all indicators) to JSON; `default_image_path()` generates timestamped PNG paths in `images/`

### Changed
- `cli.py` — removed `--save` flag; PNG now auto-saved to `images/` on every run; use `--show` for interactive window. JSON always saved to `data/` on every run.
- `.gitignore` — ignores folder contents of `images/` and `data/` but keeps the folders via `.gitkeep`
- `__init__.py` — exports `save_data_json` and `default_image_path`

### JSON format
```json
{
  "symbol": "AAPL",
  "interval": "1d",
  "exported_at": "2026-03-22T13:44:56",
  "rows": 61,
  "columns": ["datetime", "Open", "High", "Low", "Close", "Volume", "ema_10", ...],
  "data": [{ "datetime": "2025-12-22T00:00:00", "Open": 272.6, ... }, ...]
}
```


## 2026-03-22 — Initial build

### Added
- `pyproject.toml` — project metadata and dependencies (pandas, numpy, mplfinance, matplotlib, yfinance)
- `tom_demark_indicator/__init__.py` — package exports
- `tom_demark_indicator/config.py` — `PlotConfig` dataclass with all chart/indicator options
- `tom_demark_indicator/data_loader.py` — OHLCV loader via yfinance and CSV fallback; normalises column casing for mplfinance
- `tom_demark_indicator/indicators.py` — pure pandas/numpy computation of EMAs, MACD, volume MA
- `tom_demark_indicator/td_sequential.py` — TD Sequential buy/sell setup counts 1–9 with price-flip reset logic
- `tom_demark_indicator/plotting_mpf.py` — mplfinance chart: candlestick + EMA overlays + volume MA + MACD panel + TD scatter markers + numeric TD text labels via `returnfig=True`
- `tom_demark_indicator/cli.py` — `tdchart` argparse CLI with flags: `--period`, `--interval`, `--start`, `--end`, `--ema`, `--macd`, `--vol-ma`, `--no-td`, `--no-macd`, `--save`, `--style`, `--csv`
- `BLUEPRINT.md` — full project design spec

### Fixed
- Replaced `→` unicode arrow with `to` in CLI print output to avoid `UnicodeEncodeError` on Windows terminals using cp1252 encoding

### Test results (2026-03-22)
| Symbol | Period | Bars | TD Buy-9 | TD Sell-9 |
|---|---|---|---|---|
| AAPL | 6mo | 125 | 0 | 3 |
| TSLA | 1y | 251 | 3 | 3 |
| SPY | 1y (no MACD, EMA 9/21/50) | 251 | 1 | 9 |
