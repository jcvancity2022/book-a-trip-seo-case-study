const FIELDS = [
  "keyword", "parent_topic", "location", "search_volume", "volume_source",
  "traffic_potential_notes", "business_potential", "intent", "content_type",
  "content_format", "content_angle", "ranking_difficulty",
  "serp_observations", "recommended_action",
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
  submitBtn.textContent = "Add entry";
  cancelBtn.style.display = "none";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function renderRows(entries) {
  tbody.innerHTML = "";
  emptyState.style.display = entries.length ? "none" : "block";

  for (const e of entries) {
    const tr = document.createElement("tr");
    const volume = e.search_volume != null
      ? `${e.search_volume}${e.volume_source ? ` (${escapeHtml(e.volume_source)})` : ""}`
      : (e.volume_source ? escapeHtml(e.volume_source) : "Needs verification");

    tr.innerHTML = `
      <td>${escapeHtml(e.keyword)}</td>
      <td>${escapeHtml(e.parent_topic)}</td>
      <td>${escapeHtml(e.location)}</td>
      <td>${volume}</td>
      <td>${escapeHtml(e.traffic_potential_notes)}</td>
      <td>${e.business_potential ?? ""}</td>
      <td>${escapeHtml(e.intent)}</td>
      <td>${escapeHtml(e.content_type)}</td>
      <td>${escapeHtml(e.content_format)}</td>
      <td>${escapeHtml(e.content_angle)}</td>
      <td>${escapeHtml(e.ranking_difficulty)}</td>
      <td>${escapeHtml(e.serp_observations)}</td>
      <td>${escapeHtml(e.recommended_action)}</td>
      <td class="row-actions">
        <button type="button" data-action="edit" data-id="${e.id}">Edit</button>
        <button type="button" class="danger" data-action="delete" data-id="${e.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadEntries() {
  const res = await fetch("/api/keywords");
  const entries = await res.json();
  renderRows(entries);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = readForm();
  const id = entryIdInput.value;

  if (id) {
    await fetch(`/api/keywords/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } else {
    const res = await fetch("/api/keywords", {
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
    const res = await fetch(`/api/keywords/${id}`);
    const entry = await res.json();
    fillForm(entry);
  } else if (btn.dataset.action === "delete") {
    if (!confirm("Delete this keyword-research entry?")) return;
    await fetch(`/api/keywords/${id}`, { method: "DELETE" });
    loadEntries();
  }
});

loadEntries();
