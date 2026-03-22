"""Command-line interface for the DeMark/TD charting tool.

Usage examples:
  tdchart                          # loop through STOCK_LIST env var (daily signals)
  tdchart AAPL                     # single ticker
  tdchart AAPL --period 6mo --interval 1d --ema 10 30 50
  tdchart AAPL --start 2024-01-01 --end 2024-12-31 --no-td
  tdchart AAPL --show              # interactive window, still saves data JSON
  tdchart --csv data.csv --symbol MY_DATA
"""

from __future__ import annotations

import argparse
import sys

from .config import PlotConfig
from .data_loader import load_data
from .indicators import add_indicators
from .td_sequential import add_td_sequential
from .plotting_mpf import plot_with_mplfinance
from .exporter import default_image_path, save_data_json
from .signals import run_daily_signals


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tdchart",
        description=(
            "Plot candlestick chart with DeMark TD Sequential overlays.\n"
            "Run without a symbol to process all tickers in STOCK_LIST."
        ),
    )

    p.add_argument("symbol", nargs="?", default=None,
                   help="Ticker symbol. Omit to loop through STOCK_LIST env var.")

    # Data source
    src = p.add_argument_group("Data source")
    src.add_argument("--csv", metavar="PATH", help="Load OHLCV from a CSV file instead of yfinance")
    src.add_argument("--period", default="1y",
                     help="yfinance period (e.g. 1y, 6mo, 3mo). Ignored when --start/--end given.")
    src.add_argument("--interval", default="1d",
                     help="yfinance interval (e.g. 1d, 1wk, 1h). Default: 1d")
    src.add_argument("--start", metavar="YYYY-MM-DD", help="Start date")
    src.add_argument("--end",   metavar="YYYY-MM-DD", help="End date")

    # Indicators
    ind = p.add_argument_group("Indicators")
    ind.add_argument("--ema", nargs="+", type=int, default=[10, 30],
                     metavar="PERIOD", help="EMA periods to plot (default: 10 30)")
    ind.add_argument("--macd", nargs=3, type=int, default=[12, 26, 9],
                     metavar=("FAST", "SLOW", "SIGNAL"), help="MACD parameters (default: 12 26 9)")
    ind.add_argument("--vol-ma", type=int, default=20,
                     metavar="PERIOD", help="Volume MA period (default: 20)")
    ind.add_argument("--no-macd", action="store_true", help="Hide MACD panel")
    ind.add_argument("--no-td",   action="store_true", help="Hide TD Sequential markers")

    # Output
    out = p.add_argument_group("Output")
    out.add_argument("--show", action="store_true",
                     help="Open interactive chart window instead of saving PNG")
    out.add_argument("--style", default="nightclouds", help="mplfinance style (default: nightclouds)")

    return p


def _run_single(args: argparse.Namespace) -> None:
    """Process a single ticker symbol."""
    config = PlotConfig(
        symbol=args.symbol,
        interval=args.interval,
        period=args.period,
        start=args.start,
        end=args.end,
        ema_periods=args.ema,
        macd_fast=args.macd[0],
        macd_slow=args.macd[1],
        macd_signal=args.macd[2],
        volume_ma_period=args.vol_ma,
        show_td=not args.no_td,
        show_macd=not args.no_macd,
        style=args.style,
    )

    print(f"Loading data for {config.symbol}...")
    try:
        df = load_data(config, csv_path=args.csv)
    except Exception as exc:
        print(f"Error loading data: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"  {len(df)} bars loaded  ({df.index[0].date()} to {df.index[-1].date()})")

    df = add_indicators(df, config)
    df = add_td_sequential(df)

    buy9 = int(df["td_buy_9"].sum())
    sell9 = int(df["td_sell_9"].sum())
    print(f"  TD setups in range: {buy9} buy-9, {sell9} sell-9")

    last = df.iloc[-1]
    print(f"  Latest bar  [{df.index[-1].date()}]  "
          f"Buy setup: {int(last['td_buy_setup'])}/9  "
          f"Sell setup: {int(last['td_sell_setup'])}/9")

    json_path = save_data_json(df, config.symbol, config.interval)
    print(f"  Data saved: {json_path}")

    image_path = None if args.show else default_image_path(config.symbol, config.interval)
    plot_with_mplfinance(df, config, output_path=image_path)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.symbol is None:
        # No symbol given — run the full watchlist
        try:
            run_daily_signals(
                config_overrides=dict(
                    interval=args.interval,
                    period=args.period,
                    start=args.start,
                    end=args.end,
                    ema_periods=args.ema,
                    macd_fast=args.macd[0],
                    macd_slow=args.macd[1],
                    macd_signal=args.macd[2],
                    volume_ma_period=args.vol_ma,
                    show_td=not args.no_td,
                    show_macd=not args.no_macd,
                    style=args.style,
                ),
                save_charts=not args.show,
                show_charts=args.show,
            )
        except EnvironmentError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        _run_single(args)


if __name__ == "__main__":
    main()
