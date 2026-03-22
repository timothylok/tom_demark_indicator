from dataclasses import dataclass, field


@dataclass
class PlotConfig:
    symbol: str = "AAPL"
    interval: str = "1d"          # yfinance interval string
    period: str = "1y"            # yfinance period string (used when start/end not given)
    start: str | None = None      # YYYY-MM-DD
    end: str | None = None        # YYYY-MM-DD
    ema_periods: list[int] = field(default_factory=lambda: [10, 30])
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    volume_ma_period: int = 20
    show_td: bool = True
    show_macd: bool = True
    style: str = "nightclouds"    # any mplfinance built-in style
    figratio: tuple[int, int] = (16, 9)
