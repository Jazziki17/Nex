/**
 * NEX Services — Module list with status badges.
 * Fetches from /api/modules when the services view opens.
 */

(() => {
    const listEl = document.getElementById('services-list');

    function escHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    async function loadModules() {
        try {
            const resp = await fetch(`${location.protocol}//${location.hostname || 'localhost'}:${location.port || 8420}/api/modules`);
            const data = await resp.json();
            renderModules(data.modules || []);
        } catch {
            listEl.innerHTML = '<div class="services-loading">Failed to load modules.</div>';
        }
    }

    function renderModules(modules) {
        if (!modules.length) {
            listEl.innerHTML = '<div class="services-loading">No modules loaded.</div>';
            return;
        }
        listEl.innerHTML = '';
        for (const m of modules) {
            const item = document.createElement('div');
            item.className = 'service-item';
            item.dataset.name = m.name;
            item.innerHTML = `
                <div>
                    <div class="service-name">${escHtml(m.name)}</div>
                    <div class="service-type">${escHtml(m.type)}</div>
                </div>
                <span class="service-badge ${m.status}">${m.status}</span>
            `;
            listEl.appendChild(item);
        }
    }

    // Reload when services view becomes visible
    window.addEventListener('nex:viewchange', (e) => {
        if (e.detail.view === 'services') {
            loadModules();
        }
    });

    // Update status on module error events
    window.addEventListener('nex:system.module_error', (e) => {
        const name = e.detail.module;
        if (!name) return;
        const item = listEl.querySelector(`[data-name="${name}"]`);
        if (item) {
            const badge = item.querySelector('.service-badge');
            if (badge) {
                badge.className = 'service-badge error';
                badge.textContent = 'error';
            }
        }
    });
})();
