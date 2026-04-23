/* static/js/excel_import.js
   Handles the Excel import flow in the dashboard:
   file pick → preview modal → POST to Django → result display
*/

const IMPORT_URL = "/app/api/import/excel/";
let _pendingFile = null;

/* ── 1. File selected ──────────────────────────────────── */
function handleExcelImport(input) {
  const file = input.files[0];
  if (!file) return;
  _pendingFile = file;
  input.value = "";

  _setBody(`
    <div class="import-preview">
      <div class="import-file-card">
        <svg width="32" height="32" fill="#4ade80" viewBox="0 0 16 16">
          <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1L14 5.5z"/>
        </svg>
        <div>
          <strong>${_esc(file.name)}</strong>
          <span class="import-size">${(file.size / 1024).toFixed(1)} KB</span>
        </div>
      </div>
      <p class="import-note">
        Duplicates <em>(same month + client + country + creative)</em> will be
        <strong>replaced</strong>. Confirm to proceed.
      </p>
    </div>
  `);

  document.getElementById("importConfirmBtn").onclick = _doImport;
  _showFooter(true);
  _showModal();
}

/* ── 2. Confirm → POST ─────────────────────────────────── */
async function _doImport() {
  if (!_pendingFile) return;

  const btn = document.getElementById("importConfirmBtn");
  btn.disabled = true;
  btn.textContent = "Importing…";
  _showFooter(false);

  _setBody(`
    <div class="import-loading">
      <div class="import-spinner"></div>
      <p>Processing <strong>${_esc(_pendingFile.name)}</strong>…</p>
    </div>
  `);

  const form = new FormData();
  form.append("file", _pendingFile);

  try {
    const res  = await fetch(IMPORT_URL, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);

    const errBlock = data.errors?.length
      ? `<details class="import-errors">
           <summary>⚠ ${data.errors.length} row(s) with errors</summary>
           <ul>${data.errors.map(e => `<li>Row ${e.row}: ${_esc(e.error)}</li>`).join("")}</ul>
         </details>`
      : "";

    _setBody(`
      <div class="import-result import-success">
        <svg width="52" height="52" fill="#4ade80" viewBox="0 0 16 16">
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75
                   0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0
                   0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992
                   -4.99a.75.75 0 0 0-.01-1.05z"/>
        </svg>
        <h4>Import Successful!</h4>
        <div class="import-stats">
          <div class="import-stat">
            <span class="stat-val stat-created">${data.created}</span>
            <span class="stat-lbl">Created</span>
          </div>
          <div class="import-stat">
            <span class="stat-val stat-updated">${data.updated}</span>
            <span class="stat-lbl">Updated</span>
          </div>
          <div class="import-stat">
            <span class="stat-val">${data.total_processed}</span>
            <span class="stat-lbl">Total</span>
          </div>
        </div>
        ${errBlock}
      </div>
    `);

    setTimeout(() => { closeImportModal(); if (typeof loadDashboard === 'function') loadDashboard(); }, 2800);

  } catch (err) {
    _setBody(`
      <div class="import-result import-error">
        <svg width="52" height="52" fill="#f87171" viewBox="0 0 16 16">
          <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M5.354 4.646a.5.5 0 1
                   0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8
                   8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647
                   -2.646a.5.5 0 0 0-.708-.708L8 7.293z"/>
        </svg>
        <h4>Import Failed</h4>
        <p>${_esc(err.message)}</p>
      </div>
    `);
    btn.disabled = false;
    btn.textContent = "Retry";
    btn.onclick = _doImport;
    _showFooter(true);
  } finally {
    _pendingFile = null;
  }
}

/* ── 3. Modal helpers ──────────────────────────────────── */
function _showModal() {
  document.getElementById("importModal").style.display = "flex";
  document.addEventListener("keydown", _onEsc);
}

function closeImportModal() {
  document.getElementById("importModal").style.display = "none";
  document.removeEventListener("keydown", _onEsc);
  _pendingFile = null;
  const btn = document.getElementById("importConfirmBtn");
  if (btn) { btn.disabled = false; btn.textContent = "Confirm Import"; btn.onclick = null; }
  _showFooter(true);
}

function _setBody(html) {
  document.getElementById("importModalBody").innerHTML = html;
}

function _showFooter(visible) {
  const f = document.getElementById("importModalFooter");
  if (f) f.style.display = visible ? "flex" : "none";
}

function _onEsc(e) { if (e.key === "Escape") closeImportModal(); }
function _esc(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
                  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

/* Close on backdrop click */
document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("importModal");
  if (overlay) overlay.addEventListener("click", e => { if (e.target === overlay) closeImportModal(); });
});
