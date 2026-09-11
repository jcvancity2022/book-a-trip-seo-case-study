const FIELDS = [
  "project_page", "prospect_url", "domain", "channel", "relevance_note",
  "authority_status", "editorial_placement", "links_out", "verdict",
  "status", "notes",
];

const form = document.getElementById("kw-form");
const submitBtn = document.getElementById("kw-submit");
const cancelBtn = document.getElementById("kw-cancel");
const entryIdInput = document.getElementById("entry_id");
const tbody = document.getElementById("kw-tbody");
const emptyState = document.getElementById("kw-empty");

function readForm() {
  const data = {};
  for (const field of FIELDS) {
    const el = document.getElementById(field);
    if (el.value !== "") data[field] = el.value;
  }
  return data;
}

function fillForm(entry) {
  entryIdInput.value = entry.id;
  for (const field of FIELDS) {
    document.getElementById(field).value = entry[field] ?? "";
  }
  submitBtn.textContent = "Update entry";
  cancelBtn.style.display = "inline-block";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
  form.reset();
  entryIdInput.value = "";
  document.getElementById("status").value = "not contacted";
  submitBtn.textContent = "Add entry";
  cancelBtn.style.display = "none";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function verdictLabel(v) {
  if (!v) return "";
  const cls = "verdict-" + v.replace(" ", "-").replace("top-prospect", "top");
  const text = v === "top prospect" ? "Top prospect" : v.charAt(0).toUpperCase() + v.slice(1);
  return `<span class="${cls}">${text}</span>`;
}

function renderRows(entries) {
  tbody.innerHTML = "";
  emptyState.style.display = entries.length ? "none" : "block";

  for (const e of entries) {
    const tr = document.createElement("tr");
    const linksOutLabel = e.links_out === 1
      ? '<span class="badge-yes">Yes</span>'
      : e.links_out === 0
        ? '<span class="badge-no">No</span>'
        : "";

    tr.innerHTML = `
      <td>${escapeHtml(e.project_page)}</td>
      <td><a href="${escapeHtml(e.prospect_url)}" target="_blank" rel="noopener">${escapeHtml(e.domain || e.prospect_url)}</a></td>
      <td>${escapeHtml(e.channel)}</td>
      <td>${escapeHtml(e.relevance_note)}</td>
      <td>${escapeHtml(e.authority_status)}</td>
      <td>${escapeHtml(e.editorial_placement)}</td>
      <td>${linksOutLabel}</td>
      <td>${verdictLabel(e.verdict)}</td>
      <td><span class="status-pill">${escapeHtml(e.status)}</span></td>
      <td>${escapeHtml(e.notes)}</td>
      <td class="row-actions">
        <button type="button" data-action="edit" data-id="${e.id}">Edit</button>
        <button type="button" class="danger" data-action="delete" data-id="${e.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadEntries() {
  const res = await fetch("/api/link-prospects");
  const entries = await res.json();
  renderRows(entries);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = readForm();
  const id = entryIdInput.value;

  if (id) {
    await fetch(`/api/link-prospects/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } else {
    const res = await fetch("/api/link-prospects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      alert(err.error || "Could not save entry");
      return;
    }
  }

  resetForm();
  loadEntries();
});

cancelBtn.addEventListener("click", resetForm);

tbody.addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const id = btn.dataset.id;

  if (btn.dataset.action === "edit") {
    const res = await fetch(`/api/link-prospects/${id}`);
    const entry = await res.json();
    fillForm(entry);
  } else if (btn.dataset.action === "delete") {
    if (!confirm("Delete this link prospect?")) return;
    await fetch(`/api/link-prospects/${id}`, { method: "DELETE" });
    loadEntries();
  }
});

loadEntries();
