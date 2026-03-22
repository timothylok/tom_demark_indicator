from __future__ import annotations

import pandas as pd
import yfinance as yf

from .config import PlotConfig

_REQUIRED_COLS = {"Open", "High", "Low", "Close", "Volume"}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to Title-case so mplfinance is happy."""
    df = df.rename(columns={c: c.title() for c in df.columns})
    # yfinance sometimes returns multi-level columns; flatten if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


def _validate(df: pd.DataFrame) -> None:
    missing = _REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a DatetimeIndex.")


def load_from_yfinance(config: PlotConfig) -> pd.DataFrame:
    kwargs: dict = dict(
        ticker=config.symbol,
        interval=config.interval,
        auto_adjust=True,
        progress=False,
    )
    if config.start and config.end:
        kwargs["start"] = config.start
        kwargs["end"] = config.end
    else:
        kwargs["period"] = config.period

    ticker = yf.Ticker(config.symbol)
    df = ticker.history(
        interval=config.interval,
        period=config.period if not (config.start and config.end) else None,
        start=config.start,
        end=config.end,
        auto_adjust=True,
    )

    if df.empty:
        raise ValueError(f"No data returned for {config.symbol!r}. Check the symbol and date range.")

    df = _normalise_columns(df)
    # Drop columns we don't need (Dividends, Stock Splits, etc.)
    df = df[[c for c in df.columns if c in _REQUIRED_COLS]]
    df.index.name = "Date"
    _validate(df)
    return df


def load_from_csv(path: str) -> pd.DataFrame:
    """Load OHLCV from a CSV file.

    The CSV must have a date/datetime column (any name) and
    Open, High, Low, Close, Volume columns (case-insensitive).
    """
    df = pd.read_csv(path)
    df = _normalise_columns(df)

    # Find the date column (first column that parses as datetime)
    date_col = None
    for col in df.columns:
        if col.lower() in ("date", "datetime", "time", "timestamp"):
            date_col = col
            break
    if date_col is None:
        date_col = df.columns[0]

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    df.index.name = "Date"
    df = df.sort_index()
    _validate(df)
    return df


def load_data(config: PlotConfig | None = None, *, csv_path: str | None = None) -> pd.DataFrame:
    """Unified loader: prefer CSV if path given, otherwise fetch from yfinance."""
    if csv_path:
        return load_from_csv(csv_path)
    if config is None:
        raise ValueError("Either config or csv_path must be provided.")
    return load_from_yfinance(config)
