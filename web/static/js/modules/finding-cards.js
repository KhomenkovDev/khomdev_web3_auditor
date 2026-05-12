import { getState, onStateChange } from './store.js';

export function initFindingCards() {
    onStateChange(renderFindings);
}

function renderFindings(state) {
    const container = document.getElementById('findings-list');
    if (!container) return;
    const findings = state.findings || [];
    if (findings.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 12px 0;">No findings yet. Load a repository to begin.</div>';
        return;
    }
    container.innerHTML = findings.map((f, i) => `
        <div class="finding-card" data-index="${i}">
            <div class="finding-header">
                <span class="severity-badge ${f.severity}">${f.severity}</span>
                <span class="finding-title">${escapeHtml(f.title)}</span>
            </div>
            <div class="finding-meta">${f.file_path || ''}${f.line_number ? `:${f.line_number}` : ''}</div>
        </div>
    `).join('');
    container.querySelectorAll('.finding-card').forEach(card => {
        card.addEventListener('click', () => {
            const idx = parseInt(card.dataset.index);
            showFindingDetail(findings[idx]);
        });
    });
}

function showFindingDetail(finding) {
    const detail = document.getElementById('finding-detail');
    if (!detail) return;
    detail.innerHTML = `
        <h3 style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            <span class="severity-badge ${finding.severity}">${finding.severity}</span>
            ${escapeHtml(finding.title)}
        </h3>
        <p style="color:var(--text-secondary);margin-bottom:12px;">${escapeHtml(finding.description)}</p>
        ${finding.file_path ? `<p style="font-family:var(--font-mono);font-size:0.8rem;color:var(--text-secondary);">File: ${escapeHtml(finding.file_path)}${finding.line_number ? `:${finding.line_number}` : ''}</p>` : ''}
        ${finding.code_snippet ? `<pre style="background:var(--bg-surface);border:1px solid var(--border-color);border-radius:6px;padding:12px;margin:12px 0;overflow-x:auto;"><code>${escapeHtml(finding.code_snippet)}</code></pre>` : ''}
        ${finding.recommendation ? `<p style="color:var(--accent-green);font-size:0.85rem;"><strong>Recommendation:</strong> ${escapeHtml(finding.recommendation)}</p>` : ''}
        <p style="font-size:0.75rem;color:var(--text-muted);margin-top:12px;">Tool: ${finding.tool || 'gemini'}</p>
    `;
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
