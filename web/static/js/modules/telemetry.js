import { setState } from './store.js';

let eventSource = null;

export function connectTelemetry(sessionId) {
    disconnectTelemetry();
    eventSource = new EventSource(`/api/audit-stream/${sessionId}`);
    eventSource.addEventListener('phase', (e) => {
        const data = JSON.parse(e.data);
        addTelemetryEntry(data.phase, data.message);
        setState({ status: 'busy' });
    });
    eventSource.addEventListener('complete', (e) => {
        addTelemetryEntry('complete', 'Audit complete.');
        setState({ status: 'ready' });
        disconnectTelemetry();
    });
    eventSource.addEventListener('error', (e) => {
        const data = JSON.parse(e.data);
        addTelemetryEntry('error', data.message || 'An error occurred.');
        setState({ status: 'error' });
        disconnectTelemetry();
    });
    eventSource.onerror = () => {
        addTelemetryEntry('error', 'Connection lost.');
        setState({ status: 'error' });
        disconnectTelemetry();
    };
}

export function disconnectTelemetry() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

function addTelemetryEntry(phase, message) {
    const feed = document.getElementById('telemetry-feed');
    if (!feed) return;
    const entry = document.createElement('div');
    entry.className = 'entry';
    entry.innerHTML = `<span class="phase">[${phase}]</span> ${message}`;
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
}
