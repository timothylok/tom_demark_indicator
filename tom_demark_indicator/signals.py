"""Daily TD Sequential signal engine.

Reads STOCK_LIST from the environment, loops through each ticker,
computes indicators + TD setup counts, and prints a signal summary
for the most recent bar.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from .config import PlotConfig
from .data_loader import load_data
from .indicators import add_indicators
from .td_sequential import add_td_sequential
from .plotting_mpf import plot_with_mplfinance
from .exporter import save_data_json, default_image_path

# Load .env from the project root (two levels up from this file)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
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


def _signal_line(symbol: str, last_date: date, last_close: float,
                 buy: int, sell: int) -> str:
    """Format one row of the signal summary table."""
    if buy > 0:
        status = f"Buy  Setup  {buy}/9"
        flag = "  *** BUY 9 COMPLETE ***" if buy == 9 else ""
    elif sell > 0:
        status = f"Sell Setup  {sell}/9"
        flag = "  *** SELL 9 COMPLETE ***" if sell == 9 else ""
    else:
        status = "No active setup  "
        flag = ""
    return f"  {symbol:<6} | {status} | Close ${last_close:.2f} | {last_date}{flag}"


def run_daily_signals(
    config_overrides: dict | None = None,
    save_charts: bool = True,
    show_charts: bool = False,
) -> list[dict]:
    """Loop through STOCK_LIST and print TD signals for each ticker.

    Parameters
    ----------
    config_overrides: dict of PlotConfig field overrides applied to every ticker.
    save_charts:      Save PNG to images/ for each ticker.
    show_charts:      Open interactive window for each ticker (use sparingly).

    Returns a list of signal dicts (one per ticker that loaded successfully).
    """
    tickers = get_stock_list()
    overrides = config_overrides or {}

    print(f"\n=== Daily TD Sequential Signals [{date.today()}] ===")
    print(f"Watchlist: {', '.join(tickers)}\n")

    results: list[dict] = []
    errors: list[str] = []

    for symbol in tickers:
        config = PlotConfig(symbol=symbol, **overrides)
        try:
            df = load_data(config)
        except Exception as exc:
            msg = f"  [WARNING] {symbol}: could not load data — {exc}"
            print(msg)
            errors.append(symbol)
            continue

        if df.empty:
            print(f"  [WARNING] {symbol}: no data returned. Check that the ticker symbol is valid.")
            errors.append(symbol)
            continue

        df = add_indicators(df, config)
        df = add_td_sequential(df)

        last = df.iloc[-1]
        buy  = int(last["td_buy_setup"])
        sell = int(last["td_sell_setup"])
        line = _signal_line(symbol, df.index[-1].date(), float(last["Close"]), buy, sell)
        print(line)

        # Save JSON data
        json_path = save_data_json(df, symbol, config.interval)

        # Save/show chart
        image_path = default_image_path(symbol, config.interval) if save_charts else None
        if save_charts or show_charts:
            plot_with_mplfinance(df, config, output_path=None if show_charts else image_path)

        results.append({
            "symbol": symbol,
            "date": str(df.index[-1].date()),
            "close": float(last["Close"]),
            "td_buy_setup": buy,
            "td_sell_setup": sell,
            "td_buy_9": bool(last["td_buy_9"]),
            "td_sell_9": bool(last["td_sell_9"]),
            "json_path": json_path,
            "image_path": image_path,
        })

    print()
    if errors:
        print(f"  [ALERT] The following symbols were not found or failed to load: {', '.join(errors)}")
        print("  Check that each ticker is a valid symbol on Yahoo Finance.\n")

    return results
