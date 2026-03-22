from __future__ import annotations

import numpy as np
import pandas as pd

from .config import PlotConfig


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def add_emas(df: pd.DataFrame, periods: list[int]) -> pd.DataFrame:
    for p in periods:
        df[f"ema_{p}"] = _ema(df["Close"], p)
    return df


def add_macd(df: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.DataFrame:
    ema_fast = _ema(df["Close"], fast)
    ema_slow = _ema(df["Close"], slow)
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = _ema(df["macd"], signal)
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def add_volume_ma(df: pd.DataFrame, period: int) -> pd.DataFrame:
    df["volume_ma"] = df["Volume"].rolling(window=period).mean()
    return df


def add_indicators(df: pd.DataFrame, config: PlotConfig) -> pd.DataFrame:
    df = add_emas(df, config.ema_periods)
    df = add_macd(df, config.macd_fast, config.macd_slow, config.macd_signal)
    df = add_volume_ma(df, config.volume_ma_period)
    return df
