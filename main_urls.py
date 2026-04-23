// ── RAW DATA ──────────────────────────────────────────────────────────────────
const CLIENTS = [
    { id: 1, code: 'ACM', name: 'Acme Corp', country: 'PT' },
    { id: 2, code: 'BET', name: 'Beta Media', country: 'ES' },
    { id: 3, code: 'GAM', name: 'Gamma Ads', country: 'BR' },
    { id: 4, code: 'DEL', name: 'Delta Group', country: 'FR' },
    { id: 5, code: 'EPS', name: 'Epsilon Co', country: 'DE' },
    { id: 6, code: 'ZET', name: 'Zeta Brand', country: 'IT' },
    { id: 7, code: 'ETA', name: 'Eta Labs', country: 'NL' },
    { id: 8, code: 'THE', name: 'Theta Digital', country: 'PL' },
];
const COUNTRIES = ['PT', 'ES', 'BR', 'FR', 'DE', 'IT', 'PL', 'RO', 'CZ', 'NL', 'BE', 'AT'];
const PLATFORMS = [
    { id: 1, name: 'Google Ads', owner: 'Google LLC' },
    { id: 2, name: 'Meta Ads', owner: 'Meta Platforms' },
    { id: 3, name: 'TikTok Ads', owner: 'ByteDance' },
    { id: 4, name: 'Programmatic', owner: 'DV360' },
    { id: 5, name: 'Display Network', owner: 'Google LLC' },
    { id: 6, name: 'LinkedIn Ads', owner: 'Microsoft' },
    { id: 7, name: 'Taboola', owner: 'Taboola Inc' },
];
const CATEGORIES = ['Performance', 'Branding', 'Retargeting', 'Awareness', 'Conversion', 'Social'];
const CREATIVES = ['Video', 'Banner', 'Carrossel', 'Texto', 'Story', 'Native', 'Display'];
const DETAIL_TYPES = ['CPA Target', 'ROAS', 'Max Clicks', 'Max Conversões', 'CPM', 'CPV'];
const MONTHS = ['Jan 2025', 'Fev 2025', 'Mar 2025', 'Apr 2025', 'Mai 2025'];
const TEAMS = [
    { id: 1, ts_manager: 'A. Silva', ts_head: 'M. Costa', client_manager: 'P. Nunes', client_head: 'R. Sousa', fe: 'L. Ferreira', be: 'T. Alves', creative: 'C. Dias', qa: 'J. Santos', pm: 'I. Rodrigues' },
    { id: 2, ts_manager: 'A. Silva', ts_head: 'M. Costa', client_manager: 'F. Lima', client_head: 'R. Sousa', fe: 'B. Pinto', be: 'G. Lopes', creative: 'S. Cruz', qa: 'J. Santos', pm: 'I. Rodrigues' },
    { id: 3, ts_manager: 'K. Mendes', ts_head: 'M. Costa', client_manager: 'P. Nunes', client_head: 'V. Carvalho', fe: 'L. Ferreira', be: 'T. Alves', creative: 'C. Dias', qa: 'H. Mota', pm: 'I. Rodrigues' },
    { id: 4, ts_manager: 'K. Mendes', ts_head: 'D. Araújo', client_manager: 'F. Lima', client_head: 'V. Carvalho', fe: 'N. Gomes', be: 'G. Lopes', creative: 'S. Cruz', qa: 'H. Mota', pm: 'O. Faria' },
    { id: 5, ts_manager: 'A. Silva', ts_head: 'D. Araújo', client_manager: 'P. Nunes', client_head: 'V. Carvalho', fe: 'N. Gomes', be: 'T. Alves', creative: 'C. Dias', qa: 'J. Santos', pm: 'O. Faria' },
];

// ── CAMPAIGN GENERATION ───────────────────────────────────────────────────────
const CAMPAIGNS = Array.from({ length: 142 }, (_, i) => {
    const s = n => (((i * 13 + n * 7) * 9301 + 49297) % 233280) / 233280;
    const cost = Math.floor(s(1) * 79000 + 1000);
    const rev = +(cost * (s(2) * 4 + 1.5)).toFixed(2);
    const margin = +(rev - cost).toFixed(2);
    const roi = +(rev / cost).toFixed(3);
    const conv = Math.floor(s(4) * 3970 + 30);
    const cpa = +(cost / conv).toFixed(4);
    const cl = CLIENTS[Math.floor(s(5) * CLIENTS.length)];
    const pl = PLATFORMS[Math.floor(s(6) * PLATFORMS.length)];
    const c_conv = Math.floor(conv * (s(7) * 0.3 + 0.85));
    const c_rev = +(rev * (s(8) * 0.3 + 0.85)).toFixed(2);
    const v_conv = conv - c_conv;
    const v_rev = +(rev - c_rev).toFixed(2);
    const vcp = +((v_conv / c_conv) * 100).toFixed(4);
    const vrp = +((v_rev / c_rev) * 100).toFixed(4);
    return {
        id: 1000 + i,
        month: MONTHS[Math.floor(s(9) * MONTHS.length)],
        client: cl.name, client_code: cl.code,
        country: COUNTRIES[Math.floor(s(10) * COUNTRIES.length)],
        platform: pl.name, platform_id: pl.id,
        category: CATEGORIES[Math.floor(s(11) * CATEGORIES.length)],
        creative: CREATIVES[Math.floor(s(12) * CREATIVES.length)],
        detail: DETAIL_TYPES[Math.floor(s(13) * DETAIL_TYPES.length)],
        team_id: Math.floor(s(14) * TEAMS.length) + 1,
        client_camp: s(15) > 0.5 ? 1 : 0,
        invoice: s(16) > 0.3 ? 'INV-' + String(Math.floor(s(17) * 90000 + 10000)) : '—',
        cost_ts: +((cost * 1.08) + s(18) * 500).toFixed(4),
        cost_eur: cost, rev_eur: rev, margin_eur: margin, roi,
        conv, cpa,
        er_cpa: +(cpa * (1 + s(19) * 0.3)).toFixed(4),
        er_cost: +(cost * (1 + s(20) * 0.2)).toFixed(4),
        client_conv: c_conv, client_rev: c_rev,
        var_conv: v_conv, var_rev: v_rev,
        var_conv_pct: vcp, var_rev_pct: vrp,
        ok_conv: Math.abs(vcp) < 10 ? 'OK' : 'NOK',
        ok_rev: Math.abs(vrp) < 10 ? 'OK' : 'NOK',
    };
});

// ── HELPERS ───────────────────────────────────────────────────────────────────
const fmtEur = (n, compact = true) => {
    if (compact && Math.abs(n) >= 1e6) return '€' + (n / 1e6).toFixed(2) + 'M';
    if (compact && Math.abs(n) >= 1000) return '€' + (n / 1000).toFixed(1) + 'K';
    return '€' + n.toLocaleString('pt-PT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
const fmtN = n => n.toLocaleString('pt-PT');

const PLAT_COLOR = {
    'Google Ads': 't-blue', 'Meta Ads': 't-purple', 'TikTok Ads': 't-red',
    'Programmatic': 't-amber', 'Display Network': 't-teal', 'LinkedIn Ads': 't-blue', 'Taboola': 't-gray'
};
const CAT_COLOR = {
    'Performance': 't-green', 'Branding': 't-blue', 'Retargeting': 't-purple',
    'Awareness': 't-amber', 'Conversion': 't-teal', 'Social': 't-pink'
};
const AV_COLORS = ['#4ade80', '#60a5fa', '#a78bfa', '#fbbf24', '#f87171', '#5eead4', '#f9a8d4'];
function avatarColor(name) { let h = 0; for (const c of name) h = (h + c.charCodeAt(0)) % AV_COLORS.length; return AV_COLORS[h] }
function initials(name) { return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() }

// ── CHART MANAGER ─────────────────────────────────────────────────────────────
const _charts = {};
function mkChart(id, config) {
    if (_charts[id]) { _charts[id].destroy(); delete _charts[id] }
    _charts[id] = new Chart(document.getElementById(id), config);
    return _charts[id];
}

// ── PAGINATION ────────────────────────────────────────────────────────────────
function buildPager(state, panelEl, onPageChange) {
    const total = state.filtered.length;
    const pages = Math.ceil(total / state.perPage);
    const start = (state.page - 1) * state.perPage;
    const info = panelEl.querySelector('.pg-info');
    if (info) info.textContent = 'A mostrar ' + (start + 1) + '–' + Math.min(start + state.perPage, total) + ' de ' + total;
    const pbtns = panelEl.querySelector('.pbtns');
    if (!pbtns) return;
    const nums = [...new Set([1, state.page - 1, state.page, state.page + 1, pages].filter(p => p >= 1 && p <= pages))].sort((a, b) => a - b);
    let html = '<button class="pbtn" ' + (state.page === 1 ? 'disabled' : '') + ' onclick="(' + onPageChange + ')(' + (state.page - 1) + ')">← Prev</button>';
    let prev = 0;
    for (const p of nums) {
        if (prev && p - prev > 1) html += '<span style="color:var(--muted);padding:0 4px;font-size:11px">…</span>';
        html += '<button class="pbtn ' + (p === state.page ? 'active' : '') + '" onclick="(' + onPageChange + ')(' + p + ')">' + p + '</button>';
        prev = p;
    }
    html += '<button class="pbtn" ' + (state.page === pages ? 'disabled' : '') + ' onclick="(' + onPageChange + ')(' + (state.page + 1) + ')">Next →</button>';
    pbtns.innerHTML = html;
}

// ── MODAL ─────────────────────────────────────────────────────────────────────
function closeModal() {
    const c = document.getElementById('modal-container');
    if (c) c.innerHTML = '';
}
function showModal(html) {
    let c = document.getElementById('modal-container');
    if (!c) { c = document.createElement('div'); c.id = 'modal-container'; document.body.appendChild(c); }
    c.innerHTML = '<div class="modal-bg" onclick="this.isSameNode(event.target)&&closeModal()">' + html + '</div>';
}

function openCampModal(id) {
    const c = id ? CAMPAIGNS.find(x => x.id === id) : null;
    showModal('<div class="modal">'
        + '<button class="modal-close" onclick="closeModal()">×</button>'
        + '<div class="modal-title">' + (c ? 'Editar Campanha #' + c.id : 'Nova Campanha') + '</div>'
        + '<div class="form-grid">'
        + '<div class="form-field"><label class="flabel">Mês</label><select class="sel">' + MONTHS.map(m => '<option' + (c && c.month === m ? ' selected' : '') + '>' + m + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Cliente</label><select class="sel">' + CLIENTS.map(cl => '<option' + (c && c.client === cl.name ? ' selected' : '') + '>' + cl.name + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">País</label><select class="sel">' + COUNTRIES.map(co => '<option' + (c && c.country === co ? ' selected' : '') + '>' + co + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Plataforma</label><select class="sel">' + PLATFORMS.map(p => '<option' + (c && c.platform === p.name ? ' selected' : '') + '>' + p.name + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Categoria</label><select class="sel">' + CATEGORIES.map(cat => '<option' + (c && c.category === cat ? ' selected' : '') + '>' + cat + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Criativo</label><select class="sel">' + CREATIVES.map(cr => '<option' + (c && c.creative === cr ? ' selected' : '') + '>' + cr + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Tipo de Detalhe</label><select class="sel">' + DETAIL_TYPES.map(d => '<option' + (c && c.detail === d ? ' selected' : '') + '>' + d + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Equipa</label><select class="sel">' + TEAMS.map(t => '<option' + (c && c.team_id === t.id ? ' selected' : '') + '>Equipa T' + t.id + '</option>').join('') + '</select></div>'
        + '<div class="form-field"><label class="flabel">Invoice Google</label><input class="inp" type="text" value="' + (c ? c.invoice : '') + '" placeholder="INV-XXXXX"></div>'
        + '<div class="form-field"><label class="flabel">Campanha do Cliente</label><select class="sel"><option value="1"' + (c && c.client_camp ? ' selected' : '') + '>Sim</option><option value="0"' + (c && !c.client_camp ? ' selected' : '') + '>Não</option></select></div>'
        + '</div>'
        + '<div style="display:flex;gap:8px;margin-top:22px;justify-content:flex-end;">'
        + '<button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>'
        + '<button class="btn btn-primary" onclick="closeModal()">Guardar</button>'
        + '</div></div>');
}

function openCampDetail(id) {
    const c = CAMPAIGNS.find(x => x.id === id); if (!c) return;
    showModal('<div class="modal">'
        + '<button class="modal-close" onclick="closeModal()">×</button>'
        + '<div class="modal-title">Campanha #' + c.id + '</div>'
        + '<div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap;">'
        + '<span class="tag ' + (PLAT_COLOR[c.platform] || 't-gray') + '">' + c.platform + '</span>'
        + '<span class="tag ' + (CAT_COLOR[c.category] || 't-gray') + '">' + c.category + '</span>'
        + '<span class="tag t-gray">' + c.country + '</span>'
        + '<span class="tag t-gray">' + c.month + '</span></div>'
        + '<div class="form-grid" style="margin-bottom:20px;">'
        + kpiBox('Revenue EUR', fmtEur(c.rev_eur, false), 'color:var(--accent2)')
        + kpiBox('Custo EUR', fmtEur(c.cost_eur, false))
        + kpiBox('Margem EUR', fmtEur(c.margin_eur, false), c.margin_eur > 0 ? 'color:var(--accent2)' : 'color:var(--danger)')
        + kpiBox('ROI', c.roi.toFixed(3) + '×', c.roi >= 3 ? 'color:var(--accent2)' : 'color:var(--warning)')
        + '</div>'
        + '<div class="hlabel">Metrics</div>'
        + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0;margin-bottom:20px;">'
        + statRow('CPA', '€' + c.cpa.toFixed(2))
        + statRow('ER CPA', '€' + c.er_cpa.toFixed(2))
        + statRow('ER Custo', '€' + (c.er_cost / 1000).toFixed(1) + 'K')
        + statRow('Cost TS', '€' + (c.cost_ts / 1000).toFixed(1) + 'K')
        + statRow('Conversões', fmtN(c.conv))
        + statRow('Invoice', c.invoice)
        + '</div>'
        + '<div class="hlabel">Comparação</div>'
        + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0;">'
        + statRow('Conv. MAP', fmtN(c.conv))
        + statRow('Conv. Cliente', fmtN(c.client_conv))
        + statRow('Var. Conv.', (c.var_conv >= 0 ? '+' : '') + fmtN(c.var_conv))
        + statRow('Var. Conv. %', (c.var_conv_pct >= 0 ? '+' : '') + c.var_conv_pct.toFixed(2) + '%')
        + statRow('OK Conv.', '<span class="badge ' + (c.ok_conv === 'OK' ? 'b-ok' : 'b-nok') + '">' + c.ok_conv + '</span>')
        + statRow('OK Rev.', '<span class="badge ' + (c.ok_rev === 'OK' ? 'b-ok' : 'b-nok') + '">' + c.ok_rev + '</span>')
        + '</div>'
        + '<div style="display:flex;gap:8px;margin-top:22px;justify-content:flex-end;">'
        + '<button class="btn btn-ghost" onclick="closeModal()">Fechar</button>'
        + '<button class="btn btn-primary" onclick="closeModal();openCampModal(' + c.id + ')">Editar</button>'
        + '</div></div>');
}

function openClientModal(code) {
    const cl = code ? CLIENTS.find(c => c.code === code) : null;
    showModal('<div class="modal">'
        + '<button class="modal-close" onclick="closeModal()">×</button>'
        + '<div class="modal-title">' + (cl ? 'Editar ' + cl.name : 'Novo Cliente') + '</div>'
        + '<div class="form-grid">'
        + '<div class="form-field"><label class="flabel">Código</label><input class="inp" type="text" value="' + (cl ? cl.code : '') + '" placeholder="ABC"></div>'
        + '<div class="form-field"><label class="flabel">Nome</label><input class="inp" type="text" value="' + (cl ? cl.name : '') + '" placeholder="Nome da empresa"></div>'
        + '<div class="form-field"><label class="flabel">País Base</label><select class="sel">' + COUNTRIES.map(c => '<option' + (cl && cl.country === c ? ' selected' : '') + '>' + c + '</option>').join('') + '</select></div>'
        + '</div>'
        + '<div style="display:flex;gap:8px;margin-top:22px;justify-content:flex-end;">'
        + '<button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>'
        + '<button class="btn btn-primary" onclick="closeModal()">Guardar</button>'
        + '</div></div>');
}

function openTeamModal(id) {
    const t = id ? TEAMS.find(x => x.id === id) : null;
    const roles = [{ key: 'ts_manager', label: 'TS Manager' }, { key: 'ts_head', label: 'TS Head' }, { key: 'client_manager', label: 'Client Manager' }, { key: 'client_head', label: 'Client Head' }, { key: 'fe', label: 'Front-End' }, { key: 'be', label: 'Back-End' }, { key: 'creative', label: 'Creative' }, { key: 'qa', label: 'QA' }, { key: 'pm', label: 'PM' }];
    showModal('<div class="modal">'
        + '<button class="modal-close" onclick="closeModal()">×</button>'
        + '<div class="modal-title">' + (t ? 'Editar Equipa T' + t.id : 'Nova Equipa') + '</div>'
        + '<div class="form-grid">'
        + roles.map(r => '<div class="form-field"><label class="flabel">' + r.label + '</label><input class="inp" type="text" value="' + (t && t[r.key] ? t[r.key] : '') + '" placeholder="Nome…"></div>').join('')
        + '</div>'
        + '<div style="display:flex;gap:8px;margin-top:22px;justify-content:flex-end;">'
        + '<button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>'
        + '<button class="btn btn-primary" onclick="closeModal()">Guardar</button>'
        + '</div></div>');
}

function openPlatModal(id) {
    const p = id ? PLATFORMS.find(x => x.id === id) : null;
    showModal('<div class="modal">'
        + '<button class="modal-close" onclick="closeModal()">×</button>'
        + '<div class="modal-title">' + (p ? 'Editar ' + p.name : 'Nova Plataforma') + '</div>'
        + '<div class="form-grid">'
        + '<div class="form-field"><label class="flabel">Nome</label><input class="inp" type="text" value="' + (p ? p.name : '') + '" placeholder="Nome da plataforma"></div>'
        + '<div class="form-field"><label class="flabel">Proprietário</label><input class="inp" type="text" value="' + (p ? p.owner : '') + '" placeholder="Empresa proprietária"></div>'
        + '</div>'
        + '<div style="display:flex;gap:8px;margin-top:22px;justify-content:flex-end;">'
        + '<button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>'
        + '<button class="btn btn-primary" onclick="closeModal()">Guardar</button>'
        + '</div></div>');
}

// ── SMALL TEMPLATE HELPERS ────────────────────────────────────────────────────
function kpiBox(label, value, style) {
    return '<div style="background:var(--surface2);border-radius:var(--r);padding:14px;">'
        + '<div style="font-size:10px;color:var(--muted);margin-bottom:4px;">' + label + '</div>'
        + '<div style="font-family:var(--fm);font-size:20px;' + (style || '') + '">' + value + '</div>'
        + '</div>';
}
function statRow(label, value) {
    return '<div class="stat-row"><span style="color:var(--muted);font-size:11px;">' + label + '</span>'
        + '<span style="font-family:var(--fm);font-size:12px;">' + value + '</span></div>';
}

// ── NAV INIT ──────────────────────────────────────────────────────────────────
// Each page sets window.CURRENT_PAGE before loading this script (or after).
// Called at end of each page's own script.
function initNav() {
    const page = window.CURRENT_PAGE || '';
    document.querySelectorAll('.nav-item[data-page]').forEach(el => {
        el.classList.toggle('active', el.dataset.page === page);
    });
}

// ── SHARED TOPBAR CHART DEFAULTS ─────────────────────────────────────────────
const CHART_TOOLTIP = {
    backgroundColor: '#1a1e28',
    borderColor: 'rgba(255,255,255,.1)',
    borderWidth: 1,
    titleColor: '#e8eaf0',
    bodyColor: '#9ca3af',
    padding: 10,
};
const CHART_GRID = { color: 'rgba(255,255,255,.04)' };
const CHART_TICKS_X = { color: '#6b7280', font: { size: 11 } };
const CHART_TICKS_Y = { color: '#6b7280', font: { size: 10 } };

// ── THEME TOGGLE ──────────────────────────────────────────────────────────────
(function () {
    const saved = localStorage.getItem('map-theme') || 'dark';
    if (saved === 'light') document.documentElement.setAttribute('data-theme', 'light');
})();

function toggleTheme() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    if (isLight) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('map-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('map-theme', 'light');
    }
}