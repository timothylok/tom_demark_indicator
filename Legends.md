# Signal Report — Label Logic Reference

All logic is implemented in `tom_demark_indicator/formatter.py`.

---

## Trend

Determined by comparing the latest **Close** against **EMA10** and **EMA30**.

| Label | Condition |
|---|---|
| `UP` | Close > EMA10 **and** EMA10 > EMA30 |
| `DOWN` | Close < EMA10 **and** EMA10 < EMA30 |
| `FLAT` | Neither of the above (mixed signals) |

### FLAT sub-cases (shown in detail line)

| Sub-label | Condition | Interpretation |
|---|---|---|
| `Close > EMA10 but EMA10 < EMA30` | Close above short EMA but short EMA still below long EMA | Crossover zone — early bullish attempt |
| `Close < EMA10 but EMA10 > EMA30` | Close below short EMA but short EMA still above long EMA | Pullback zone — trend intact but price pulling back |
| `mixed signals` | All other cases | No clear directional bias |

---

## EMA Offset Tags

Shown in parentheses next to each EMA value, e.g. `(-$5.45)`.

| Sign | Meaning |
|---|---|
| `+$X.XX` | Close is **above** that EMA by $X.XX |
| `-$X.XX` | Close is **below** that EMA by $X.XX |

Useful for gauging how extended price is from its moving averages.

---

## Risk

Determined by the direction of the **MACD histogram** over the last two bars.

| Label | Condition | Interpretation |
|---|---|---|
| `LOW` | Hist > 0 **and** rising (hist > prev hist) | Bullish momentum building |
| `MODERATE` | Hist > 0 **and** falling (hist < prev hist) | Bullish momentum fading — watch for weakening |
| `MODERATE` | Hist < 0 **and** rising (hist > prev hist) | Bearish but momentum recovering — possible bottoming |
| `HIGH` | Hist < 0 **and** falling (hist < prev hist) | Bearish momentum building — avoid longs |

---

## TD Sequential Setup Counts

Based on Tom DeMark's TD Sequential methodology.

### Buy Setup
- Each bar's **Close < Close 4 bars earlier**
- Consecutive qualifying bars are counted 1 through 9
- Count resets on a price flip (a bar where Close > Close 4 bars earlier)
- Count restarts from 1 after reaching 9

### Sell Setup
- Each bar's **Close > Close 4 bars earlier**
- Same counting logic, opposite direction

### Price Flip
- A move from a sell-condition bar to a buy-condition bar resets the sell count
- A move from a buy-condition bar to a sell-condition bar resets the buy count
- Equal closes (Close == Close[-4]) do not increment or reset either count

---

## Action Labels

Assigned based on TD setup count, completion status, and trend.

| Action Label | Condition | Meaning |
|---|---|---|
| `WATCH FOR REVERSAL -- BUY 9 COMPLETE` | `td_buy_9 == True` | TD buy setup completed; potential exhaustion of downtrend. **Alert triggered (`>>>`)** |
| `WATCH FOR REVERSAL -- SELL 9 COMPLETE` | `td_sell_9 == True` | TD sell setup completed; potential exhaustion of uptrend. **Alert triggered (`>>>`)** |
| `BUY SETUP FORMING -- N bar(s) to completion` | `td_buy in {7, 8}` | Setup close to completion; monitor for reversal signal |
| `SELL SETUP FORMING -- N bar(s) to completion` | `td_sell in {7, 8}` | Setup close to completion; monitor for reversal signal |
| `BUY SETUP IN PROGRESS -- count N/9` | `td_buy in 1..6` | Early-stage buy setup; no action yet |
| `SELL SETUP IN PROGRESS -- count N/9` | `td_sell in 1..6` | Early-stage sell setup; no action yet |
| `TREND INTACT -- bullish` | No active setup **and** Trend == UP | Price above both EMAs; hold or look for pullback entries |
| `TREND INTACT -- bearish` | No active setup **and** Trend == DOWN | Price below both EMAs; avoid longs, wait for reversal confirmation |
| `CONSOLIDATING` | No active setup **and** Trend == FLAT | No clear trend or setup; wait for direction |

### Alert Highlighting (`>>>` / `<<<`)

Only triggered when a **TD 9 is complete** (buy or sell).
These are the highest-priority signals — potential trend exhaustion and reversal points.

```
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ACTION:  WATCH FOR REVERSAL -- BUY 9 COMPLETE. Potential exhaustion of downtrend.
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
```

---

## Summary Table Flags

| Flag | Condition |
|---|---|
| `***` | Ticker has a completed TD 9 (buy or sell) |
| `<-- WATCH FOR REVERSAL` | Listed in BUY 9 or SELL 9 signals section |

---

## Discord Embed Colour Coding

Implemented in `tom_demark_indicator/discord_notifier.py`.

| Colour | Hex | Condition |
|---|---|---|
| Bright green | `#00e676` | BUY 9 complete |
| Bright red | `#ff1744` | SELL 9 complete |
| Light green | `#69f0ae` | Buy setup count 7 or 8 |
| Orange | `#ff6d00` | Sell setup count 7 or 8 |
| Grey | `#9e9e9e` | Buy or sell setup in progress (count 1-6) |
| Sky blue | `#40c4ff` | No setup, trend UP |
| Salmon | `#ff5252` | No setup, trend DOWN |
| Light grey | `#bdbdbd` | No setup, trend FLAT (consolidating) |
| Discord blurple | `#5865f2` | Summary embed |

### Discord Emoji Indicators

| Emoji | Meaning |
|---|---|
| :rotating_light: | TD 9 signal (buy or sell complete) -- alert |
| :white_check_mark: | Buy 9 complete |
| :warning: | Sell 9 complete |
| :arrows_counterclockwise: | Setup in progress (not yet 9) |
| :black_small_square: | No active setup |
| :green_circle: | Risk LOW |
| :yellow_circle: | Risk MODERATE |
| :red_circle: | Risk HIGH |
| :chart_with_upwards_trend: | Trend UP |
| :chart_with_downwards_trend: | Trend DOWN |
| :left_right_arrow: | Trend FLAT |

---

## Important Caveats

- TD Sequential counts price **exhaustion**, not direction. A Buy 9 means a downtrend may be exhausted — it does **not** guarantee a bounce.
- Always confirm with other signals (MACD direction, EMA alignment, volume) before acting.
- Risk labels are based on a 2-bar MACD histogram comparison — they reflect short-term momentum only.
- EMA offsets show distance from price to the average, not rate of change.
