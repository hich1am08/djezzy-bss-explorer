/* Djezzy BSS Explorer v3 — Frontend Logic */
const BAND_COLORS = {
    "GSM900": "#3B82F6", "DCS1800": "#60A5FA", "U900": "#7C3AED", "U2100": "#A78BFA",
    "L900": "#F97316", "L1800": "#F59E0B", "L2100": "#FBBF24", "TDD2300": "#EF4444",
    "NR_N78": "#10B981", "NR_N77": "#06B6D4"
};
const TECH_COLORS = { "2G": "#3B82F6", "3G": "#8B5CF6", "4G": "#F59E0B", "5G": "#10B981" };
let chartInstances = {};

document.addEventListener('DOMContentLoaded', async () => {
    await fetchCsrf(); checkSession();
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // Nav
    document.querySelectorAll('.nav-links li').forEach(item => {
        item.addEventListener('click', e => {
            const li = e.target.closest('li');
            document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
            li.classList.add('active');
            const view = li.getAttribute('data-view');
            document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
            document.getElementById(`view-${view}`).classList.remove('hidden');
        });
    });

    // View handlers
    document.getElementById('btn-site-search').addEventListener('click', doSiteLookup);
    document.getElementById('site-search-input').addEventListener('keypress', e => { if (e.key === 'Enter') doSiteLookup() });
    document.getElementById('btn-param-search').addEventListener('click', doParamSearch);
    document.getElementById('param-value-input').addEventListener('keypress', e => { if (e.key === 'Enter') doParamSearch() });
    document.getElementById('btn-sites-list-search').addEventListener('click', () => loadSitesList(1));
    document.getElementById('sites-list-search').addEventListener('keypress', e => { if (e.key === 'Enter') loadSitesList(1) });
    document.getElementById('btn-dataset-load').addEventListener('click', () => loadDataset(1));
    document.getElementById('dataset-search').addEventListener('keypress', e => { if (e.key === 'Enter') loadDataset(1) });
    document.getElementById('btn-batch-search').addEventListener('click', doBatchSearch);
    document.getElementById('btn-batch-export').addEventListener('click', doBatchExport);
    document.getElementById('btn-reload-data').addEventListener('click', triggerReload);
    document.getElementById('btn-upload-dataset').addEventListener('click', uploadDataset);
    document.getElementById('btn-create-user').addEventListener('click', createUser);
    document.getElementById('btn-change-password').addEventListener('click', changePassword);
});

// ═══ AUTH ═══
async function checkSession() {
    try {
        const r = await fetch('/api/auth/session', { credentials: 'include' });
        if (r.ok) { loginSuccess(await r.json()) }
        else { document.getElementById('login-screen').classList.remove('hidden'); document.getElementById('app-screen').classList.add('hidden') }
    } catch (e) { }
}
async function handleLogin(e) {
    e.preventDefault(); const btn = document.querySelector('#login-form button');
    btn.textContent = "Authenticating..."; btn.disabled = true;
    try {
        const r = await fetch('/api/auth/login', {
            method: 'POST', headers: getCsrfHeaders(), credentials: 'include',
            body: JSON.stringify({ username: document.getElementById('username').value, password: document.getElementById('password').value })
        });
        const d = await r.json();
        if (r.ok) { loginSuccess(d); showToast("Welcome to Djezzy BSS Explorer", "success") }
        else showToast(d.error || "Login failed", "error");
    } catch (e) { showToast("Server error", "error") }
    finally { btn.textContent = "Secure Sign In"; btn.disabled = false }
}
async function handleLogout() { try { await fetch('/api/auth/logout', { method: 'POST', headers: getCsrfHeaders(), credentials: 'include' }); window.location.reload() } catch (e) { } }

function loginSuccess(data) {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    const role = data.user?.role || data.role || 'user';
    document.getElementById('display-user').textContent = data.user?.username || data.user || '';
    document.getElementById('display-role').textContent = role;
    if (role === 'admin') {
        document.getElementById('nav-admin').classList.remove('hidden');
        document.getElementById('nav-dataset').classList.remove('hidden');
        loadUsersList();
    }
    loadDashboard(); loadDatasetSelect(); loadParamSelect();
}

// ═══ DASHBOARD ═══
async function loadDashboard() {
    try {
        const r = await fetch('/api/dashboard', { credentials: 'include' });
        if (!r.ok) return;
        const d = await r.json();

        // Stats cards
        const cards = document.getElementById('dash-stats-cards');
        cards.innerHTML = `
            <div class="stat-card glass-panel"><div class="stat-value">${(d.total_sites || 0).toLocaleString()}</div><div class="stat-label">Unique Sites</div></div>
            <div class="stat-card glass-panel"><div class="stat-value">${Object.keys(d.datasets || {}).length}</div><div class="stat-label">Datasets Loaded</div></div>
            <div class="stat-card glass-panel" style="--accent:#3B82F6"><div class="stat-value">${(d.tech_counts?.['2G'] || 0).toLocaleString()}</div><div class="stat-label">2G Cells</div></div>
            <div class="stat-card glass-panel" style="--accent:#8B5CF6"><div class="stat-value">${(d.tech_counts?.['3G'] || 0).toLocaleString()}</div><div class="stat-label">3G Cells</div></div>
            <div class="stat-card glass-panel" style="--accent:#F59E0B"><div class="stat-value">${(d.tech_counts?.['4G'] || 0).toLocaleString()}</div><div class="stat-label">4G Cells</div></div>
            <div class="stat-card glass-panel" style="--accent:#10B981"><div class="stat-value">${(d.tech_counts?.['5G'] || 0).toLocaleString()}</div><div class="stat-label">5G Cells</div></div>`;

        // Charts
        renderChart('chart-tech', 'doughnut',
            Object.keys(d.tech_counts || {}), Object.values(d.tech_counts || {}),
            ['#3B82F6', '#8B5CF6', '#F59E0B', '#10B981']);

        const b4g = d.band_distribution_4g || {};
        renderChart('chart-4g-bands', 'bar',
            Object.keys(b4g), Object.values(b4g),
            Object.keys(b4g).map(k => BAND_COLORS[k] || '#888'));

        const wil = d.sites_by_wilaya || {};
        const wilKeys = Object.keys(wil).slice(0, 25);
        renderChart('chart-wilaya', 'bar',
            wilKeys, wilKeys.map(k => wil[k]),
            wilKeys.map(() => '#E11326'));

        const eq = d.equipment_types || {};
        renderChart('chart-equip', 'doughnut',
            Object.keys(eq), Object.values(eq),
            ['#3B82F6', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6', '#06B6D4']);

        // Expert Dashboard Charts
        const plat = d.platform_distribution || {};
        if (Object.keys(plat).length > 0) {
            renderChart('chart-platform', 'doughnut',
                Object.keys(plat), Object.values(plat),
                ['#06B6D4', '#F97316', '#8B5CF6', '#64748B']);
        }

        const rruT = d.rru_type_distribution || {};
        if (Object.keys(rruT).length > 0) {
            renderChart('chart-rru-types', 'bar',
                Object.keys(rruT), Object.values(rruT),
                Object.keys(rruT).map((_, i) => ['#F97316', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#06B6D4'][i % 6]));
        }

        const rruM = d.rru_working_mode_distribution || {};
        if (Object.keys(rruM).length > 0) {
            renderChart('chart-rru-modes', 'doughnut',
                Object.keys(rruM), Object.values(rruM),
                ['#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#3B82F6']);
        }

    } catch (e) { console.error("Dashboard error", e) }
}

function renderChart(canvasId, type, labels, data, colors) {
    if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    chartInstances[canvasId] = new Chart(ctx, {
        type, data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0, borderRadius: type === 'bar' ? 4 : 0 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: type === 'doughnut', position: 'right', labels: { color: '#AAA', font: { size: 11 } } } },
            scales: type === 'bar' ? { x: { ticks: { color: '#888', font: { size: 10 } }, grid: { display: false } }, y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.04)' } } } : {}
        }
    });
}

// ═══ SITE LOOKUP ═══
async function doSiteLookup() {
    let code = document.getElementById('site-search-input').value.trim().toUpperCase();
    if (!code) return showToast("Enter a site code", "error");
    const m = code.match(/^[345]?[A-Z](\d{2}[A-Z]\d{3,4})/);
    if (m) code = m[1];
    const c = document.getElementById('site-results');
    c.innerHTML = renderSkeletonBlock(4);
    try {
        const r = await fetch(`/api/search/site?code=${encodeURIComponent(code)}`, { credentials: 'include' });
        const d = await r.json();
        if (r.ok) {
            renderSiteProfile(d, c);
            // Fetch expert data asynchronously
            try {
                const er = await fetch(`/api/expert/site?code=${encodeURIComponent(code)}`, { credentials: 'include' });
                if (er.ok) { const ed = await er.json(); renderExpertSections(ed, c); }
            } catch (ex) { console.error('Expert data load failed', ex); }
        } else c.innerHTML = `<div class="empty-state"><p>${d.error}</p></div>`;
    } catch (e) { c.innerHTML = `<div class="empty-state"><p>Server error</p></div>` }
}

function renderSiteProfile(data, container) {
    if (!data.config_bands || data.config_bands.length === 0) {
        container.innerHTML = `<div class="empty-state"><p>No data found for <strong>${data.site_code}</strong></p></div>`; return;
    }
    let h = '';

    // ═══ CONFIG BANDS DISPLAY ═══
    h += `<div class="glass-panel fade-in config-hero">
        <h3 class="config-site-title">Site: <span class="text-primary">${data.site_code}</span></h3>
        <div class="config-bands-grid">`;
    data.config_bands.forEach(b => {
        h += `<div class="config-band-card" style="--band-color:${b.color}">
            <div class="band-header"><span class="band-dot" style="background:${b.color}"></span><span class="band-name">${b.band}</span><span class="band-tech">${b.tech}</span></div>
            <div class="band-config">${b.sectors.map((s, i) => `<span class="sector-val ${s > 0 ? 'active' : ''}">${s}</span>`).join('<span class="sector-sep">/</span>')}</div>
            <div class="band-labels"><span>S1</span><span>S2</span><span>S3</span><span>S4</span></div>
            <div class="band-total">${b.total_cells} cells</div>
        </div>`;
    });
    h += `</div></div>`;

    // ═══ TECHNOLOGY TABLES ═══
    for (const tech of ['2G', '3G', '4G', '5G']) {
        const cells = data.technologies?.[tech];
        if (!cells || !cells.length) continue;
        const color = TECH_COLORS[tech];
        const keys = Object.keys(cells[0]).filter(k => !k.startsWith('_'));
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid ${color}">
            <h4>${tech} Cells <span class="count-chip">${cells.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr><th>S</th><th>Band</th>`;
        keys.forEach(k => { h += `<th>${k}</th>` });
        h += `</tr></thead><tbody>`;
        cells.forEach(c => {
            h += `<tr><td><span class="badge-sector">S${c._sector || '?'}</span></td>
                <td><span class="band-chip-sm" style="--chip-color:${c._band_color || '#888'}">${c._band || '-'}</span></td>`;
            keys.forEach(k => { h += `<td>${safe(c[k])}</td>` });
            h += `</tr>`;
        });
        h += `</tbody></table></div></div>`;
    }

    // ═══ EQUIPMENT ═══
    if (data.equipment?.length) {
        const ek = Object.keys(data.equipment[0]).filter(k => !k.startsWith('_'));
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #FF6B35">
            <h4>Equipment <span class="count-chip">${data.equipment.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr>`;
        ek.forEach(k => { h += `<th>${k}</th>` });
        h += `</tr></thead><tbody>`;
        data.equipment.forEach(eq => { h += `<tr>`; ek.forEach(k => { h += `<td>${safe(eq[k])}</td>` }); h += `</tr>` });
        h += `</tbody></table></div></div>`;
    }

    // ═══ EXTENDED DATA ═══
    if (data.extended && Object.keys(data.extended).length > 0) {
        for (const [key, rows] of Object.entries(data.extended)) {
            if (!rows.length) continue;
            const xk = Object.keys(rows[0]).filter(k => !k.startsWith('_'));
            h += `<div class="data-section glass-panel fade-in"><div class="section-heading">
                <h4>${key} <span class="count-chip">${rows.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr>`;
            xk.forEach(k => { h += `<th>${k}</th>` });
            h += `</tr></thead><tbody>`;
            rows.slice(0, 100).forEach(r => { h += `<tr>`; xk.forEach(k => { h += `<td>${safe(r[k])}</td>` }); h += `</tr>` });
            h += `</tbody></table></div></div>`;
        }
    }

    container.innerHTML = h;
}

// ═══ EXPERT SECTIONS RENDERING ═══
function renderExpertSections(data, container) {
    let h = '';

    // Status badge helper
    const badge = (val) => {
        const cls = (val === 'Normal' || val === 'Up') ? 'expert-ok' : (val === '-' || val === 'nan') ? 'expert-na' : 'expert-err';
        return `<span class="expert-badge ${cls}">${val}</span>`;
    };

    // ─── Hardware & Software ───
    if (data.hardware_versions?.length) {
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #06B6D4">
            <h4>⚙ Hardware & Software <span class="count-chip">${data.hardware_versions.length}</span></h4></div>
            <div class="expert-cards-grid">`;
        data.hardware_versions.forEach(hw => {
            h += `<div class="expert-hw-card">
                <div class="expert-hw-tech" style="color:${TECH_COLORS[hw.tech] || '#888'}">${hw.tech}</div>
                <div class="expert-hw-platform">${hw.platform}</div>
                <div class="expert-hw-version">${hw.version}</div>
                ${hw.transport ? `<div class="expert-hw-detail">Transport: ${hw.transport}</div>` : ''}
            </div>`;
        });
        h += `</div></div>`;
    }

    // ─── RRU Inventory ───
    if (data.rru_inventory?.length) {
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #F97316">
            <h4>📡 RRU Inventory <span class="count-chip">${data.rru_inventory.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr>
                <th>Tech</th><th>RRU Name</th><th>Type</th><th>Mode</th><th>Cell</th><th>PCI</th><th>Status</th><th>Fiber (m)</th>
            </tr></thead><tbody>`;
        data.rru_inventory.forEach(r => {
            h += `<tr><td><span class="band-chip-sm" style="--chip-color:${TECH_COLORS[r.tech] || '#888'}">${r.tech}</span></td>
                <td><strong>${r.rru_name}</strong></td><td>${r.rru_type}</td><td>${r.working_mode}</td>
                <td>${r.cell_name}</td><td>${r.pci}</td><td>${badge(r.availability)}</td>
                <td>${r.fiber_length_m || '-'}</td></tr>`;
        });
        h += `</tbody></table></div></div>`;
    }

    // ─── CPRI Health ───
    if (data.cpri_health?.length) {
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #8B5CF6">
            <h4>🔗 CPRI / Fronthaul Health <span class="count-chip">${data.cpri_health.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr>
                <th>Tech</th><th>Port</th><th>Type</th><th>Line Rate</th><th>Allocated</th><th>Remaining</th><th>Utilization</th><th>Consistency</th><th>Mux</th>
            </tr></thead><tbody>`;
        data.cpri_health.forEach(c => {
            const pct = c.utilization_pct || 0;
            const barColor = pct > 80 ? '#EF4444' : pct > 50 ? '#F59E0B' : '#10B981';
            h += `<tr><td><span class="band-chip-sm" style="--chip-color:${TECH_COLORS[c.tech] || '#888'}">${c.tech}</span></td>
                <td>${c.port}</td><td>${c.port_type}</td>
                <td>${c.line_rate_mbps} Mbps</td><td>${c.allocated_mbps} Mbps</td><td>${c.remaining_mbps} Mbps</td>
                <td><div class="expert-util-bar"><div class="expert-util-fill" style="width:${Math.min(pct, 100)}%;background:${barColor}"></div><span>${pct}%</span></div></td>
                <td>${badge(c.rate_consistency === 'Yes' ? 'Normal' : c.rate_consistency)}</td><td>${c.mux_type}</td></tr>`;
        });
        h += `</tbody></table></div></div>`;
    }

    // ─── NSA Anchoring ───
    if (data.nsa_anchoring?.length) {
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #10B981">
            <h4>🔄 NSA Anchoring (4G ↔ 5G) <span class="count-chip">${data.nsa_anchoring.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr>
                <th>Direction</th><th>Local Cell</th><th>Peer Cell</th><th>Local Type</th><th>Peer Type</th><th>X2 Status</th>
            </tr></thead><tbody>`;
        data.nsa_anchoring.forEach(n => {
            h += `<tr><td><span class="expert-badge expert-dir">${n.source}</span></td>
                <td>${n.local_cell}</td><td>${n.peer_cell}</td>
                <td>${n.local_type}</td><td>${n.peer_type}</td><td>${badge(n.x2_status)}</td></tr>`;
        });
        h += `</tbody></table></div></div>`;
    }

    // ─── X2 Neighbors ───
    if (data.x2_neighbors?.length) {
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #EC4899">
            <h4>🌐 X2 Neighbor Topology <span class="count-chip">${data.x2_neighbors.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr>
                <th>Tech</th><th>Peer Site</th><th>Peer NE</th><th>Local X2</th><th>Peer X2</th><th>SCTP</th><th>Local IP</th><th>Peer IP</th>
            </tr></thead><tbody>`;
        data.x2_neighbors.forEach(x => {
            h += `<tr><td><span class="band-chip-sm" style="--chip-color:${TECH_COLORS[x.tech] || '#888'}">${x.tech}</span></td>
                <td><strong>${x.peer_site}</strong></td><td>${x.peer_name}</td>
                <td>${badge(x.local_x2_status)}</td><td>${badge(x.peer_x2_status)}</td>
                <td>${badge(x.sctp_status)}</td><td class="text-muted">${x.local_ip}</td><td class="text-muted">${x.peer_ip}</td></tr>`;
        });
        h += `</tbody></table></div></div>`;
    }

    // ─── S1 Interfaces ───
    if (data.s1_interfaces?.length) {
        h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #6366F1">
            <h4>📶 S1 Interface (MME) <span class="count-chip">${data.s1_interfaces.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr>
                <th>S1 ID</th><th>Status</th><th>SCTP</th><th>MME (GUMMEIs)</th><th>Local IP</th><th>Peer IP</th>
            </tr></thead><tbody>`;
        data.s1_interfaces.forEach(s => {
            h += `<tr><td>${s.s1_id}</td><td>${badge(s.status)}</td><td>${badge(s.sctp_status)}</td>
                <td>${s.mme}</td><td class="text-muted">${s.local_ip}</td><td class="text-muted">${s.peer_ip}</td></tr>`;
        });
        h += `</tbody></table></div></div>`;
    }

    if (h) container.innerHTML += h;
}

// ═══ PARAMETER SEARCH ═══
async function loadParamSelect() {
    try {
        const r = await fetch('/api/dashboard', { credentials: 'include' });
        if (!r.ok) return;
        const d = await r.json();
        const sel = document.getElementById('param-select');
        sel.innerHTML = '<option value="">-- Parameter --</option>';
        (d.searchable_params || []).forEach(p => { sel.innerHTML += `<option value="${p}">${p}</option>` });
    } catch (e) { }
}

async function doParamSearch() {
    const param = document.getElementById('param-select').value;
    const value = document.getElementById('param-value-input').value.trim();
    if (!param) return showToast("Select a parameter", "error");
    if (!value) return showToast("Enter a search value", "error");

    const c = document.getElementById('param-results');
    c.innerHTML = renderTableSkeleton(6);
    try {
        const r = await fetch(`/api/search/parameter?param=${encodeURIComponent(param)}&value=${encodeURIComponent(value)}&limit=100`, { credentials: 'include' });
        const d = await r.json();
        if (!r.ok) { c.innerHTML = `<div class="empty-state"><p>${d.error}</p></div>`; return }
        if (!d.results || !d.results.length) { c.innerHTML = `<div class="empty-state"><p>No results for ${param} = "${value}"</p></div>`; return }

        // Group by source
        const grouped = {};
        d.results.forEach(r => { const s = r._source || 'Unknown'; if (!grouped[s]) grouped[s] = []; grouped[s].push(r) });

        let h = `<p class="text-muted mb-4">${d.count} results for <strong>${param}</strong> = "${value}"</p>`;
        for (const [src, rows] of Object.entries(grouped)) {
            const keys = Object.keys(rows[0]).filter(k => !k.startsWith('_'));
            const color = TECH_COLORS[src] || TECH_COLORS[src.split('_')[0]] || '#888';
            h += `<div class="data-section glass-panel fade-in mb-4">
                <div class="section-heading" style="border-left:4px solid ${color}"><h4>${src} <span class="count-chip">${rows.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr>`;
            keys.forEach(k => { h += `<th>${k}</th>` });
            h += `</tr></thead><tbody>`;
            rows.forEach(row => { h += `<tr>`; keys.forEach(k => { h += `<td>${safe(row[k])}</td>` }); h += `</tr>` });
            h += `</tbody></table></div></div>`;
        }
        c.innerHTML = h;
    } catch (e) { c.innerHTML = `<div class="empty-state"><p>Server error</p></div>` }
}

// ═══ SITES LIST ═══
async function loadSitesList(page = 1) {
    const search = document.getElementById('sites-list-search').value.trim();
    const c = document.getElementById('sites-list-container');
    c.innerHTML = renderTableSkeleton(8);
    try {
        const r = await fetch(`/api/sites/list?page=${page}&per_page=50&q=${encodeURIComponent(search)}`, { credentials: 'include' });
        const d = await r.json();
        if (!r.ok || !d.sites?.length) { c.innerHTML = `<div class="empty-state"><p>No sites found</p></div>`; return }

        let h = `<p class="text-muted mb-4">${d.total} sites (page ${d.page})</p><div class="sites-cards-grid">`;
        d.sites.forEach(site => {
            h += `<div class="site-mini-card glass-panel" onclick="quickLookup('${site.site_code}')">
                <div class="site-mini-code">${site.site_code}</div>
                <div class="site-mini-bands">`;
            (site.config_bands || []).forEach(b => {
                h += `<div class="mini-band"><span class="mini-dot" style="background:${b.color}"></span>${b.band}: <strong>${b.config_str}</strong></div>`;
            });
            h += `</div></div>`;
        });
        h += `</div>`;
        c.innerHTML = h;
        renderPagination('sites-list-pagination', d.page, Math.ceil(d.total / d.per_page), loadSitesList);
    } catch (e) { c.innerHTML = `<div class="empty-state"><p>Server error</p></div>` }
}

function quickLookup(code) {
    document.getElementById('site-search-input').value = code;
    document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
    document.querySelector('[data-view="site-lookup"]').classList.add('active');
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById('view-site-lookup').classList.remove('hidden');
    doSiteLookup();
}

// ═══ DATASET BROWSER ═══
async function loadDatasetSelect() {
    try {
        const r = await fetch('/api/datasets', { credentials: 'include' }); if (!r.ok) return;
        const d = await r.json(); const s = document.getElementById('dataset-select');
        s.innerHTML = '<option value="">-- Select Dataset --</option>';
        d.datasets.forEach(n => { s.innerHTML += `<option value="${n}">${n}</option>` });
    } catch (e) { }
}

async function loadDataset(page = 1) {
    const name = document.getElementById('dataset-select').value;
    const search = document.getElementById('dataset-search').value.trim();
    if (!name) return showToast("Select a dataset", "error");
    const c = document.getElementById('dataset-table-container');
    c.innerHTML = renderTableSkeleton(10);
    try {
        const r = await fetch(`/api/datasets/${name}?page=${page}&per_page=50&q=${encodeURIComponent(search)}`, { credentials: 'include' });
        const d = await r.json();
        if (!r.ok || !d.rows?.length) { c.innerHTML = `<div class="empty-state"><p>No rows</p></div>`; return }
        let h = `<p class="text-muted mb-4">${d.total} rows (page ${d.page})</p><div class="table-wrapper"><table><thead><tr>`;
        d.columns.forEach(col => { h += `<th>${col}</th>` });
        h += `</tr></thead><tbody>`;
        d.rows.forEach(row => { h += `<tr>`; d.columns.forEach(col => { h += `<td>${safe(row[col])}</td>` }); h += `</tr>` });
        h += `</tbody></table></div>`;
        c.innerHTML = h;
        renderPagination('dataset-pagination', d.page, Math.ceil(d.total / d.per_page), loadDataset);
    } catch (e) { c.innerHTML = `<div class="empty-state"><p>Server error</p></div>` }
}

// ═══ BATCH ═══
function parseBatchCodes() { return document.getElementById('batch-codes-input').value.split(/[\n,;]+/).map(c => c.trim()).filter(c => c.length >= 4) }
async function doBatchSearch() {
    const codes = parseBatchCodes(); if (!codes.length) return showToast("Enter site codes", "error");
    document.getElementById('batch-count').textContent = `Processing ${codes.length}...`;
    const c = document.getElementById('batch-results'); c.innerHTML = renderSkeletonBlock(3);
    try {
        const r = await fetch('/api/batch/search', { method: 'POST', headers: getCsrfHeaders(), credentials: 'include', body: JSON.stringify({ codes }) });
        const d = await r.json();
        if (!r.ok) { c.innerHTML = `<div class="empty-state"><p>${d.error}</p></div>`; return }
        document.getElementById('batch-count').textContent = `${d.count} sites analyzed`;
        let h = `<div class="sites-cards-grid">`;
        d.results.forEach(site => {
            if (!site.site_code) return;
            h += `<div class="site-mini-card glass-panel" onclick="quickLookup('${site.site_code}')">
                <div class="site-mini-code">${site.site_code}</div><div class="site-mini-bands">`;
            (site.config_bands || []).forEach(b => {
                h += `<div class="mini-band"><span class="mini-dot" style="background:${b.color}"></span>${b.band}: <strong>${b.config_str}</strong></div>`;
            });
            h += `</div></div>`;
        });
        h += `</div>`; c.innerHTML = h;
    } catch (e) { c.innerHTML = `<div class="empty-state"><p>Server error</p></div>` }
}
async function doBatchExport() {
    const codes = parseBatchCodes(); if (!codes.length) return showToast("Enter site codes", "error");
    showToast(`Generating Excel for ${codes.length} sites...`, "info", 5000);
    try {
        const r = await fetch('/api/batch/export', { method: 'POST', headers: getCsrfHeaders(), credentials: 'include', body: JSON.stringify({ codes }) });
        if (r.ok) {
            const arrayBuf = await r.arrayBuffer();
            const blob = new Blob([arrayBuf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Djezzy_BSS_Report_${codes.length}_sites.xlsx`;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 200);
            showToast("Report downloaded!", "success");
        }
        else { const d = await r.json(); showToast(d.error || "Export failed", "error") }
    } catch (e) { showToast("Export error", "error") }
}

// ═══ ADMIN ═══
async function triggerReload() {
    try {
        const r = await fetch('/api/admin/reload', { method: 'POST', headers: getCsrfHeaders(), credentials: 'include' });
        const d = await r.json(); showToast(d.message || d.error || "Error", r.ok ? "success" : "error")
    } catch (e) { showToast("Error", "error") }
}
async function uploadDataset() {
    const key = document.getElementById('upload-dataset-select').value;
    const fi = document.getElementById('upload-file-input');
    if (!key) return showToast("Select a category", "error");
    if (!fi.files?.length) return showToast("Select file(s)", "error");
    const fd = new FormData();
    for (let i = 0; i < fi.files.length; i++) fd.append('file', fi.files[i]);
    fd.append('dataset', key);
    showToast(`Uploading ${fi.files.length} file(s)...`, "info");
    try {
        const r = await fetch('/api/admin/upload', { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() }, credentials: 'include', body: fd });
        const d = await r.json(); showToast(d.message || d.error, r.ok ? "success" : "error");
        if (r.ok) { fi.value = ''; loadDashboard(); }
    } catch (e) { showToast("Upload error", "error") }
}

// ═══ PAGINATION ═══
function renderPagination(id, page, total, cb) {
    const c = document.getElementById(id); if (total <= 1) { c.innerHTML = ''; return }
    let h = '<div class="pagination-controls">';
    if (page > 1) h += `<button class="btn-page" onclick="window._pgCb(${page - 1})">← Prev</button>`;
    for (let i = Math.max(1, page - 2); i <= Math.min(total, page + 2); i++)
        h += `<button class="btn-page ${i === page ? 'active' : ''}" onclick="window._pgCb(${i})">${i}</button>`;
    if (page < total) h += `<button class="btn-page" onclick="window._pgCb(${page + 1})">Next →</button>`;
    h += `<span class="page-info">Page ${page}/${total}</span></div>`;
    c.innerHTML = h; window._pgCb = cb;
}

// ═══ USER MANAGEMENT ═══
async function loadUsersList() {
    try {
        const r = await fetch('/api/admin/users', { credentials: 'include' });
        if (!r.ok) return;
        const d = await r.json();
        const list = document.getElementById('users-list');
        const sel = document.getElementById('chg-user-select');
        if (!list) return;

        // Populate users list
        let h = '<div class="users-table"><table><thead><tr><th>Username</th><th>Role</th><th>Actions</th></tr></thead><tbody>';
        (d.users || []).forEach(u => {
            h += `<tr><td><strong>${u.username}</strong></td>
                <td><span class="badge-role ${u.role === 'admin' ? 'role-admin' : 'role-user'}">${u.role}</span></td>
                <td><button class="btn-link" onclick="deleteUserAccount('${u.username}')">Delete</button></td></tr>`;
        });
        h += '</tbody></table></div>';
        list.innerHTML = h;

        // Populate password change dropdown
        if (sel) {
            sel.innerHTML = '<option value="">-- User --</option>';
            (d.users || []).forEach(u => { sel.innerHTML += `<option value="${u.username}">${u.username}</option>` });
        }
    } catch (e) { console.error("Failed to load users", e) }
}

async function createUser() {
    const username = document.getElementById('new-username').value.trim();
    const password = document.getElementById('new-password').value;
    const role = document.getElementById('new-role').value;
    if (!username || !password) return showToast("Enter username and password", "error");
    try {
        const r = await fetch('/api/admin/users', {
            method: 'POST', headers: getCsrfHeaders(), credentials: 'include',
            body: JSON.stringify({ username, password, role })
        });
        const d = await r.json();
        showToast(d.message || d.error, r.ok ? "success" : "error");
        if (r.ok) {
            document.getElementById('new-username').value = '';
            document.getElementById('new-password').value = '';
            loadUsersList();
        }
    } catch (e) { showToast("Error", "error") }
}

async function changePassword() {
    const username = document.getElementById('chg-user-select').value;
    const password = document.getElementById('chg-new-password').value;
    if (!username) return showToast("Select a user", "error");
    if (!password) return showToast("Enter new password", "error");
    try {
        const r = await fetch('/api/admin/users/password', {
            method: 'POST', headers: getCsrfHeaders(), credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        const d = await r.json();
        showToast(d.message || d.error, r.ok ? "success" : "error");
        if (r.ok) document.getElementById('chg-new-password').value = '';
    } catch (e) { showToast("Error", "error") }
}

async function deleteUserAccount(username) {
    if (!confirm(`Delete user "${username}"?`)) return;
    try {
        const r = await fetch('/api/admin/users/delete', {
            method: 'POST', headers: getCsrfHeaders(), credentials: 'include',
            body: JSON.stringify({ username })
        });
        const d = await r.json();
        showToast(d.message || d.error, r.ok ? "success" : "error");
        if (r.ok) loadUsersList();
    } catch (e) { showToast("Error", "error") }
}

// ═══════════════════════════════════════════════════════
//  EXPERT MODULES — 7 NEW FEATURES (ADDITIVE)
// ═══════════════════════════════════════════════════════

const WILAYA_NAMES = {
    "01": "Adrar", "02": "Chlef", "03": "Laghouat", "04": "Oum El Bouaghi", "05": "Batna",
    "06": "Béjaïa", "07": "Biskra", "08": "Béchar", "09": "Blida", "10": "Bouira",
    "11": "Tamanrasset", "12": "Tébessa", "13": "Tlemcen", "14": "Tiaret", "15": "Tizi Ouzou",
    "16": "Alger", "17": "Djelfa", "18": "Jijel", "19": "Sétif", "20": "Saïda",
    "21": "Skikda", "22": "Sidi Bel Abbès", "23": "Annaba", "24": "Guelma", "25": "Constantine",
    "26": "Médéa", "27": "Mostaganem", "28": "M'Sila", "29": "Mascara", "30": "Ouargla",
    "31": "Oran", "32": "El Bayadh", "33": "Illizi", "34": "Bordj Bou Arréridj", "35": "Boumerdès",
    "36": "El Tarf", "37": "Tindouf", "38": "Tissemsilt", "39": "El Oued", "40": "Khenchela",
    "41": "Souk Ahras", "42": "Tipaza", "43": "Mila", "44": "Aïn Defla", "45": "Naâma",
    "46": "Aïn Témouchent", "47": "Ghardaïa", "48": "Relizane",
    "49": "El M'Ghair", "50": "El Meniaa", "51": "Ouled Djellal", "52": "Bordj Badji Mokhtar",
    "53": "Béni Abbès", "54": "Timimoun", "55": "Touggourt", "56": "Djanet",
    "57": "In Salah", "58": "In Guezzam"
};

let heatmapData = null;

// ═══ 1. TOPOLOGY GRAPH ═══
let _topoNetwork = null, _topoData = null, _topoAllNodes = null, _topoAllEdges = null;
const HEALTH_COLORS = { healthy: '#10B981', warning: '#F59E0B', critical: '#EF4444' };

async function loadTopology() {
    const center = document.getElementById('topo-center-input').value.trim();
    const container = document.getElementById('topo-container');
    container.innerHTML = '<div class="empty-state"><p>Loading topology...</p></div>';
    document.getElementById('topo-info').style.display = 'none';
    try {
        const url = center ? `/api/topology?center=${encodeURIComponent(center)}` : '/api/topology';
        const r = await fetch(url, { credentials: 'include' });
        const d = await r.json();
        _topoData = d;
        if (!d.nodes?.length) { container.innerHTML = '<div class="empty-state"><p>No topology data found</p></div>'; return; }

        // Stats bar
        const statsBar = document.getElementById('topo-stats');
        if (statsBar && d.summary) {
            statsBar.style.display = 'block';
            document.getElementById('topo-stat-healthy').textContent = d.summary.healthy_nodes;
            document.getElementById('topo-stat-warning').textContent = d.summary.warning_nodes;
            document.getElementById('topo-stat-critical').textContent = d.summary.critical_nodes;
            document.getElementById('topo-stat-links').textContent = d.summary.total_edges;
            document.getElementById('topo-stat-faults').textContent = d.summary.total_faults;
        }

        // Build nodes with health-based colors
        _topoAllNodes = new vis.DataSet(d.nodes.map(n => {
            const isCenter = n.id === center?.toUpperCase();
            const hColor = HEALTH_COLORS[n.health] || '#3B82F6';
            return {
                id: n.id, label: n.label,
                color: {
                    background: isCenter ? '#E11326' : hColor, border: isCenter ? '#FFF' : '#333',
                    highlight: { background: '#FFF', border: hColor }
                },
                font: { color: '#FFF', size: isCenter ? 13 : 10, bold: isCenter },
                shape: 'dot', size: isCenter ? 22 : (n.health === 'critical' ? 14 : (n.health === 'warning' ? 12 : 10)),
                title: `${n.id} | ${n.tech} | ${n.total_links} links, ${n.fault_count} faults`,
                _health: n.health, _faultCount: n.fault_count, _totalLinks: n.total_links, _tech: n.tech
            };
        }));

        // Build edges with fault highlighting
        _topoAllEdges = new vis.DataSet(d.edges.map((e, i) => ({
            id: i, from: e.from, to: e.to,
            color: { color: e.status === 'ok' ? '#10B981' : '#EF4444', opacity: e.status === 'ok' ? 0.4 : 0.9 },
            width: e.status === 'ok' ? 1 : 2.5,
            dashes: e.status === 'fault',
            title: `${e.from} ↔ ${e.to} | X2: ${e.x2_status} | SCTP: ${e.sctp_status}`,
            _status: e.status, _x2: e.x2_status, _sctp: e.sctp_status, _tech: e.tech
        })));

        container.innerHTML = '';
        _topoNetwork = new vis.Network(container, { nodes: _topoAllNodes, edges: _topoAllEdges }, {
            physics: { barnesHut: { gravitationalConstant: -4000, springLength: 100, damping: 0.3 }, stabilization: { iterations: 80 } },
            interaction: { hover: true, tooltipDelay: 200 },
            nodes: { borderWidth: 2, borderWidthSelected: 3 },
            edges: { smooth: { type: 'continuous' } }
        });

        // Click handler — detailed info panel
        const info = document.getElementById('topo-info');
        _topoNetwork.on('click', params => {
            if (params.nodes.length) {
                const nid = params.nodes[0];
                const nd = d.nodes.find(n => n.id === nid);
                const conns = d.edges.filter(e => e.from === nid || e.to === nid);
                const okCount = conns.filter(e => e.status === 'ok').length;
                const faultCount = conns.length - okCount;
                const hBadge = nd.health === 'healthy' ? '🟢' : (nd.health === 'warning' ? '🟡' : '🔴');
                let faultList = '';
                if (faultCount > 0) {
                    const faultEdges = conns.filter(e => e.status === 'fault');
                    faultList = '<div style="margin-top:.5rem;font-size:.8rem"><strong>Faulty links:</strong><ul style="margin:.25rem 0;padding-left:1.2rem">' +
                        faultEdges.map(e => {
                            const peer = e.from === nid ? e.to : e.from;
                            return `<li>${peer} — X2: ${e.x2_status}, SCTP: ${e.sctp_status}</li>`;
                        }).join('') + '</ul></div>';
                }
                info.style.display = 'block';
                info.innerHTML = `<div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">
                    <span style="font-size:1.1rem">${hBadge} <strong>${nid}</strong></span>
                    <span style="font-size:.8rem;color:#999">${nd.tech}</span>
                    <span style="margin-left:auto;font-size:.85rem">X2 Links: <strong>${conns.length}</strong> &nbsp;|&nbsp;
                    ✅ ${okCount} healthy &nbsp;|&nbsp; ❌ ${faultCount} faulty</span>
                </div>${faultList}`;
            } else { info.style.display = 'none'; }
        });

        // Reset fault filter checkbox
        const cb = document.getElementById('topo-faults-only');
        if (cb) cb.checked = false;

        showToast(`Loaded ${d.nodes.length} sites, ${d.edges.length} links (${d.summary?.total_faults || 0} faults)`, 'success');
    } catch (e) { container.innerHTML = '<div class="empty-state"><p>Error loading topology</p></div>'; }
}

function filterTopoFaults() {
    if (!_topoNetwork || !_topoData) return;
    const faultsOnly = document.getElementById('topo-faults-only')?.checked;
    if (faultsOnly) {
        // Show only nodes involved in faults and fault edges
        const faultNodeIds = new Set();
        _topoData.edges.forEach(e => { if (e.status === 'fault') { faultNodeIds.add(e.from); faultNodeIds.add(e.to); } });
        _topoAllNodes.forEach(n => { _topoAllNodes.update({ id: n.id, hidden: !faultNodeIds.has(n.id) }); });
        _topoAllEdges.forEach(e => { _topoAllEdges.update({ id: e.id, hidden: e._status === 'ok' }); });
    } else {
        _topoAllNodes.forEach(n => { _topoAllNodes.update({ id: n.id, hidden: false }); });
        _topoAllEdges.forEach(e => { _topoAllEdges.update({ id: e.id, hidden: false }); });
    }
}

// ═══ 2. SITE COMPARISON ═══
async function doCompare() {
    const codes = [
        document.getElementById('cmp-site-1').value.trim(),
        document.getElementById('cmp-site-2').value.trim(),
        document.getElementById('cmp-site-3').value.trim()
    ].filter(Boolean);
    if (codes.length < 2) return showToast('Enter at least 2 site codes', 'error');
    const c = document.getElementById('compare-results');
    c.innerHTML = renderSkeletonBlock(3);
    try {
        const r = await fetch('/api/compare', {
            method: 'POST', headers: getCsrfHeaders(), credentials: 'include',
            body: JSON.stringify({ codes })
        });
        const d = await r.json();
        if (!d.sites?.length) { c.innerHTML = '<div class="empty-state"><p>No data</p></div>'; return; }

        const sites = d.sites;
        const rows = [
            { label: 'Technologies', key: 'technologies', fmt: v => v.join(', ') },
            { label: 'Bands', key: 'bands', fmt: v => v.join(', ') },
            { label: 'Total Cells', key: 'total_cells', fmt: v => v },
            { label: 'Equipment Count', key: 'equipment_count', fmt: v => v },
            { label: 'NSA Anchors', key: 'nsa_anchor_count', fmt: v => v },
            { label: 'X2 Neighbors', key: 'x2_neighbor_count', fmt: v => v },
            { label: 'RRU Models', key: 'rru_models', fmt: v => v.join(', ') || '-' },
            { label: 'HW Platforms', key: 'hardware_platforms', fmt: v => Object.entries(v).map(([k, v2]) => `${k}:${v2}`).join(', ') || '-' },
            { label: 'SW Versions', key: 'hardware_versions', fmt: v => Object.entries(v).map(([k, v2]) => `${k}:${v2}`).join(', ') || '-' },
        ];

        let h = `<div class="glass-panel data-section fade-in"><div class="table-wrapper"><table><thead><tr><th>Attribute</th>`;
        sites.forEach(s => { h += `<th style="color:#E11326">${s.site_code}</th>`; });
        h += `</tr></thead><tbody>`;
        rows.forEach(row => {
            h += `<tr><td><strong>${row.label}</strong></td>`;
            const vals = sites.map(s => row.fmt(s[row.key]));
            const allSame = vals.every(v => JSON.stringify(v) === JSON.stringify(vals[0]));
            vals.forEach(v => {
                const cls = allSame ? 'cmp-match' : 'cmp-diff';
                h += `<td class="${cls}">${safe(v)}</td>`;
            });
            h += `</tr>`;
        });
        // Config bands comparison
        h += `<tr><td><strong>Config Bands</strong></td>`;
        sites.forEach(s => {
            h += `<td>${(s.config_bands || []).map(b => `<span class="band-chip-sm" style="--chip-color:${b.color}">${b.band} ${b.sectors.join('/')}</span>`).join(' ')}</td>`;
        });
        h += `</tr>`;
        h += `</tbody></table></div></div>`;
        c.innerHTML = h;
    } catch (e) { c.innerHTML = '<div class="empty-state"><p>Error</p></div>'; }
}

// ═══ 3. WILAYA HEATMAP ═══
async function loadHeatmap() {
    try {
        const r = await fetch('/api/heatmap/wilaya', { credentials: 'include' });
        heatmapData = await r.json();
        renderHeatmapGrid();
    } catch (e) { console.error('Heatmap error', e); }
}

function renderHeatmapGrid() {
    if (!heatmapData) return;
    const metric = document.getElementById('heatmap-metric').value;
    const grid = document.getElementById('heatmap-grid');
    const vals = Object.values(heatmapData).map(w => w[metric] || 0);
    const max = Math.max(...vals, 1);

    let h = '';
    for (let i = 1; i <= 58; i++) {
        const code = String(i).padStart(2, '0');
        const name = WILAYA_NAMES[code] || `W${code}`;
        const data = heatmapData[code] || {};
        const val = data[metric] || 0;
        const pct = val / max;
        const hue = 120 * pct; // 0=red, 60=yellow, 120=green
        const bg = `hsla(${hue}, 70%, 40%, ${0.3 + pct * 0.6})`;
        h += `<div class="heatmap-cell" style="background:${bg}" title="${name}: ${val}">
            <div class="heatmap-code">${code}</div>
            <div class="heatmap-name">${name}</div>
            <div class="heatmap-val">${val.toLocaleString()}</div>
        </div>`;
    }
    grid.innerHTML = h;
}

// ═══ 4. NETWORK AUDIT ═══
async function runAudit() {
    const btn = document.getElementById('btn-run-audit');
    btn.disabled = true; btn.textContent = '⏳ Scanning...';
    const c = document.getElementById('audit-results');
    c.innerHTML = renderSkeletonBlock(5);
    try {
        const r = await fetch('/api/audit', { credentials: 'include' });
        const d = await r.json();
        const s = d.summary;

        let h = `<div class="stats-cards">
            <div class="stat-card glass-panel" style="--accent:#EF4444"><div class="stat-value">${s.faulty_x2_count}</div><div class="stat-label">Faulty X2</div></div>
            <div class="stat-card glass-panel" style="--accent:#F59E0B"><div class="stat-value">${s.faulty_s1_count}</div><div class="stat-label">Faulty S1</div></div>
            <div class="stat-card glass-panel" style="--accent:#8B5CF6"><div class="stat-value">${s.missing_nsa_count}</div><div class="stat-label">Missing NSA</div></div>
            <div class="stat-card glass-panel" style="--accent:#3B82F6"><div class="stat-value">${s.old_firmware_count}</div><div class="stat-label">Old Firmware</div></div>
            <div class="stat-card glass-panel" style="--accent:#EC4899"><div class="stat-value">${s.cpri_saturation_count}</div><div class="stat-label">CPRI >80%</div></div>
        </div>`;

        // Faulty X2
        if (d.faulty_x2?.length) {
            h += `<div class="data-section glass-panel mt-2"><div class="section-heading" style="border-left:4px solid #EF4444"><h4>⚠ Faulty X2 Interfaces <span class="count-chip">${d.faulty_x2.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr><th>Site</th><th>Peer</th><th>Tech</th><th>X2 Status</th><th>SCTP</th></tr></thead><tbody>`;
            d.faulty_x2.slice(0, 50).forEach(x => {
                h += `<tr><td><strong>${x.site}</strong></td><td>${x.peer}</td><td>${x.tech}</td><td><span class="expert-badge expert-err">${x.x2_status}</span></td><td><span class="expert-badge expert-err">${x.sctp_status}</span></td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        // Missing NSA
        if (d.missing_nsa?.length) {
            h += `<div class="data-section glass-panel mt-2"><div class="section-heading" style="border-left:4px solid #8B5CF6"><h4>🔗 4G Sites Missing NSA Anchor <span class="count-chip">${d.missing_nsa.length}</span></h4></div>
            <div style="padding:1rem;display:flex;flex-wrap:wrap;gap:.4rem">`;
            d.missing_nsa.forEach(s => { h += `<span class="expert-badge expert-na">${s}</span>`; });
            h += `</div></div>`;
        }

        // Old firmware
        if (d.old_firmware?.length) {
            h += `<div class="data-section glass-panel mt-2"><div class="section-heading" style="border-left:4px solid #3B82F6"><h4>📦 Old Firmware <span class="count-chip">${d.old_firmware.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr><th>Site</th><th>Tech</th><th>Current Version</th><th>Latest Version</th></tr></thead><tbody>`;
            d.old_firmware.slice(0, 50).forEach(f => {
                h += `<tr><td><strong>${f.site}</strong></td><td>${f.tech}</td><td><span class="expert-badge expert-err">${f.current}</span></td><td><span class="expert-badge expert-ok">${f.latest}</span></td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        // CPRI saturation
        if (d.cpri_saturation?.length) {
            h += `<div class="data-section glass-panel mt-2"><div class="section-heading" style="border-left:4px solid #EC4899"><h4>🔥 CPRI Saturation >80% <span class="count-chip">${d.cpri_saturation.length}</span></h4></div>
            <div class="table-wrapper"><table><thead><tr><th>Site</th><th>Tech</th><th>Port</th><th>Utilization</th></tr></thead><tbody>`;
            d.cpri_saturation.forEach(cp => {
                const barColor = cp.utilization_pct > 90 ? '#EF4444' : '#F59E0B';
                h += `<tr><td><strong>${cp.site}</strong></td><td>${cp.tech}</td><td>${cp.port}</td>
                    <td><div class="expert-util-bar"><div class="expert-util-fill" style="width:${Math.min(cp.utilization_pct, 100)}%;background:${barColor}"></div><span>${cp.utilization_pct}%</span></div></td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        c.innerHTML = h;
        showToast('Audit complete', 'success');
    } catch (e) { c.innerHTML = '<div class="empty-state"><p>Audit failed</p></div>'; }
    btn.disabled = false; btn.textContent = '🔍 Run Full Audit';
}

// ═══ 5. SMART FILTER ═══
function populateFilterDropdowns() {
    const sel = document.getElementById('flt-wilaya');
    if (sel.options.length <= 1) {
        for (let i = 1; i <= 58; i++) {
            const code = String(i).padStart(2, '0');
            const opt = document.createElement('option');
            opt.value = code; opt.textContent = `${code} - ${WILAYA_NAMES[code] || ''}`;
            sel.appendChild(opt);
        }
    }
}

async function doFilter() {
    const criteria = {
        wilaya: document.getElementById('flt-wilaya').value,
        technology: document.getElementById('flt-tech').value,
        platform: document.getElementById('flt-platform').value,
    };
    const c = document.getElementById('filter-results');
    c.innerHTML = renderSkeletonBlock(2);
    try {
        const r = await fetch('/api/filter', {
            method: 'POST', headers: getCsrfHeaders(), credentials: 'include',
            body: JSON.stringify(criteria)
        });
        const d = await r.json();
        let h = `<div class="glass-panel" style="padding:.75rem;margin-bottom:.5rem">
            <strong>${d.total}</strong> sites match your filters ${d.total > 200 ? '(showing first 200)' : ''}
        </div>`;
        if (d.sites?.length) {
            h += `<div class="filter-results-grid">`;
            d.sites.forEach(s => {
                h += `<div class="filter-site-card glass-panel" onclick="document.getElementById('site-search-input').value='${s.site_code}';document.querySelectorAll('[data-view]').forEach(n=>n.classList.remove('active'));document.querySelector('[data-view=site-lookup]').classList.add('active');document.querySelectorAll('.view').forEach(v=>v.classList.add('hidden'));document.getElementById('view-site-lookup').classList.remove('hidden');doSiteLookup()">
                    <div class="filter-site-code">${s.site_code}</div>
                    <div class="filter-site-wilaya">${WILAYA_NAMES[s.wilaya] || s.wilaya}</div>
                </div>`;
            });
            h += `</div>`;
        }
        c.innerHTML = h;
    } catch (e) { c.innerHTML = '<div class="empty-state"><p>Error</p></div>'; }
}

// ═══ 6. FREQUENCY PLAN ═══
async function loadFrequencyPlan() {
    const code = document.getElementById('freq-site-input').value.trim();
    if (!code) return showToast('Enter a site code', 'error');
    const c = document.getElementById('freq-results');
    c.innerHTML = renderSkeletonBlock(3);
    try {
        const r = await fetch(`/api/frequency?code=${encodeURIComponent(code)}`, { credentials: 'include' });
        const d = await r.json();
        let h = `<div class="glass-panel" style="padding:.75rem;margin-bottom:.5rem"><h3>Frequency Plan: <span style="color:#E11326">${d.site_code}</span></h3></div>`;

        // 2G Carriers
        if (d.carriers_2g?.length) {
            h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #3B82F6">
                <h4>2G Carriers <span class="count-chip">${d.carriers_2g.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr><th>Cell</th><th>BCCH Freq</th><th>TRX</th><th>Hopping</th><th>TSC</th><th>Power</th></tr></thead><tbody>`;
            d.carriers_2g.forEach(c2 => {
                h += `<tr><td>${c2.cell_name}</td><td><strong>${c2.bcch}</strong></td><td>${c2.trx}</td><td>${c2.hopping}</td><td>${c2.tsc}</td><td>${c2.power}</td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        // 3G Cells
        if (d.cells_3g?.length) {
            h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #8B5CF6">
                <h4>3G Cells <span class="count-chip">${d.cells_3g.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr><th>Cell</th><th>UL Freq</th><th>DL Freq</th><th>Max Power</th><th>HSDPA</th><th>HSUPA</th><th>LAC</th></tr></thead><tbody>`;
            d.cells_3g.forEach(c3 => {
                h += `<tr><td>${c3.cell_name}</td><td>${c3.ul_freq}</td><td><strong>${c3.dl_freq}</strong></td><td>${c3.max_power}</td><td>${c3.hsdpa}</td><td>${c3.hsupa}</td><td>${c3.lac}</td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        // 4G Cells
        if (d.cells_4g?.length) {
            h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #F59E0B">
                <h4>4G Cells <span class="count-chip">${d.cells_4g.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr><th>Cell</th><th>Band</th><th>TAC</th><th>PCI</th><th>Status</th><th>Admin</th></tr></thead><tbody>`;
            d.cells_4g.forEach(c4 => {
                h += `<tr><td>${c4.cell_name}</td><td><strong>${c4.band}</strong></td><td>${c4.tac}</td><td>${c4.pci}</td><td>${c4.status}</td><td>${c4.admin}</td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        // 5G Cells
        if (d.cells_5g?.length) {
            h += `<div class="data-section glass-panel fade-in"><div class="section-heading" style="border-left:4px solid #10B981">
                <h4>5G Cells <span class="count-chip">${d.cells_5g.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr><th>Cell</th><th>Band</th><th>TAC</th><th>PCI</th><th>Status</th><th>Admin</th></tr></thead><tbody>`;
            d.cells_5g.forEach(c5 => {
                h += `<tr><td>${c5.cell_name}</td><td><strong>${c5.band}</strong></td><td>${c5.tac}</td><td>${c5.pci}</td><td>${c5.status}</td><td>${c5.admin}</td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        if (!d.carriers_2g?.length && !d.cells_3g?.length && !d.cells_4g?.length && !d.cells_5g?.length) {
            h += '<div class="empty-state"><p>No frequency data for this site</p></div>';
        }
        c.innerHTML = h;
    } catch (e) { c.innerHTML = '<div class="empty-state"><p>Error</p></div>'; }
}

// ═══ 7. EQUIPMENT LIFECYCLE ═══
async function loadLifecycle() {
    const btn = document.getElementById('btn-lifecycle');
    btn.disabled = true; btn.textContent = '⏳ Analyzing...';
    const c = document.getElementById('lifecycle-results');
    c.innerHTML = renderSkeletonBlock(3);
    try {
        const r = await fetch('/api/lifecycle', { credentials: 'include' });
        const d = await r.json();

        let h = `<div class="glass-panel" style="padding:.75rem;margin-bottom:.5rem">
            <strong>${(d.total_equipment || 0).toLocaleString()}</strong> equipment items analyzed
        </div>`;

        // Age distribution chart
        const ageDist = d.age_distribution || {};
        h += `<div class="glass-panel chart-card" style="margin-bottom:1rem"><h4>Age Distribution</h4><canvas id="chart-lifecycle"></canvas></div>`;

        // Type breakdown
        if (d.type_breakdown && Object.keys(d.type_breakdown).length) {
            h += `<div class="data-section glass-panel"><div class="section-heading" style="border-left:4px solid #06B6D4"><h4>Age by Equipment Type</h4></div>
                <div class="table-wrapper"><table><thead><tr><th>Type</th><th>&lt;1yr</th><th>1-3yr</th><th>3-5yr</th><th>5-7yr</th><th>&gt;7yr</th></tr></thead><tbody>`;
            for (const [type, ages] of Object.entries(d.type_breakdown)) {
                h += `<tr><td><strong>${type}</strong></td>
                    <td style="color:#10B981">${ages['<1yr'] || 0}</td>
                    <td style="color:#3B82F6">${ages['1-3yr'] || 0}</td>
                    <td style="color:#F59E0B">${ages['3-5yr'] || 0}</td>
                    <td style="color:#F97316">${ages['5-7yr'] || 0}</td>
                    <td style="color:#EF4444;font-weight:700">${ages['>7yr'] || 0}</td></tr>`;
            }
            h += `</tbody></table></div></div>`;
        }

        // Aging equipment list
        if (d.aging_equipment?.length) {
            h += `<div class="data-section glass-panel mt-2"><div class="section-heading" style="border-left:4px solid #EF4444">
                <h4>🔴 Aging Equipment (>7 Years) <span class="count-chip">${d.aging_equipment.length}</span></h4></div>
                <div class="table-wrapper"><table><thead><tr><th>Site</th><th>Equipment</th><th>Type</th><th>Manufactured</th><th>Age</th></tr></thead><tbody>`;
            d.aging_equipment.slice(0, 50).forEach(eq => {
                h += `<tr><td><strong>${eq.site}</strong></td><td>${eq.equipment}</td><td>${eq.type}</td>
                    <td>${eq.manufactured}</td><td><span class="expert-badge expert-err">${eq.age_years}yr</span></td></tr>`;
            });
            h += `</tbody></table></div></div>`;
        }

        c.innerHTML = h;

        // Render chart after DOM insert
        setTimeout(() => {
            renderChart('chart-lifecycle', 'bar',
                Object.keys(ageDist), Object.values(ageDist),
                ['#10B981', '#3B82F6', '#F59E0B', '#F97316', '#EF4444', '#64748B']);
        }, 100);

        showToast('Lifecycle analysis complete', 'success');
    } catch (e) { c.innerHTML = '<div class="empty-state"><p>Error</p></div>'; }
    btn.disabled = false; btn.textContent = '📊 Analyze Lifecycle';
}

// ═══ Auto-loading hooks for expert modules ═══
document.addEventListener('DOMContentLoaded', () => {
    // View switch hooks
    document.querySelectorAll('[data-view]').forEach(el => {
        el.addEventListener('click', () => {
            const view = el.dataset.view;
            if (view === 'heatmap-view' && !heatmapData) loadHeatmap();
            if (view === 'filter-view') populateFilterDropdowns();
        });
    });
});
