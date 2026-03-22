/**
 * SummaryCard — shows the latest signal snapshot above the chart.
 *
 * Displays: symbol, latest close, trend badge, TD event text,
 * risk badge, and a one-line plain-English summary.
 *
 * All values come from the pre-computed daily_signal_summary written
 * by Python so no signal logic lives in the frontend.
 */

import React from 'react';
import type { DailySignalSummary, ChartRow } from '../types/td';
import styles from './SummaryCard.module.css';

interface SummaryCardProps {
  symbol:  string;
  lastRow: ChartRow;
  summary: DailySignalSummary;
}

// ── Badge colour maps ─────────────────────────────────────────────────────────

const TREND_COLOR: Record<string, string> = {
  UP:   '#26a69a',
  DOWN: '#ef5350',
  FLAT: '#9e9e9e',
};

const RISK_COLOR: Record<string, string> = {
  LOW:      '#26a69a',
  MODERATE: '#ff9800',
  HIGH:     '#ef5350',
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function SummaryCard({ symbol, lastRow, summary }: SummaryCardProps) {
  const { trend, td_event, risk, is_alert } = summary;

  // Build a human-readable one-liner, e.g.:
  // "Uptrend  |  TD Buy Setup In Progress (count 3/9)  |  Risk: LOW"
  const trendWord = trend === 'UP' ? 'Uptrend' : trend === 'DOWN' ? 'Downtrend' : 'Sideways';
  const oneLiner  = `${trendWord}  |  ${td_event}  |  Risk: ${risk}`;

  // Format close price with 2 decimal places
  const closeStr = lastRow.Close.toLocaleString('en-US', {
    style: 'currency', currency: 'USD', minimumFractionDigits: 2,
  });

  // EMA relationship label
  const emaLabel = (() => {
    const { Close, ema_10, ema_30 } = lastRow;
    if (Close > ema_10 && ema_10 > ema_30) return 'Close > EMA10 > EMA30';
    if (Close < ema_10 && ema_10 < ema_30) return 'Close < EMA10 < EMA30';
    return 'Mixed EMA alignment';
  })();

  return (
    <div className={styles.card} data-alert={is_alert}>
      {/* Symbol + price row */}
      <div className={styles.header}>
        <span className={styles.symbol}>{symbol}</span>
        <span className={styles.close}>{closeStr}</span>
        {is_alert && <span className={styles.alertBadge}>SIGNAL</span>}
      </div>

      {/* Badges row */}
      <div className={styles.badges}>
        <Badge label="Trend" value={trend}  color={TREND_COLOR[trend]  ?? '#888'} />
        <Badge label="Risk"  value={risk}   color={RISK_COLOR[risk]    ?? '#888'} />
        <span className={styles.emaHint}>{emaLabel}</span>
      </div>

      {/* TD event text */}
      <div className={styles.event}>{td_event}</div>

      {/* One-liner summary */}
      <div className={styles.oneLiner}>{oneLiner}</div>
    </div>
  );
}

// ── Small reusable badge ──────────────────────────────────────────────────────

function Badge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <span className={styles.badge} style={{ borderColor: color, color }}>
      <span className={styles.badgeLabel}>{label}:</span> {value}
    </span>
  );
}
