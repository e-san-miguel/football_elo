/**
 * Shared Plotly chart configuration and helpers.
 */

export const CHART_LAYOUT = {
    paper_bgcolor: '#0f172a',
    plot_bgcolor: '#0f172a',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 12 },
    xaxis: {
        gridcolor: '#1e293b',
        linecolor: '#1e293b',
        zerolinecolor: '#1e293b',
        tickfont: { size: 11 },
    },
    yaxis: {
        gridcolor: '#1e293b',
        linecolor: '#1e293b',
        zerolinecolor: '#1e293b',
        tickfont: { size: 11 },
        title: { text: 'Elo Rating', font: { size: 12 } },
    },
    margin: { l: 55, r: 20, t: 40, b: 50 },
    hoverlabel: {
        bgcolor: '#1e293b',
        bordercolor: '#06d6a0',
        font: { color: '#f1f5f9', size: 13 },
    },
    legend: {
        bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#94a3b8', size: 11 },
    },
    hovermode: 'x unified',
};

export const CHART_CONFIG = {
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
    displaylogo: false,
    responsive: true,
};

/** Default team color when not in the color map */
export const DEFAULT_COLOR = '#06d6a0';

/** Baseline rating line shape */
export function baselineShape(y = 1500) {
    return {
        type: 'line',
        x0: 0, x1: 1, xref: 'paper',
        y0: y, y1: y, yref: 'y',
        line: { color: '#334155', width: 1, dash: 'dash' },
    };
}
