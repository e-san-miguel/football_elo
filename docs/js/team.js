/**
 * Team detail view — rating history chart, stats, recent matches.
 */

import { getRankings, getTeamHistory, getTeamColors } from './data.js';
import { CHART_LAYOUT, CHART_CONFIG, DEFAULT_COLOR, baselineShape } from './charts.js';
import { el, formatRating, formatChange, changeClass } from './utils.js';

export async function render(container, slug) {
    container.innerHTML = '<div class="loading">Loading team data...</div>';

    const [rankings, teamData, colors] = await Promise.all([
        getRankings(),
        getTeamHistory(slug),
        getTeamColors(),
    ]);

    const teamInfo = rankings.teams.find(t => t.slug === slug);
    if (!teamInfo) {
        container.innerHTML = '<p>Team not found.</p>';
        return;
    }

    const history = teamData.history;
    const color = colors[slug] || DEFAULT_COLOR;

    container.innerHTML = '';

    // Back link
    container.appendChild(el('a', { class: 'back-link', href: '#/', html: '&larr; Back to Rankings' }));

    // Header
    const header = el('div', { class: 'team-header' }, [
        el('h1', { text: teamInfo.team }),
        el('span', { class: 'team-rank-badge', text: `#${teamInfo.rank}` }),
    ]);
    container.appendChild(header);

    // Big rating
    const lastChange = history.length > 0 ? history[history.length - 1].rc : 0;
    const ratingDiv = el('div', { class: 'team-rating-big' }, [
        document.createTextNode(formatRating(teamInfo.rating)),
        el('span', {
            class: `team-rating-change ${changeClass(lastChange)}`,
            text: formatChange(lastChange),
        }),
    ]);
    container.appendChild(ratingDiv);

    // Stats cards
    const peakRating = Math.max(...history.map(h => h.ra));
    const peakDate = history.find(h => h.ra === peakRating)?.date || '';
    const lowRating = Math.min(...history.map(h => h.ra));
    const wins = history.filter(h => h.ts > h.os).length;
    const draws = history.filter(h => h.ts === h.os).length;
    const losses = history.filter(h => h.ts < h.os).length;

    const statsRow = el('div', { class: 'stat-cards' }, [
        statCard(formatRating(peakRating), `Peak (${peakDate})`),
        statCard(formatRating(lowRating), 'Lowest'),
        statCard(history.length.toString(), 'Matches'),
        statCard(`${wins}W ${draws}D ${losses}L`, 'Record'),
    ]);
    container.appendChild(statsRow);

    // Chart
    const chartCard = el('div', { class: 'card' }, [
        el('h2', { text: 'Rating History' }),
        el('div', { class: 'chart-container', id: 'team-chart' }),
    ]);
    container.appendChild(chartCard);

    // Recent matches
    const matchesCard = el('div', { class: 'card' }, [
        el('h2', { text: 'Recent Matches' }),
        buildMatchesTable(history.slice(-20).reverse()),
    ]);
    container.appendChild(matchesCard);

    // Compare button
    const compareBtn = el('a', {
        href: `#/compare/${slug}`,
        class: 'back-link',
        text: 'Compare with other teams \u2192',
    });
    container.appendChild(compareBtn);

    // Render Plotly chart
    renderChart(history, color, teamInfo.team);
}

function statCard(value, label) {
    return el('div', { class: 'stat-card' }, [
        el('div', { class: 'stat-value', text: value }),
        el('div', { class: 'stat-label', text: label }),
    ]);
}

function renderChart(history, color, teamName) {
    const dates = history.map(h => h.date);
    const ratings = history.map(h => h.ra);
    const hoverText = history.map(h => {
        const result = h.ts > h.os ? 'W' : h.ts < h.os ? 'L' : 'D';
        return `${h.date}<br>${result} ${h.ts}-${h.os} vs ${h.opponent}<br>Rating: ${h.ra} (${h.rc >= 0 ? '+' : ''}${h.rc})<br>${h.tournament}`;
    });

    const trace = {
        x: dates,
        y: ratings,
        type: 'scatter',
        mode: 'lines',
        line: { color: color === '#ffffff' ? '#94a3b8' : color, width: 2 },
        name: teamName,
        hovertext: hoverText,
        hoverinfo: 'text',
    };

    const layout = {
        ...CHART_LAYOUT,
        showlegend: false,
        shapes: [baselineShape()],
        xaxis: {
            ...CHART_LAYOUT.xaxis,
            rangeslider: { bgcolor: '#111827', bordercolor: '#1e293b' },
            range: ['1990-01-01', dates[dates.length - 1]],
        },
    };

    Plotly.newPlot('team-chart', [trace], layout, CHART_CONFIG);
}

function buildMatchesTable(matches) {
    const table = el('table', { class: 'matches-table' });
    const thead = el('thead');
    const headerRow = el('tr');
    for (const h of ['Date', 'Opponent', 'Score', 'Tournament', 'Change', 'Rating']) {
        headerRow.appendChild(el('th', { text: h }));
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = el('tbody');
    for (const m of matches) {
        const result = m.ts > m.os ? 'W' : m.ts < m.os ? 'L' : 'D';
        const tr = el('tr');
        tr.appendChild(el('td', { text: m.date }));
        tr.appendChild(el('td', { text: m.opponent }));
        tr.appendChild(el('td', { text: `${result} ${m.ts}-${m.os}` }));
        tr.appendChild(el('td', { text: m.tournament }));
        tr.appendChild(el('td', {
            class: changeClass(m.rc),
            text: formatChange(m.rc),
        }));
        tr.appendChild(el('td', { text: formatRating(m.ra) }));
        tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    return table;
}
