// This is the Pages static build's copy of script.js. Destination cards on
// /destinations/ are plain links to /plan-a-trip/?destination=... now (each
// is its own page), so this only reads that query param to pre-select the
// dropdown. The booking form intentionally does NOT call /api/... -- there's
// no backend on GitHub Pages, so it shows an honest message instead of
// failing silently or faking a result. The real flow lives in the Flask app
// (see README).

function showError(message, tone) {
  const box = document.getElementById("error-box");
  if (!box) return;
  box.textContent = message;
  box.className = "error-box show" + (tone === "info" ? " info" : "");
}

// --- destination prefill on the plan-a-trip page ---
const destSelect = document.getElementById("destination");
if (destSelect) {
  const requested = new URLSearchParams(window.location.search).get("destination");
  if (requested && [...destSelect.options].some((o) => o.value === requested)) {
    destSelect.value = requested;
  }
}

// --- booking form: honest boundary on the static Pages build ---
const bookingForm = document.getElementById("booking-form");
if (bookingForm) {
  bookingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    showError(
      "This is the static GitHub Pages build -- the booking flow, SQLite record, and Stripe-ready checkout only run in the real Flask app. Run it locally or deploy it (see the README) to try the working version.",
      "info"
    );
  });
}
