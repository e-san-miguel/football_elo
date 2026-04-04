/**
 * SPA router and initialization.
 */

import { render as renderRankings } from './rankings.js';
import { render as renderTeam } from './team.js';
import { render as renderCompare } from './compare.js';
import { render as renderMethodology } from './methodology.js';

const app = document.getElementById('app');

const routes = [
    { pattern: /^#\/team\/(.+)$/, handler: (m) => renderTeam(app, m[1]) },
    { pattern: /^#\/compare\/(.+)\/(.+)$/, handler: (m) => renderCompare(app, m[1], m[2]) },
    { pattern: /^#\/compare\/(.+)$/, handler: (m) => renderCompare(app, m[1]) },
    { pattern: /^#\/compare$/, handler: () => renderCompare(app) },
    { pattern: /^#\/methodology$/, handler: () => renderMethodology(app) },
    { pattern: /^#\/$/, handler: () => renderRankings(app) },
];

function updateActiveNav() {
    const hash = window.location.hash || '#/';
    document.querySelectorAll('.nav-link').forEach(link => {
        const route = link.dataset.route;
        let isActive = false;
        if (route === 'rankings') isActive = hash === '#/' || hash === '';
        else if (route === 'compare') isActive = hash.startsWith('#/compare');
        else if (route === 'history') isActive = hash.startsWith('#/history');
        else if (route === 'methodology') isActive = hash === '#/methodology';
        link.classList.toggle('active', isActive);
    });
}

async function navigate() {
    const hash = window.location.hash || '#/';
    updateActiveNav();

    for (const route of routes) {
        const match = hash.match(route.pattern);
        if (match) {
            try {
                await route.handler(match);
            } catch (err) {
                console.error('Route error:', err);
                app.innerHTML = `<div class="loading">Error loading page. Check console for details.</div>`;
            }
            return;
        }
    }

    // Default: rankings
    try {
        await renderRankings(app);
    } catch (err) {
        console.error('Route error:', err);
        app.innerHTML = `<div class="loading">Error loading page.</div>`;
    }
}

window.addEventListener('hashchange', navigate);
window.addEventListener('DOMContentLoaded', navigate);

// Initial load
navigate();
