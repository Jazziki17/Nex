/**
 * ═══════════════════════════════════════════════════════════
 * NODE MATRIX — Living Neural Network Visualization
 * ═══════════════════════════════════════════════════════════
 *
 * A responsive node-graph system that visualizes Nex's neural
 * state in real time. Nodes represent modules, processes, and
 * data flows. Edges pulse with energy as data moves between them.
 *
 * REACTS TO:
 *   - Voice input  → nodes pulse with audio amplitude
 *   - Gestures     → node clusters shift and reorganize
 *   - Mouse        → nodes gravitate, edges glow
 *   - Commands     → new nodes spawn, data flows animate
 *
 * The matrix is alive — it breathes, pulses, and reorganizes
 * continuously, creating a "thinking" visualization.
 */

class NodeMatrix {
    constructor(containerId) {
        this.container = document.getElementById(containerId);

        // Create a dedicated canvas inside the container
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'matrix-canvas';
        this.canvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;border-radius:8px;';
        this.container.style.position = 'relative';
        this.container.prepend(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.nodes = [];
        this.edges = [];
        this.dataPackets = [];         // Animated data flowing along edges
        this.mouse = { x: 0, y: 0, active: false };
        this.time = 0;
        this.voiceAmplitude = 0;       // Reactive to voice
        this.gestureVector = { x: 0, y: 0 }; // Reactive to gesture
        this.pulseWaves = [];          // Expanding ripples from events

        // Node types with colors and behaviors
        this.nodeTypes = {
            core:    { color: { r: 0,   g: 240, b: 255 }, size: 18, label: 'NEX CORE' },
            voice:   { color: { r: 0,   g: 240, b: 255 }, size: 10, label: 'VOICE' },
            speech:  { color: { r: 255, g: 0,   b: 170 }, size: 10, label: 'SPEECH' },
            nlp:     { color: { r: 255, g: 80,  b: 200 }, size: 8,  label: 'NLP' },
            intent:  { color: { r: 255, g: 120, b: 220 }, size: 7,  label: 'INTENT' },
            vision:  { color: { r: 180, g: 74,  b: 255 }, size: 10, label: 'VISION' },
            motion:  { color: { r: 140, g: 60,  b: 255 }, size: 8,  label: 'MOTION' },
            gesture: { color: { r: 200, g: 100, b: 255 }, size: 8,  label: 'GESTURE' },
            io:      { color: { r: 0,   g: 255, b: 136 }, size: 10, label: 'FILE I/O' },
            memory:  { color: { r: 0,   g: 200, b: 110 }, size: 7,  label: 'MEMORY' },
            config:  { color: { r: 0,   g: 180, b: 100 }, size: 7,  label: 'CONFIG' },
            tts:     { color: { r: 255, g: 50,  b: 150 }, size: 8,  label: 'TTS' },
            camera:  { color: { r: 160, g: 50,  b: 255 }, size: 8,  label: 'CAMERA' },
            event:   { color: { r: 255, g: 231, b: 68  }, size: 9,  label: 'EVENT BUS' },
        };

        this._resize();
        this._initGraph();
        this._bindEvents();
        this._animate();
    }

    _resize() {
        const rect = this.container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.cx = this.canvas.width / 2;
        this.cy = this.canvas.height / 2;
    }

    _initGraph() {
        // Create the neural network graph structure
        // Core at center, modules around it, sub-modules further out
        const cx = this.canvas.width / 2;
        const cy = this.canvas.height / 2;

        const layout = [
            // [type, angle_offset, distance_from_center]
            { type: 'core',    angle: 0,   dist: 0 },
            { type: 'event',   angle: 0,   dist: 60 },

            // Voice cluster (top-left)
            { type: 'voice',   angle: -2.2, dist: 160 },

            // Speech cluster (top-right)
            { type: 'speech',  angle: -0.8, dist: 170 },
            { type: 'nlp',     angle: -0.5, dist: 230 },
            { type: 'intent',  angle: -1.0, dist: 240 },
            { type: 'tts',     angle: -0.2, dist: 220 },

            // Vision cluster (bottom-right)
            { type: 'vision',  angle: 0.8,  dist: 165 },
            { type: 'camera',  angle: 0.5,  dist: 225 },
            { type: 'motion',  angle: 1.1,  dist: 230 },
            { type: 'gesture', angle: 0.8,  dist: 260 },

            // IO cluster (bottom-left)
            { type: 'io',      angle: 2.2,  dist: 155 },
            { type: 'memory',  angle: 2.5,  dist: 215 },
            { type: 'config',  angle: 1.9,  dist: 210 },
        ];

        this.nodes = layout.map((n, i) => {
            const def = this.nodeTypes[n.type];
            return {
                id: i,
                type: n.type,
                label: def.label,
                x: cx + Math.cos(n.angle) * n.dist,
                y: cy + Math.sin(n.angle) * n.dist,
                targetX: cx + Math.cos(n.angle) * n.dist,
                targetY: cy + Math.sin(n.angle) * n.dist,
                homeX: cx + Math.cos(n.angle) * n.dist,
                homeY: cy + Math.sin(n.angle) * n.dist,
                vx: 0,
                vy: 0,
                size: def.size,
                color: def.color,
                energy: 0.5,      // Current activation level
                pulsePhase: Math.random() * Math.PI * 2,
                angle: n.angle,
                dist: n.dist,
            };
        });

        // Define edges (connections) between nodes
        // [fromIndex, toIndex, strength]
        const connections = [
            // Core connections
            [0, 1, 1.0],   // core → event bus

            // Event bus to all modules
            [1, 2, 0.8],   // event → voice
            [1, 3, 0.8],   // event → speech
            [1, 7, 0.8],   // event → vision
            [1, 11, 0.8],  // event → io

            // Voice cluster
            [2, 3, 0.6],   // voice → speech

            // Speech cluster
            [3, 4, 0.7],   // speech → nlp
            [4, 5, 0.7],   // nlp → intent
            [3, 6, 0.5],   // speech → tts
            [5, 0, 0.4],   // intent → core

            // Vision cluster
            [7, 8, 0.7],   // vision → camera
            [7, 9, 0.7],   // vision → motion
            [9, 10, 0.6],  // motion → gesture
            [10, 0, 0.4],  // gesture → core

            // IO cluster
            [11, 12, 0.7], // io → memory
            [11, 13, 0.6], // io → config
            [12, 0, 0.3],  // memory → core

            // Cross-cluster connections
            [5, 11, 0.3],  // intent → io (save results)
            [2, 6, 0.3],   // voice → tts (echo)
        ];

        this.edges = connections.map(([from, to, strength]) => ({
            from: this.nodes[from],
            to: this.nodes[to],
            strength,
            energy: 0,
            flowOffset: Math.random() * 100,
        }));
    }

    _bindEvents() {
        window.addEventListener('resize', () => this._resize());

        this.container.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
            this.mouse.active = true;
        });

        this.container.addEventListener('mouseleave', () => {
            this.mouse.active = false;
        });

        // Click on canvas triggers a pulse wave
        this.container.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            this.triggerPulse(x, y, { r: 0, g: 240, b: 255 });
            this._activateNearestNode(x, y);
        });
    }

    // ─── PUBLIC API: React to external events ──────────────

    /**
     * React to voice input.
     * @param {number} amplitude - Voice amplitude (0-1)
     */
    onVoiceInput(amplitude) {
        this.voiceAmplitude = Math.min(amplitude, 1);

        // Energize voice-related nodes
        this.nodes.forEach(n => {
            if (['voice', 'speech', 'nlp', 'tts'].includes(n.type)) {
                n.energy = Math.min(n.energy + amplitude * 0.5, 1.0);
            }
        });

        // Send data packets along voice→speech edges
        if (amplitude > 0.3) {
            this._sendPacket(2, 3);  // voice → speech
            this._sendPacket(3, 4);  // speech → nlp
        }

        // Pulse from voice node
        const voiceNode = this.nodes[2];
        if (amplitude > 0.5) {
            this.triggerPulse(voiceNode.x, voiceNode.y, voiceNode.color);
        }
    }

    /**
     * React to gesture detection.
     * @param {string} gesture - Gesture name
     * @param {number} dx - Horizontal direction (-1 to 1)
     * @param {number} dy - Vertical direction (-1 to 1)
     */
    onGesture(gesture, dx = 0, dy = 0) {
        this.gestureVector.x = dx * 30;
        this.gestureVector.y = dy * 30;

        // Energize vision-related nodes
        this.nodes.forEach(n => {
            if (['vision', 'camera', 'motion', 'gesture'].includes(n.type)) {
                n.energy = 1.0;
            }
        });

        // Pulse from gesture node
        const gestureNode = this.nodes[10];
        this.triggerPulse(gestureNode.x, gestureNode.y, gestureNode.color);

        // Send data packets
        this._sendPacket(10, 0);  // gesture → core
        this._sendPacket(9, 10);  // motion → gesture
    }

    /**
     * React to a new command being processed.
     * @param {string} command
     */
    onCommand(command) {
        // Light up the entire pipeline
        const sequence = [2, 3, 4, 5, 0, 1, 11]; // voice→speech→nlp→intent→core→event→io
        sequence.forEach((nodeIdx, i) => {
            setTimeout(() => {
                this.nodes[nodeIdx].energy = 1.0;
                if (i < sequence.length - 1) {
                    this._sendPacket(nodeIdx, sequence[i + 1]);
                }
            }, i * 200);
        });

        // Pulse from core
        setTimeout(() => {
            this.triggerPulse(this.cx, this.cy, { r: 255, g: 231, b: 68 });
        }, 400);
    }

    /**
     * Trigger a ripple/pulse wave at a position.
     */
    triggerPulse(x, y, color) {
        this.pulseWaves.push({
            x, y,
            radius: 0,
            maxRadius: 200,
            color,
            alpha: 0.6,
        });
    }

    // ─── PRIVATE ───────────────────────────────────────────

    _activateNearestNode(x, y) {
        let nearest = null;
        let minDist = Infinity;

        for (const node of this.nodes) {
            const dx = node.x - x;
            const dy = node.y - y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < minDist) {
                minDist = dist;
                nearest = node;
            }
        }

        if (nearest && minDist < 50) {
            nearest.energy = 1.0;

            // Send packets from this node to connected nodes
            this.edges.forEach(e => {
                if (e.from === nearest) this._sendPacket(nearest.id, e.to.id);
                if (e.to === nearest) this._sendPacket(e.from.id, nearest.id);
            });
        }
    }

    _sendPacket(fromId, toId) {
        const from = this.nodes[fromId];
        const to = this.nodes[toId];
        if (!from || !to) return;

        this.dataPackets.push({
            from, to,
            progress: 0,       // 0 to 1
            speed: 0.015 + Math.random() * 0.01,
            color: from.color,
            size: 3 + Math.random() * 2,
        });
    }

    // ─── ANIMATION LOOP ────────────────────────────────────

    _animate() {
        this.time += 0.016;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this._drawGridBackground();
        this._updateNodes();
        this._drawEdges();
        this._drawDataPackets();
        this._drawNodes();
        this._drawPulseWaves();
        this._drawHexOverlay();

        // Decay voice amplitude
        this.voiceAmplitude *= 0.95;
        this.gestureVector.x *= 0.95;
        this.gestureVector.y *= 0.95;

        requestAnimationFrame(() => this._animate());
    }

    _drawGridBackground() {
        const ctx = this.ctx;
        const gridSize = 40;
        const alpha = 0.03 + this.voiceAmplitude * 0.02;

        ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
        ctx.lineWidth = 0.5;

        // Vertical lines
        for (let x = 0; x < this.canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, this.canvas.height);
            ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y < this.canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(this.canvas.width, y);
            ctx.stroke();
        }
    }

    _updateNodes() {
        const cx = this.canvas.width / 2;
        const cy = this.canvas.height / 2;

        for (const node of this.nodes) {
            // Target position with gesture offset
            node.targetX = node.homeX + this.gestureVector.x * (node.dist / 200);
            node.targetY = node.homeY + this.gestureVector.y * (node.dist / 200);

            // Mouse attraction for nearby nodes
            if (this.mouse.active) {
                const dx = this.mouse.x - node.x;
                const dy = this.mouse.y - node.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const mouseRadius = 150;

                if (dist < mouseRadius && dist > 0) {
                    const force = 0.3 * (1 - dist / mouseRadius);
                    node.targetX += dx * force * 0.1;
                    node.targetY += dy * force * 0.1;
                }
            }

            // Voice amplitude makes nodes "breathe" outward
            if (this.voiceAmplitude > 0.1) {
                const dirX = node.homeX - cx;
                const dirY = node.homeY - cy;
                const dist = Math.sqrt(dirX * dirX + dirY * dirY);
                if (dist > 0) {
                    node.targetX += (dirX / dist) * this.voiceAmplitude * 20;
                    node.targetY += (dirY / dist) * this.voiceAmplitude * 20;
                }
            }

            // Organic bob
            node.targetX += Math.sin(this.time * 0.8 + node.pulsePhase) * 3;
            node.targetY += Math.cos(this.time * 0.6 + node.pulsePhase) * 3;

            // Spring physics
            const spring = 0.04;
            const damp = 0.85;
            node.vx += (node.targetX - node.x) * spring;
            node.vy += (node.targetY - node.y) * spring;
            node.vx *= damp;
            node.vy *= damp;
            node.x += node.vx;
            node.y += node.vy;

            // Energy decay
            node.energy *= 0.98;
            node.energy = Math.max(node.energy, 0.15);
        }
    }

    _drawEdges() {
        const ctx = this.ctx;

        for (const edge of this.edges) {
            const { from, to, strength } = edge;
            const { r, g, b } = from.color;

            // Energy along edge = average of connected nodes
            edge.energy = (from.energy + to.energy) / 2;
            const alpha = 0.05 + edge.energy * strength * 0.2;

            // Draw edge line
            ctx.beginPath();
            ctx.moveTo(from.x, from.y);
            ctx.lineTo(to.x, to.y);
            ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            ctx.lineWidth = 1 + edge.energy * 1.5;
            ctx.stroke();

            // Animated flow dots along edge
            edge.flowOffset += 0.5 + edge.energy * 2;
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const dotCount = Math.floor(dist / 30);

            for (let i = 0; i < dotCount; i++) {
                const t = ((edge.flowOffset / dist + i / dotCount) % 1);
                const px = from.x + dx * t;
                const py = from.y + dy * t;
                const dotAlpha = alpha * 0.8 * (0.3 + Math.sin(t * Math.PI) * 0.7);

                ctx.beginPath();
                ctx.arc(px, py, 1, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${dotAlpha})`;
                ctx.fill();
            }
        }
    }

    _drawDataPackets() {
        const ctx = this.ctx;

        for (let i = this.dataPackets.length - 1; i >= 0; i--) {
            const p = this.dataPackets[i];
            p.progress += p.speed;

            if (p.progress >= 1) {
                // Arrived — energize destination
                p.to.energy = Math.min(p.to.energy + 0.4, 1.0);
                this.dataPackets.splice(i, 1);
                continue;
            }

            const x = p.from.x + (p.to.x - p.from.x) * p.progress;
            const y = p.from.y + (p.to.y - p.from.y) * p.progress;
            const { r, g, b } = p.color;

            // Glow
            const grad = ctx.createRadialGradient(x, y, 0, x, y, p.size * 4);
            grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.5)`);
            grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
            ctx.beginPath();
            ctx.arc(x, y, p.size * 4, 0, Math.PI * 2);
            ctx.fillStyle = grad;
            ctx.fill();

            // Core
            ctx.beginPath();
            ctx.arc(x, y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.9)`;
            ctx.fill();

            // White center
            ctx.beginPath();
            ctx.arc(x, y, p.size * 0.4, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, 0.8)`;
            ctx.fill();
        }
    }

    _drawNodes() {
        const ctx = this.ctx;

        for (const node of this.nodes) {
            const { r, g, b } = node.color;
            const energy = node.energy;
            const size = node.size * (0.8 + energy * 0.4);
            const pulse = Math.sin(this.time * 2 + node.pulsePhase) * 0.15 + 0.85;

            // Outer glow
            const glowRadius = size * (2 + energy * 3);
            const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowRadius);
            grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${energy * 0.3 * pulse})`);
            grad.addColorStop(0.4, `rgba(${r}, ${g}, ${b}, ${energy * 0.1})`);
            grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
            ctx.beginPath();
            ctx.arc(node.x, node.y, glowRadius, 0, Math.PI * 2);
            ctx.fillStyle = grad;
            ctx.fill();

            // Hexagon node shape
            this._drawHexagon(ctx, node.x, node.y, size, node, energy, pulse);

            // Activation ring
            if (energy > 0.5) {
                const ringSize = size * 2 + Math.sin(this.time * 4 + node.pulsePhase) * 3;
                ctx.beginPath();
                ctx.arc(node.x, node.y, ringSize, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${(energy - 0.5) * 0.4})`;
                ctx.lineWidth = 1;
                ctx.setLineDash([4, 4]);
                ctx.lineDashOffset = -this.time * 40;
                ctx.stroke();
                ctx.setLineDash([]);
            }

            // Label
            ctx.font = `bold 9px "Orbitron", sans-serif`;
            ctx.textAlign = 'center';
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.3 + energy * 0.5})`;
            ctx.fillText(node.label, node.x, node.y + size + 14);
        }
    }

    _drawHexagon(ctx, x, y, size, node, energy, pulse) {
        const { r, g, b } = node.color;
        const sides = 6;

        ctx.beginPath();
        for (let i = 0; i <= sides; i++) {
            const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
            const px = x + Math.cos(angle) * size;
            const py = y + Math.sin(angle) * size;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();

        // Fill
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.1 + energy * 0.15})`;
        ctx.fill();

        // Border
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${0.4 + energy * 0.5})`;
        ctx.lineWidth = 1.5 + energy;
        ctx.stroke();

        // Inner bright hexagon
        ctx.beginPath();
        const innerSize = size * 0.4;
        for (let i = 0; i <= sides; i++) {
            const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
            const px = x + Math.cos(angle) * innerSize;
            const py = y + Math.sin(angle) * innerSize;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${energy * 0.6 * pulse})`;
        ctx.fill();
    }

    _drawPulseWaves() {
        const ctx = this.ctx;

        for (let i = this.pulseWaves.length - 1; i >= 0; i--) {
            const pw = this.pulseWaves[i];
            pw.radius += 3;
            pw.alpha *= 0.96;

            if (pw.alpha < 0.01 || pw.radius > pw.maxRadius) {
                this.pulseWaves.splice(i, 1);
                continue;
            }

            const { r, g, b } = pw.color;

            ctx.beginPath();
            ctx.arc(pw.x, pw.y, pw.radius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${pw.alpha})`;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Inner fill
            ctx.beginPath();
            ctx.arc(pw.x, pw.y, pw.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${pw.alpha * 0.05})`;
            ctx.fill();
        }
    }

    _drawHexOverlay() {
        // Decorative corner hex brackets
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const s = 20;
        const pad = 15;
        const alpha = 0.12 + this.voiceAmplitude * 0.1;

        ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
        ctx.lineWidth = 1;

        // Top-left
        ctx.beginPath();
        ctx.moveTo(pad, pad + s);
        ctx.lineTo(pad, pad);
        ctx.lineTo(pad + s, pad);
        ctx.stroke();

        // Top-right
        ctx.beginPath();
        ctx.moveTo(w - pad - s, pad);
        ctx.lineTo(w - pad, pad);
        ctx.lineTo(w - pad, pad + s);
        ctx.stroke();

        // Bottom-left
        ctx.beginPath();
        ctx.moveTo(pad, h - pad - s);
        ctx.lineTo(pad, h - pad);
        ctx.lineTo(pad + s, h - pad);
        ctx.stroke();

        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(w - pad - s, h - pad);
        ctx.lineTo(w - pad, h - pad);
        ctx.lineTo(w - pad, h - pad - s);
        ctx.stroke();
    }
}

// ─── Voice simulation (reacts to audio) ────────────────────
// Simulates voice amplitude changes. In production, this connects
// to real microphone data via WebSocket.

let matrix = null;

function initMatrix() {
    matrix = new NodeMatrix('center-display');

    // Simulate periodic voice bursts
    setInterval(() => {
        if (Math.random() < 0.3) {
            const amp = 0.3 + Math.random() * 0.7;
            matrix.onVoiceInput(amp);
        }
    }, 2000);

    // Simulate periodic gestures
    setInterval(() => {
        if (Math.random() < 0.15) {
            const gestures = ['wave', 'point', 'stop', 'thumbs_up'];
            const g = gestures[Math.floor(Math.random() * gestures.length)];
            const dx = (Math.random() - 0.5) * 2;
            const dy = (Math.random() - 0.5) * 2;
            matrix.onGesture(g, dx, dy);
        }
    }, 5000);

    // Simulate data flow
    setInterval(() => {
        const edgeCount = matrix.edges.length;
        const idx = Math.floor(Math.random() * edgeCount);
        const edge = matrix.edges[idx];
        matrix._sendPacket(edge.from.id, edge.to.id);
    }, 800);
}

// Wait for DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMatrix);
} else {
    initMatrix();
}
