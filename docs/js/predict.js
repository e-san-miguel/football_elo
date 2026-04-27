/**
 * Match Predictor — pick any two teams and a venue, get W/D/L odds + expected score.
 * Uses the same Poisson score model as the World Cup simulations, computed analytically.
 */

import { getRankings, getTeamFlags } from './data.js';
import { el, flagImg, formatRating } from './utils.js';

const GOAL_BASELINE = 1.2414;
const GOAL_ELO_SCALING = 0.002174;
const GOAL_ELO_SCALING_SQ = -5.246e-7;
const HOME_ADV = 50;
const MAX_GOALS = 10;

let allTeams = [];
let flagsData = {};
let teamA = null;
let teamB = null;
let venue = 'neutral'; // 'home_a' | 'neutral' | 'home_b'

function poissonPmf(k, lam) {
    let logp = -lam + k * Math.log(lam);
    for (let i = 2; i <= k; i++) logp -= Math.log(i);
    return Math.exp(logp);
}

function computePrediction(ratingA, ratingB, v) {
    let ha = 0;
    if (v === 'home_a') ha = HOME_ADV;
    else if (v === 'home_b') ha = -HOME_ADV;
    const dr = (ratingA - ratingB) + ha;
    const quad = GOAL_ELO_SCALING_SQ * dr * dr;
    const lamA = GOAL_BASELINE * Math.exp(GOAL_ELO_SCALING * dr + quad);
    const lamB = GOAL_BASELINE * Math.exp(-GOAL_ELO_SCALING * dr + quad);

    const pA = [], pB = [];
    for (let k = 0; k <= MAX_GOALS; k++) {
        pA.push(poissonPmf(k, lamA));
        pB.push(poissonPmf(k, lamB));
    }

    let pWin = 0, pDraw = 0, pLoss = 0;
    const scorelines = [];
    for (let i = 0; i <= MAX_GOALS; i++) {
        for (let j = 0; j <= MAX_GOALS; j++) {
            const p = pA[i] * pB[j];
            if (i > j) pWin += p;
            else if (i < j) pLoss += p;
            else pDraw += p;
            scorelines.push({ a: i, b: j, p });
        }
    }
    const total = pWin + pDraw + pLoss;
    pWin /= total; pDraw /= total; pLoss /= total;
    scorelines.sort((x, y) => y.p - x.p);

    return {
        pWin, pDraw, pLoss,
        expectedGoalsA: lamA,
        expectedGoalsB: lamB,
        topScorelines: scorelines.slice(0, 6),
    };
}

export async function render(container) {
    container.innerHTML = '<div class="loading">Loading...</div>';

    teamA = null;
    teamB = null;
    venue = 'neutral';

    const [rankings, flags] = await Promise.all([
        getRankings(),
        getTeamFlags(),
    ]);
    allTeams = rankings.teams;
    flagsData = flags;

    container.innerHTML = '';

    container.appendChild(el('div', { class: 'hero' }, [
        el('h1', { text: 'Match Predictor' }),
        el('p', {
            class: 'hero-subtitle',
            text: 'Pick two teams and a venue \u2014 get win/draw/loss odds and expected score.',
        }),
    ]));

    const card = el('div', { class: 'card' });
    const pickerRow = el('div', { class: 'predict-picker-row' });
    pickerRow.appendChild(buildTeamPicker('a'));
    pickerRow.appendChild(el('div', { class: 'predict-vs', text: 'vs' }));
    pickerRow.appendChild(buildTeamPicker('b'));
    card.appendChild(pickerRow);

    const venueWrap = el('div', { style: 'margin-top:24px;text-align:center' });
    venueWrap.appendChild(el('div', {
        style: 'font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-tertiary);margin-bottom:8px',
        text: 'Venue',
    }));
    const venueRow = el('div', {
        id: 'predict-venue-selector',
        style: 'display:inline-flex;gap:8px;flex-wrap:wrap;justify-content:center',
    });
    for (const [v, label] of [['home_a', 'Team A home'], ['neutral', 'Neutral'], ['home_b', 'Team B home']]) {
        venueRow.appendChild(el('button', {
            class: `toggle-btn${v === venue ? ' active' : ''}`,
            'data-venue': v,
            text: label,
            onclick: () => setVenue(v),
        }));
    }
    venueWrap.appendChild(venueRow);
    card.appendChild(venueWrap);
    container.appendChild(card);

    container.appendChild(el('div', { id: 'predict-results' }));
    updateResults();
}

function buildTeamPicker(slot) {
    const wrap = el('div', { class: 'predict-picker' });
    wrap.appendChild(el('div', {
        class: 'predict-picker-label',
        text: slot === 'a' ? 'Team A' : 'Team B',
    }));

    const searchWrap = el('div', { style: 'position:relative' });
    const input = el('input', {
        class: 'search-input',
        type: 'text',
        placeholder: 'Search teams\u2026',
        id: `predict-search-${slot}`,
    });
    const dropdown = el('div', {
        class: 'predict-dropdown',
        id: `predict-dropdown-${slot}`,
    });
    searchWrap.appendChild(input);
    searchWrap.appendChild(dropdown);
    wrap.appendChild(searchWrap);

    wrap.appendChild(el('div', { id: `predict-chip-${slot}`, style: 'margin-top:10px' }));

    input.addEventListener('input', () => renderDropdown(slot));
    input.addEventListener('focus', () => renderDropdown(slot));
    input.addEventListener('blur', () => {
        setTimeout(() => { dropdown.style.display = 'none'; }, 150);
    });

    return wrap;
}

function renderDropdown(slot) {
    const input = document.getElementById(`predict-search-${slot}`);
    const dropdown = document.getElementById(`predict-dropdown-${slot}`);
    if (!input || !dropdown) return;
    const q = input.value.toLowerCase().trim();
    const otherSlug = slot === 'a' ? teamB?.slug : teamA?.slug;
    const matches = allTeams
        .filter(t => t.slug !== otherSlug && (q === '' || t.team.toLowerCase().includes(q)))
        .slice(0, 10);
    dropdown.innerHTML = '';
    if (matches.length === 0) { dropdown.style.display = 'none'; return; }
    for (const t of matches) {
        const item = el('div', {
            class: 'predict-dropdown-item',
            onmouseenter: (e) => { e.currentTarget.style.background = 'var(--bg-tertiary)'; },
            onmouseleave: (e) => { e.currentTarget.style.background = 'transparent'; },
            onmousedown: (e) => {
                e.preventDefault();
                selectTeam(slot, t);
            },
        });
        const f = flagImg(flagsData[t.slug], t.team, 'sm');
        if (f) item.appendChild(f);
        item.appendChild(document.createTextNode(`${t.team} (#${t.rank} \u2014 ${formatRating(t.rating)})`));
        dropdown.appendChild(item);
    }
    dropdown.style.display = 'block';
}

function selectTeam(slot, t) {
    if (slot === 'a') teamA = t; else teamB = t;
    const input = document.getElementById(`predict-search-${slot}`);
    const dropdown = document.getElementById(`predict-dropdown-${slot}`);
    if (input) input.value = '';
    if (dropdown) dropdown.style.display = 'none';
    renderChip(slot);
    updateResults();
}

function clearTeam(slot) {
    if (slot === 'a') teamA = null; else teamB = null;
    renderChip(slot);
    updateResults();
}

function renderChip(slot) {
    const chip = document.getElementById(`predict-chip-${slot}`);
    if (!chip) return;
    chip.innerHTML = '';
    const t = slot === 'a' ? teamA : teamB;
    if (!t) return;
    const badge = el('div', { class: 'predict-chip' });
    const f = flagImg(flagsData[t.slug], t.team, 'sm');
    if (f) badge.appendChild(f);
    badge.appendChild(el('span', { style: 'font-weight:600', text: t.team }));
    badge.appendChild(el('span', {
        class: 'predict-chip-meta',
        text: `#${t.rank} \u00b7 ${formatRating(t.rating)}`,
    }));
    badge.appendChild(el('button', {
        class: 'predict-chip-close',
        text: '\u00d7',
        title: 'Remove',
        onclick: () => clearTeam(slot),
    }));
    chip.appendChild(badge);
}

function setVenue(v) {
    venue = v;
    document.querySelectorAll('#predict-venue-selector button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.venue === v);
    });
    updateResults();
}

function updateResults() {
    const container = document.getElementById('predict-results');
    if (!container) return;
    container.innerHTML = '';
    if (!teamA || !teamB) {
        container.appendChild(el('div', {
            class: 'card',
            style: 'text-align:center;color:var(--text-tertiary);padding:40px',
            text: 'Pick two teams to see the prediction.',
        }));
        return;
    }

    const res = computePrediction(teamA.rating, teamB.rating, venue);
    const pct = (p) => Math.round(p * 1000) / 10;
    const pW = pct(res.pWin);
    const pD = pct(res.pDraw);
    const pL = pct(res.pLoss);

    const mainCard = el('div', { class: 'card' });
    mainCard.appendChild(el('h2', { text: 'Prediction' }));

    const nameRow = el('div', { class: 'predict-names' });
    nameRow.appendChild(el('span', { class: 'predict-name-home', text: teamAHomeLabel() }));
    nameRow.appendChild(el('span', { class: 'predict-name-draw', text: 'Draw' }));
    nameRow.appendChild(el('span', { class: 'predict-name-away', text: teamBHomeLabel() }));
    mainCard.appendChild(nameRow);

    const bar = el('div', { class: 'wc-prob-bar', style: 'margin-bottom:12px' });
    bar.appendChild(el('div', { class: 'wc-prob-segment wc-prob-home', style: `width:${pW}%`, text: pW >= 6 ? `${pW}%` : '' }));
    bar.appendChild(el('div', { class: 'wc-prob-segment wc-prob-draw', style: `width:${pD}%`, text: pD >= 6 ? `${pD}%` : '' }));
    bar.appendChild(el('div', { class: 'wc-prob-segment wc-prob-away', style: `width:${pL}%`, text: pL >= 6 ? `${pL}%` : '' }));
    mainCard.appendChild(bar);

    const top = res.topScorelines[0];
    const stats = el('div', { class: 'predict-stats-grid' });
    stats.appendChild(statTile('Expected goals',
        `${res.expectedGoalsA.toFixed(2)} \u2014 ${res.expectedGoalsB.toFixed(2)}`));
    stats.appendChild(statTile('Most likely score',
        `${top.a} \u2013 ${top.b}`, `${pct(top.p)}% chance`));
    mainCard.appendChild(stats);

    container.appendChild(mainCard);

    const slCard = el('div', { class: 'card' });
    slCard.appendChild(el('h2', { text: 'Top Scorelines' }));
    const list = el('div', { class: 'predict-scorelines' });
    for (const sl of res.topScorelines) {
        list.appendChild(el('div', { class: 'predict-scoreline' }, [
            el('span', { class: 'predict-scoreline-score', text: `${sl.a} \u2013 ${sl.b}` }),
            el('span', { class: 'predict-scoreline-pct', text: `${pct(sl.p)}%` }),
        ]));
    }
    slCard.appendChild(list);
    container.appendChild(slCard);
}

function teamAHomeLabel() {
    return venue === 'home_a' ? `${teamA.team} (H)` : teamA.team;
}

function teamBHomeLabel() {
    return venue === 'home_b' ? `${teamB.team} (H)` : teamB.team;
}

function statTile(label, value, sub) {
    const tile = el('div', { class: 'predict-stat-tile' });
    tile.appendChild(el('div', { class: 'predict-stat-label', text: label }));
    tile.appendChild(el('div', { class: 'predict-stat-value', text: value }));
    if (sub) tile.appendChild(el('div', { class: 'predict-stat-sub', text: sub }));
    return tile;
}
