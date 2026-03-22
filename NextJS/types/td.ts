// ── Per-bar row (one object per candle) ──────────────────────────────────────

export interface ChartRow {
  datetime:       string;   // ISO 8601, e.g. "2026-01-02T00:00:00"
  Open:           number;
  High:           number;
  Low:            number;
  Close:          number;
  Volume:         number;
  ema_10:         number;
  ema_30:         number;
  macd:           number;
  macd_signal:    number;
  macd_hist:      number;
  volume_ma:      number;
  td_buy_setup:   number;   // int 0-9  (0 = no active buy setup)
  td_sell_setup:  number;   // int 0-9  (0 = no active sell setup)
  td_buy_9:       0 | 1;   // 1 = buy setup complete on this bar
  td_sell_9:      0 | 1;   // 1 = sell setup complete on this bar
}

// ── Pre-computed signal summary (one object per ticker per run) ───────────────
// Computed by Python (formatter.py) so the web UI never re-implements logic.

export interface DailySignalSummary {
  trend:    'UP' | 'DOWN' | 'FLAT';
  td_event: string;           // full action label, e.g. "SELL SETUP FORMING -- 1 bar(s) to completion."
  risk:     'LOW' | 'MODERATE' | 'HIGH';
  is_alert: boolean;          // true only when a TD 9 is complete
}

// ── Top-level JSON payload ────────────────────────────────────────────────────

export interface ChartData {
  symbol:               string;
  interval:             string;   // yfinance interval, e.g. "1d", "1wk"
  exported_at:          string;   // ISO 8601
  rows:                 number;
  columns:              string[];
  daily_signal_summary: DailySignalSummary;
  data:                 ChartRow[];
}

// ── index.json entry (one per exported file) ──────────────────────────────────

export interface IndexEntry {
  ticker:               string;
  interval:             string;
  file:                 string;   // e.g. "AAPL_1d.json"
  rows:                 number;
  exported_at:          string;
  daily_signal_summary: DailySignalSummary;
}

export interface IndexFile {
  generated_at: string;
  entries:      IndexEntry[];
}

// ── UI state ──────────────────────────────────────────────────────────────────

export interface ChartVisibility {
  ema10:      boolean;
  ema30:      boolean;
  macd:       boolean;
  tdMarkers:  boolean;
}
