import { getState } from './store.js';

export function initReport() {
    document.addEventListener('click', (e) => {
        const exportJson = e.target.closest('#export-json');
        const exportPdf = e.target.closest('#export-pdf');
        if (exportJson) exportReport('json');
        if (exportPdf) exportReport('pdf');
    });
}

async function exportReport(format) {
    const { sessionId } = getState();
    if (!sessionId) return;
    try {
        const res = await fetch(`/api/export/${sessionId}?format=${format}`);
        const data = await res.json();
        if (data.status === 'success') {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit-${sessionId}.${format}`;
            a.click();
            URL.revokeObjectURL(url);
        }
    } catch (err) {
        console.error('Export failed:', err);
    }
}
