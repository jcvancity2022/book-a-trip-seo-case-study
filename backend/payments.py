"""Payment processor abstraction for Book a Trip.

Wired for Stripe Checkout. When no Stripe keys are configured (the
default), every call runs in DEMO MODE: it returns a local confirmation
URL instead of a real Checkout Session, so the booking UI works
end-to-end with no real payment credentials involved anywhere.

To go live: set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in .env
(see .env.example) and `pip install stripe`. No route or template
changes are needed — app.py already calls through this module.
"""

import os
import uuid

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

try:
    import stripe as _stripe
except ImportError:
    _stripe = None

LIVE_MODE = bool(_stripe and STRIPE_SECRET_KEY)
if LIVE_MODE:
    _stripe.api_key = STRIPE_SECRET_KEY


def create_checkout_session(booking_id, amount, currency, description,
                             success_url, cancel_url):
    """Start a checkout. Returns {id, url, mode}.

    mode is "live" when a real Stripe session was created, or "demo"
    when standing in for one because no processor is configured yet.
    """
    if LIVE_MODE:
        session = _stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": description},
                    "unit_amount": int(round(amount * 100)),
                },
                "quantity": 1,
            }],
            metadata={"booking_id": str(booking_id)},
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"id": session.id, "url": session.url, "mode": "live"}

    demo_ref = f"demo_{uuid.uuid4().hex[:12]}"
    return {
        "id": demo_ref,
        "url": f"{success_url}?demo_session={demo_ref}&booking_id={booking_id}",
        "mode": "demo",
    }


def verify_webhook(payload, sig_header):
    """Verify + parse a Stripe webhook event.

    Returns None if webhooks aren't configured, the payload is malformed,
    or the signature doesn't check out -- callers treat None as "reject
    this request" rather than trusting an unverified body. Without this,
    a bad/missing signature raises inside construct_event and an
    unhandled exception 500s the route instead of cleanly rejecting it.
    """
    if not LIVE_MODE or not STRIPE_WEBHOOK_SECRET:
        return None
    try:
        return _stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, _stripe.error.SignatureVerificationError):
        return None
