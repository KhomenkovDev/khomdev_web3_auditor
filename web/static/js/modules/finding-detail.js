import { getState } from './store.js';

export function renderReportContent(rawHtml) {
    const area = document.getElementById('content-area');
    if (!area) return;
    area.innerHTML = `<div class="report-content">${rawHtml}</div>`;
}
