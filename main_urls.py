const API_CAMPAIGNS = "/app/api/campaigns/";
const API_EXRATES = "/app/api/exchange-rates/";
const API_ADJUSTMENTS = pk => `/app/api/campaigns/${pk}/adjustments/`;
const API_ADJUSTMENT_DELETE = (pk, adjPk) => `/app/api/campaigns/${pk}/adjustments/${adjPk}/delete/`;

// month lock state keyed by "YYYY-MM" → {is_closed, month_pk, closed_by, closed_at}
let _monthState = {};
let _adjCampaignPk = null;

let _searchQuery = "";
let _filterClient = "";
let _filterMonth = "";
let _filterPlatform = "";

// exchange rate lookup: "USD_2026_2" → 1.085
let _rateMap = {};

// ── Country → Currency mapping ────────────────────────────────────
const COUNTRY_CURRENCY = {
    AE: "AED", BG: "BGN", CY: "EUR", DE: "EUR", DOM: "DOP",
    ES: "EUR", FR: "EUR", GG: "GBP", GR: "EUR", IQ: "IQD",
    IT: "EUR", KW: "KWD", LY: "LYD", MX: "MXN", NL: "EUR",
    OM: "OMR", PE: "PEN", PL: "PLN", PT: "EUR", RO: "RON",
    SA: "SAR", SI: "EUR", SK: "EUR", US: "USD", GB: "GBP",
    AU: "AUD", CA: "CAD", CH: "CHF", JP: "JPY", IN: "INR",
    BR: "BRL", ZA: "ZAR", TR: "TRY", EG: "EGP", NG: "NGN",
};

const CURRENCY_SYMBOLS = {
    USD: "$", GBP: "£", JPY: "¥", AUD: "A$", CAD: "C$",
    CHF: "Fr", INR: "₹", BRL: "R$", ZAR: "R", TRY: "₺",
};

const MONTH_NAMES = {
    Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6,
    Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12,
};

// ── Formatters ────────────────────────────────────────────────────
function fmtEur(n) {
    if (n == null) return "—";
    n = parseFloat(n);
    const abs = Math.abs(n), sign = n < 0 ? "-" : "";
    if (abs >= 1_000_000) return sign + "€ " + (abs / 1_000_000).toFixed(2) + "M";
    if (abs >= 1_000) return sign + "€ " + (abs / 1_000).toFixed(1) + "K";
    return sign + "€ " + abs.toFixed(2);
}
function fmtNum(n) { return n == null ? "—" : parseInt(n).toLocaleString("en"); }
function fmtRoi(n) { return n == null ? "—" : (parseFloat(n) * 100).toFixed(1) + "%"; }

function fmtCurrency(amount, currency) {
    if (amount == null || !currency) return null;
    const n = parseFloat(amount);
    const abs = Math.abs(n), sign = n < 0 ? "-" : "";
    const sym = CURRENCY_SYMBOLS[currency] || (currency + " ");
    if (abs >= 1_000_000) return sign + sym + (abs / 1_000_000).toFixed(2) + "M";
    if (abs >= 1_000) return sign + sym + (abs / 1_000).toFixed(1) + "K";
    return sign + sym + abs.toFixed(2);
}

function fmtLocal(eur_amount, currency, rate) {
    if (eur_amount == null || rate == null || currency === "EUR") return null;
    const n = parseFloat(eur_amount) * rate;
    const abs = Math.abs(n), sign = n < 0 ? "-" : "";
    const sym = CURRENCY_SYMBOLS[currency] || (currency + " ");
    if (abs >= 1_000_000) return sign + sym + (abs / 1_000_000).toFixed(2) + "M";
    if (abs >= 1_000) return sign + sym + (abs / 1_000).toFixed(1) + "K";
    return sign + sym + abs.toFixed(2);
}

function _parseMonthLabel(label) {
    if (!label) return null;
    const parts = label.trim().split(/\s+/);
    if (parts.length === 2) {
        const month = MONTH_NAMES[parts[0]];
        const year = parseInt(parts[1]);
        if (month && year) return { year, month };
    }
    const m = label.match(/(\d{4})-(\d{2})/);
    if (m) return { year: parseInt(m[1]), month: parseInt(m[2]) };
    return null;
}

function _getRate(country, monthLabel) {
    const currency = COUNTRY_CURRENCY[country];
    if (!currency || currency === "EUR") return { currency: "EUR", rate: null };
    const parsed = _parseMonthLabel(monthLabel);
    if (!parsed) return { currency, rate: null };
    const key = `${currency}_${parsed.year}_${parsed.month}`;
    const rate = _rateMap[key] || null;
    return { currency, rate };
}

function _fmtCostCell(cost_eur, cost_ts, cost_ts_currency) {
    const eur = fmtEur(cost_eur);
    if (cost_ts == null || !cost_ts_currency || cost_ts_currency === "EUR") return eur;
    const orig = parseFloat(cost_ts).toLocaleString("en", { maximumFractionDigits: 0 });
    return `<span style="display:block;">${eur}</span>
            <span class="tag tag-gray" style="font-size:10px;margin-top:3px;">${orig} ${cost_ts_currency}</span>`;
}

function _fmtCpaCell(cpa, country, monthLabel) {
    if (cpa == null) return "—";
    const { currency, rate } = _getRate(country, monthLabel);
    const local = fmtLocal(cpa, currency, rate);
    const eurStr = "€ " + parseFloat(cpa).toFixed(2);
    if (!local) return eurStr;
    return `<span style="display:block;font-weight:500;">${local}</span>
            <span style="display:block;font-size:10px;color:var(--muted);">${eurStr}</span>`;
}

// Revenue in original currency (top) + EUR below
function _fmtRevenueCell(revenue, revenue_currency, revenue_eur) {
    const eurStr = fmtEur(revenue_eur);
    if (revenue == null || !revenue_currency || revenue_currency === "EUR")
        return `<span style="color:var(--accent2);">${eurStr}</span>`;
    const orig = parseFloat(revenue).toLocaleString("en", { maximumFractionDigits: 0 });
    return `<span style="display:block;color:var(--accent2);">${eurStr}</span>
            <span class="tag tag-gray" style="font-size:10px;margin-top:3px;">${orig} ${revenue_currency}</span>`;
}

// convs_google (top) / convs_mob (bottom) stacked
function _fmtConvCell(convs_google, convs_mob) {
    const g = convs_google != null ? parseInt(convs_google).toLocaleString("en") : null;
    const m = convs_mob != null ? parseInt(convs_mob).toLocaleString("en") : null;
    if (!g && !m) return "—";
    if (g && !m) return `<span title="Google">${g}</span>`;
    if (!g && m) return `<span title="Mob">${m}</span>`;
    return `<span style="display:block;" title="Google">${g}</span>
            <span style="display:block;font-size:10px;color:var(--muted);" title="Mob">${m}</span>`;
}

// ── Filters & params ──────────────────────────────────────────────
function _buildParams(extra = {}) {
    const p = new URLSearchParams();
    if (_filterClient) p.set("client", _filterClient);
    if (_filterPlatform) p.set("platform", _filterPlatform);
    if (_filterMonth) {
        const [y, m] = _filterMonth.split("-");
        if (y) p.set("year", y);
        if (m) p.set("month", m);
    }
    if (_searchQuery) p.set("search", _searchQuery);
    Object.entries(extra).forEach(([k, v]) => { if (v != null && v !== "") p.set(k, v); });
    return p.toString() ? "?" + p.toString() : "";
}

function _syncUrl() {
    const p = new URLSearchParams();
    if (_filterMonth) p.set("month", _filterMonth);
    if (_filterClient) p.set("client", _filterClient);
    if (_filterPlatform) p.set("platform", _filterPlatform);
    if (_searchQuery) p.set("search", _searchQuery);
    const qs = p.toString();
    history.replaceState(null, "", qs ? "?" + qs : window.location.pathname);
}

function applyFilters() {
    _filterClient = document.getElementById("filterClient")?.value || "";
    _filterMonth = document.getElementById("filterMonth")?.value || "";
    _filterPlatform = document.getElementById("filterPlatform")?.value || "";
    _syncUrl();
    loadCampaigns();
}

let _searchTimer = null;
function onSearch(q) {
    _searchQuery = q;
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(() => { _syncUrl(); loadCampaigns(); }, 350);
}

// ── Render ────────────────────────────────────────────────────────
function renderFxChips() {
    const el = document.getElementById("fx-chips");
    if (!el) return;
    if (!_filterMonth) { el.innerHTML = ""; return; }
    const [y, m] = _filterMonth.split("-");
    const year = parseInt(y, 10), month = parseInt(m, 10);
    const chips = Object.entries(_rateMap)
        .filter(([k]) => k.endsWith(`_${year}_${month}`))
        .map(([k, rate]) => {
            const currency = k.split("_")[0];
            return `<span class="tag tag-gray" style="font-size:11px;font-family:var(--font-mono);">€1 = ${parseFloat(rate).toFixed(4)} ${currency}</span>`;
        });
    el.innerHTML = chips.length
        ? `<span style="font-size:11px;color:var(--muted);margin-right:2px;">FX</span>` + chips.join("")
        : "";
}

function renderTable(results, count, page, pages, totals = {}) {
    renderFxChips();
    const tbody = document.getElementById("table-body");

    if (!results.length) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:40px;color:var(--muted);">No data for the selected filters.</td></tr>`;
        document.getElementById("table-info").textContent = "0 results";
        document.getElementById("table-sub").textContent = "0 campaigns";
        document.getElementById("pagination").innerHTML = "";
        return;
    }

    const totalMargin = totals.total_margin != null
        ? totals.total_margin
        : (totals.total_revenue || 0) - (totals.total_cost || 0);

    const totalConv = (totals.total_convs_google || 0) + (totals.total_convs_mob || 0);
    document.getElementById("kpi-cost").textContent = fmtEur(totals.total_cost);
    document.getElementById("kpi-conv").textContent = fmtNum(totalConv || null);
    document.getElementById("kpi-revenue").textContent = fmtEur(totals.total_revenue);
    document.getElementById("kpi-margin").textContent = fmtEur(totalMargin);
    document.getElementById("kpi-margin").style.color = totalMargin >= 0 ? "var(--accent2)" : "var(--danger)";
    const roiEl = document.getElementById("kpi-roi");
    const avgRoi = totals.avg_roi;
    roiEl.textContent = avgRoi != null ? fmtRoi(avgRoi) : "—";
    roiEl.style.color = avgRoi == null ? "" : avgRoi > 0.3 ? "var(--accent2)" : avgRoi > 0 ? "var(--warning)" : "var(--danger)";

    _drillOpen.clear();

    tbody.innerHTML = results.map(c => {
        const m = c.metric || {};
        const margin = parseFloat(m.margin_eur);
        const roi = parseFloat(m.roi);
        const roiColor = roi > 0.3 ? "var(--accent2)" : roi > 0 ? "var(--warning)" : "var(--danger)";
        const campId = c.campaign_id || ("#" + c.id);
        const canEdit = !c.month_is_current && !c.month_is_closed;
        const adjActive = c.has_adjustments;
        const _hq = s => JSON.stringify(s).replace(/"/g, '&quot;');
        const editCircle = canEdit
            ? `<button onclick="openAdjModal(event,${c.id},${_hq(c.client)},${_hq(c.country)},${_hq(campId)})"
                title="Manage adjustments"
                style="width:24px;height:24px;border-radius:50%;border:1px solid ${adjActive ? "var(--accent)" : "var(--border2)"};background:${adjActive ? "rgba(99,102,241,0.08)" : "var(--surface2)"};cursor:pointer;color:${adjActive ? "var(--accent)" : "var(--muted)"};display:inline-flex;align-items:center;justify-content:center;padding:0;flex-shrink:0;">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M7 1.5l1.5 1.5-5 5L2 8.5l.5-1.5 5-5z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>`
            : `<span style="width:24px;height:24px;display:inline-block;"></span>`;
        return `<tr data-pk="${c.id}" data-month-key="${c.month}">
            <td>
                <button data-drill-btn="${c.id}" onclick="toggleDrilldown(event,${c.id})" style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:10px;margin-right:5px;vertical-align:middle;line-height:1;padding:0;">▶</button>
                <span style="font-family:var(--font-mono);color:var(--muted);font-size:11px;">${campId}</span>
            </td>
            <td><strong>${c.client || "—"}</strong></td>
            <td><span class="tag tag-gray">${c.country || "—"}</span></td>
            <td class="num">${_fmtCostCell(m.cost_eur, m.cost_ts, m.cost_ts_currency)}</td>
            <td class="num">${m.convs_google != null ? fmtNum(m.convs_google) : "—"}</td>
            <td class="num">${m.convs_mob != null ? fmtNum(m.convs_mob) : "—"}</td>
            <td class="num">${_fmtCpaCell(m.cpa, c.country, c.month)}</td>
            <td class="num">${_fmtRevenueCell(m.revenue, m.revenue_currency, m.revenue_eur)}</td>
            <td class="num" style="color:${!isNaN(margin) && margin < 0 ? "var(--danger)" : ""};">${fmtEur(m.margin_eur)}</td>
            <td class="num" style="color:${roiColor};">${m.roi != null ? fmtRoi(m.roi) : "—"}</td>
            <td style="text-align:center;padding:0 8px;">${editCircle}</td>
        </tr>`;
    }).join("");

    document.getElementById("table-info").textContent =
        `${count} campaign${count !== 1 ? "s" : ""}`;
    document.getElementById("table-sub").textContent =
        `${count} campaign${count !== 1 ? "s" : ""}`;
    document.getElementById("pagination").innerHTML = "";

    _updateLockButton(results);
}

let _lastResults = [];

async function exportCSV() {
    const res = await fetch(API_CAMPAIGNS + _buildParams({ page_size: 9999 }));
    const data = await res.json();
    const results = data.results || [];

    const header = ["Campaign ID", "Client", "Country", "Platform", "Category",
        "Cost EUR", "Conv. Google", "Conv. Mob", "CPA", "Revenue EUR",
        "Margin EUR", "ROI"];

    const rows = results.map(c => {
        const m = c.metric || {};
        const roi = m.roi != null ? (parseFloat(m.roi) * 100).toFixed(1) + "%" : "";
        return [
            c.campaign_id || c.id,
            c.client || "",
            c.country || "",
            c.platform || "",
            c.category || "",
            m.cost_eur != null ? parseFloat(m.cost_eur).toFixed(2) : "",
            m.convs_google != null ? m.convs_google : "",
            m.convs_mob != null ? m.convs_mob : "",
            m.cpa != null ? parseFloat(m.cpa).toFixed(2) : "",
            m.revenue_eur != null ? parseFloat(m.revenue_eur).toFixed(2) : "",
            m.margin_eur != null ? parseFloat(m.margin_eur).toFixed(2) : "",
            roi,
        ];
    });

    const csv = [header, ...rows]
        .map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(","))
        .join("\n");

    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = "campaigns.csv";
    a.click();
}

// ── Load ──────────────────────────────────────────────────────────
async function loadExchangeRates() {
    try {
        const res = await fetch(API_EXRATES);
        const data = await res.json();
        _rateMap = {};
        (data.results || []).forEach(r => {
            const key = `${r.currency}_${r.year}_${r.month}`;
            _rateMap[key] = r.rate;
        });
    } catch (err) {
        console.warn("Could not load exchange rates:", err);
    }
}

async function loadCampaigns() {
    try {
        const res = await fetch(API_CAMPAIGNS + _buildParams({}));
        const data = await res.json();
        renderTable(data.results || [], data.count || 0, data.page || 1, data.pages || 1, data.totals || {});
    } catch (err) {
        console.error("Campaigns error:", err);
    }
}

// ── Operator drilldown ────────────────────────────────────────────
const _drillOpen = new Set();
const _drillCache = {};

async function toggleDrilldown(event, pk) {
    event.stopPropagation();
    const btn = document.querySelector(`[data-drill-btn="${pk}"]`);

    if (_drillOpen.has(pk)) {
        _drillOpen.delete(pk);
        document.querySelectorAll(`[data-drill="${pk}"]`).forEach(r => r.remove());
        if (btn) btn.textContent = "▶";
        return;
    }

    _drillOpen.add(pk);
    if (btn) btn.textContent = "…";

    if (!_drillCache[pk]) {
        try {
            const res = await fetch(`/app/api/campaigns/${pk}/conversions/`);
            if (!res.ok) throw new Error();
            _drillCache[pk] = await res.json();
        } catch {
            _drillOpen.delete(pk);
            if (btn) btn.textContent = "▶";
            return;
        }
    }

    if (btn) btn.textContent = "▼";
    const row = document.querySelector(`tr[data-pk="${pk}"]`);
    const data = _drillCache[pk];
    if (row) _renderDrillRows(pk, data.operators || [], row, data);
}

function toggleHistory(event, pk, opIdx) {
    event.stopPropagation();
    const btn = event.currentTarget;
    const attr = `drill-hist-${pk}-${opIdx}`;
    const existing = document.querySelectorAll(`[data-hist="${attr}"]`);
    if (existing.length) {
        existing.forEach(r => r.remove());
        btn.textContent = "▶";
        return;
    }
    btn.textContent = "▼";
    const op = ((_drillCache[pk] || {}).operators || [])[opIdx];
    if (!op) return;
    const opRow = document.getElementById(`drill-op-${pk}-${opIdx}`);
    if (!opRow) return;

    const isOverride = op.adjustment && op.adjustment.mode === "override";
    const histRows = op.history.map(h => {
        const endDisplay = (() => {
            if (!h.end || h.end === "current") return h.end || "—";
            const [y, mo, d] = h.end.split("-").map(Number);
            const dt = new Date(y, mo - 1, d - 1);
            return `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,"0")}-${String(dt.getDate()).padStart(2,"0")}`;
        })();
        const period = h.start ? `${h.start} → ${endDisplay}` : "—";
        const payEur = h.payout_eur != null ? `€ ${parseFloat(h.payout_eur).toFixed(2)}` : "—";
        const payOrig = h.payout != null ? `${parseFloat(h.payout).toFixed(2)} ${h.payout_currency}` : "";
        const strikeStyle = isOverride ? "text-decoration:line-through;opacity:0.45;" : "";
        return `<tr data-drill="${pk}" data-hist="${attr}" style="background:var(--surface);">
            <td colspan="11" style="padding:0;">
                <div style="display:flex;align-items:center;gap:20px;padding:5px 12px 5px 36px;border-bottom:1px solid var(--border);font-size:11px;color:var(--muted);${strikeStyle}">
                    <span style="width:12px;flex-shrink:0;"></span>
                    <span style="min-width:180px;padding-left:12px;">${period}</span>
                    <span style="min-width:60px;text-align:right;font-family:var(--font-mono);">${fmtNum(h.count)}</span>
                    <span style="min-width:150px;text-align:right;">
                        <span style="display:block;font-family:var(--font-mono);">${payEur}</span>
                        ${payOrig ? `<span class="tag tag-gray" style="font-size:9px;margin-top:2px;">${payOrig}</span>` : ""}
                    </span>
                    <span style="min-width:100px;text-align:right;font-family:var(--font-mono);">${fmtEur(h.total_eur)}</span>
                </div>
            </td>
        </tr>`;
    });

    if (op.adjustment) {
        const a = op.adjustment;
        const adjPayEur = a.payout_eur != null ? `€ ${parseFloat(a.payout_eur).toFixed(2)}` : "—";
        const adjPayOrig = a.payout != null ? `${parseFloat(a.payout).toFixed(4)} ${a.payout_currency}` : "";
        const adjLabel = `Month — Adjustment`;
        histRows.push(`<tr data-drill="${pk}" data-hist="${attr}" style="background:var(--surface);">
            <td colspan="11" style="padding:0;">
                <div style="display:flex;align-items:center;gap:20px;padding:5px 12px 5px 36px;border-bottom:1px solid var(--border);font-size:11px;">
                    <span style="width:12px;flex-shrink:0;"></span>
                    <span style="min-width:180px;padding-left:12px;color:var(--accent);font-style:italic;">${adjLabel}</span>
                    <span style="min-width:60px;text-align:right;font-family:var(--font-mono);color:var(--accent);">${fmtNum(a.count)}</span>
                    <span style="min-width:150px;text-align:right;">
                        <span style="display:block;font-family:var(--font-mono);color:var(--accent);">${adjPayEur}</span>
                        ${adjPayOrig ? `<span class="tag tag-gray" style="font-size:9px;margin-top:2px;">${adjPayOrig}</span>` : ""}
                    </span>
                    <span style="min-width:100px;text-align:right;font-family:var(--font-mono);color:var(--accent);">${fmtEur(a.total_eur)}</span>
                </div>
            </td>
        </tr>`);
    }

    opRow.insertAdjacentHTML("afterend", histRows.join(""));
}

function _fmtCpcCell(orig, eur, currency) {
    const eurStr = eur != null ? `€ ${parseFloat(eur).toFixed(2)}` : "—";
    if (!currency || currency === "EUR" || orig == null) return `<span style="font-family:var(--font-mono);">${eurStr}</span>`;
    const origStr = `${parseFloat(orig).toFixed(2)} ${currency}`;
    return `<span style="display:block;font-family:var(--font-mono);">${eurStr}</span>
            <span class="tag tag-gray" style="font-size:10px;margin-top:2px;">${origStr}</span>`;
}

function _renderDrillRows(pk, operators, afterRow, drillData = {}) {
    const canEdit = !drillData.month_is_current && !drillData.month_is_closed;
    const editBtnHtml = canEdit
        ? `<button onclick="openAdjModal(event,${pk})" title="Manage adjustments" style="background:none;border:none;cursor:pointer;color:var(--accent);font-size:10px;padding:0 0 0 6px;line-height:1;">✎ Edit</button>`
        : "";

    const headerRow = `<tr data-drill="${pk}" style="background:var(--surface2);">
        <td colspan="11" style="padding:0;">
            <div style="display:flex;align-items:center;gap:20px;padding:5px 12px 5px 36px;border-bottom:1px solid var(--border);font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:var(--muted);">
                <span style="width:12px;flex-shrink:0;"></span>
                <span style="min-width:180px;">Operator${editBtnHtml}</span>
                <span style="min-width:60px;text-align:right;">Convs</span>
                <span style="min-width:150px;text-align:right;">Payout</span>
                <span style="min-width:100px;text-align:right;">Revenue</span>
            </div>
        </td>
    </tr>`;

    if (!operators.length) {
        afterRow.insertAdjacentHTML("afterend",
            headerRow + `<tr data-drill="${pk}"><td colspan="11" style="padding:10px 36px;font-size:12px;color:var(--muted);background:var(--surface2);">No operator data</td></tr>`);
        return;
    }
    const html = operators.map((op, opIdx) => {
        const adj = op.adjustment;
        const hasHistory = (op.history && op.history.length > 0) || !!adj;
        const expandBtn = hasHistory
            ? `<button onclick="toggleHistory(event,${pk},${opIdx})" style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:10px;padding:0;line-height:1;">▶</button>`
            : `<span style="display:inline-block;width:12px;"></span>`;

        const countCell = `<span style="font-family:var(--font-mono);">${fmtNum(op.total_count)}</span>`;
        const adjBadge = adj ? `<span class="tag tag-gray" style="font-size:9px;margin-left:4px;">${adj.mode}</span>` : "";

        return `<tr data-drill="${pk}" id="drill-op-${pk}-${opIdx}" style="background:var(--surface2);">
            <td colspan="11" style="padding:0;">
                <div style="display:flex;align-items:center;gap:20px;padding:7px 12px 7px 36px;border-bottom:1px solid var(--border);font-size:12px;">
                    <span style="width:12px;flex-shrink:0;">${expandBtn}</span>
                    <span style="min-width:180px;font-weight:500;">${op.operator}${adjBadge}</span>
                    <span style="min-width:60px;text-align:right;">${countCell}</span>
                    <span style="min-width:150px;text-align:right;">${_fmtCpcCell(op.cost_per_conv_orig, op.cost_per_conv_eur, op.payout_currency)}</span>
                    <span style="min-width:100px;text-align:right;font-family:var(--font-mono);">${fmtEur(op.total_cost_eur)}</span>
                </div>
            </td>
        </tr>`;
    }).join("");
    afterRow.insertAdjacentHTML("afterend", headerRow + html);
}

// ── Helpers ───────────────────────────────────────────────────────
function _defaultMonth() {
    const today = new Date();
    const target = today.getDate() === 1
        ? new Date(today.getFullYear(), today.getMonth() - 1, 1)
        : today;
    const y = target.getFullYear();
    const m = String(target.getMonth() + 1).padStart(2, "0");
    return `${y}-${m}`;
}

window.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);

    // Month: URL param → default month logic → most recent available
    const selMonth = document.getElementById("filterMonth");
    if (selMonth) {
        const monthOptions = [...selMonth.options].filter(o => o.value !== "");
        const fromUrl = params.get("month");
        const def = fromUrl || _defaultMonth();
        if (monthOptions.some(o => o.value === def)) {
            selMonth.value = def;
        } else if (monthOptions.length) {
            selMonth.value = monthOptions[0].value;
        }
        _filterMonth = selMonth.value;
    }

    // Client & platform from URL
    const selClient = document.getElementById("filterClient");
    if (selClient && params.get("client")) {
        selClient.value = params.get("client");
        _filterClient = selClient.value;
    }
    const selPlatform = document.getElementById("filterPlatform");
    if (selPlatform && params.get("platform")) {
        selPlatform.value = params.get("platform");
        _filterPlatform = selPlatform.value;
    }

    // Search
    const searchInput = document.getElementById("searchInput");
    if (searchInput && params.get("search")) {
        searchInput.value = params.get("search");
        _searchQuery = params.get("search");
    }

    _syncUrl();
    await loadExchangeRates();
    loadCampaigns();
});

// ── Month Reset ───────────────────────────────────────────────────
function resetMonth() {
    if (!_lockMonthPk) return;
    const body = document.getElementById("modal-reset-body");
    body.textContent = `Reset ${_lockMonthLabel}? This will delete all campaign data for this month and re-fetch from the API. Exchange rates will be kept.`;
    document.getElementById("modal-reset").style.display = "flex";
}

function closeResetModal() {
    document.getElementById("modal-reset").style.display = "none";
}

async function confirmResetMonth() {
    const btn = document.getElementById("btn-reset-confirm");
    btn.disabled = true;
    closeResetModal();

    _showLoading("Deleting month data…");
    try {
        const res = await fetch(`/app/api/months/${_lockMonthPk}/reset/`, {
            method: "POST",
            headers: { "X-CSRFToken": _getCsrf() },
        });
        if (!res.ok) throw new Error((await res.json()).error || "Reset failed");
        const { task_id } = await res.json();
        _showLoading("Re-fetching data from API…");
        await _pollTask(task_id);
        _hideLoading();
        _drillCache && Object.keys(_drillCache).forEach(k => delete _drillCache[k]);
        _drillOpen.clear();
        await loadExchangeRates();
        loadCampaigns();
    } catch (e) {
        _hideLoading();
        alert(e.message || "Reset failed.");
    } finally {
        btn.disabled = false;
    }
}

function _showLoading(text) {
    document.getElementById("overlay-loading-text").textContent = text || "Loading…";
    document.getElementById("overlay-loading").style.display = "flex";
}

function _hideLoading() {
    document.getElementById("overlay-loading").style.display = "none";
}

function _pollTask(taskId) {
    return new Promise((resolve, reject) => {
        const iv = setInterval(async () => {
            try {
                const res = await fetch(`/app/api/tasks/${taskId}/status/`);
                const data = await res.json();
                if (data.status === "SUCCESS") { clearInterval(iv); resolve(data.result); }
                else if (data.status === "FAILURE") { clearInterval(iv); reject(new Error(data.error || "Task failed")); }
            } catch (e) { clearInterval(iv); reject(e); }
        }, 2000);
    });
}

// ── Month Lock ────────────────────────────────────────────────────
let _lockMonthPk = null;
let _lockMonthLabel = "";

function _updateLockButton(results) {
    const btn = document.getElementById("btn-lock-month");
    if (!btn) return;
    if (!_filterMonth || !results.length) { btn.style.display = "none"; return; }

    const sample = results[0];
    const key = _filterMonth;
    if (!_monthState[key]) {
        _monthState[key] = {
            is_closed: sample.month_is_closed,
            is_current: sample.month_is_current,
        };
    }
    const state = _monthState[key];

    _lockMonthPk = sample.month_pk || null;
    _lockMonthLabel = _filterMonth;

    const resetBtn = document.getElementById("btn-reset-month");

    if (state.is_current) {
        btn.style.display = "none";
        if (resetBtn) resetBtn.style.display = "none";
        return;
    }

    btn.style.display = "";
    if (resetBtn) resetBtn.style.display = "";

    if (state.is_closed) {
        btn.textContent = "✓ Closed";
        btn.disabled = true;
        btn.style.opacity = "0.5";
        btn.style.cursor = "default";
        if (resetBtn) { resetBtn.disabled = true; resetBtn.style.opacity = "0.5"; }
    } else {
        btn.textContent = "Lock Month";
        btn.disabled = false;
        btn.style.opacity = "";
        btn.style.cursor = "";
        if (resetBtn) { resetBtn.disabled = false; resetBtn.style.opacity = ""; }
    }
}

function lockMonth() {
    if (!_lockMonthPk) return;
    const body = document.getElementById("modal-lock-body");
    body.textContent = `Close ${_lockMonthLabel}? This will lock all data for this month. No further adjustments will be allowed.`;
    const modal = document.getElementById("modal-lock");
    modal.style.display = "flex";
}

function closeLockModal() {
    document.getElementById("modal-lock").style.display = "none";
}

async function confirmLockMonth() {
    const btn = document.getElementById("btn-lock-confirm");
    btn.disabled = true;
    try {
        const res = await fetch(`/app/api/months/${_lockMonthPk}/close/`, { method: "POST", headers: { "X-CSRFToken": _getCsrf() } });
        if (!res.ok) throw new Error();
        _monthState[_lockMonthLabel] = { is_closed: true, is_current: false };
        closeLockModal();
        loadCampaigns();
    } catch {
        alert("Failed to close month.");
    } finally {
        btn.disabled = false;
    }
}

// ── Adjustment Modal ──────────────────────────────────────────────
let _adjData = null;

async function openAdjModal(event, pk, client, country, campId) {
    event.stopPropagation();
    _adjCampaignPk = pk;

    const [adjRes] = await Promise.all([
        fetch(API_ADJUSTMENTS(pk)),
    ]);
    const adjData = await adjRes.json();

    _adjData = adjData;

    if (adjData.month_is_closed || adjData.month_is_current) return;

    document.getElementById("modal-adj-title").textContent = "Adjustments";
    document.getElementById("modal-adj-info").innerHTML =
        `<span style="font-family:var(--font-mono);font-weight:600;">${campId || ""}</span>` +
        `<span class="tag tag-gray" style="margin-left:8px;">${country || ""}</span>` +
        `<span style="margin-left:8px;color:var(--muted);">${client || ""}</span>`;

    // Populate operator datalist
    const dl = document.getElementById("adj-operator-datalist");
    dl.innerHTML = (adjData.available_operators || []).map(op =>
        `<option value="${op}">`
    ).join("");

    _renderAdjList(pk, adjData.adjustments || []);
    _clearAdjForm();

    document.getElementById("modal-adj").style.display = "flex";
}

function closeAdjModal() {
    document.getElementById("modal-adj").style.display = "none";
    _adjCampaignPk = null;
    _adjData = null;
}

function _renderAdjList(pk, adjustments) {
    const el = document.getElementById("adj-list");
    if (!adjustments.length) {
        el.innerHTML = `<div style="font-size:12px;color:var(--muted);padding:8px 0;">No adjustments yet.</div>`;
        return;
    }
    el.innerHTML = adjustments.map(a => `
        <div style="display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--border);font-size:12px;" id="adj-row-${a.id}">
            <span style="flex:1;font-weight:500;">${a.operator}</span>
            <span style="font-family:var(--font-mono);color:var(--muted);">${fmtNum(a.count)}</span>
            <span style="font-family:var(--font-mono);color:var(--muted);">${parseFloat(a.payout).toFixed(4)} ${a.payout_currency}</span>
            <span class="tag tag-gray" style="font-size:9px;">${a.mode}</span>
            <button onclick="editAdj(${JSON.stringify(a).replace(/"/g,'&quot;')})" style="background:none;border:none;cursor:pointer;color:var(--accent);font-size:11px;padding:0;">Edit</button>
            <button onclick="deleteAdj(${a.id})" style="background:none;border:none;cursor:pointer;color:var(--danger);font-size:11px;padding:0;">✕</button>
        </div>
    `).join("");
}

function editAdj(a) {
    document.getElementById("adj-operator").value = a.operator;
    document.getElementById("adj-count").value = a.count;
    document.getElementById("adj-payout").value = a.payout;
    document.getElementById("adj-currency").value = a.payout_currency;
    document.getElementById(`adj-mode-${a.mode}`).checked = true;
    document.getElementById("adj-form-label").textContent = `Edit Adjustment — ${a.operator}`;
    document.getElementById("adj-save-btn").textContent = "Update Adjustment";
}

function _clearAdjForm() {
    document.getElementById("adj-operator").value = "";
    document.getElementById("adj-count").value = "";
    document.getElementById("adj-payout").value = "";
    document.getElementById("adj-currency").value = "";
    document.getElementById("adj-mode-addition").checked = true;
    document.getElementById("adj-form-label").textContent = "Add Adjustment";
    document.getElementById("adj-save-btn").textContent = "Save Adjustment";
}

function onAdjOperatorInput(op) {
    if (!op || !_adjData) return;
    const existing = (_adjData.adjustments || []).find(a => a.operator === op);
    if (existing) editAdj(existing);
}

async function saveAdjustment(event) {
    event.preventDefault();
    const pk = _adjCampaignPk;
    if (!pk) return;

    const operator = document.getElementById("adj-operator").value;
    const count = document.getElementById("adj-count").value;
    const payout = document.getElementById("adj-payout").value;
    const currency = document.getElementById("adj-currency").value.toUpperCase();
    const mode = document.querySelector('input[name="adj-mode"]:checked').value;

    if (!operator || !count || !payout || !currency) {
        alert("All fields are required.");
        return;
    }

    const btn = document.getElementById("adj-save-btn");
    btn.disabled = true;
    try {
        const res = await fetch(API_ADJUSTMENTS(pk), {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": _getCsrf() },
            body: JSON.stringify({ operator, count: parseInt(count), payout: parseFloat(payout), payout_currency: currency, mode }),
        });
        if (!res.ok) throw new Error((await res.json()).error || "Save failed");
        const saved = await res.json();
        await _refreshAdjModal(pk);
        _refreshDrilldown(pk);
        loadCampaigns();
        if (saved.fetching_rate) _showToast(`Exchange rate for ${currency} not found — fetching it now. Revenue values will update shortly.`);
    } catch (e) {
        alert(e.message || "Failed to save adjustment.");
    } finally {
        btn.disabled = false;
    }
}

async function deleteAdj(adjId) {
    const pk = _adjCampaignPk;
    if (!pk) return;
    const res = await fetch(API_ADJUSTMENT_DELETE(pk, adjId), {
        method: "POST",
        headers: { "X-CSRFToken": _getCsrf() },
    });
    if (!res.ok) { alert("Failed to delete adjustment."); return; }
    await _refreshAdjModal(pk);
    _refreshDrilldown(pk);
    loadCampaigns();
}

async function _refreshAdjModal(pk) {
    const res = await fetch(API_ADJUSTMENTS(pk));
    _adjData = await res.json();
    _renderAdjList(pk, _adjData.adjustments || []);
    _clearAdjForm();
}

async function _refreshDrilldown(pk) {
    if (!_drillOpen.has(pk)) return;
    delete _drillCache[pk];
    document.querySelectorAll(`[data-drill="${pk}"]`).forEach(r => r.remove());
    const res = await fetch(`/app/api/campaigns/${pk}/conversions/`);
    if (!res.ok) return;
    _drillCache[pk] = await res.json();
    const row = document.querySelector(`tr[data-pk="${pk}"]`);
    const data = _drillCache[pk];
    if (row) _renderDrillRows(pk, data.operators || [], row, data);
}

function _getCsrf() {
    return document.cookie.split(";").map(c => c.trim()).find(c => c.startsWith("csrftoken="))?.split("=")[1] || "";
}

function _showToast(msg, duration = 5000) {
    let el = document.getElementById("_toast");
    if (!el) {
        el = document.createElement("div");
        el.id = "_toast";
        el.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--surface2);border:1px solid var(--border2);color:var(--text);font-size:12px;padding:10px 18px;border-radius:var(--radius);box-shadow:0 4px 16px rgba(0,0,0,0.3);z-index:9999;max-width:420px;text-align:center;transition:opacity 0.3s;";
        document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.opacity = "1";
    clearTimeout(el._timer);
    el._timer = setTimeout(() => { el.style.opacity = "0"; }, duration);
}

function openExportModal() {
    const m = document.getElementById("modal-export");
    m.style.display = "flex";
}

function closeExportModal() {
    document.getElementById("modal-export").style.display = "none";
}

function exportXLSX() {
    const params = new URLSearchParams();
    if (_filterMonth) params.set("month", _filterMonth);
    if (_filterClient) params.set("client", _filterClient);
    const qs = params.toString() ? "?" + params.toString() : "";
    window.location.href = "/app/api/export/excel/" + qs;
}