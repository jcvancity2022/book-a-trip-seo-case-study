// This is the Pages static build's copy of script.js. Destination-card
// selection is the same client-side logic as the real app. The booking
// form intentionally does NOT call /api/... -- there's no backend on
// GitHub Pages, so it shows an honest message instead of failing silently
// or faking a result. The real flow lives in the Flask app (see README).

function showError(message, tone) {
  const box = document.getElementById("error-box");
  if (!box) return;
  box.textContent = message;
  box.className = "error-box show" + (tone === "info" ? " info" : "");
}

// --- destination card selection (index page) ---
const destSelect = document.getElementById("destination");
const destCards = document.querySelectorAll(".dest-card");

function selectDestination(value) {
  if (destSelect) destSelect.value = value;
  destCards.forEach((card) => {
    card.classList.toggle("selected", card.dataset.destination === value);
  });
}

destCards.forEach((card) => {
  card.addEventListener("click", () => {
    selectDestination(card.dataset.destination);
    const plan = document.getElementById("plan");
    if (plan) plan.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

if (destSelect) {
  selectDestination(destSelect.value);
  destSelect.addEventListener("change", () => selectDestination(destSelect.value));
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
