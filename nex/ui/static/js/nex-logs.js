/**
 * NEX Logs — Audit log viewer with filtering and auto-scroll.
 * Fetches from /api/logs and appends live WebSocket events.
 */

(() => {
    const logsBody = document.getElementById('logs-body');
    const logsScroll = document.getElementById('logs-scroll');
    const filterSelect = document.getElementById('log-filter');
    let allEntries = [];
    let userScrolledUp = false;
    let pollTimer = null;

    function escHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function badgeClass(eventType) {
        if (eventType.startsWith('system.command')) return 'cmd';
        if (eventType.startsWith('tool.')) return 'tool';
        if (eventType.includes('error')) return 'err';
        return '';
    }

    function summarize(data) {
        if (!data) return '';
        if (data.command) return data.command;
        if (data.text) return data.text.substring(0, 120);
        if (data.name) return data.name;
        if (data.raw) return data.raw.substring(0, 120);
        return JSON.stringify(data).substring(0, 120);
    }

    function shortTime(timestamp) {
        if (!timestamp) return '';
        // Extract just the time portion (HH:MM:SS)
        const match = timestamp.match(/(\d{2}:\d{2}:\d{2})/);
        return match ? match[1] : timestamp.substring(0, 19);
    }

    function renderEntries() {
        const filter = filterSelect ? filterSelect.value : 'all';
        const filtered = filter === 'all'
            ? allEntries
            : allEntries.filter(e => e.event_type === filter || e.event_type.startsWith(filter));

        logsBody.innerHTML = '';
        for (const entry of filtered) {
            const div = document.createElement('div');
            div.className = 'log-entry';
            const cls = badgeClass(entry.event_type);
            div.innerHTML = `<span class="log-time">${escHtml(shortTime(entry.timestamp))}</span><span class="log-type ${cls}">${escHtml(entry.event_type)}</span><span class="log-detail">${escHtml(summarize(entry.data))}</span>`;
            logsBody.appendChild(div);
        }

        if (!userScrolledUp && logsScroll) {
            logsScroll.scrollTop = logsScroll.scrollHeight;
        }
    }

    async function fetchLogs() {
        try {
            const resp = await fetch(`${location.protocol}//${location.hostname || 'localhost'}:${location.port || 8420}/api/logs?limit=200`);
            const data = await resp.json();
            allEntries = data.entries || [];
            renderEntries();
        } catch {}
    }

    // Detect user scroll-up to pause auto-scroll
    if (logsScroll) {
        logsScroll.addEventListener('scroll', () => {
            const atBottom = logsScroll.scrollHeight - logsScroll.scrollTop - logsScroll.clientHeight < 40;
            userScrolledUp = !atBottom;
        });
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', renderEntries);
    }

    // Load and start polling when logs view is active
    window.addEventListener('nex:viewchange', (e) => {
        if (e.detail.view === 'logs') {
            fetchLogs();
            if (!pollTimer) {
                pollTimer = setInterval(fetchLogs, 5000);
            }
        } else {
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
        }
    });

    // Append live events from WebSocket
    const liveTypes = ['system.command', 'command.response', 'tool.executing', 'tool.completed', 'system.ready', 'system.module_error'];
    for (const type of liveTypes) {
        window.addEventListener('nex:' + type, (e) => {
            allEntries.push({
                timestamp: new Date().toLocaleString(),
                event_type: type,
                data: e.detail || {},
            });
            // Only re-render if logs view is visible
            const logsView = document.getElementById('logs-view');
            if (logsView && logsView.classList.contains('active')) {
                renderEntries();
            }
        });
    }
})();
