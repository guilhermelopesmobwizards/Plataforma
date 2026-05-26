/* exchange_rates.js — Exchange Rates page */

const ER_LIST_URL = "/app/api/exchange-rates/";
const ER_CREATE_URL = "/app/api/exchange-rates/create/";
const ER_DELETE_URL = "/app/api/exchange-rates/";

let _allRates = [];
let _searchQuery = "";
let _filterYear = "";
let _filterCurrency = "";

function _getCsrfToken() {
    const m = document.cookie.match("(^|;) ?csrftoken=([^;]*)(;|$)");
    return m ? m[2] : "";
}

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// ── Load ──────────────────────────────────────────────────────────
async function loadRates() {
    try {
        const res = await fetch(ER_LIST_URL);
        const data = await res.json();
        _allRates = data.results || [];
        _populateFilters();
        renderTable();
    } catch (err) {
        console.error("Exchange rates error:", err);
    }
}

function _populateFilters() {
    const years = [...new Set(_allRates.map(r => r.year))].sort((a, b) => b - a);
    const currencies = [...new Set(_allRates.map(r => r.currency))].sort();

    const yEl = document.getElementById("filterYear");
    yEl.innerHTML = '<option value="">All Years</option>' +
        years.map(y => `<option value="${y}">${y}</option>`).join("");

    const cEl = document.getElementById("filterCurrency");
    cEl.innerHTML = '<option value="">All Currencies</option>' +
        currencies.map(c => `<option value="${c}">${c}</option>`).join("");
}

function applyFilters() {
    _filterYear = document.getElementById("filterYear")?.value || "";
    _filterCurrency = document.getElementById("filterCurrency")?.value || "";
    renderTable();
}

function onSearch(q) { _searchQuery = q.toUpperCase(); renderTable(); }

// ── Render ────────────────────────────────────────────────────────
function renderTable() {
    let rows = _allRates.filter(r => {
        if (_filterYear && String(r.year) !== _filterYear) return false;
        if (_filterCurrency && r.currency !== _filterCurrency) return false;
        if (_searchQuery && !r.currency.includes(_searchQuery)) return false;
        return true;
    });

    // KPIs
    const currencies = new Set(_allRates.map(r => r.currency));
    document.getElementById("kpi-total").textContent = _allRates.length;
    document.getElementById("kpi-currencies").textContent = currencies.size;
    const latest = _allRates[0];
    document.getElementById("kpi-latest").textContent = latest
        ? `${MONTHS[latest.month]} ${latest.year}` : "—";
    document.getElementById("table-sub").textContent =
        `${rows.length} record${rows.length !== 1 ? "s" : ""}`;

    const tbody = document.getElementById("table-body");
    if (!rows.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--muted);">No records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = rows.map(r => {
        const period = `${MONTHS[r.month]} ${r.year}`;
        const created = r.created_at ? r.created_at.slice(0, 10) : "—";
        return `<tr>
            <td><span style="font-family:var(--font-mono);font-size:12px;">${period}</span></td>
            <td><span class="tag tag-blue">${r.currency}</span></td>
            <td class="num" style="font-family:var(--font-mono);">${parseFloat(r.rate).toFixed(6)}</td>
            <td style="color:var(--muted);font-size:11px;">${created}</td>
            <td style="display:flex;gap:6px;align-items:center;">
                <button class="btn btn-ghost" style="font-size:11px;padding:3px 10px;"
                    onclick="openEditModal(${r.id}, ${r.year}, ${r.month}, '${r.currency}', ${r.rate})">
                    Edit
                </button>
                <button class="btn btn-ghost" style="font-size:11px;padding:3px 10px;color:var(--red,#ef4444);"
                    onclick="deleteRate(${r.id}, '${r.currency}', '${period}')">
                    Delete
                </button>
            </td>
        </tr>`;
    }).join("");
}

// ── Modal ─────────────────────────────────────────────────────────
let _editId = null;

function openAddModal() {
    _editId = null;
    document.getElementById("erModalTitle").textContent = "Add Exchange Rate";
    document.getElementById("erSubmitBtn").textContent = "Save";
    document.getElementById("er_year").value = new Date().getFullYear();
    document.getElementById("er_month").value = new Date().getMonth() + 1;
    document.getElementById("er_currency").value = "";
    document.getElementById("er_rate").value = "";
    document.getElementById("erError").style.display = "none";
    document.getElementById("erSubmitBtn").disabled = false;
    document.getElementById("erModal").style.display = "flex";
}

function openEditModal(id, year, month, currency, rate) {
    _editId = id;
    document.getElementById("erModalTitle").textContent = "Edit Exchange Rate";
    document.getElementById("erSubmitBtn").textContent = "Update";
    document.getElementById("er_year").value = year;
    document.getElementById("er_month").value = month;
    document.getElementById("er_currency").value = currency;
    document.getElementById("er_rate").value = rate;
    document.getElementById("erError").style.display = "none";
    document.getElementById("erSubmitBtn").disabled = false;
    document.getElementById("erModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("erModal").style.display = "none";
    _editId = null;
}

async function submitRate() {
    const errEl = document.getElementById("erError");
    errEl.style.display = "none";

    const year = document.getElementById("er_year").value.trim();
    const month = document.getElementById("er_month").value;
    const currency = document.getElementById("er_currency").value.trim().toUpperCase();
    const rate = document.getElementById("er_rate").value.trim();

    if (!year || !month || !currency || !rate) {
        errEl.textContent = "All fields are required.";
        errEl.style.display = "block";
        return;
    }
    if (currency.length !== 3) {
        errEl.textContent = "Currency must be exactly 3 letters (e.g. USD).";
        errEl.style.display = "block";
        return;
    }

    const btn = document.getElementById("erSubmitBtn");
    btn.disabled = true;
    btn.textContent = "Saving…";

    try {
        const res = await fetch(ER_CREATE_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": _getCsrfToken() },
            body: JSON.stringify({ year, month, currency, rate }),
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.error || `Error ${res.status}`;
            errEl.style.display = "block";
            btn.disabled = false;
            btn.textContent = _editId ? "Update" : "Save";
            return;
        }
        closeModal();
        loadRates();
    } catch (err) {
        errEl.textContent = `Connection error: ${err.message}`;
        errEl.style.display = "block";
        btn.disabled = false;
        btn.textContent = _editId ? "Update" : "Save";
    }
}

async function deleteRate(id, currency, period) {
    if (!confirm(`Delete ${currency} rate for ${period}?`)) return;
    try {
        const res = await fetch(`${ER_DELETE_URL}${id}/delete/`, {
            method: "POST",
            headers: { "X-CSRFToken": _getCsrfToken() },
        });
        if (res.ok) loadRates();
        else alert("Failed to delete.");
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

// ── Init ──────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
    loadRates();
    const modal = document.getElementById("erModal");
    if (modal) modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });
});