"""Daily TD Sequential signal engine.

Reads STOCK_LIST from the environment, loops through each ticker,
computes indicators + TD setup counts, and prints an enhanced signal report.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

from .config import PlotConfig
from .data_loader import load_data
from .indicators import add_indicators
from .td_sequential import add_td_sequential
from .plotting_mpf import plot_with_mplfinance
from .exporter import save_data_json, default_image_path
from .formatter import (
    build_signal_summary,
    build_daily_signal_summary,
    format_report_header,
    format_ticker_block,
    format_summary,
)
from .discord_notifier import send_daily_signals, send_error_alert

# Load .env from the project root (two levels up from this file)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
load_dotenv(_ENV_PATH)


def get_stock_list() -> list[str]:
    """Return tickers from STOCK_LIST env var. Raises if not set or empty."""
    raw = os.environ.get("STOCK_LIST", "").strip()
    if not raw:
        raise EnvironmentError(
            "STOCK_LIST environment variable is not set or empty. "
            "Add it to your .env file, e.g.: STOCK_LIST=AAPL,TSLA,SPY,QQQ"
        )
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def _output_path() -> Path:
    """Return a timestamped path inside output/ for today's run."""
    _OUTPUT_DIR.mkdir(exist_ok=True)
    now = datetime.now()
    weekday = now.strftime("%A")
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    return _OUTPUT_DIR / f"{weekday}_{timestamp}.txt"


def run_daily_signals(
    config_overrides: dict | None = None,
    save_charts: bool = True,
    show_charts: bool = False,
    write_output: bool = False,
) -> list[dict]:
    """Loop through STOCK_LIST, print enhanced TD signals, and optionally save report.

    Parameters
    ----------
    config_overrides: dict of PlotConfig field overrides applied to every ticker.
    save_charts:      Save PNG to images/ for each ticker.
    show_charts:      Open interactive window for each ticker (use sparingly).
    write_output:     Also write the full report to output/ as a .txt file.

    Returns a list of result dicts (one per ticker that loaded successfully).
    """
    tickers = get_stock_list()
    overrides = config_overrides or {}

    buffer = io.StringIO()
    tee = _TeeWriter(sys.stdout, buffer)

    with redirect_stdout(tee):
        print(format_report_header(date.today(), tickers))

        results: list[dict] = []
        summaries = []
        errors: list[str] = []

        for idx, symbol in enumerate(tickers, start=1):
            config = PlotConfig(symbol=symbol, **overrides)
            try:
                df = load_data(config)
            except Exception as exc:
                msg = f"Could not load data for {symbol}: {exc}"
                print(f"\n  [WARNING] {msg}")
                send_error_alert(f"Data Load Failed: {symbol}", msg)
                errors.append(symbol)
                continue

            if df.empty:
                msg = f"No data returned for {symbol}. Check that the ticker symbol is valid on Yahoo Finance."
                print(f"\n  [WARNING] {msg}")
                send_error_alert(f"Symbol Not Found: {symbol}", msg)
                errors.append(symbol)
                continue

            df = add_indicators(df, config)
            df = add_td_sequential(df)

            summary = build_signal_summary(symbol, df)
            summaries.append(summary)

            print(format_ticker_block(idx, len(tickers), summary))

            # Save JSON data
            json_path = save_data_json(
                df, symbol, config.interval,
                signal_summary=build_daily_signal_summary(summary),
            )

            # Save/show chart
            image_path = default_image_path(symbol, config.interval) if save_charts else None
            if save_charts or show_charts:
                plot_with_mplfinance(df, config, output_path=None if show_charts else image_path)
                print(f"  Chart : {image_path}")
            print(f"  Data  : {json_path}")

            results.append({
                "symbol":       symbol,
                "date":         summary.last_date,
                "close":        summary.close,
                "ema10":        summary.ema10,
                "ema30":        summary.ema30,
                "macd_hist":    summary.macd_hist,
                "td_buy_setup": summary.td_buy,
                "td_sell_setup":summary.td_sell,
                "td_buy_9":     summary.td_buy_9,
                "td_sell_9":    summary.td_sell_9,
                "json_path":    json_path,
                "image_path":   image_path,
            })

        # Summary block
        if summaries:
            print(format_summary(summaries, date.today()))

        if errors:
            print(f"\n  [ALERT] Symbols not found or failed to load: {', '.join(errors)}")
            print("  Check that each ticker is a valid symbol on Yahoo Finance.")

    if write_output:
        out_path = _output_path()
        out_path.write_text(buffer.getvalue(), encoding="utf-8")
        sys.stdout.write(f"\n  Output saved: {out_path}\n")

    # Send to Discord after all output is written
    if summaries:
        send_daily_signals(summaries, date.today())

    return results


class _TeeWriter:
    """Write to two streams simultaneously."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> int:
        for s in self._streams:
            s.write(data)
        return len(data)

    def flush(self) -> None:
        for s in self._streams:
            s.flush()
