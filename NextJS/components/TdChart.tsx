/**
 * TdChart — interactive Plotly chart with three stacked subplots:
 *
 *   [1] Candlestick  +  EMA 10  +  EMA 30  +  TD markers
 *   [2] Volume bars  +  Volume MA
 *   [3] MACD histogram  +  MACD line  +  Signal line
 *
 * All panels share the same x-axis so zoom / pan stays in sync.
 * Visibility of EMA lines, MACD panel, and TD markers is controlled
 * by the `visibility` prop — no page reload required.
 *
 * react-plotly.js is loaded client-side only (no SSR) to avoid a
 * "window is not defined" error during Next.js static generation.
 */

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import type { PlotParams } from 'react-plotly.js';
import type { ChartRow, ChartVisibility } from '../types/td';

// Dynamic import disables SSR for this heavyweight library (~3 MB)
const Plot = dynamic<PlotParams>(() => import('react-plotly.js'), { ssr: false });

// ── Props ─────────────────────────────────────────────────────────────────────

interface TdChartProps {
  symbol:     string;
  data:       ChartRow[];
  visibility: ChartVisibility;
}

// ── Colour palette ────────────────────────────────────────────────────────────

const C = {
  bg:          '#0d1117',
  plotBg:      '#161b22',
  grid:        '#21262d',
  text:        '#c9d1d9',
  candleUp:    '#26a69a',
  candleDown:  '#ef5350',
  ema10:       '#ff9800',
  ema30:       '#42a5f5',
  volUp:       '#26a69a55',
  volDown:     '#ef535055',
  volMa:       '#ffd54f',
  macdHist:    { pos: '#26a69a77', neg: '#ef535077' },
  macdLine:    '#42a5f5',
  macdSignal:  '#ff9800',
  tdBuy:       '#66bb6a',
  tdSell:      '#ef9a9a',
  tdBuy9:      '#00e676',
  tdSell9:     '#ff1744',
  spike:       '#666677',
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function TdChart({ symbol, data, visibility }: TdChartProps) {

  const figure = useMemo(() => {
    const xs = data.map(r => r.datetime);

    // ── Subplot y-axis domains ────────────────────────────────────────────────
    // Vertical space is allocated depending on whether the MACD panel is shown.
    const priceDomain: [number, number] = visibility.macd ? [0.47, 1.00] : [0.30, 1.00];
    const volDomain:   [number, number] = visibility.macd ? [0.27, 0.44] : [0.00, 0.27];
    const macdDomain:  [number, number] = [0.00, 0.24];

    // ── [1] Candlestick ───────────────────────────────────────────────────────
    const candlestick = {
      type:       'candlestick' as const,
      name:       symbol,
      x:          xs,
      open:       data.map(r => r.Open),
      high:       data.map(r => r.High),
      low:        data.map(r => r.Low),
      close:      data.map(r => r.Close),
      increasing: { line: { color: C.candleUp },   fillcolor: C.candleUp },
      decreasing: { line: { color: C.candleDown },  fillcolor: C.candleDown },
      xaxis: 'x', yaxis: 'y',
      hoverinfo: 'x+y' as const,
      showlegend: false,
    };

    // ── [1] EMA lines ─────────────────────────────────────────────────────────
    const ema10Trace = {
      type:     'scatter' as const,
      name:     'EMA 10',
      x:        xs,
      y:        data.map(r => r.ema_10),
      mode:     'lines' as const,
      line:     { color: C.ema10, width: 1.5 },
      xaxis: 'x', yaxis: 'y',
      visible:  visibility.ema10 as boolean | 'legendonly',
      hovertemplate: 'EMA10: %{y:.2f}<extra></extra>',
    };

    const ema30Trace = {
      type:     'scatter' as const,
      name:     'EMA 30',
      x:        xs,
      y:        data.map(r => r.ema_30),
      mode:     'lines' as const,
      line:     { color: C.ema30, width: 1.5 },
      xaxis: 'x', yaxis: 'y',
      visible:  visibility.ema30 as boolean | 'legendonly',
      hovertemplate: 'EMA30: %{y:.2f}<extra></extra>',
    };

    // ── [1] TD markers ────────────────────────────────────────────────────────
    // Bars 1-8: small number above (sell) or below (buy) each bar.
    // Bar 9: larger bold number + triangle marker.

    const buyRows   = data.filter(r => r.td_buy_setup  > 0 && !r.td_buy_9);
    const sellRows  = data.filter(r => r.td_sell_setup > 0 && !r.td_sell_9);
    const buy9Rows  = data.filter(r => r.td_buy_9  === 1);
    const sell9Rows = data.filter(r => r.td_sell_9 === 1);

    // Small numbers placed at the bar's low / high (Plotly keeps them off-price)
    const tdBuyNumbers = {
      type:      'scatter' as const,
      name:      'TD Buy',
      x:         buyRows.map(r => r.datetime),
      y:         buyRows.map(r => r.Low),
      mode:      'text' as const,
      text:      buyRows.map(r => String(r.td_buy_setup)),
      textfont:  { color: C.tdBuy, size: 9 },
      textposition: 'bottom center' as const,
      xaxis: 'x', yaxis: 'y',
      visible:   visibility.tdMarkers as boolean | 'legendonly',
      hoverinfo: 'skip' as const,
    };

    const tdSellNumbers = {
      type:      'scatter' as const,
      name:      'TD Sell',
      x:         sellRows.map(r => r.datetime),
      y:         sellRows.map(r => r.High),
      mode:      'text' as const,
      text:      sellRows.map(r => String(r.td_sell_setup)),
      textfont:  { color: C.tdSell, size: 9 },
      textposition: 'top center' as const,
      xaxis: 'x', yaxis: 'y',
      visible:   visibility.tdMarkers as boolean | 'legendonly',
      hoverinfo: 'skip' as const,
    };

    // TD 9 — highlighted with triangle marker + bold "9"
    const tdBuy9 = {
      type:      'scatter' as const,
      name:      'Buy 9',
      x:         buy9Rows.map(r => r.datetime),
      y:         buy9Rows.map(r => r.Low),
      mode:      'markers+text' as const,
      marker:    { color: C.tdBuy9, size: 11, symbol: 'triangle-up' },
      text:      buy9Rows.map(() => '9'),
      textfont:  { color: C.tdBuy9, size: 11, family: 'Arial Black' },
      textposition: 'bottom center' as const,
      xaxis: 'x', yaxis: 'y',
      visible:   visibility.tdMarkers as boolean | 'legendonly',
      hovertemplate: '<b>BUY 9</b><br>%{x}<extra></extra>',
    };

    const tdSell9 = {
      type:      'scatter' as const,
      name:      'Sell 9',
      x:         sell9Rows.map(r => r.datetime),
      y:         sell9Rows.map(r => r.High),
      mode:      'markers+text' as const,
      marker:    { color: C.tdSell9, size: 11, symbol: 'triangle-down' },
      text:      sell9Rows.map(() => '9'),
      textfont:  { color: C.tdSell9, size: 11, family: 'Arial Black' },
      textposition: 'top center' as const,
      xaxis: 'x', yaxis: 'y',
      visible:   visibility.tdMarkers as boolean | 'legendonly',
      hovertemplate: '<b>SELL 9</b><br>%{x}<extra></extra>',
    };

    // ── [2] Volume bars ───────────────────────────────────────────────────────
    const volColors = data.map((r, i) =>
      i === 0 ? C.volUp : r.Close >= r.Open ? C.volUp : C.volDown
    );

    const volBars = {
      type:    'bar' as const,
      name:    'Volume',
      x:       xs,
      y:       data.map(r => r.Volume),
      marker:  { color: volColors },
      xaxis: 'x', yaxis: 'y2',
      hovertemplate: 'Vol: %{y:.3s}<extra></extra>',
      showlegend: false,
    };

    const volMaLine = {
      type:  'scatter' as const,
      name:  'Vol MA',
      x:     xs,
      y:     data.map(r => r.volume_ma),
      mode:  'lines' as const,
      line:  { color: C.volMa, width: 1.2 },
      xaxis: 'x', yaxis: 'y2',
      hovertemplate: 'VolMA: %{y:.3s}<extra></extra>',
    };

    // ── [3] MACD ──────────────────────────────────────────────────────────────
    const macdHistColors = data.map(r =>
      r.macd_hist >= 0 ? C.macdHist.pos : C.macdHist.neg
    );

    const macdHist = {
      type:    'bar' as const,
      name:    'Hist',
      x:       xs,
      y:       data.map(r => r.macd_hist),
      marker:  { color: macdHistColors },
      xaxis: 'x', yaxis: 'y3',
      visible: visibility.macd as boolean | 'legendonly',
      hovertemplate: 'Hist: %{y:.4f}<extra></extra>',
    };

    const macdLine = {
      type:  'scatter' as const,
      name:  'MACD',
      x:     xs,
      y:     data.map(r => r.macd),
      mode:  'lines' as const,
      line:  { color: C.macdLine, width: 1.5 },
      xaxis: 'x', yaxis: 'y3',
      visible: visibility.macd as boolean | 'legendonly',
      hovertemplate: 'MACD: %{y:.4f}<extra></extra>',
    };

    const macdSignalLine = {
      type:  'scatter' as const,
      name:  'Signal',
      x:     xs,
      y:     data.map(r => r.macd_signal),
      mode:  'lines' as const,
      line:  { color: C.macdSignal, width: 1.5 },
      xaxis: 'x', yaxis: 'y3',
      visible: visibility.macd as boolean | 'legendonly',
      hovertemplate: 'Sig: %{y:.4f}<extra></extra>',
    };

    // ── Layout ────────────────────────────────────────────────────────────────
    const layout = {
      paper_bgcolor: C.bg,
      plot_bgcolor:  C.plotBg,
      font:  { color: C.text, family: "'Courier New', monospace", size: 11 },
      margin: { t: 48, r: 24, b: 40, l: 70 },

      // Shared x-axis — all subplots zoom/pan together
      xaxis: {
        type:          'date' as const,
        gridcolor:     C.grid,
        linecolor:     C.grid,
        tickfont:      { size: 10 },
        rangeslider:   { visible: false },
        rangeselector: {
          bgcolor:    C.plotBg,
          bordercolor: C.grid,
          font:        { size: 10 },
          buttons: [
            { count: 1,  label: '1M',  step: 'month' as const, stepmode: 'backward' as const },
            { count: 3,  label: '3M',  step: 'month' as const, stepmode: 'backward' as const },
            { count: 6,  label: '6M',  step: 'month' as const, stepmode: 'backward' as const },
            { count: 1,  label: '1Y',  step: 'year'  as const, stepmode: 'backward' as const },
            {             label: 'All', step: 'all'   as const },
          ],
        },
        showspikes:    true,
        spikecolor:    C.spike,
        spikethickness: 1,
        spikemode:     'across' as const,
      },

      // y-axis 1 — price
      yaxis: {
        domain:     priceDomain,
        gridcolor:  C.grid,
        linecolor:  C.grid,
        tickfont:   { size: 10 },
        title:      { text: 'Price', font: { size: 11 } },
        showspikes: true,
        spikecolor: C.spike,
        spikethickness: 1,
        fixedrange: false,
      },

      // y-axis 2 — volume
      yaxis2: {
        domain:    volDomain,
        gridcolor: C.grid,
        linecolor: C.grid,
        tickfont:  { size: 9 },
        title:     { text: 'Vol', font: { size: 10 }, standoff: 4 },
        fixedrange: true,
      },

      // y-axis 3 — MACD
      yaxis3: {
        domain:        macdDomain,
        gridcolor:     C.grid,
        linecolor:     C.grid,
        zerolinecolor: '#444455',
        tickfont:      { size: 9 },
        title:         { text: 'MACD', font: { size: 10 }, standoff: 4 },
        fixedrange:    true,
      },

      legend: {
        orientation: 'h' as const,
        x: 0, y: 1.04,
        bgcolor: 'transparent',
        font:    { size: 10 },
      },

      hovermode:  'x unified' as const,
      dragmode:   'zoom' as const,
      showlegend: true,

      // Gap between subplot panels
      yaxis2_anchor: 'x',
      yaxis3_anchor: 'x',
    };

    return {
      traces: [
        candlestick,
        ema10Trace, ema30Trace,
        tdBuyNumbers, tdSellNumbers, tdBuy9, tdSell9,
        volBars, volMaLine,
        macdHist, macdLine, macdSignalLine,
      ],
      layout,
    };
  }, [data, symbol, visibility]);

  return (
    <Plot
      data={figure.traces as PlotParams['data']}
      layout={figure.layout as PlotParams['layout']}
      config={{
        responsive:               true,
        scrollZoom:               true,
        displayModeBar:           true,
        modeBarButtonsToRemove:   ['toImage', 'sendDataToCloud'] as any,
        displaylogo:              false,
      }}
      style={{ width: '100%', height: '720px' }}
      useResizeHandler
    />
  );
}
