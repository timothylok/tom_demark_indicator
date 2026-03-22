/**
 * Server-side helpers for reading generated JSON files.
 * Only imported inside getStaticProps / getStaticPaths — never in browser code.
 *
 * export_for_nextjs.py writes all JSON to NextJS/data/.
 * process.cwd() is the NextJS/ directory when `next build` runs.
 */

import fs   from 'fs';
import path from 'path';
import type { ChartData, IndexFile } from '../types/td';

const DATA_DIR = path.join(process.cwd(), 'data');

/** Load chart data for one ticker + interval. */
export function loadChartData(ticker: string, interval = '1d'): ChartData {
  const filePath = path.join(DATA_DIR, `${ticker}_${interval}.json`);
  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw) as ChartData;
}

/** Load index.json which lists all exported (ticker, interval) pairs. */
export function loadIndex(): IndexFile {
  const indexPath = path.join(DATA_DIR, 'index.json');
  const raw = fs.readFileSync(indexPath, 'utf-8');
  return JSON.parse(raw) as IndexFile;
}
