/**
 * Home page — watchlist grid.
 *
 * Reads export/nextjs/index.json (via NextJS/data/index.json) at build time
 * and renders one card per ticker with its pre-computed signal summary.
 * Clicking a card navigates to /symbol/[ticker].
 */

import type { GetStaticProps, NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { loadIndex } from '../lib/dataLoader';
import type { IndexEntry } from '../types/td';
import styles from './index.module.css';

// ── Colour maps (duplicated from SummaryCard intentionally — pages are standalone) ──

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

// ── Page component ────────────────────────────────────────────────────────────

interface Props {
  entries:      IndexEntry[];
  generated_at: string;
}

const Home: NextPage<Props> = ({ entries, generated_at }) => {
  const ts = new Date(generated_at).toLocaleString();

  return (
    <>
      <Head>
        <title>TD Sequential — Watchlist</title>
        <meta name="description" content="TD Sequential signal dashboard" />
      </Head>

      <main className={styles.main}>
        <header className={styles.header}>
          <h1>TD Sequential</h1>
          <span className={styles.ts}>Last export: {ts}</span>
        </header>

        <div className={styles.grid}>
          {entries.map(entry => {
            const { ticker, interval, daily_signal_summary: s } = entry;
            const trendColor = TREND_COLOR[s.trend]  ?? '#888';
            const riskColor  = RISK_COLOR[s.risk]    ?? '#888';

            return (
              <Link key={`${ticker}_${interval}`} href={`/symbol/${ticker}`} className={styles.card}>
                <div className={styles.cardTop}>
                  <span className={styles.ticker}>{ticker}</span>
                  <span className={styles.interval}>{interval}</span>
                  {s.is_alert && <span className={styles.alertDot} title="TD 9 alert" />}
                </div>

                <div className={styles.badges}>
                  <span className={styles.badge} style={{ color: trendColor, borderColor: trendColor }}>
                    {s.trend}
                  </span>
                  <span className={styles.badge} style={{ color: riskColor, borderColor: riskColor }}>
                    {s.risk}
                  </span>
                </div>

                <p className={styles.event}>{s.td_event}</p>
              </Link>
            );
          })}
        </div>
      </main>
    </>
  );
};

export default Home;

// ── SSG ───────────────────────────────────────────────────────────────────────

export const getStaticProps: GetStaticProps<Props> = async () => {
  const index = loadIndex();
  return {
    props: {
      entries:      index.entries,
      generated_at: index.generated_at,
    },
  };
};
