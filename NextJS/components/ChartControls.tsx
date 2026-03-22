/**
 * ChartControls — toggle buttons for chart layer visibility.
 *
 * Toggles: EMA 10 | EMA 30 | MACD panel | TD markers
 *
 * State lives in the parent page and is passed down as props so the
 * chart re-renders without a page reload.
 */

import React from 'react';
import type { ChartVisibility } from '../types/td';
import styles from './ChartControls.module.css';

interface ChartControlsProps {
  visibility: ChartVisibility;
  onChange:   (next: ChartVisibility) => void;
}

type Key = keyof ChartVisibility;

const CONTROLS: { key: Key; label: string; color: string }[] = [
  { key: 'ema10',     label: 'EMA 10',     color: '#ff9800' },
  { key: 'ema30',     label: 'EMA 30',     color: '#42a5f5' },
  { key: 'macd',      label: 'MACD',       color: '#66bb6a' },
  { key: 'tdMarkers', label: 'TD Markers', color: '#e0e0e0' },
];

export default function ChartControls({ visibility, onChange }: ChartControlsProps) {
  const toggle = (key: Key) =>
    onChange({ ...visibility, [key]: !visibility[key] });

  return (
    <div className={styles.bar}>
      <span className={styles.label}>Show:</span>
      {CONTROLS.map(({ key, label, color }) => (
        <button
          key={key}
          className={styles.btn}
          data-active={visibility[key]}
          style={{ '--accent': color } as React.CSSProperties}
          onClick={() => toggle(key)}
          aria-pressed={visibility[key]}
          title={`Toggle ${label}`}
        >
          <span className={styles.dot} />
          {label}
        </button>
      ))}
    </div>
  );
}
