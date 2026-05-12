import { setState, getState } from './store.js';
import { connectTelemetry, disconnectTelemetry } from './telemetry.js';
import { initFindingCards } from './finding-cards.js';
import { renderReportContent } from './finding-detail.js';
import { initReport } from './report.js';

document.addEventListener('DOMContentLoaded', () => {
    initFindingCards();
    initReport();
    setupGitHubForm();
    setupLocalUpload();
    setupChat();
    setupStatusBar();
});

function updateStatus(text, isBusy) {
    const dot = document.getElementById('status-dot');
    const label = document.getElementById('status-label');
    if (!dot || !label) return;
    label.textContent = text;
    dot.className = 'status-dot' + (isBusy ? ' busy' : '');
}

function setupStatusBar() {
    updateStatus('Ready', false);
}

async function handleResponse(res, onSuccess) {
    const data = await res.json();
    if (data.status === 'success') {
        setState({ sessionId: data.session_id });
        renderReportContent(data.html_review);
        connectTelemetry(data.session_id);
        onSuccess(data);
    } else {
        renderReportContent(`<div class="placeholder-message"><h2>Error</h2><p>${escapeHtml(data.message || 'Request failed.')}</p></div>`);
    }
    updateStatus('Ready', false);
}

const githubForm = document.getElementById('github-form');
function setupGitHubForm() {
    if (!githubForm) return;
    githubForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('repo-url');
        const url = input.value.trim();
        if (!url) return;
        updateStatus('Cloning...', true);
        const formData = new FormData();
        formData.append('repo_url', url);
        try {
            const res = await fetch('/api/load-github', { method: 'POST', body: formData });
            await handleResponse(res, () => {});
        } catch (err) {
            renderReportContent(`<div class="placeholder-message"><h2>Network Error</h2><p>${escapeHtml(err.message)}</p></div>`);
            updateStatus('Error', false);
        }
    });
}

const localForm = document.getElementById('local-form');
function setupLocalUpload() {
    if (!localForm) return;
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('local-files');
    if (dropZone && fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) uploadFiles(fileInput.files);
        });
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
            dropZone.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); });
        });
        dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) uploadFiles(e.dataTransfer.files);
        });
    }
}

async function uploadFiles(files) {
    updateStatus('Uploading...', true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    try {
        const res = await fetch('/api/load-local', { method: 'POST', body: formData });
        await handleResponse(res, () => {});
    } catch (err) {
        renderReportContent(`<div class="placeholder-message"><h2>Network Error</h2><p>${escapeHtml(err.message)}</p></div>`);
        updateStatus('Error', false);
    }
}

const chatForm = document.getElementById('chat-form');
function setupChat() {
    if (!chatForm) return;
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const msg = input.value.trim();
        if (!msg) return;
        const { sessionId } = getState();
        if (!sessionId) {
            renderReportContent('<div class="placeholder-message"><h2>No Session</h2><p>Load a repository first.</p></div>');
            return;
        }
        updateStatus('Thinking...', true);
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('message', msg);
        try {
            const res = await fetch('/api/chat', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                renderReportContent(data.html_response);
            } else {
                renderReportContent(`<div class="placeholder-message"><h2>Chat Error</h2><p>${escapeHtml(data.message || 'Chat failed.')}</p></div>`);
            }
        } catch (err) {
            renderReportContent(`<div class="placeholder-message"><h2>Network Error</h2><p>${escapeHtml(err.message)}</p></div>`);
        }
        updateStatus('Ready', false);
        input.value = '';
    });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
