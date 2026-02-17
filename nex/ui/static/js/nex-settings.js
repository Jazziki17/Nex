/**
 * NEX Settings — Memory controls, user preferences, voice authentication.
 */

(() => {
    const API = `${location.protocol}//${location.hostname || 'localhost'}:${location.port || 8420}/api/settings`;
    const memoryView = document.getElementById('memory-view');
    const memoryClear = document.getElementById('memory-clear');
    const memoryOutput = document.getElementById('memory-output');
    const userNameInput = document.getElementById('user-name-input');
    const userNameSave = document.getElementById('user-name-save');
    const voiceEnroll = document.getElementById('voice-enroll');
    const voiceReset = document.getElementById('voice-reset');
    const voiceAuthStatus = document.getElementById('voice-auth-status');

    // ─── Load current settings ──────────────────────────

    async function loadSettings() {
        try {
            const resp = await fetch(API + '/current');
            const data = await resp.json();
            if (data.user_name) userNameInput.value = data.user_name;
        } catch {}
        loadVoiceAuthStatus();
    }

    // ─── Voice auth status ───────────────────────────────

    async function loadVoiceAuthStatus() {
        try {
            const resp = await fetch(`${location.protocol}//${location.hostname || 'localhost'}:${location.port || 8420}/api/settings/voice-auth-status`);
            const data = await resp.json();
            if (voiceAuthStatus) {
                voiceAuthStatus.textContent = data.enrolled ? 'Enrolled' : 'Not enrolled';
                voiceAuthStatus.style.color = data.enrolled ? '#4ade80' : '#94a3b8';
            }
        } catch {
            if (voiceAuthStatus) voiceAuthStatus.textContent = 'Unavailable';
        }
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

    // ─── Voice auth controls ─────────────────────────────

    if (voiceEnroll) {
        voiceEnroll.addEventListener('click', () => {
            const ws = window._nexWs;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'command', command: 'Set up voice authentication' }));
                if (voiceAuthStatus) voiceAuthStatus.textContent = 'Enrolling...';
            }
        });
    }

    if (voiceReset) {
        voiceReset.addEventListener('click', () => {
            if (!confirm('Reset voice authentication? You will need to re-enroll.')) return;
            const ws = window._nexWs;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'command', command: 'Reset voice authentication' }));
                if (voiceAuthStatus) {
                    voiceAuthStatus.textContent = 'Not enrolled';
                    voiceAuthStatus.style.color = '#94a3b8';
                }
            }
        });
    }

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

    window.addEventListener('nex:viewchange', (e) => {
        if (e.detail.view === 'settings') {
            loadSettings();
        }
    });

    // Initial load
    loadSettings();
})();
