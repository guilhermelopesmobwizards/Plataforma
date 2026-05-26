/* =================================================================
   static/js/index.js
   Dashboard — all data comes from the Django API, no static values.
   ================================================================= */

const API_DASHBOARD = "/app/api/dashboard/";
const API_CAMPAIGNS = "/app/api/campaigns/";
const API_EXRATES = "/app/api/exchange-rates/";
const NC_URL = "/app/api/campaigns/create/";
const CHART_COLORS = ["#60faf2", "#c8f135", "#a78bfa", "#4ade80", "#f97316", "#f43f5e", "#38bdf8", "#facc15"];

let _byMonth = [];
let _byPlat = [];
let _chartMode = "revenue";
let _revChart = null;
let _platChart = null;
let _currentPage = 1;
let _totalPages = 1;
let _totalCount = 0;
let _searchQuery = "";
let _filterClient = "";
let _filterMonth = "";
let _rateMap = {};  // {year: {month: {currency: rate}}}

// ── Exchange rate helpers ─────────────────────────────────────────
const MONTH_NAMES = {Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};

function _parseMonthLabel(label) {
    if (!label) return {};
    const s = String(label).trim();
    // "Apr 2026"
    const mY = s.match(/^([A-Za-z]{3})\s+(\d{4})$/);
    if (mY && MONTH_NAMES[mY[1]]) return {year: parseInt(mY[2]), month: MONTH_NAMES[mY[1]]};
    // "2026-04" or "2026-04-01"
    const yM = s.match(/^(\d{4})-(\d{2})/);
    if (yM) return {year: parseInt(yM[1]), month: parseInt(yM[2])};
    return {};
}

function _toEur(amount, currency, monthLabel) {
    if (amount == null) return null;
    const val = parseFloat(amount);
    if (!currency || currency === "EUR") return val;
    const {year, month} = _parseMonthLabel(monthLabel);
    if (!year || !month) return null;
    const rate = (_rateMap[year] || {})[month]?.[currency];
    if (!rate) return null;
    return val / rate;
}

async function _loadExRates() {
    try {
        const res = await fetch(API_EXRATES);
        if (!res.ok) return;
        const data = await res.json();
        _rateMap = {};
        for (const r of (data.results || [])) {
            if (!_rateMap[r.year]) _rateMap[r.year] = {};
            if (!_rateMap[r.year][r.month]) _rateMap[r.year][r.month] = {};
            _rateMap[r.year][r.month][r.currency] = r.rate;
        }
    } catch (e) {
        console.error("Failed to load exchange rates:", e);
    }
}

// ── Formatters ────────────────────────────────────────────────────
function fmtEur(n) {
    if (n == null) return "—";
    n = parseFloat(n);
    const sign = n < 0 ? "-" : "";
    const abs = Math.abs(n);
    if (abs >= 1_000_000) return sign + "€ " + (abs / 1_000_000).toFixed(2) + "M";
    if (abs >= 1_000) return sign + "€ " + (abs / 1_000).toFixed(1) + "K";
    return sign + "€ " + abs.toFixed(2);
}
function fmtNum(n) { return n == null ? "—" : parseInt(n).toLocaleString(); }
function fmtRoi(n) { return n == null ? "—" : parseFloat(n).toFixed(2) + "×"; }

// ── KPIs ──────────────────────────────────────────────────────────
function renderKPIs(t) {
    document.getElementById("kpi-campaigns").textContent = fmtNum(t.total_campaigns);
    document.getElementById("kpi-conv").textContent = fmtNum(t.total_conv);
    document.getElementById("kpi-revenue").textContent = fmtEur(t.total_revenue);
    document.getElementById("kpi-margin").textContent = fmtEur(t.total_margin);
    document.getElementById("kpi-roi").textContent = fmtRoi(t.avg_roi);
}

// ── Bar chart ─────────────────────────────────────────────────────
function buildBarData(mode) {
    const labels = _byMonth.map(m => m.label || m.month_date);
    const cfgs = {
        revenue: { key: "revenue", color: "rgba(200,241,53,", label: "Revenue EUR" },
        cost: { key: "cost", color: "rgba(96,165,250,", label: "Cost EUR" },
        margin: { key: "margin", color: "rgba(74,222,128,", label: "Margin EUR" },
    };
    const cfg = cfgs[mode] || cfgs.revenue;
    return {
        labels,
        datasets: [{
            label: cfg.label,
            data: _byMonth.map(m => parseFloat(m[cfg.key]) || 0),
            backgroundColor: cfg.color + "0.18)",
            borderColor: cfg.color + "0.8)",
            borderWidth: 1.5, borderRadius: 4, borderSkipped: false,
        }]
    };
}

const barOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: "#1a1e28", borderColor: "rgba(255,255,255,0.1)", borderWidth: 1,
            titleColor: "#e8eaf0", bodyColor: "#9ca3af", padding: 10,
            callbacks: { label: ctx => " " + fmtEur(ctx.parsed.y) }
        }
    },
    scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", font: { size: 11 } } },
        y: {
            grid: { color: "rgba(255,255,255,0.04)" },
            ticks: {
                color: "#6b7280", font: { size: 10 },
                callback: v => v >= 1_000_000 ? (v / 1_000_000).toFixed(1) + "M" : "€" + Math.round(v / 1000) + "K"
            }
        }
    }
};

function renderBarChart() {
    if (_revChart) { _revChart.data = buildBarData(_chartMode); _revChart.update(); return; }
    _revChart = new Chart(document.getElementById("revChart"), { type: "bar", data: buildBarData(_chartMode), options: barOptions });
}

function switchChartTab(el, mode) {
    el.closest(".tabs").querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    el.classList.add("active");
    _chartMode = mode;
    renderBarChart();
}

// ── Donut chart ───────────────────────────────────────────────────
function renderPlatChart() {
    const valid = _byPlat.filter(p => p.platform_name && parseFloat(p.cost) > 0);
    const labels = valid.map(p => p.platform_name);
    const costs = valid.map(p => parseFloat(p.cost) || 0);
    const total = costs.reduce((a, b) => a + b, 0);

    if (_platChart) {
        _platChart.data.labels = labels;
        _platChart.data.datasets[0].data = costs;
        _platChart.data.datasets[0].backgroundColor = CHART_COLORS.slice(0, labels.length);
        _platChart.update();
    } else {
        _platChart = new Chart(document.getElementById("platChart"), {
            type: "doughnut",
            data: { labels, datasets: [{ data: costs, backgroundColor: CHART_COLORS.slice(0, labels.length), borderWidth: 0, hoverOffset: 4 }] },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: "72%",
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#1a1e28", borderColor: "rgba(255,255,255,0.1)", borderWidth: 1,
                        titleColor: "#e8eaf0", bodyColor: "#9ca3af", padding: 8,
                        callbacks: { label: ctx => ` ${ctx.label}: ${fmtEur(ctx.parsed)}` }
                    }
                }
            }
        });
    }

    const legend = document.getElementById("plat-legend");
    legend.innerHTML = valid.map((p, i) => {
        const pct = total > 0 ? ((parseFloat(p.cost) / total) * 100).toFixed(1) : "0";
        return `<div style="display:flex;align-items:center;justify-content:space-between;font-size:11px;">
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:8px;height:8px;border-radius:2px;background:${CHART_COLORS[i % CHART_COLORS.length]};display:inline-block;"></span>
            <span style="color:var(--muted)">${p.platform_name}</span>
        </span>
        <span style="font-family:var(--font-mono);">${pct}%</span>
    </div>`;
    }).join("");
}

// ── Table ─────────────────────────────────────────────────────────
function statusBadge(okConv, okRev) {
    if (okConv === "ok" && okRev === "ok") return `<span class="status-dot dot-green"></span>OK`;
    if (okConv === "not ok" || okRev === "not ok") return `<span class="status-dot dot-red"></span>Not OK`;
    return `<span class="status-dot dot-amber"></span>N/A`;
}

function renderTable(results, count, page, pages) {
    _totalCount = count; _totalPages = pages; _currentPage = page;
    const tbody = document.getElementById("table-body");

    if (!results.length) {
        tbody.innerHTML = `<tr><td colspan="12" style="text-align:center;padding:40px;color:var(--muted);">
            No data. Import an Excel file to get started.
        </td></tr>`;
        document.getElementById("table-info").textContent = "0 results";
        document.getElementById("table-sub").textContent = "0 campaigns";
        document.getElementById("pagination").innerHTML = "";
        return;
    }

    tbody.innerHTML = results.map(c => {
        const m = c.metric || {};
        const cp = c.comparison || {};
        const monthLabel = c.month || "";

        // Use stored EUR values; fall back to client-side conversion via _rateMap
        const costEur = m.cost_eur != null
            ? parseFloat(m.cost_eur)
            : _toEur(m.cost_ts, m.cost_ts_currency, monthLabel);
        const revEur = m.revenue_eur != null
            ? parseFloat(m.revenue_eur)
            : _toEur(m.revenue, m.revenue_currency, monthLabel);
        const margin = (revEur != null && costEur != null) ? revEur - costEur : null;
        const roi = m.roi != null
            ? parseFloat(m.roi)
            : (margin != null && costEur && costEur !== 0 ? margin / costEur : null);

        return `<tr>
          <td><span style="font-family:var(--font-mono);color:var(--muted);font-size:11px;">#${c.id}</span></td>
          <td><span style="font-weight:500;">${c.client || "—"}</span></td>
          <td><span class="tag tag-gray">${c.country || "—"}</span></td>
          <td><span class="tag tag-blue">${c.platform || "—"}</span></td>
          <td><span style="color:var(--muted);font-size:11px;">${c.category || "—"}</span></td>
          <td class="num">${fmtEur(costEur)}</td>
          <td class="num" style="color:var(--accent2);">${fmtEur(revEur)}</td>
          <td class="num" style="color:${margin != null && margin >= 0 ? "var(--accent2)" : "var(--danger)"};">${fmtEur(margin)}</td>
          <td class="num">${m.cpa != null ? parseFloat(m.cpa).toFixed(2) : "—"}</td>
          <td class="num">${m.conv != null ? fmtNum(m.conv) : "—"}</td>
          <td class="num" style="color:${roi != null && roi > 0.3 ? "var(--accent2)" : roi != null && roi > 0 ? "var(--warning)" : "var(--danger)"};">
              ${roi != null ? fmtRoi(roi) : "—"}</td>
          <td style="font-size:11px;">${statusBadge(cp.ok_conv, cp.ok_rev)}</td>
        </tr>`;
    }).join("");

    document.getElementById("table-info").textContent =
        `Showing ${(page - 1) * 25 + 1}–${Math.min(page * 25, count)} of ${count}`;
    document.getElementById("table-sub").textContent = `${count} campaign${count !== 1 ? "s" : ""}`;
    renderPagination(page, pages);
}

function renderPagination(page, pages) {
    const el = document.getElementById("pagination");
    if (pages <= 1) { el.innerHTML = ""; return; }
    const start = Math.max(1, page - 2), end = Math.min(pages, page + 2);
    let html = `<button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;"
        onclick="goToPage(${page - 1})" ${page === 1 ? "disabled" : ""}>← Anterior</button>`;
    for (let p = start; p <= end; p++) {
        const s = p === page ? "background:var(--surface2);color:var(--accent);" : "";
        html += `<button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;${s}"
            onclick="goToPage(${p})">${p}</button>`;
    }
    html += `<button class="btn btn-ghost" style="padding:4px 10px;font-size:11px;"
        onclick="goToPage(${page + 1})" ${page === pages ? "disabled" : ""}>Próximo →</button>`;
    el.innerHTML = html;
}

function goToPage(p) { if (p < 1 || p > _totalPages) return; _currentPage = p; loadCampaigns(); }

// ── Search & Export ───────────────────────────────────────────────
let _searchTimer = null;
function onSearch(q) {
    _searchQuery = q; _currentPage = 1;
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(loadCampaigns, 350);
}

// function exportCSV() {
//     const header = ["ID", "Cliente", "País", "Plataforma", "Categoria", "Cost EUR", "Receita EUR", "Margin EUR", "CPA", "Conv", "ROI"];
//     const rows = [[...header]];
//     document.querySelectorAll("#table-body tr").forEach(tr => {
//         const cells = [...tr.querySelectorAll("td")].map(td => td.textContent.trim());
//         if (cells.length > 1) rows.push(cells.slice(0, 11));
//     });
//     const csv = rows.map(r => r.map(c => `"${c}"`).join(",")).join("\n");
//     const a = document.createElement("a");
//     a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
//     a.download = "campaigns.csv";
//     a.click();
// }

function exportExcel() {
    const params = new URLSearchParams();
    if (_filterMonth) params.set("month", _filterMonth);
    if (_filterClient) params.set("client", _filterClient);
    const url = "/app/api/export/excel/" + (params.toString() ? "?" + params.toString() : "");

    const btn = document.getElementById("exportExcelBtn");
    const originalText = btn ? btn.innerHTML : "";
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Generating…`;
    }

    const a = document.createElement("a");
    a.href = url;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => {
        if (btn) { btn.disabled = false; btn.innerHTML = originalText; }
    }, 2500);
}

// ── Filters ───────────────────────────────────────────────────────
function applyFilters() {
    _filterClient = document.getElementById("filterClient")?.value || "";
    _filterMonth = document.getElementById("filterMonth")?.value || "";
    _currentPage = 1;
    _toggleExRateBtn();
    loadDashboard();
}

function _buildParams(extra = {}) {
    const p = new URLSearchParams();
    if (_filterClient) p.set("client", _filterClient);
    if (_filterMonth) {
        const [y, m] = _filterMonth.split("-");
        if (y) p.set("year", y);
        if (m) p.set("month", m);
    }
    Object.entries(extra).forEach(([k, v]) => { if (v != null && v !== "") p.set(k, v); });
    return p.toString() ? "?" + p.toString() : "";
}

// ── API calls ─────────────────────────────────────────────────────
async function loadDashboard() {
    await _loadExRates();
    try {
        const res = await fetch(API_DASHBOARD + _buildParams());
        if (!res.ok) throw new Error(`Server error: HTTP ${res.status}`);
        const data = await res.json();
        _byMonth = data.by_month || [];
        _byPlat = data.by_platform || [];
        renderKPIs(data.totals || {});
        renderBarChart();
        renderPlatChart();
    } catch (err) {
        console.error("Dashboard API error:", err);
        const kpiEl = document.getElementById("kpi-area");
        if (kpiEl) kpiEl.innerHTML = `<p style="color:var(--red,#ef4444);padding:16px">Failed to load dashboard: ${err.message}</p>`;
    }
    loadCampaigns();
}

async function loadCampaigns() {
    const params = _buildParams({ page: _currentPage, page_size: 25, search: _searchQuery });
    try {
        const res = await fetch(API_CAMPAIGNS + params);
        if (!res.ok) throw new Error(`Server error: HTTP ${res.status}`);
        const data = await res.json();
        renderTable(data.results || [], data.count || 0, data.page || 1, data.pages || 1);
    } catch (err) {
        console.error("Campaigns API error:", err);
        const tbody = document.getElementById("table-body");
        if (tbody) tbody.innerHTML = `<tr><td colspan="12" style="text-align:center;padding:40px;color:var(--red,#ef4444)">Failed to load campaigns: ${err.message}</td></tr>`;
    }
}

// ── Nova Campanha Modal ───────────────────────────────────────────
function _getCsrfToken() {
    const m = document.cookie.match("(^|;) ?csrftoken=([^;]*)(;|$)");
    return m ? m[2] : "";
}

function openNewCampaignModal() {
    document.getElementById("ncError").style.display = "none";
    document.getElementById("ncSubmitBtn").disabled = false;
    document.getElementById("ncSubmitBtn").textContent = "Create Campaign";
    ["nc_cpa", "nc_cost_ts", "nc_conv", "nc_cost_eur", "nc_revenue_eur", "nc_margin_display"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });
    document.getElementById("nc_creative_name").value = "";
    document.getElementById("newCampaignModal").style.display = "flex";
    // document.addEventListener("keydown", _ncEsc);
    // ["nc_cost_eur", "nc_revenue_eur"].forEach(id =>
    //     document.getElementById(id).addEventListener("input", _ncCalcMargin)
    // );
}

function closeNewCampaignModal() {
    document.getElementById("newCampaignModal").style.display = "none";
    document.removeEventListener("keydown", _ncEsc);
}

function _ncEsc(e) { if (e.key === "Escape") closeNewCampaignModal(); }

function _ncCalcMargin() {
    const cost = parseFloat(document.getElementById("nc_cost_eur").value);
    const rev = parseFloat(document.getElementById("nc_revenue_eur").value);
    const el = document.getElementById("nc_margin_display");
    if (!isNaN(cost) && !isNaN(rev)) {
        const margin = rev - cost;
        el.value = margin.toFixed(2);
        el.style.color = margin >= 0 ? "var(--accent2, #4ade80)" : "var(--danger, #ef4444)";
    } else {
        el.value = "";
        el.style.color = "";
    }
}

function _ncVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

async function submitNewCampaign() {
    const errEl = document.getElementById("ncError");
    errEl.style.display = "none";

    const month = _ncVal("nc_month");
    const client = _ncVal("nc_client");
    const country = _ncVal("nc_country");

    if (!month || !client || !country) {
        errEl.textContent = "Month, Client and Country are required.";
        errEl.style.display = "block";
        return;
    }

    const btn = document.getElementById("ncSubmitBtn");
    btn.disabled = true;
    btn.textContent = "Creating…";

    const payload = {
        month: month,
        client_id: client,
        country_id: country,
        category_id: _ncVal("nc_category") || null,
        creative_id: _ncVal("nc_creative") || null,
        creative_name: _ncVal("nc_creative_name") || null,
        platform_id: _ncVal("nc_platform") || null,
        plat_owner_id: _ncVal("nc_plat_owner") || null,
        detail_type_id: _ncVal("nc_detail_type") || null,
        client_camp: _ncVal("nc_client_camp") || null,
        cpa: _ncVal("nc_cpa") || null,
        cost_ts: _ncVal("nc_cost_ts") || null,
        conv: _ncVal("nc_conv") || null,
        cost_eur: _ncVal("nc_cost_eur") || null,
        revenue_eur: _ncVal("nc_revenue_eur") || null,
    };

    try {
        const res = await fetch(NC_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": _getCsrfToken(),
            },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (!res.ok) {
            errEl.textContent = data.error || `Error ${res.status}`;
            errEl.style.display = "block";
            btn.disabled = false;
            btn.textContent = "Create Campaign";
            return;
        }

        closeNewCampaignModal();
        loadDashboard();
    } catch (err) {
        errEl.textContent = `Connection error: ${err.message}`;
        errEl.style.display = "block";
        btn.disabled = false;
        btn.textContent = "Create Campaign";
    }
}

// ── Init ──────────────────────────────────────────────────────────
function _defaultMonth() {
    const today = new Date();
    const target = today.getDate() === 1
        ? new Date(today.getFullYear(), today.getMonth() - 1, 1)
        : today;
    const y = target.getFullYear();
    const m = String(target.getMonth() + 1).padStart(2, "0");
    return `${y}-${m}`;
}

window.addEventListener("DOMContentLoaded", () => {
    const sel = document.getElementById("filterMonth");
    if (sel) {
        const def = _defaultMonth();
        const monthOptions = [...sel.options].filter(o => o.value !== "");
        if (monthOptions.some(o => o.value === def)) {
            sel.value = def;
        } else if (monthOptions.length) {
            sel.value = monthOptions[0].value;
        }
        _filterMonth = sel.value;
    }
    _toggleExRateBtn();
    loadDashboard();
    const modal = document.getElementById("newCampaignModal");
    if (modal) modal.addEventListener("click", e => { if (e.target === modal) closeNewCampaignModal(); });
    const erModal = document.getElementById("exRateModal");
    if (erModal) erModal.addEventListener("click", e => { if (e.target === erModal) closeExRateModal(); });
});

// ── Exchange Rate Modal ───────────────────────────────────────────
const ER_URL = "/app/api/exchange-rates/create/";

function _toggleExRateBtn() {
    const btn = document.getElementById("addExRateBtn");
    if (btn) btn.style.display = _filterMonth ? "flex" : "none";
}

function openExRateModal() {
    if (!_filterMonth) return;
    const [y, m] = _filterMonth.split("-");
    document.getElementById("er_period").value = _filterMonth;
    document.getElementById("er_currency").value = "";
    document.getElementById("er_rate").value = "";
    document.getElementById("exRateError").style.display = "none";
    document.getElementById("erSubmitBtn").disabled = false;
    document.getElementById("erSubmitBtn").textContent = "Save";
    document.getElementById("exRateModal").style.display = "flex";
}

function closeExRateModal() {
    document.getElementById("exRateModal").style.display = "none";
}

async function submitExRate() {
    const errEl = document.getElementById("exRateError");
    errEl.style.display = "none";

    const [year, month] = _filterMonth.split("-");
    const currency = document.getElementById("er_currency").value.trim().toUpperCase();
    const rate = document.getElementById("er_rate").value.trim();

    if (!currency || !rate) {
        errEl.textContent = "Currency and Rate are required.";
        errEl.style.display = "block";
        return;
    }
    if (currency.length !== 3) {
        errEl.textContent = "Currency must be exactly 3 letters.";
        errEl.style.display = "block";
        return;
    }

    const btn = document.getElementById("erSubmitBtn");
    btn.disabled = true;
    btn.textContent = "Saving…";

    try {
        const res = await fetch(ER_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": _getCsrfToken() },
            body: JSON.stringify({ year, month, currency, rate }),
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.error || `Error ${res.status}`;
            errEl.style.display = "block";
            btn.disabled = false;
            btn.textContent = "Save";
            return;
        }
        closeExRateModal();
    } catch (err) {
        errEl.textContent = `Connection error: ${err.message}`;
        errEl.style.display = "block";
        btn.disabled = false;
        btn.textContent = "Save";
    }
}
