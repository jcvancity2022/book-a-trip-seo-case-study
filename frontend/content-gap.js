const FIELDS = [
  "project_page", "target1_url", "target2_url", "target3_url", "keyword",
  "search_volume", "kd", "cpc", "target1_position", "target2_position",
  "target3_position", "intersections", "include_on_page", "notes",
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
    const includeLabel = e.include_on_page === 1
      ? '<span class="badge-yes">Yes</span>'
      : e.include_on_page === 0
        ? '<span class="badge-no">No</span>'
        : "";

    tr.innerHTML = `
      <td>${escapeHtml(e.project_page)}</td>
      <td>${escapeHtml(e.keyword)}</td>
      <td class="num">${e.search_volume ?? ""}</td>
      <td class="num">${e.kd ?? ""}</td>
      <td class="num">${e.cpc ?? ""}</td>
      <td class="num">${e.target1_position ?? ""}</td>
      <td class="num">${e.target2_position ?? ""}</td>
      <td class="num">${e.target3_position ?? ""}</td>
      <td>${escapeHtml(e.intersections)}</td>
      <td>${includeLabel}</td>
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
  const res = await fetch("/api/content-gap");
  const entries = await res.json();
  renderRows(entries);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = readForm();
  const id = entryIdInput.value;

  if (id) {
    await fetch(`/api/content-gap/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } else {
    const res = await fetch("/api/content-gap", {
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
    const res = await fetch(`/api/content-gap/${id}`);
    const entry = await res.json();
    fillForm(entry);
  } else if (btn.dataset.action === "delete") {
    if (!confirm("Delete this content-gap entry?")) return;
    await fetch(`/api/content-gap/${id}`, { method: "DELETE" });
    loadEntries();
  }
});

loadEntries();
