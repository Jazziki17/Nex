/**
 * KAI Settings — Voice selection, memory controls, user preferences.
 */

(() => {
    const API = `${location.protocol}//${location.hostname || 'localhost'}:${location.port || 8420}/api/settings`;
    const voiceSelect = document.getElementById('voice-select');
    const voiceTest = document.getElementById('voice-test');
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
            // Load voices then select current
            await loadVoices(data.voice || 'Samantha');
        } catch {}
    }

    // ─── Voice list ─────────────────────────────────────

    async function loadVoices(currentVoice) {
        try {
            const resp = await fetch(API + '/voices');
            const data = await resp.json();
            voiceSelect.innerHTML = '';
            for (const v of data.voices) {
                const opt = document.createElement('option');
                opt.value = v.name;
                opt.textContent = v.name + ' (' + v.language + ')';
                if (v.name === currentVoice) opt.selected = true;
                voiceSelect.appendChild(opt);
            }
        } catch {
            voiceSelect.innerHTML = '<option value="">Failed to load</option>';
        }
    }

    // ─── Voice change ───────────────────────────────────

    voiceSelect.addEventListener('change', async () => {
        const voice = voiceSelect.value;
        if (!voice) return;
        try {
            await fetch(API + '/voice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ voice }),
            });
        } catch {}
    });

    // ─── Voice test ─────────────────────────────────────

    voiceTest.addEventListener('click', () => {
        const ws = window._kaiWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'command',
                command: 'Say hello and introduce yourself briefly',
            }));
        }
    });

    // ─── Memory controls ────────────────────────────────

    memoryView.addEventListener('click', () => {
        const ws = window._kaiWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'command', command: 'Recall all your memories' }));
            memoryOutput.textContent = 'Loading...';
            // Listen for the response
            const handler = (e) => {
                if (e.detail && e.detail.text) {
                    memoryOutput.textContent = e.detail.text;
                    window.removeEventListener('kai:command.response', handler);
                }
            };
            window.addEventListener('kai:command.response', handler);
            setTimeout(() => window.removeEventListener('kai:command.response', handler), 10000);
        }
    });

    memoryClear.addEventListener('click', () => {
        if (!confirm('Clear all memories? This cannot be undone.')) return;
        const ws = window._kaiWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'command', command: 'Clear all your memories and confirm' }));
            memoryOutput.textContent = 'Cleared.';
        }
    });

    // ─── User name ──────────────────────────────────────

    userNameSave.addEventListener('click', () => {
        const name = userNameInput.value.trim();
        if (!name) return;
        const ws = window._kaiWs;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'command', command: `My name is ${name}. Remember it.` }));
        }
    });

    // ─── Sync from events ───────────────────────────────

    window.addEventListener('kai:settings.voice_change', (e) => {
        if (e.detail && e.detail.voice) {
            voiceSelect.value = e.detail.voice;
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
