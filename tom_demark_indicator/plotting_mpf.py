from __future__ import annotations

import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

from .config import PlotConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _td_marker_series(
    df: pd.DataFrame,
    count_col: str,
    price_col: str,
    direction: str,  # "buy" or "sell"
    offset_frac: float = 0.003,
) -> pd.Series:
    """Return a Series with price offsets where TD count > 0, NaN elsewhere.

    offset_frac: fraction of the bar's price used as vertical spacing.
    """
    offset = df[price_col] * offset_frac
    mask = df[count_col] > 0
    values = np.where(
        mask,
        df[price_col] + (offset if direction == "sell" else -offset),
        np.nan,
    )
    return pd.Series(values, index=df.index)


def _add_td_text_labels(axes, df: pd.DataFrame, offset_frac: float = 0.003) -> None:
    """Overlay numeric TD counts as text using raw Matplotlib."""
    ax = axes[0]
    for i, (_, row) in enumerate(df.iterrows()):
        buy = int(row["td_buy_setup"])
        sell = int(row["td_sell_setup"])
        if buy > 0:
            y = row["Low"] * (1 - offset_frac * 2)
            ax.text(
                i, y, str(buy),
                ha="center", va="top",
                color="#00c853", fontsize=6, fontweight="bold",
            )
        if sell > 0:
            y = row["High"] * (1 + offset_frac * 2)
            ax.text(
                i, y, str(sell),
                ha="center", va="bottom",
                color="#ff1744", fontsize=6, fontweight="bold",
            )


# ---------------------------------------------------------------------------
# Main plotting function
# ---------------------------------------------------------------------------

def plot_with_mplfinance(
    df: pd.DataFrame,
    config: PlotConfig,
    output_path: str | None = None,
) -> None:
    """Render a candlestick chart with EMAs, MACD, volume MA, and TD markers.

    Parameters
    ----------
    df:          OHLCV + indicator columns (output of add_indicators + add_td_sequential).
    config:      PlotConfig controlling what to show.
    output_path: File path to save PNG.  None → interactive window.
    """
    apds: list = []

    # ------------------------------------------------------------------
    # EMA overlays on price panel (panel 0)
    # ------------------------------------------------------------------
    ema_colors = ["#2196f3", "#ff9800", "#9c27b0", "#00bcd4", "#f44336"]
    for idx, p in enumerate(config.ema_periods):
        col = f"ema_{p}"
        if col in df.columns:
            apds.append(
                mpf.make_addplot(
                    df[col],
                    panel=0,
                    color=ema_colors[idx % len(ema_colors)],
                    width=1.2,
                    label=f"EMA {p}",
                )
            )

    # ------------------------------------------------------------------
    # Volume MA on volume panel (panel 1)
    # ------------------------------------------------------------------
    if "volume_ma" in df.columns:
        apds.append(
            mpf.make_addplot(
                df["volume_ma"],
                panel=1,
                color="#b0bec5",
                width=1.0,
                label=f"Vol MA {config.volume_ma_period}",
            )
        )

    # ------------------------------------------------------------------
    # MACD panel (panel 2)
    # ------------------------------------------------------------------
    macd_panel = None
    if config.show_macd and "macd" in df.columns:
        macd_panel = 2
        apds.extend([
            mpf.make_addplot(df["macd"],        panel=macd_panel, color="#7b1fa2", width=1.2, label="MACD"),
            mpf.make_addplot(df["macd_signal"], panel=macd_panel, color="#9e9e9e", width=1.0, label="Signal"),
            mpf.make_addplot(
                df["macd_hist"],
                panel=macd_panel,
                type="bar",
                color=np.where(df["macd_hist"] >= 0, "#26a69a", "#ef5350").tolist(),
                alpha=0.6,
            ),
        ])

    # ------------------------------------------------------------------
    # TD Sequential markers on price panel
    # ------------------------------------------------------------------
    if config.show_td and "td_buy_setup" in df.columns:
        td_buy_marker = _td_marker_series(df, "td_buy_setup", "Low",  "buy")
        td_sell_marker = _td_marker_series(df, "td_sell_setup", "High", "sell")

        apds.append(
            mpf.make_addplot(
                td_buy_marker,
                panel=0,
                type="scatter",
                marker="^",
                color="#00c853",
                markersize=40,
            )
        )
        apds.append(
            mpf.make_addplot(
                td_sell_marker,
                panel=0,
                type="scatter",
                marker="v",
                color="#ff1744",
                markersize=40,
            )
        )

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------
    available_styles = mpf.available_styles()
    style_name = config.style if config.style in available_styles else "nightclouds"
    style = mpf.make_mpf_style(
        base_mpf_style=style_name,
        rc={"font.size": 8},
    )

    # ------------------------------------------------------------------
    # Panel ratios: price (3), volume (1), MACD (1.5) if present
    # ------------------------------------------------------------------
    panel_ratios = (3, 1, 1.5) if config.show_macd else (3, 1)

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    plot_kwargs = dict(
        type="candle",
        volume=True,
        addplot=apds if apds else None,
        style=style,
        figratio=config.figratio,
        figscale=1.2,
        title=f"\n{config.symbol}  [{config.interval}]",
        ylabel="Price",
        ylabel_lower="Volume",
        panel_ratios=panel_ratios,
        returnfig=True,
        warn_too_much_data=500,
    )

    fig, axes = mpf.plot(df, **plot_kwargs)

    # ------------------------------------------------------------------
    # Numeric TD labels (added after fig is built)
    # ------------------------------------------------------------------
    if config.show_td and "td_buy_setup" in df.columns:
        _add_td_text_labels(axes, df)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Chart saved to {output_path}")
    else:
        plt.show()

    plt.close(fig)
