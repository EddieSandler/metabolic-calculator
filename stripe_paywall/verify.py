# stripe_paywall/verify.py

import stripe
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from stripe_paywall.config import STRIPE_SECRET_KEY, STRIPE_PRICE_ID

router = APIRouter()

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY


@router.get("/paywall/success")
def stripe_success(session_id: str = Query(...)):
    """
    Called by Stripe after a successful checkout.
    Verifies the session, sets an access cookie, and redirects to the calculator.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid session ID: {e}")

    # Basic sanity checks
    if session.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="Payment not completed")

    if session.get("mode") != "payment":
        raise HTTPException(status_code=400, detail="Unexpected session mode")

    # Optional: ensure our price was used (defensive)
    # This assumes you only have one line item and it's our PRICE_ID.
    try:
        line_items = stripe.checkout.Session.list_line_items(session.id, limit=1)
        price_id = line_items.data[0].price.id if line_items.data else None
    except Exception:
        price_id = None

    if STRIPE_PRICE_ID and price_id and price_id != STRIPE_PRICE_ID:
        raise HTTPException(status_code=400, detail="Unexpected product/price in session")

    # At this point, payment is good.
    # Grant access by setting a cookie and redirect to calculator home ("/").
    response = RedirectResponse(url="/")
    # 1 year access cookie — adjust if you want shorter
    response.set_cookie(
        key="calculator_access",
        value="granted",
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,  # 1 year
    )
    return response


@router.get("/paywall/cancel")
def stripe_cancel():
    """
    Called when user cancels on Stripe Checkout.
    Redirect back to paywall or show a simple message.
    """
    # For now just redirect back to the paywall.
    return RedirectResponse(url="/paywall")