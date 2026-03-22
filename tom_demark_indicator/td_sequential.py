"""TD Sequential setup counts.

TD Buy Setup:
  - Each bar's Close < Close 4 bars earlier.
  - Count consecutive qualifying bars (1–9); reset on failure.
  - Count resets after a completed sell setup 9 prints (price flip).

TD Sell Setup:
  - Each bar's Close > Close 4 bars earlier.
  - Same counting logic, opposite direction.

A "price flip" resets the opposing setup count:
  - Buy flip  (Close > Close[-4] after a bar where Close < Close[-4]) resets sell count.
  - Sell flip (Close < Close[-4] after a bar where Close > Close[-4]) resets buy count.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_td_sequential(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"].to_numpy(dtype=float)
    n = len(close)

    td_buy = np.zeros(n, dtype=int)
    td_sell = np.zeros(n, dtype=int)

    buy_count = 0
    sell_count = 0

    for i in range(4, n):
        c = close[i]
        c4 = close[i - 4]

        # TD Buy condition: close < close 4 bars ago
        if c < c4:
            # Price flip from sell side resets buy count to 1
            if sell_count > 0:
                buy_count = 0
            sell_count = 0
            buy_count += 1
            if buy_count > 9:
                buy_count = 1  # restart after 9
        # TD Sell condition: close > close 4 bars ago
        elif c > c4:
            # Price flip from buy side resets sell count to 1
            if buy_count > 0:
                sell_count = 0
            buy_count = 0
            sell_count += 1
            if sell_count > 9:
                sell_count = 1  # restart after 9
        else:
            # Equal close: counts continue (no flip, no increment)
            pass

        td_buy[i] = buy_count
        td_sell[i] = sell_count

    df["td_buy_setup"] = td_buy
    df["td_sell_setup"] = td_sell
    df["td_buy_9"] = td_buy == 9
    df["td_sell_9"] = td_sell == 9

    return df
