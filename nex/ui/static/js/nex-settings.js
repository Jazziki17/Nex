/**
 * NEX Settings — Memory controls, user preferences.
 */

(() => {
    const API = `${location.protocol}//${location.hostname || 'localhost'}:${location.port || 8420}/api/settings`;
    const memoryView = document.getElementById('memory-view');
    const memoryClear = document.getElementById('memory-clear');
    const memoryOutput = document.getElementById('memory-output');
    const userNameInput = document.getElementById('user-name-input');
    const userNameSave = document.getElementById('user-name-save');

    // ─── Load current settings ──────────────────────────

    async function loadSettings() {
        try {
            const resp = await fetch(API + '/current');
            const data = await resp.json();
            if (data.user_name) userNameInput.value = data.user_name;
        } catch {}
    }

    // ─── Memory controls ────────────────────────────────

    memoryView.addEventListener('click', () => {
        const ws = window._nexWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'command', command: 'Recall all your memories' }));
            memoryOutput.textContent = 'Loading...';
            // Listen for the response
            const handler = (e) => {
                if (e.detail && e.detail.text) {
                    memoryOutput.textContent = e.detail.text;
                    window.removeEventListener('nex:command.response', handler);
                }
            };
            window.addEventListener('nex:command.response', handler);
            setTimeout(() => window.removeEventListener('nex:command.response', handler), 10000);
        }
    });

    memoryClear.addEventListener('click', () => {
        if (!confirm('Clear all memories? This cannot be undone.')) return;
        const ws = window._nexWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'command', command: 'Clear all your memories and confirm' }));
            memoryOutput.textContent = 'Cleared.';
        }
    });

    // ─── User name ──────────────────────────────────────

    userNameSave.addEventListener('click', () => {
        const name = userNameInput.value.trim();
        if (!name) return;
        const ws = window._nexWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'command', command: `My name is ${name}. Remember it.` }));
        }
    });

    // ─── Init on settings view open ─────────────────────

    const observer = new MutationObserver(() => {
        const settingsView = document.getElementById('settings-view');
        if (settingsView && settingsView.classList.contains('active')) {
            loadSettings();
        }
    });

    const settingsView = document.getElementById('settings-view');
    if (settingsView) {
        observer.observe(settingsView, { attributes: true, attributeFilter: ['class'] });
    }

    // Initial load
    loadSettings();
})();
