/**
 * KAI Dashboard — Live system stats rendering.
 * Listens for kai:system.stats CustomEvent from orb.
 */

(() => {
    let prevNet = null;
    let prevTime = null;

    function formatBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
        return (bytes / 1073741824).toFixed(2) + ' GB';
    }

    function setBar(id, percent) {
        const el = document.getElementById(id);
        if (!el) return;
        el.style.width = percent + '%';
        el.classList.remove('warn', 'crit');
        if (percent > 85) el.classList.add('crit');
        else if (percent > 65) el.classList.add('warn');
    }

    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    window.addEventListener('kai:system.stats', (e) => {
        const s = e.detail;
        if (!s) return;

        // CPU
        if (s.cpu) {
            setText('stat-cpu', Math.round(s.cpu.percent) + '%');
            setBar('bar-cpu', s.cpu.percent);
            setText('sub-cpu', s.cpu.count + ' cores');
        }

        // Memory
        if (s.memory) {
            setText('stat-memory', Math.round(s.memory.percent) + '%');
            setBar('bar-memory', s.memory.percent);
            setText('sub-memory', s.memory.used_gb + ' / ' + s.memory.total_gb + ' GB');
        }

        // Disk
        if (s.disk) {
            setText('stat-disk', Math.round(s.disk.percent) + '%');
            setBar('bar-disk', s.disk.percent);
            setText('sub-disk', s.disk.used_gb + ' / ' + s.disk.total_gb + ' GB');
        }

        // Battery
        if (s.battery) {
            setText('stat-battery', Math.round(s.battery.percent) + '%');
            setBar('bar-battery', s.battery.percent);
            setText('sub-battery', s.battery.plugged ? 'Plugged in' : 'On battery');
        } else {
            setText('stat-battery', 'N/A');
            setText('sub-battery', 'No battery');
        }

        // Network — calculate throughput from deltas
        if (s.network) {
            const now = Date.now();
            if (prevNet && prevTime) {
                const dt = (now - prevTime) / 1000;
                if (dt > 0) {
                    const upRate = (s.network.bytes_sent - prevNet.bytes_sent) / dt;
                    const downRate = (s.network.bytes_recv - prevNet.bytes_recv) / dt;
                    setText('stat-network', formatBytes(upRate) + '/s  /  ' + formatBytes(downRate) + '/s');
                }
            }
            setText('sub-network', formatBytes(s.network.bytes_sent) + ' sent  /  ' + formatBytes(s.network.bytes_recv) + ' recv');
            prevNet = s.network;
            prevTime = now;
        }
    });
})();
