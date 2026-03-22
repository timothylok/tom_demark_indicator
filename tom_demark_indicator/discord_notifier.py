"""Discord webhook notifier for daily TD Sequential signals.

Sends one embed per ticker plus a summary embed to a Discord channel.
Requires DISCORD_WEBHOOK_URL in .env.

Discord embed colour coding
---------------------------
BUY  9 complete  : bright green  (0x00e676)
SELL 9 complete  : bright red    (0xff1744)
Buy  setup 7-8   : light green   (0x69f0ae)
Sell setup 7-8   : orange        (0xff6d00)
Setup in progress: grey          (0x9e9e9e)
Trend intact UP  : sky blue      (0x40c4ff)
Trend intact DOWN: salmon        (0xff5252)
Consolidating    : light grey    (0xbdbdbd)
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from .formatter import SignalSummary, _trend, _risk, _action, _hist_tag, _ema_tag

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


# ---------------------------------------------------------------------------
# Colour map
# ---------------------------------------------------------------------------

def _embed_colour(s: SignalSummary) -> int:
    if s.td_buy_9:
        return 0x00e676   # bright green
    if s.td_sell_9:
        return 0xff1744   # bright red
    if s.td_buy in (7, 8):
        return 0x69f0ae   # light green
    if s.td_sell in (7, 8):
        return 0xff6d00   # orange
    if s.td_buy > 0 or s.td_sell > 0:
        return 0x9e9e9e   # grey — setup in progress
    t = _trend(s.close, s.ema10, s.ema30)
    if t == "UP":
        return 0x40c4ff   # sky blue
    if t == "DOWN":
        return 0xff5252   # salmon
    return 0xbdbdbd       # light grey — consolidating


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------

def _td_field_value(s: SignalSummary) -> str:
    if s.td_buy > 0:
        bar = ":white_check_mark:" if s.td_buy_9 else ":arrows_counterclockwise:"
        return f"{bar} Buy {s.td_buy}/9"
    if s.td_sell > 0:
        bar = ":warning:" if s.td_sell_9 else ":arrows_counterclockwise:"
        return f"{bar} Sell {s.td_sell}/9"
    return ":black_small_square: None"


def _risk_emoji(s: SignalSummary) -> str:
    r = _risk(s.macd_hist, s.macd_hist_prev).split()[0]
    return {"LOW": ":green_circle:", "MODERATE": ":yellow_circle:", "HIGH": ":red_circle:"}.get(r, "")


def _trend_emoji(s: SignalSummary) -> str:
    t = _trend(s.close, s.ema10, s.ema30)
    return {"UP": ":chart_with_upwards_trend:", "DOWN": ":chart_with_downwards_trend:", "FLAT": ":left_right_arrow:"}.get(t, "")


def _build_ticker_embed(s: SignalSummary) -> dict:
    action_text, is_alert = _action(s)
    trend_str  = _trend(s.close, s.ema10, s.ema30)
    risk_label = _risk(s.macd_hist, s.macd_hist_prev).split("(")[0].strip()

    alert_prefix = ":rotating_light: **SIGNAL** :rotating_light:  " if is_alert else ""
    title = f"{alert_prefix}{s.symbol}  |  {s.last_date}"

    description = f"> **Action:** {action_text}"

    fields = [
        {"name": ":moneybag: Close",      "value": f"`${s.close:.2f}`",                                "inline": True},
        {"name": ":chart: EMA10",         "value": f"`${s.ema10:.2f}` ({_ema_tag(s.close, s.ema10)})", "inline": True},
        {"name": ":chart: EMA30",         "value": f"`${s.ema30:.2f}` ({_ema_tag(s.close, s.ema30)})", "inline": True},
        {"name": ":bar_chart: TD Setup",  "value": _td_field_value(s),                                 "inline": True},
        {"name": ":abacus: MACD Hist",    "value": f"`{_hist_tag(s.macd_hist)}`",                      "inline": True},
        {"name": f"{_risk_emoji(s)} Risk","value": risk_label,                                          "inline": True},
        {"name": f"{_trend_emoji(s)} Trend", "value": trend_str,                                       "inline": False},
    ]

    return {
        "title":       title,
        "description": description,
        "color":       _embed_colour(s),
        "fields":      fields,
        "footer":      {"text": "TD Sequential Daily Signals"},
    }


def _build_summary_embed(signals: list[SignalSummary], run_date: date) -> dict:
    buy9s  = [s.symbol for s in signals if s.td_buy_9]
    sell9s = [s.symbol for s in signals if s.td_sell_9]

    # Headline
    if buy9s or sell9s:
        parts = []
        if buy9s:
            parts.append(f":rotating_light: **BUY 9:** {', '.join(buy9s)}")
        if sell9s:
            parts.append(f":rotating_light: **SELL 9:** {', '.join(sell9s)}")
        headline = "  |  ".join(parts)
    else:
        headline = ":white_check_mark: No TD 9 signals today."

    # Setup progress table (code block for alignment)
    rows = ["```", f"{'Symbol':<7} {'TD':<14} {'Trend':<6} {'MACD Hist':<11} Risk", "-" * 46]
    for s in signals:
        td_str = (
            f"Buy  {s.td_buy}/9" if s.td_buy  > 0
            else f"Sell {s.td_sell}/9" if s.td_sell > 0
            else "None     "
        )
        t     = _trend(s.close, s.ema10, s.ema30)
        risk  = _risk(s.macd_hist, s.macd_hist_prev).split()[0]
        hist  = _hist_tag(s.macd_hist)
        flag  = " ***" if (s.td_buy_9 or s.td_sell_9) else ""
        rows.append(f"{s.symbol:<7} {td_str:<14} {t:<6} {hist:<11} {risk}{flag}")
    rows.append("```")

    return {
        "title":       f":clipboard: Daily Summary  |  {run_date}",
        "description": headline + "\n\n" + "\n".join(rows),
        "color":       0x5865f2,   # Discord blurple
        "footer":      {"text": "TD Sequential Daily Signals"},
    }


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------

def _post_embeds(webhook_url: str, embeds: list[dict]) -> None:
    """POST up to 10 embeds per request (Discord limit)."""
    # Split into chunks of 10
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i + 10]
        payload = json.dumps({"embeds": chunk}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 204):
                    print(f"  [Discord] Unexpected status {resp.status}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"  [Discord] HTTP {exc.code}: {body}")
        except Exception as exc:
            print(f"  [Discord] Failed to send: {exc}")


def send_daily_signals(signals: list[SignalSummary], run_date: date) -> None:
    """Build and post all ticker + summary embeds to the Discord webhook.

    Silently skips if DISCORD_WEBHOOK_URL is not set.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("  [Discord] DISCORD_WEBHOOK_URL not set — skipping notification.")
        return

    embeds = [_build_ticker_embed(s) for s in signals]
    embeds.append(_build_summary_embed(signals, run_date))

    _post_embeds(webhook_url, embeds)
    print(f"  [Discord] Sent {len(embeds)} embeds to webhook.")
