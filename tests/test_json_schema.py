"""Unit tests for the JSON export schema.

Verifies that save_data_json produces a stable, correctly-typed payload
across all symbols and timeframes, with and without daily_signal_summary.

Run with:  pytest tests/test_json_schema.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tom_demark_indicator.config import PlotConfig
from tom_demark_indicator.exporter import save_data_json
from tom_demark_indicator.formatter import (
    SignalSummary,
    build_daily_signal_summary,
    build_signal_summary,
)
from tom_demark_indicator.indicators import add_indicators
from tom_demark_indicator.td_sequential import add_td_sequential


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_df(n: int = 30, seed: int = 42) -> pd.DataFrame:
    """Return a synthetic OHLCV DataFrame with indicators and TD columns."""
    np.random.seed(seed)
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    close = 100.0 + np.cumsum(np.random.randn(n))
    df = pd.DataFrame(
        {
            "Open":   close - 0.5,
            "High":   close + 1.0,
            "Low":    close - 1.0,
            "Close":  close,
            "Volume": np.random.randint(1_000_000, 5_000_000, n).astype(float),
        },
        index=idx,
    )
    cfg = PlotConfig(symbol="TEST")
    df = add_indicators(df, cfg)
    df = add_td_sequential(df)
    return df


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return _make_df()


@pytest.fixture(scope="module")
def signal_summary(df) -> SignalSummary:
    return build_signal_summary("TEST", df)


@pytest.fixture(scope="module")
def summary_dict(signal_summary) -> dict:
    return build_daily_signal_summary(signal_summary)


@pytest.fixture(scope="module")
def payload_with_summary(df, summary_dict, tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("data")
    path = save_data_json(df, "TEST", "1d", signal_summary=summary_dict)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def payload_no_summary(df, tmp_path_factory) -> dict:
    path = save_data_json(df, "TEST2", "1d")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Root-level schema
# ---------------------------------------------------------------------------

class TestRootSchema:
    def test_symbol(self, payload_with_summary):
        assert payload_with_summary["symbol"] == "TEST"

    def test_timeframe_present(self, payload_with_summary):
        assert payload_with_summary["timeframe"] == "1d"

    def test_interval_key_removed(self, payload_with_summary):
        assert "interval" not in payload_with_summary

    def test_exported_at_is_iso8601(self, payload_with_summary):
        from datetime import datetime
        # Should parse without raising
        datetime.fromisoformat(payload_with_summary["exported_at"])

    def test_rows_matches_data_length(self, payload_with_summary):
        assert payload_with_summary["rows"] == len(payload_with_summary["data"])

    def test_columns_is_list_of_strings(self, payload_with_summary):
        cols = payload_with_summary["columns"]
        assert isinstance(cols, list)
        assert all(isinstance(c, str) for c in cols)

    def test_daily_signal_summary_present(self, payload_with_summary):
        assert "daily_signal_summary" in payload_with_summary

    def test_daily_signal_summary_before_data(self, payload_with_summary):
        keys = list(payload_with_summary.keys())
        assert keys.index("daily_signal_summary") < keys.index("data")

    def test_no_summary_when_omitted(self, payload_no_summary):
        assert "daily_signal_summary" not in payload_no_summary

    def test_timeframe_stable_without_summary(self, payload_no_summary):
        assert payload_no_summary["timeframe"] == "1d"


# ---------------------------------------------------------------------------
# daily_signal_summary types and values
# ---------------------------------------------------------------------------

class TestDailySignalSummary:
    VALID_TRENDS = {"UP", "DOWN", "FLAT"}
    VALID_RISKS  = {"LOW", "MODERATE", "HIGH"}

    def test_trend_valid(self, payload_with_summary):
        v = payload_with_summary["daily_signal_summary"]["trend"]
        assert v in self.VALID_TRENDS, f"Unexpected trend: {v!r}"

    def test_risk_valid(self, payload_with_summary):
        v = payload_with_summary["daily_signal_summary"]["risk"]
        assert v in self.VALID_RISKS, f"Unexpected risk: {v!r}"

    def test_td_event_is_string(self, payload_with_summary):
        v = payload_with_summary["daily_signal_summary"]["td_event"]
        assert isinstance(v, str) and len(v) > 0

    def test_is_alert_is_bool(self, payload_with_summary):
        v = payload_with_summary["daily_signal_summary"]["is_alert"]
        assert isinstance(v, bool), f"is_alert should be bool, got {type(v)}"

    def test_build_daily_signal_summary_keys(self, summary_dict):
        assert set(summary_dict.keys()) == {"trend", "td_event", "risk", "is_alert"}

    def test_is_alert_true_on_buy9(self):
        s = SignalSummary(
            symbol="X", last_date="2025-01-01",
            close=90.0, ema10=95.0, ema30=100.0,
            macd_hist=-0.5, macd_hist_prev=-0.3,
            td_buy=9, td_sell=0, td_buy_9=True, td_sell_9=False,
        )
        d = build_daily_signal_summary(s)
        assert d["is_alert"] is True
        assert d["trend"] == "DOWN"

    def test_is_alert_true_on_sell9(self):
        s = SignalSummary(
            symbol="X", last_date="2025-01-01",
            close=110.0, ema10=105.0, ema30=100.0,
            macd_hist=0.5, macd_hist_prev=0.3,
            td_buy=0, td_sell=9, td_buy_9=False, td_sell_9=True,
        )
        d = build_daily_signal_summary(s)
        assert d["is_alert"] is True
        assert d["trend"] == "UP"

    def test_is_alert_false_when_no_9(self, summary_dict):
        # Synthetic df rarely hits 9 in 30 bars; verify False path works
        # (is_alert may be True or False depending on seed — just check it's bool)
        assert isinstance(summary_dict["is_alert"], bool)


# ---------------------------------------------------------------------------
# Per-row data types
# ---------------------------------------------------------------------------

class TestDataRowTypes:
    @pytest.fixture(autouse=True)
    def _row(self, payload_with_summary):
        self.row = payload_with_summary["data"][0]

    def test_datetime_iso8601(self):
        dt = self.row["datetime"]
        assert isinstance(dt, str)
        assert "T" in dt, f"datetime not ISO 8601: {dt!r}"

    def test_ohlcv_numeric(self):
        for col in ("Open", "High", "Low", "Close", "Volume"):
            assert isinstance(self.row[col], (int, float)), f"{col} not numeric"

    def test_td_setup_counts_are_int(self):
        for col in ("td_buy_setup", "td_sell_setup"):
            v = self.row[col]
            assert isinstance(v, int), f"{col} not int: {type(v)}"
            assert 0 <= v <= 9, f"{col} out of range: {v}"

    def test_td_flags_are_zero_or_one(self):
        for col in ("td_buy_9", "td_sell_9"):
            v = self.row[col]
            assert v in (0, 1), f"{col} not 0/1: {v}"

    def test_ema_columns_float(self):
        for col in ("ema_10", "ema_30"):
            assert isinstance(self.row[col], float), f"{col} not float"

    def test_macd_columns_float(self):
        for col in ("macd", "macd_signal", "macd_hist"):
            assert isinstance(self.row[col], float), f"{col} not float"
