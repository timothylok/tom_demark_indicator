#!/usr/bin/env python3
"""Export TD Sequential chart data for Next.js consumption.

For each (ticker, interval) pair this script:
  1. Loads OHLCV data via yfinance
  2. Computes EMAs, MACD, volume MA
  3. Computes TD Sequential setup counts
  4. Writes NextJS/data/{TICKER}_{interval}.json

Also writes NextJS/data/index.json so Next.js can enumerate available pages
without scanning the filesystem.

Usage
-----
    python export_for_nextjs.py                      # uses STOCK_LIST from .env, interval=1d
    python export_for_nextjs.py AAPL TSLA            # explicit tickers
    python export_for_nextjs.py AAPL --interval 1wk  # alternate interval
    python export_for_nextjs.py AAPL --period 2y     # longer history

Typical CI nightly job
----------------------
    python export_for_nextjs.py && cd NextJS && npm run build
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# ── Make the package importable when run from project root ───────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from tom_demark_indicator.config import PlotConfig
from tom_demark_indicator.data_loader import load_data
from tom_demark_indicator.indicators import add_indicators
from tom_demark_indicator.td_sequential import add_td_sequential
from tom_demark_indicator.formatter import build_signal_summary, build_daily_signal_summary

# JSON files land inside the Next.js project so getStaticProps can read them
OUTPUT_DIR = _PROJECT_ROOT / "NextJS" / "data"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_tickers_from_env() -> list[str]:
    raw = os.environ.get("STOCK_LIST", "").strip()
    if not raw:
        raise EnvironmentError(
            "STOCK_LIST is not set in .env. "
            "Add e.g. STOCK_LIST=AAPL,TSLA,SPY or pass tickers as arguments."
        )
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def export_ticker(symbol: str, interval: str, period: str) -> dict | None:
    """Compute indicators and write one JSON file.

    Returns an index entry dict on success, None on failure.
    """
    print(f"  {symbol:8s} [{interval}]  ", end="", flush=True)

    config = PlotConfig(symbol=symbol, interval=interval, period=period)

    try:
        df = load_data(config)
    except Exception as exc:
        print(f"FAILED (load error): {exc}")
        return None

    if df.empty:
        print("FAILED (no data returned -- check the symbol)")
        return None

    df = add_indicators(df, config)
    df = add_td_sequential(df)

    # Build pre-computed signal summary so the web UI never re-implements logic
    sig = build_signal_summary(symbol, df)
    daily = build_daily_signal_summary(sig)

    # ── Serialise DataFrame ───────────────────────────────────────────────────
    export_df = df.copy()
    export_df.index = export_df.index.strftime("%Y-%m-%dT%H:%M:%S")
    export_df.index.name = "datetime"
    export_df = export_df.reset_index()

    # bool columns -> 0/1 so JSON stays numeric
    bool_cols = export_df.select_dtypes(include="bool").columns
    export_df[bool_cols] = export_df[bool_cols].astype(int)

    # Use pandas to_json so NaN becomes null, not the bare token "NaN"
    # (Python's json.dump writes NaN as a literal which JSON.parse rejects)
    records = json.loads(export_df.to_json(orient="records"))
    exported_at = datetime.now().isoformat()

    payload = {
        # ── root metadata ────────────────────────────────────────────────────
        "symbol":     symbol,
        "interval":   interval,
        "exported_at": exported_at,
        "rows":       len(records),
        "columns":    list(export_df.columns),
        # ── pre-computed summary for the web UI summary card ─────────────────
        "daily_signal_summary": daily,
        # ── per-bar data ─────────────────────────────────────────────────────
        # datetime : ISO 8601 string
        # Open/High/Low/Close/Volume : float
        # ema_10 / ema_30            : float
        # macd / macd_signal / macd_hist / volume_ma : float
        # td_buy_setup / td_sell_setup : int 0-9
        # td_buy_9 / td_sell_9         : int 0 or 1
        "data": records,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{symbol}_{interval}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"OK  ({len(records)} bars)  -> {out_path.name}")

    return {
        "ticker":    symbol,
        "interval":  interval,
        "file":      f"{symbol}_{interval}.json",
        "rows":      len(records),
        "exported_at": exported_at,
        "daily_signal_summary": daily,
    }


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export TD Sequential data for Next.js static site generation"
    )
    parser.add_argument(
        "tickers", nargs="*",
        help="Ticker symbols (default: STOCK_LIST from .env)",
    )
    parser.add_argument(
        "--interval", default="1d",
        help="yfinance interval, e.g. 1d, 1wk, 4h (default: 1d)",
    )
    parser.add_argument(
        "--period", default="1y",
        help="yfinance period, e.g. 1y, 2y, 6mo (default: 1y)",
    )
    args = parser.parse_args()

    tickers = (
        [t.upper() for t in args.tickers]
        if args.tickers
        else _get_tickers_from_env()
    )

    print(f"Exporting {len(tickers)} ticker(s)  interval={args.interval}  period={args.period}")
    print(f"Output dir: {OUTPUT_DIR}\n")

    index_entries: list[dict] = []
    for symbol in tickers:
        entry = export_ticker(symbol, args.interval, args.period)
        if entry:
            index_entries.append(entry)

    # ── Write index.json ──────────────────────────────────────────────────────
    # Next.js getStaticPaths reads this to enumerate all symbol pages.
    index_payload = {
        "generated_at": datetime.now().isoformat(),
        "entries": index_entries,
    }
    index_path = OUTPUT_DIR / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_payload, f, indent=2)

    ok  = len(index_entries)
    err = len(tickers) - ok
    print(f"\nDone.  {ok} exported, {err} failed.")
    print(f"index.json -> {index_path}")


if __name__ == "__main__":
    main()
