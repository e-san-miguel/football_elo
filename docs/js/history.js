/**
 * Historical Rankings view — see rankings at any point in time.
 */

import { getHistoricalRankings, getTournaments, getTeamFlags, getRankings } from './data.js';
import { el, formatRating, flagImg } from './utils.js';

let snapshots = [];
let snapshotIndex = {};  // date string -> index
let flags = {};
let currentRankings = null;
let showCompare = false;

export async function render(container) {
    container.innerHTML = '<div class="loading">Loading historical data...</div>';

    const [snapshotsData, tournaments, flagsData, rankingsData] = await Promise.all([
        getHistoricalRankings(),
        getTournaments(),
        getTeamFlags(),
        getRankings(),
    ]);

    snapshots = snapshotsData;
    flags = flagsData;
    currentRankings = rankingsData;

    // Build index for quick lookup
    snapshotIndex = {};
    snapshots.forEach((s, i) => { snapshotIndex[s.date] = i; });

    container.innerHTML = '';

    // Title
    container.appendChild(el('h1', {
        style: 'font-family:var(--font-display);font-weight:800;font-size:2.2rem;text-transform:uppercase;margin-bottom:24px',
        text: 'Historical Rankings',
    }));

    // Date controls card
    const controlsCard = el('div', { class: 'card' });

    // Date slider + label
    const dateRow = el('div', { style: 'display:flex;align-items:center;gap:16px;margin-bottom:16px;flex-wrap:wrap' });
    const dateLabel = el('span', {
        id: 'history-date-label',
        style: 'font-family:var(--font-display);font-weight:700;font-size:1.5rem;min-width:140px',
        text: snapshots[snapshots.length - 1].date,
    });
    dateRow.appendChild(dateLabel);

    const slider = el('input', {
        type: 'range',
        min: '0',
        max: (snapshots.length - 1).toString(),
        value: (snapshots.length - 1).toString(),
        class: 'history-slider',
        id: 'history-slider',
        oninput: (e) => onSliderChange(parseInt(e.target.value)),
    });
    dateRow.appendChild(slider);
    controlsCard.appendChild(dateRow);

    // Quick-jump buttons
    const jumpRow = el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px' });
    for (const t of tournaments) {
        // Find closest snapshot to tournament date
        const idx = findClosestSnapshot(t.date);
        if (idx === null) continue;
        const btn = el('button', {
            class: 'toggle-btn',
            text: t.name,
            onclick: () => {
                document.getElementById('history-slider').value = idx;
                onSliderChange(idx);
            },
        });
        jumpRow.appendChild(btn);
    }
    controlsCard.appendChild(jumpRow);

    // Compare to current toggle
    const compareRow = el('div', { style: 'display:flex;align-items:center;gap:8px' });
    const checkbox = el('input', {
        type: 'checkbox',
        id: 'compare-toggle',
        onchange: (e) => { showCompare = e.target.checked; renderTable(parseInt(document.getElementById('history-slider').value)); },
    });
    compareRow.appendChild(checkbox);
    compareRow.appendChild(el('label', { for: 'compare-toggle', text: 'Compare to current rankings', style: 'font-size:0.9rem;color:var(--text-secondary);cursor:pointer' }));
    controlsCard.appendChild(compareRow);

    container.appendChild(controlsCard);

    // Table container
    container.appendChild(el('div', { class: 'rankings-table-wrap', id: 'history-table-wrap' }));

    // Render initial (latest snapshot)
    renderTable(snapshots.length - 1);
}

function findClosestSnapshot(dateStr) {
    // Find first snapshot AFTER the given date (to show results after a tournament)
    for (let i = 0; i < snapshots.length; i++) {
        if (snapshots[i].date > dateStr) {
            return i;
        }
    }
    return snapshots.length - 1;
}

function onSliderChange(idx) {
    const label = document.getElementById('history-date-label');
    if (label) label.textContent = snapshots[idx].date;
    renderTable(idx);
}

function renderTable(idx) {
    const wrap = document.getElementById('history-table-wrap');
    if (!wrap) return;

    const snapshot = snapshots[idx];
    const teams = snapshot.teams;

    // Build current rank lookup for comparison
    const currentRankMap = {};
    if (currentRankings) {
        for (const t of currentRankings.teams) {
            currentRankMap[t.slug] = t;
        }
    }

    const table = el('table', { class: 'rankings-table' });

    // Header
    const thead = el('thead');
    const headerRow = el('tr');
    const headers = ['#', 'Team', 'Rating'];
    if (showCompare) headers.push('Current Rank', 'Current Rating', 'Rating Diff');
    for (const h of headers) {
        headerRow.appendChild(el('th', { text: h, class: h !== 'Team' ? 'text-right' : '' }));
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body
    const tbody = el('tbody');
    for (const t of teams) {
        const tr = el('tr', {
            style: 'cursor:pointer',
            onclick: () => { window.location.hash = `#/team/${t.s}`; },
        });

        const rankClass = t.rk <= 3 ? 'rank-cell top3' : 'rank-cell';
        tr.appendChild(el('td', { class: rankClass, text: t.rk.toString() }));

        // Team cell with flag
        const teamTd = el('td', { class: 'team-cell' });
        const flag = flagImg(flags[t.s], t.t, 'sm');
        if (flag) { teamTd.appendChild(flag); teamTd.appendChild(document.createTextNode(' ')); }
        teamTd.appendChild(document.createTextNode(t.t));
        tr.appendChild(teamTd);

        tr.appendChild(el('td', { class: 'rating-cell text-right', text: formatRating(t.r) }));

        if (showCompare) {
            const cur = currentRankMap[t.s];
            if (cur) {
                tr.appendChild(el('td', { class: 'text-right', text: `#${cur.rank}` }));
                tr.appendChild(el('td', { class: 'text-right', text: formatRating(cur.rating) }));
                const diff = cur.rating - t.r;
                const diffClass = diff > 0 ? 'change-positive' : diff < 0 ? 'change-negative' : 'change-neutral';
                tr.appendChild(el('td', {
                    class: `text-right ${diffClass}`,
                    text: (diff >= 0 ? '+' : '') + Math.round(diff).toString(),
                }));
            } else {
                tr.appendChild(el('td', { class: 'text-right text-tertiary', text: '—' }));
                tr.appendChild(el('td', { class: 'text-right text-tertiary', text: '—' }));
                tr.appendChild(el('td', { class: 'text-right text-tertiary', text: '—' }));
            }
        }

        tbody.appendChild(tr);
    }
    table.appendChild(tbody);

    wrap.innerHTML = '';
    wrap.appendChild(table);
}
