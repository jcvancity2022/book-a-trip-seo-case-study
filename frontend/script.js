function showError(message, tone) {
  const box = document.getElementById("error-box");
  if (!box) return;
  box.textContent = message;
  box.className = "error-box show" + (tone === "info" ? " info" : "");
}

// --- booking page: prefill, live order summary, submit ---
const bookingForm = document.getElementById("booking-form");
if (bookingForm) {
  const params = new URLSearchParams(window.location.search);
  const money = (n) => "$" + Number(n).toFixed(2);
  const checked = (name) => bookingForm.querySelector('input[name="' + name + '"]:checked');

  const requestedDest = params.get("destination");
  if (requestedDest) {
    const match = [...bookingForm.querySelectorAll('input[name="destination"]')].find((i) => i.value === requestedDest);
    if (match) match.checked = true;
  }
  const requestedPkg = params.get("package");
  if (requestedPkg) {
    const match = [...bookingForm.querySelectorAll('input[name="package"]')].find((i) => i.value === requestedPkg);
    if (match) match.checked = true;
  }

  const dateInput = document.getElementById("trip_date");
  const today = new Date();
  dateInput.min = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0") + "-" + String(today.getDate()).padStart(2, "0");

  function updateSummary() {
    const dest = checked("destination");
    const pkg = checked("package");
    const price = pkg ? Number(pkg.dataset.price) : 0;
    document.getElementById("sum-destination").textContent = dest ? dest.value : "";
    document.getElementById("sum-plan").textContent = pkg ? pkg.dataset.label : "";
    document.getElementById("sum-date").textContent = dateInput.value || "Not chosen yet";
    document.getElementById("sum-total").textContent = money(price) + " CAD";
    document.getElementById("submit-btn").textContent = "Pay " + money(price) + " CAD";
  }
  bookingForm.addEventListener("change", updateSummary);
  updateSummary();

  // Keep displayed prices in sync with the server, which is the source of truth.
  if (!window.BAT_STATIC) {
    fetch("/api/packages").then((r) => r.json()).then((pkgs) => {
      Object.entries(pkgs).forEach(([key, p]) => {
        const input = bookingForm.querySelector('input[name="package"][value="' + key + '"]');
        const label = bookingForm.querySelector('[data-price-for="' + key + '"]');
        if (input) input.dataset.price = p.amount;
        if (label) label.textContent = money(p.amount);
      });
      updateSummary();
    }).catch(() => {});
  }

  bookingForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (window.BAT_STATIC) {
      showError(
        "This is the static GitHub Pages build -- the booking flow, SQLite record, and Stripe-ready checkout only run in the real Flask app. Run it locally or deploy it (see the README) to try the working version.",
        "info"
      );
      return;
    }
    const btn = document.getElementById("submit-btn");
    btn.disabled = true;
    btn.textContent = "Working...";

    const payload = {
      traveler_name: document.getElementById("traveler_name").value.trim(),
      email: document.getElementById("email").value.trim(),
      destination: checked("destination").value,
      trip_date: dateInput.value,
    };

    try {
      const bookingRes = await fetch("/api/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const booking = await bookingRes.json();
      if (!bookingRes.ok) throw new Error(booking.error || "Could not save booking");

      const packageInput = checked("package");
      const checkoutRes = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          booking_id: booking.booking_id,
          package: packageInput ? packageInput.value : undefined,
        }),
      });
      const session = await checkoutRes.json();
      if (!checkoutRes.ok) throw new Error(session.error || "Could not start checkout");

      window.location.href = session.url;
    } catch (err) {
      showError(err.message);
      btn.disabled = false;
      updateSummary();
    }
  });
}

// --- confirmation page ---
function confirmationPage() {
  const params = new URLSearchParams(window.location.search);
  const demoSession = params.get("demo_session");
  const bookingId = params.get("booking_id");

  const iconWrap = document.getElementById("icon-wrap");
  const heading = document.getElementById("heading");
  const subheading = document.getElementById("subheading");
  const summaryCard = document.getElementById("summary-card");
  const summaryBody = document.getElementById("summary-body");

  function renderSummary(booking, status, payment) {
    const isPaid = status === "completed";
    iconWrap.className = `confirm-icon ${isPaid ? "ok" : "wait"}`;
    iconWrap.innerHTML = isPaid
      ? '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false"><path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      : '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/><path d="M12 7v5l3 2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

    heading.textContent = isPaid ? "Your BC trip is booked" : "Booking received, payment pending";
    subheading.textContent = isPaid
      ? "Your planning session is confirmed. A summary is below."
      : "We have your booking on file, but payment hasn't completed yet.";

    if (booking) {
      summaryCard.style.display = "block";
      const packageRow = payment
        ? `<div class="summary-row"><span class="k">Package</span><span class="v">$${Number(payment.amount).toFixed(2)} ${payment.currency}</span></div>`
        : "";
      summaryBody.innerHTML = `
        <div class="summary-row"><span class="k">Booking</span><span class="v">#${booking.id}</span></div>
        <div class="summary-row"><span class="k">Traveler</span><span class="v">${booking.traveler_name}</span></div>
        <div class="summary-row"><span class="k">Destination</span><span class="v">${booking.destination}</span></div>
        <div class="summary-row"><span class="k">Trip date</span><span class="v">${booking.trip_date}</span></div>
        ${packageRow}
        <div class="summary-row"><span class="k">Payment status</span><span class="v"><span class="badge ${isPaid ? "completed" : "pending"}">${status}</span></span></div>
      `;
    }
  }

  (async () => {
    try {
      let status = "pending";

      if (demoSession) {
        const res = await fetch("/api/confirm-demo", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ demo_session: demoSession }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Could not confirm demo payment");
        status = data.status;
      }

      let latestPayment = null;
      if (bookingId) {
        const payRes = await fetch(`/api/bookings/${bookingId}/payments`);
        const paymentsList = await payRes.json();
        latestPayment = paymentsList[paymentsList.length - 1] || null;
        if (!demoSession) status = latestPayment ? latestPayment.status : "pending";
      }

      if (bookingId) {
        const bookingRes = await fetch(`/api/bookings/${bookingId}`);
        const booking = bookingRes.ok ? await bookingRes.json() : null;
        renderSummary(booking, status, latestPayment);
      } else {
        heading.textContent = "No booking found";
        subheading.textContent = "Start a new booking from the home page.";
      }
    } catch (err) {
      heading.textContent = "Something went wrong";
      subheading.textContent = err.message;
    }
  })();
}
