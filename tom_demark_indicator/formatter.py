"""Enhanced signal report formatter.

Produces a human-readable text report for each ticker and a daily summary.
All output is ASCII-only (Windows cp1252 terminal safe).
"""

from __future__ import annotations

from datetime import date
from typing import NamedTuple

import pandas as pd


_W = 66  # total line width


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

class SignalSummary(NamedTuple):
    symbol:        str
    last_date:     str
    close:         float
    ema10:         float
    ema30:         float
    macd_hist:     float
    macd_hist_prev: float
    td_buy:        int
    td_sell:       int
    td_buy_9:      bool
    td_sell_9:     bool


# ---------------------------------------------------------------------------
# Derived labels
# ---------------------------------------------------------------------------

def _trend(close: float, ema10: float, ema30: float) -> str:
    if close > ema10 and ema10 > ema30:
        return "UP"
    if close < ema10 and ema10 < ema30:
        return "DOWN"
    return "FLAT"


def _trend_detail(close: float, ema10: float, ema30: float) -> str:
    t = _trend(close, ema10, ema30)
    if t == "UP":
        return "UP   (Close > EMA10 > EMA30)"
    if t == "DOWN":
        return "DOWN (Close < EMA10 < EMA30)"
    # Flat: describe which condition broke
    if close > ema10:
        return "FLAT (Close > EMA10 but EMA10 < EMA30 -- crossover zone)"
    if close < ema10:
        return "FLAT (Close < EMA10 but EMA10 > EMA30 -- pullback zone)"
    return "FLAT (mixed signals)"


def _risk(macd_hist: float, macd_hist_prev: float) -> str:
    rising = macd_hist > macd_hist_prev
    if macd_hist > 0 and rising:
        return "LOW      (bullish momentum building)"
    if macd_hist > 0 and not rising:
        return "MODERATE (bullish momentum fading)"
    if macd_hist < 0 and not rising:
        return "HIGH     (bearish momentum building)"
    # macd_hist < 0 and rising
    return "MODERATE (bearish but momentum recovering)"


def _action(s: SignalSummary) -> tuple[str, bool]:
    """Return (action_text, is_alert).  is_alert=True triggers >>> <<< highlighting."""
    if s.td_buy_9:
        return "WATCH FOR REVERSAL -- BUY 9 COMPLETE. Potential exhaustion of downtrend.", True
    if s.td_sell_9:
        return "WATCH FOR REVERSAL -- SELL 9 COMPLETE. Potential exhaustion of uptrend.", True
    if s.td_buy in (7, 8):
        bars_left = 9 - s.td_buy
        return f"BUY SETUP FORMING -- {bars_left} bar(s) to completion. Monitor for reversal signal.", False
    if s.td_sell in (7, 8):
        bars_left = 9 - s.td_sell
        return f"SELL SETUP FORMING -- {bars_left} bar(s) to completion. Monitor for reversal signal.", False
    if s.td_buy in range(1, 7):
        return f"BUY SETUP IN PROGRESS -- count {s.td_buy}/9. No action yet.", False
    if s.td_sell in range(1, 7):
        return f"SELL SETUP IN PROGRESS -- count {s.td_sell}/9. No action yet.", False
    # No active TD setup
    t = _trend(s.close, s.ema10, s.ema30)
    if t == "UP":
        return "TREND INTACT -- bullish. Hold or look for pullback entries.", False
    if t == "DOWN":
        return "TREND INTACT -- bearish. Avoid longs; wait for reversal confirmation.", False
    return "CONSOLIDATING -- no clear trend or setup. Wait for direction.", False


def _ema_tag(close: float, ema: float) -> str:
    """Show +/- relative to close for quick at-a-glance."""
    diff = close - ema
    sign = "+" if diff >= 0 else "-"
    return f"{sign}${abs(diff):.2f}"


def _hist_tag(h: float) -> str:
    sign = "+" if h >= 0 else ""
    return f"{sign}{h:.3f}"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _divider(char: str = "-") -> str:
    return char * _W


def _header_line(text: str, char: str = "=") -> str:
    return char * _W + "\n" + f"  {text}" + "\n" + char * _W


def _col(label: str, value: str, width: int = 22) -> str:
    entry = f"{label}: {value}"
    return entry.ljust(width)


# ---------------------------------------------------------------------------
# Public: format one ticker block
# ---------------------------------------------------------------------------

def format_ticker_block(idx: int, total: int, s: SignalSummary) -> str:
    lines: list[str] = []

    action_text, is_alert = _action(s)
    trend_str = _trend_detail(s.close, s.ema10, s.ema30)
    risk_str  = _risk(s.macd_hist, s.macd_hist_prev)

    td_str = (
        f"Buy {s.td_buy}/9" if s.td_buy > 0
        else f"Sell {s.td_sell}/9" if s.td_sell > 0
        else "None"
    )

    # Title row
    alert_badge = "  [*** SIGNAL ***]" if is_alert else ""
    lines.append(_divider())
    lines.append(f"  [{idx}/{total}]  {s.symbol:<6}  |  {s.last_date}{alert_badge}")
    lines.append(_divider())

    # Key numbers (two columns per row)
    lines.append(
        "  " +
        _col("Close",    f"${s.close:.2f}") +
        _col("EMA10",    f"${s.ema10:.2f}  ({_ema_tag(s.close, s.ema10)})")
    )
    lines.append(
        "  " +
        _col("TD Setup", td_str) +
        _col("EMA30",    f"${s.ema30:.2f}  ({_ema_tag(s.close, s.ema30)})")
    )
    lines.append(
        "  " +
        _col("MACD Hist", _hist_tag(s.macd_hist)) +
        _col("Risk",     risk_str)
    )
    lines.append(
        "  " +
        f"Trend:   {trend_str}"
    )

    lines.append("")

    # Action line — highlighted for alerts
    if is_alert:
        lines.append("  " + ">" * (_W - 2))
        lines.append(f"  ACTION:  {action_text}")
        lines.append("  " + "<" * (_W - 2))
    else:
        lines.append(f"  Action:  {action_text}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public: daily summary block
# ---------------------------------------------------------------------------

def format_summary(signals: list[SignalSummary], run_date: date) -> str:
    lines: list[str] = []
    lines.append("")
    lines.append(_divider("="))
    lines.append(f"  DAILY SUMMARY  |  {run_date}")
    lines.append(_divider("="))

    buy9s  = [s.symbol for s in signals if s.td_buy_9]
    sell9s = [s.symbol for s in signals if s.td_sell_9]
    buy_active  = [s for s in signals if s.td_buy  > 0 and not s.td_buy_9]
    sell_active = [s for s in signals if s.td_sell > 0 and not s.td_sell_9]

    if buy9s:
        lines.append(f"  BUY  9 Signals  : {', '.join(buy9s)}  <-- WATCH FOR REVERSAL")
    if sell9s:
        lines.append(f"  SELL 9 Signals  : {', '.join(sell9s)}  <-- WATCH FOR REVERSAL")
    if not buy9s and not sell9s:
        lines.append("  No TD 9 signals today.")

    lines.append("")

    # Setup progress table
    lines.append("  Setup Progress:")
    lines.append(f"  {'Symbol':<8} {'TD':<16} {'Trend':<8} {'MACD Hist':<12} {'Risk'}")
    lines.append("  " + "-" * 58)
    for s in signals:
        td_str = (
            f"Buy  {s.td_buy}/9" if s.td_buy > 0
            else f"Sell {s.td_sell}/9" if s.td_sell > 0
            else "None     "
        )
        t = _trend(s.close, s.ema10, s.ema30)
        risk_short = _risk(s.macd_hist, s.macd_hist_prev).split()[0]
        hist_str = _hist_tag(s.macd_hist)
        flag = " ***" if (s.td_buy_9 or s.td_sell_9) else ""
        lines.append(
            f"  {s.symbol:<8} {td_str:<16} {t:<8} {hist_str:<12} {risk_short}{flag}"
        )

    lines.append(_divider("="))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public: full report header
# ---------------------------------------------------------------------------

def format_report_header(run_date: date, watchlist: list[str]) -> str:
    lines = [
        _divider("="),
        "  TD SEQUENTIAL DAILY SIGNALS",
        f"  Date      : {run_date}",
        f"  Watchlist : {', '.join(watchlist)}",
        _divider("="),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public: extract SignalSummary from a finished DataFrame
# ---------------------------------------------------------------------------

def build_signal_summary(symbol: str, df: pd.DataFrame) -> SignalSummary:
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    return SignalSummary(
        symbol=symbol,
        last_date=str(df.index[-1].date()),
        close=float(last["Close"]),
        ema10=float(last.get("ema_10", float("nan"))),
        ema30=float(last.get("ema_30", float("nan"))),
        macd_hist=float(last.get("macd_hist", 0.0)),
        macd_hist_prev=float(prev.get("macd_hist", 0.0)),
        td_buy=int(last["td_buy_setup"]),
        td_sell=int(last["td_sell_setup"]),
        td_buy_9=bool(last["td_buy_9"]),
        td_sell_9=bool(last["td_sell_9"]),
    )
