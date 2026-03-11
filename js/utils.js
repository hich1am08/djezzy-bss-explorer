// js/utils.js

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

async function fetchCsrf() {
    try {
        const res = await fetch('/api/auth/csrf', { credentials: 'include' });
        if (res.ok) {
            const data = await res.json();
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) meta.setAttribute('content', data.csrf_token);
        }
    } catch (e) {
        console.error("Failed to fetch CSRF", e);
    }
}

function getCsrfHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
    };
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function safe(val) {
    if (val === null || val === undefined || val === '') return '-';
    return val;
}

// Generates structural HTML elements for placeholders
function renderSkeletonBlock(count = 1) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `<div class="skeleton h-32"></div>`;
    }
    return `<div class="grid-cards">${html}</div>`;
}

function renderTableSkeleton(rows = 5) {
    let html = '<div class="table-wrapper"><table><thead><tr>';
    for (let i = 0; i < 5; i++) html += '<th><div class="skeleton"></div></th>';
    html += '</tr></thead><tbody>';
    for (let r = 0; r < rows; r++) {
        html += '<tr>';
        for (let i = 0; i < 5; i++) html += '<td><div class="skeleton"></div></td>';
        html += '</tr>';
    }
    html += '</tbody></table></div>';
    return html;
}
