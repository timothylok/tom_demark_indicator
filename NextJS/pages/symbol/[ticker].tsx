/**
 * /symbol/[ticker] — individual symbol chart page.
 *
 * Static generation flow (runs at `next build` time):
 *
 *   getStaticPaths  →  reads NextJS/data/index.json
 *                       returns one path per ticker (always 1d interval)
 *
 *   getStaticProps  →  reads NextJS/data/{TICKER}_1d.json
 *                       parses it into ChartData and passes as props
 *
 * At runtime in the browser:
 *   - SummaryCard shows pre-computed signal data (no JS logic needed)
 *   - ChartControls toggles layer visibility via React state
 *   - TdChart renders the Plotly figure, reacting to visibility changes
 */

import React, { useState } from 'react';
import type { GetStaticPaths, GetStaticProps, NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';

import { loadChartData, loadIndex } from '../../lib/dataLoader';
import SummaryCard    from '../../components/SummaryCard';
import ChartControls  from '../../components/ChartControls';
import TdChart        from '../../components/TdChart';

import type { ChartData, ChartVisibility } from '../../types/td';
import styles from './ticker.module.css';

// ── Props ─────────────────────────────────────────────────────────────────────

interface Props {
  chartData: ChartData;
}

// ── Page component ────────────────────────────────────────────────────────────

const SymbolPage: NextPage<Props> = ({ chartData }) => {
  const { symbol, interval, exported_at, data, daily_signal_summary } = chartData;
  const lastRow = data[data.length - 1];

  // All layers visible by default
  const [visibility, setVisibility] = useState<ChartVisibility>({
    ema10:     true,
    ema30:     true,
    macd:      true,
    tdMarkers: true,
  });

  const exportedTs = new Date(exported_at).toLocaleString();

  return (
    <>
      <Head>
        <title>{symbol} — TD Sequential</title>
        <meta
          name="description"
          content={`${symbol} TD Sequential chart: ${daily_signal_summary.td_event}`}
        />
      </Head>

      <main className={styles.main}>
        {/* ── Nav ─────────────────────────────────────────────────────────── */}
        <nav className={styles.nav}>
          <Link href="/" className={styles.back}>← Watchlist</Link>
          <span className={styles.meta}>
            {symbol} &nbsp;·&nbsp; {interval} &nbsp;·&nbsp;
            {data.length} bars &nbsp;·&nbsp; exported {exportedTs}
          </span>
        </nav>

        {/* ── Summary card ─────────────────────────────────────────────────── */}
        <SummaryCard
          symbol={symbol}
          lastRow={lastRow}
          summary={daily_signal_summary}
        />

        {/* ── Layer toggle controls ─────────────────────────────────────────── */}
        <ChartControls visibility={visibility} onChange={setVisibility} />

        {/* ── Interactive chart ─────────────────────────────────────────────── */}
        <div className={styles.chartWrap}>
          <TdChart
            symbol={symbol}
            data={data}
            visibility={visibility}
          />
        </div>
      </main>
    </>
  );
};

export default SymbolPage;

// ── SSG: paths ────────────────────────────────────────────────────────────────

export const getStaticPaths: GetStaticPaths = async () => {
  const index = loadIndex();

  // One path per ticker; the interval is fixed to 1d here.
  // If you later export multiple intervals, you can include interval in the
  // slug or add a second dynamic segment.
  const paths = index.entries.map(entry => ({
    params: { ticker: entry.ticker },
  }));

  return { paths, fallback: false };
};

// ── SSG: props ────────────────────────────────────────────────────────────────

export const getStaticProps: GetStaticProps<Props> = async ({ params }) => {
  const ticker = params?.ticker as string;

  // Hardcoded to 1d — extend here when multi-interval support is added
  const chartData = loadChartData(ticker, '1d');

  return {
    props: { chartData },
  };
};
