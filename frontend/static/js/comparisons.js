const API_COMP = "/app/api/comparisons/";
const CHART_COLORS = ["#60faf2", "#c8f135", "#a78bfa", "#4ade80", "#f97316", "#f43f5e"];

let _revChart = null;
let _convChart = null;

function fmtEur(n) {
    if (n == null) return "—";
    n = parseFloat(n);
    if (n >= 1_000_000) return "€\u00A0" + (n / 1_000_000).toFixed(2) + "M";
    if (n >= 1_000) return "€\u00A0" + (n / 1_000).toFixed(1) + "K";
    return "€\u00A0" + n.toFixed(2);
}
function fmtNum(n) { return n == null ? "—" : parseInt(n).toLocaleString("pt-PT"); }
function fmtRoi(n) { return n == null ? "—" : parseFloat(n).toFixed(2) + "×"; }
function delta(a, b, fmt, invertColor = false) {
    if (a == null || b == null) return "—";
    const d = parseFloat(b) - parseFloat(a);
    const pct = parseFloat(a) !== 0 ? ((d / parseFloat(a)) * 100).toFixed(1) : "0";
    const up = d >= 0;
    const color = invertColor
        ? (up ? "var(--danger)" : "var(--accent2)")
        : (up ? "var(--accent2)" : "var(--danger)");
    return `<span style="color:${color};">${up ? "▲" : "▼"} ${up ? "+" : ""}${pct}%</span>`;
}

async function loadComparisons() {
    const res = await fetch(API_COMP);
    const data = await res.json();

    const months = data.by_month || [];
    const clients = data.by_client || [];
    const plats = data.by_platform || [];

    // Pick last 2 months for comparison
    const mA = months.at(-2);
    const mB = months.at(-1);
    const labelA = mA?.label || "Mês A";
    const labelB = mB?.label || "Mês B";

    // Update panel titles
    document.getElementById("rev-comp-title").textContent = `Revenue: ${labelA} vs ${labelB}`;
    document.getElementById("conv-comp-title").textContent = `Conversões: ${labelA} vs ${labelB}`;
    document.getElementById("client-comp-sub").textContent = `${labelA} vs ${labelB}`;
    document.getElementById("plat-comp-sub").textContent = `${labelA} vs ${labelB}`;

    // Revenue chart
    if (_revChart) _revChart.destroy();
    _revChart = new Chart(document.getElementById("revCompChart"), {
        type: "bar",
        data: {
            labels: months.map(m => m.label || m.month_date),
            datasets: [{
                label: "Revenue EUR",
                data: months.map(m => parseFloat(m.revenue) || 0),
                backgroundColor: "rgba(200,241,53,0.18)",
                borderColor: "rgba(200,241,53,0.8)",
                borderWidth: 1.5, borderRadius: 4,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", font: { size: 11 } } },
                y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", font: { size: 10 }, callback: v => "€" + Math.round(v / 1000) + "K" } }
            }
        }
    });

    // Conv chart
    if (_convChart) _convChart.destroy();
    _convChart = new Chart(document.getElementById("convCompChart"), {
        type: "bar",
        data: {
            labels: months.map(m => m.label || m.month_date),
            datasets: [{
                label: "Conversões",
                data: months.map(m => parseInt(m.conv) || 0),
                backgroundColor: "rgba(96,250,242,0.18)",
                borderColor: "rgba(96,250,242,0.8)",
                borderWidth: 1.5, borderRadius: 4,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", font: { size: 11 } } },
                y: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#6b7280", font: { size: 10 } } }
            }
        }
    });

    // Client comparison table
    const clientMap = {};
    clients.forEach(r => {
        if (!clientMap[r.client_name]) clientMap[r.client_name] = [];
        clientMap[r.client_name].push(r);
    });
    document.getElementById("client-tbody").innerHTML = Object.entries(clientMap).map(([name, rows]) => {
        const a = rows.at(-2), b = rows.at(-1);
        if (!a || !b) return "";
        return `<tr>
            <td><strong>${name}</strong></td>
            <td class="num">${fmtEur(a.revenue)}</td>
            <td class="num">${fmtEur(b.revenue)}</td>
            <td class="num">${delta(a.revenue, b.revenue)}</td>
            <td class="num">${fmtRoi(a.avg_roi)}</td>
            <td class="num">${fmtRoi(b.avg_roi)}</td>
            <td class="num">${delta(a.avg_roi, b.avg_roi)}</td>
            <td class="num">${fmtNum(a.conv)}</td>
            <td class="num">${fmtNum(b.conv)}</td>
            <td class="num">${delta(a.conv, b.conv)}</td>
            <td class="num">${fmtEur(a.avg_cpa)}</td>
            <td class="num">${fmtEur(b.avg_cpa)}</td>
        </tr>`;
    }).join("");

    // Platform comparison table
    const platMap = {};
    plats.forEach(r => {
        if (!platMap[r.platform_name]) platMap[r.platform_name] = [];
        platMap[r.platform_name].push(r);
    });
    document.getElementById("plat-tbody").innerHTML = Object.entries(platMap).map(([name, rows]) => {
        const a = rows.at(-2), b = rows.at(-1);
        if (!a || !b) return "";
        return `<tr>
            <td><span class="tag tag-blue">${name}</span></td>
            <td class="num">${fmtEur(a.cost)}</td>
            <td class="num">${fmtEur(b.cost)}</td>
            <td class="num">${delta(a.cost, b.cost, fmtEur, true)}</td>
            <td class="num">${fmtEur(a.revenue)}</td>
            <td class="num">${fmtEur(b.revenue)}</td>
            <td class="num">${delta(a.revenue, b.revenue)}</td>
            <td class="num">${fmtRoi(a.avg_roi)}</td>
            <td class="num">${fmtRoi(b.avg_roi)}</td>
            <td class="num">${delta(a.avg_roi, b.avg_roi)}</td>
        </tr>`;
    }).join("");
}

window.addEventListener("DOMContentLoaded", loadComparisons);