"""Book a Trip - Flask app.

Serves the booking/checkout UI and a small JSON API backed by an
embedded SQLite database (auto-created on first run, no server to
install). Payment processing runs through payments.py, which is
prepared for Stripe but falls back to a demo flow until real keys
are configured.
"""

import os
from flask import Flask, request, jsonify, send_from_directory, Response
from dotenv import load_dotenv

import database as db
import payments

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

db.init_db()

TRIP_PACKAGES = {
    "self_guided": {
        "description": "Self-Guided Trip Checklist - British Columbia",
        "amount": 15.00,
        "currency": "CAD",
    },
    "full_session": {
        "description": "Full Planning Session - British Columbia",
        "amount": 49.00,
        "currency": "CAD",
    },
}
DEFAULT_PACKAGE = "self_guided"


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/confirmation")
def confirmation():
    return send_from_directory(FRONTEND_DIR, "confirmation.html")


@app.route("/destinations/british-columbia/weekend-trips-from-vancouver/")
def weekend_trips_from_vancouver():
    return send_from_directory(FRONTEND_DIR, "weekend-trips-from-vancouver.html")


@app.route("/destinations/british-columbia/vancouver-to-nanaimo-ferry/")
def vancouver_to_nanaimo_ferry():
    return send_from_directory(FRONTEND_DIR, "vancouver-to-nanaimo-ferry.html")


@app.route("/robots.txt")
def robots_txt():
    sitemap_url = request.host_url.rstrip("/") + "/sitemap.xml"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /api/",
        "Disallow: /research",
        "Disallow: /content-gap",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    # Only real, indexable pages go here. The confirmation page is
    # intentionally excluded -- it's a per-booking, query-string page
    # with a noindex tag, not something search engines should index.
    base = request.host_url.rstrip("/")
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <url><loc>{base}/</loc></url>",
        f"  <url><loc>{base}/destinations/british-columbia/weekend-trips-from-vancouver/</loc></url>",
        f"  <url><loc>{base}/destinations/british-columbia/vancouver-to-nanaimo-ferry/</loc></url>",
        "</urlset>",
    ]
    return Response("\n".join(xml), mimetype="application/xml")


@app.route("/research")
def research_tool():
    # Internal-only research log, not part of the public site: no nav link,
    # noindexed, and blocked in robots.txt. No auth -- don't deploy this
    # route publicly without adding some.
    return send_from_directory(FRONTEND_DIR, "research.html")


@app.route("/api/keywords", methods=["GET", "POST"])
def keyword_entries():
    if request.method == "GET":
        return jsonify(db.get_keyword_entries())

    data = request.get_json(force=True) or {}
    if not data.get("keyword", "").strip():
        return jsonify({"error": "keyword is required"}), 400
    try:
        entry_id = db.create_keyword_entry(**{
            k: v for k, v in data.items() if k in db.KEYWORD_FIELDS and v not in (None, "")
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(db.get_keyword_entry(entry_id)), 201


@app.route("/api/keywords/<int:entry_id>", methods=["GET", "PUT", "DELETE"])
def keyword_entry(entry_id):
    if request.method == "GET":
        entry = db.get_keyword_entry(entry_id)
        if not entry:
            return jsonify({"error": "Unknown entry"}), 404
        return jsonify(entry)

    if request.method == "DELETE":
        db.delete_keyword_entry(entry_id)
        return jsonify({"deleted": entry_id})

    data = request.get_json(force=True) or {}
    db.update_keyword_entry(entry_id, **{
        k: v for k, v in data.items() if k in db.KEYWORD_FIELDS
    })
    return jsonify(db.get_keyword_entry(entry_id))


@app.route("/content-gap")
def content_gap_tool():
    # Internal-only, same treatment as /research: no nav link, noindexed,
    # blocked in robots.txt, no auth -- don't deploy publicly as-is.
    return send_from_directory(FRONTEND_DIR, "content-gap.html")


@app.route("/api/content-gap", methods=["GET", "POST"])
def content_gap_entries():
    if request.method == "GET":
        project_page = request.args.get("project_page")
        return jsonify(db.get_content_gap_entries(project_page))

    data = request.get_json(force=True) or {}
    if not data.get("project_page", "").strip():
        return jsonify({"error": "project_page is required"}), 400
    if not data.get("keyword", "").strip():
        return jsonify({"error": "keyword is required"}), 400
    try:
        entry_id = db.create_content_gap_entry(**{
            k: v for k, v in data.items() if k in db.CONTENT_GAP_FIELDS and v not in (None, "")
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(db.get_content_gap_entry(entry_id)), 201


@app.route("/api/content-gap/<int:entry_id>", methods=["GET", "PUT", "DELETE"])
def content_gap_entry(entry_id):
    if request.method == "GET":
        entry = db.get_content_gap_entry(entry_id)
        if not entry:
            return jsonify({"error": "Unknown entry"}), 404
        return jsonify(entry)

    if request.method == "DELETE":
        db.delete_content_gap_entry(entry_id)
        return jsonify({"deleted": entry_id})

    data = request.get_json(force=True) or {}
    db.update_content_gap_entry(entry_id, **{
        k: v for k, v in data.items() if k in db.CONTENT_GAP_FIELDS
    })
    return jsonify(db.get_content_gap_entry(entry_id))


@app.route("/api/packages")
def list_packages():
    # Single source of truth for pricing -- the frontend reads this rather
    # than hardcoding amounts, so there's one place to change a price.
    return jsonify({key: pkg for key, pkg in TRIP_PACKAGES.items()})


@app.route("/api/bookings", methods=["POST"])
def create_booking():
    data = request.get_json(force=True) or {}
    required = ["traveler_name", "email", "destination", "trip_date"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    booking_id = db.create_booking(
        data["traveler_name"], data["email"], data["destination"], data["trip_date"]
    )
    return jsonify({"booking_id": booking_id}), 201


@app.route("/api/checkout", methods=["POST"])
def start_checkout():
    data = request.get_json(force=True) or {}
    booking_id = data.get("booking_id")
    if not booking_id or not db.get_booking(booking_id):
        return jsonify({"error": "Unknown booking_id"}), 400

    # Look up the price server-side by key -- never trust a client-submitted
    # amount, even in demo mode.
    package_key = data.get("package", DEFAULT_PACKAGE)
    package = TRIP_PACKAGES.get(package_key)
    if not package:
        return jsonify({"error": "Unknown package"}), 400

    success_url = request.host_url.rstrip("/") + "/confirmation"
    cancel_url = request.host_url.rstrip("/") + "/"

    session = payments.create_checkout_session(
        booking_id=booking_id,
        amount=package["amount"],
        currency=package["currency"],
        description=package["description"],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    db.record_payment(
        booking_id=booking_id,
        amount=package["amount"],
        method="card",
        currency=package["currency"],
        status="pending",
        transaction_ref=session["id"],
    )

    return jsonify(session)


@app.route("/api/confirm-demo", methods=["POST"])
def confirm_demo():
    """Demo-mode only: marks a demo payment completed. Real payments are
    confirmed via /api/webhook/stripe instead, never by the client."""
    data = request.get_json(force=True) or {}
    demo_session = data.get("demo_session", "")
    if not demo_session.startswith("demo_"):
        return jsonify({"error": "Not a demo session"}), 400

    payment = db.get_payment_by_transaction_ref(demo_session)
    if not payment:
        return jsonify({"error": "Unknown session"}), 404

    db.update_payment_status(demo_session, "completed")
    return jsonify({"status": "completed"})


@app.route("/api/bookings/<int:booking_id>")
def get_booking(booking_id):
    booking = db.get_booking(booking_id)
    if not booking:
        return jsonify({"error": "Unknown booking_id"}), 404
    return jsonify(booking)


@app.route("/api/bookings/<int:booking_id>/payments")
def list_payments(booking_id):
    return jsonify(db.get_payments_for_booking(booking_id))


@app.route("/api/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")
    event = payments.verify_webhook(payload, sig_header)
    if event is None:
        return jsonify({"error": "Webhook not configured or invalid"}), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        db.update_payment_status(session["id"], "completed")

    return jsonify({"received": True})


@app.errorhandler(404)
def not_found(_error):
    return send_from_directory(FRONTEND_DIR, "404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5090)
