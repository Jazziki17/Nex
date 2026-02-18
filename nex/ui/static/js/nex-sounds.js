/**
 * NEX SOUNDS — Procedural sci-fi audio via Web Audio API.
 * No external files needed — all tones are synthesized.
 */

(() => {
    let ctx = null;
    let enabled = true;

    function getCtx() {
        if (!ctx) {
            ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return ctx;
    }

    // Resume AudioContext on first user interaction
    function resumeOnInteraction() {
        const resume = () => {
            if (ctx && ctx.state === 'suspended') ctx.resume();
            document.removeEventListener('click', resume);
            document.removeEventListener('keydown', resume);
        };
        document.addEventListener('click', resume);
        document.addEventListener('keydown', resume);
    }

    // ─── Synth Primitives ────────────────────────────────

    function playTone(freq, duration, volume = 0.15, type = 'sine', fadeOut = 0.1) {
        if (!enabled) return;
        const ac = getCtx();
        const osc = ac.createOscillator();
        const gain = ac.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, ac.currentTime);
        gain.gain.setValueAtTime(volume, ac.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);

        osc.connect(gain);
        gain.connect(ac.destination);
        osc.start(ac.currentTime);
        osc.stop(ac.currentTime + duration);
    }

    function playNoise(duration, volume = 0.05) {
        if (!enabled) return;
        const ac = getCtx();
        const bufferSize = ac.sampleRate * duration;
        const buffer = ac.createBuffer(1, bufferSize, ac.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1) * 0.5;
        }

        const source = ac.createBufferSource();
        const gain = ac.createGain();
        const filter = ac.createBiquadFilter();

        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(2000, ac.currentTime);
        filter.Q.setValueAtTime(0.5, ac.currentTime);

        source.buffer = buffer;
        gain.gain.setValueAtTime(volume, ac.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);

        source.connect(filter);
        filter.connect(gain);
        gain.connect(ac.destination);
        source.start(ac.currentTime);
    }

    // ─── Sound Presets ───────────────────────────────────

    const sounds = {
        // Boot sequence beep — short digital chirp
        bootBeep() {
            playTone(880, 0.08, 0.1, 'square');
            setTimeout(() => playTone(1100, 0.06, 0.06, 'sine'), 50);
        },

        // Orb appear — ascending whoosh + chime
        orbAppear() {
            const ac = getCtx();
            const osc = ac.createOscillator();
            const gain = ac.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(200, ac.currentTime);
            osc.frequency.exponentialRampToValueAtTime(800, ac.currentTime + 0.6);
            gain.gain.setValueAtTime(0.15, ac.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.8);

            osc.connect(gain);
            gain.connect(ac.destination);
            osc.start(ac.currentTime);
            osc.stop(ac.currentTime + 0.8);

            // Chime
            setTimeout(() => {
                playTone(1200, 0.4, 0.08, 'sine');
                playTone(1500, 0.3, 0.05, 'sine');
            }, 400);
        },

        // Message send — upward blip
        messageSend() {
            playTone(600, 0.08, 0.08, 'sine');
            setTimeout(() => playTone(900, 0.06, 0.06, 'sine'), 40);
        },

        // Message receive — gentle descending chime
        messageReceive() {
            playTone(900, 0.12, 0.08, 'sine');
            setTimeout(() => playTone(700, 0.15, 0.06, 'sine'), 60);
        },

        // Button hover — subtle tick
        buttonHover() {
            playTone(2400, 0.03, 0.04, 'sine');
        },

        // Button click — mechanical click
        buttonClick() {
            playNoise(0.04, 0.08);
            playTone(1800, 0.04, 0.06, 'square');
        },

        // Workspace slide — whoosh
        workspaceSlide() {
            const ac = getCtx();
            if (!enabled) return;
            const osc = ac.createOscillator();
            const gain = ac.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(400, ac.currentTime);
            osc.frequency.exponentialRampToValueAtTime(100, ac.currentTime + 0.3);
            gain.gain.setValueAtTime(0.04, ac.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.3);

            osc.connect(gain);
            gain.connect(ac.destination);
            osc.start(ac.currentTime);
            osc.stop(ac.currentTime + 0.3);

            playNoise(0.2, 0.03);
        },

        // Error — warning tone
        error() {
            playTone(300, 0.15, 0.1, 'sawtooth');
            setTimeout(() => playTone(200, 0.2, 0.08, 'sawtooth'), 150);
        },

        // Tool executing — digital processing
        toolStart() {
            playTone(500, 0.06, 0.06, 'square');
            setTimeout(() => playTone(700, 0.06, 0.05, 'square'), 60);
            setTimeout(() => playTone(600, 0.08, 0.04, 'square'), 120);
        },

        // Tool complete — success ding
        toolDone() {
            playTone(800, 0.1, 0.08, 'sine');
            setTimeout(() => playTone(1200, 0.15, 0.06, 'sine'), 80);
        },

        // Glitch — digital artifact
        glitch() {
            playNoise(0.08, 0.06);
            playTone(150, 0.05, 0.04, 'sawtooth');
        },
    };

    // ─── Public API ──────────────────────────────────────

    window.NexSounds = {
        play(name) {
            if (sounds[name]) {
                try { sounds[name](); } catch (e) { /* ignore audio errors */ }
            }
        },
        toggle() {
            enabled = !enabled;
            return enabled;
        },
        get enabled() { return enabled; },
        set enabled(v) { enabled = v; },
    };

    resumeOnInteraction();

    // Hook into sidebar button hovers
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.sidebar-btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => window.NexSounds.play('buttonHover'));
            btn.addEventListener('click', () => window.NexSounds.play('buttonClick'));
        });
    });
})();
