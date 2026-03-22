# Changelog

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
